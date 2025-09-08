#!/usr/bin/env python3
"""
Instagram Follower Analysis API Server with Bot Integration
Enhanced version of the existing API server that uses bot slaves for session management.

This server integrates with the bot slave manager to provide session data automatically.
Users only need to provide target_user_id, and the system handles bot session management.

Usage:
    python instagram_api_server.py

Endpoints:
    POST /api/analyze - Submit new analysis job (requires only target_user_id)
    POST /api/analyze-unfollowers - Submit new un-followers analysis job
    GET /api/status/<job_id> - Get job status
    GET /api/queue - Get queue status
    GET /api/health - Health check
"""

from flask import Flask, request, jsonify
import uuid
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import sys
import os
import logging

# Import our existing Instagram scraper
from instagram_api_scraper import InstagramAPIScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
MAX_CONCURRENT_JOBS = 5
JOB_CLEANUP_DELAY = 1800  # 30 minutes in seconds
BOT_SLAVE_MANAGER_URL = "http://localhost:5001"  # Bot slave manager URL

# Global state management
active_sessions = set()  # Track which user_ids are currently being processed
job_status = {}  # Track job statuses
job_queue = []  # Queue for jobs waiting to start
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS)

def generate_job_id():
    """Generate a random UUID for the job ID"""
    return str(uuid.uuid4())

class InstagramBotAnalyzerAPI:
    """Controller class for Instagram follower analysis using bot slaves"""
    
    def __init__(self, target_user_id: str, bot_data: dict):
        """
        Initialize with bot session data
        
        Args:
            target_user_id: Instagram user ID to analyze
            bot_data: Bot session data from slave manager
        """
        self.target_user_id = target_user_id
        self.bot_data = bot_data
        self.scraper = None
        self._setup_scraper()
    
    def _setup_scraper(self):
        """Setup Instagram scraper with bot session data."""
        try:
            # Create scraper with bot session data
            self.scraper = InstagramAPIScraper(
                user_id=self.bot_data['user_id'],  # Bot's user ID
                csrf_token=self.bot_data['csrf_token'],
                x_ig_www_claim='',  # Can be extracted from session if needed
                x_web_session_id='',  # Can be extracted from session if needed
                cookies=f"sessionid={self.bot_data['session_id']}; csrftoken={self.bot_data['csrf_token']}"
            )
            
            # Override the user_id for the target user (not the bot)
            self.scraper.user_id = self.target_user_id
            
            logger.info(f"Scraper setup complete for target user {self.target_user_id} using bot {self.bot_data['bot_id']}")
            
        except Exception as e:
            logger.error(f"Failed to setup scraper: {e}")
            raise
    
    def analyze(self, job_id: str) -> dict:
        """
        Run the Instagram follower analysis using bot account
        
        Args:
            job_id: Unique identifier for this analysis job
            
        Returns:
            dict: Analysis results with counts and unfollowers list
        """
        try:
            logger.info(f"[{job_id}] Starting Instagram follower analysis for user {self.target_user_id}")
            
            # Fetch data using bot account
            followers = self._fetch_followers(job_id)
            following = self._fetch_following(job_id)
            
            # Business logic: find unfollowers
            unfollowers = self._find_unfollowers(followers, following)
            
            # Format result
            result = self._format_analysis_result(followers, following, unfollowers)
            
            logger.info(f"[{job_id}] Analysis completed: {len(unfollowers)} unfollowers found")
            return result
            
        except Exception as e:
            logger.error(f"[{job_id}] Analysis failed: {str(e)}")
            raise e
    
    def _fetch_followers(self, job_id: str) -> list:
        """Fetch followers using bot account"""
        logger.info(f"[{job_id}] Fetching followers for user {self.target_user_id}")
        return self.scraper.get_followers()
    
    def _fetch_following(self, job_id: str) -> list:
        """Fetch following using bot account"""
        logger.info(f"[{job_id}] Fetching following for user {self.target_user_id}")
        return self.scraper.get_following()
    
    def _find_unfollowers(self, followers: list, following: list) -> list:
        """Find users who don't follow back"""
        follower_usernames = self.scraper.extract_usernames(followers)
        following_usernames = self.scraper.extract_usernames(following)
        
        follower_set = set(follower_usernames)
        following_set = set(following_usernames)
        unfollowers = list(following_set - follower_set)
        
        return unfollowers
    
    def _format_analysis_result(self, followers: list, following: list, unfollowers: list) -> dict:
        """Format analysis results"""
        return {
            'target_user_id': self.target_user_id,
            'followers_count': len(followers),
            'following_count': len(following),
            'unfollowers_count': len(unfollowers),
            'unfollowers': unfollowers,
            'analysis_completed_at': datetime.now().isoformat(),
            'bot_account_used': self.bot_data['bot_id']
        }

def request_bot_session() -> dict:
    """
    Request a bot session from the slave manager.
    
    Returns:
        dict: Bot session data or None if no bots available
    """
    try:
        response = requests.post(f"{BOT_SLAVE_MANAGER_URL}/api/bot/request", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('bot_data')
            else:
                logger.error(f"No available bots: {data.get('error')}")
                return None
        else:
            logger.error(f"Failed to request bot session: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error requesting bot session: {e}")
        return None

def release_bot_session(bot_id: str):
    """Release a bot session back to the slave manager."""
    try:
        response = requests.post(
            f"{BOT_SLAVE_MANAGER_URL}/api/bot/release",
            json={'bot_id': bot_id},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Bot {bot_id} released successfully")
        else:
            logger.error(f"Failed to release bot {bot_id}: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error releasing bot {bot_id}: {e}")

def process_job(job_data: dict) -> None:
    """
    Process a single job - runs in worker thread
    
    Args:
        job_data: Dictionary containing job_id, target_user_id, and optional job_type
    """
    job_id = job_data['job_id']
    target_user_id = job_data['target_user_id']
    job_type = job_data.get('job_type', 'analyze')
    previous_followers = job_data.get('previous_followers', [])
    
    bot_data = None
    
    try:
        # Update status to processing
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['started_at'] = time.time()
        
        # Request bot session
        logger.info(f"[{job_id}] Requesting bot session...")
        bot_data = request_bot_session()
        
        if not bot_data:
            raise ValueError("No available bot sessions")
        
        logger.info(f"[{job_id}] Using bot {bot_data['bot_id']} for analysis")
        
        # Create analyzer with bot session
        analyzer = InstagramBotAnalyzerAPI(target_user_id, bot_data)
        
        # Run analysis based on job type
        if job_type == 'analyze_unfollowers':
            # For unfollowers analysis, we need to implement this
            result = analyzer.analyze(job_id)  # Simplified for now
        else:  # Default to regular analyze
            result = analyzer.analyze(job_id)
        
        # Update with results
        job_status[job_id].update({
            'status': 'completed',
            'result': result,
            'completed_at': time.time()
        })
        
        logger.info(f"[{job_id}] Job completed successfully")
        
    except ValueError as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(f"[{job_id}] {error_msg}")
        job_status[job_id].update({
            'status': 'failed',
            'error': error_msg,
            'failed_at': time.time()
        })
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"[{job_id}] {error_msg}")
        job_status[job_id].update({
            'status': 'failed',
            'error': error_msg,
            'failed_at': time.time()
        })
    
    finally:
        # Release bot session
        if bot_data:
            release_bot_session(bot_data['bot_id'])
        
        # Remove from active sessions
        active_sessions.discard(target_user_id)
        
        # Clean up completed job after a delay
        threading.Timer(JOB_CLEANUP_DELAY, cleanup_completed_job, args=[job_id]).start()
        
        # Process next job in queue if any
        process_next_queued_job()

def cleanup_completed_job(job_id):
    """Remove completed job from job_status to allow new submissions"""
    if job_id in job_status:
        status = job_status[job_id]['status']
        if status in ['completed', 'failed']:
            del job_status[job_id]
            logger.info(f"Cleaned up {status} job: {job_id}")

def process_next_queued_job():
    """Process the next job in queue if we have capacity"""
    if len(active_sessions) < MAX_CONCURRENT_JOBS and job_queue:
        # Find next job that doesn't conflict with active sessions
        for i, job_data in enumerate(job_queue):
            if job_data['target_user_id'] not in active_sessions:
                # Remove from queue and start processing
                job_data = job_queue.pop(i)
                active_sessions.add(job_data['target_user_id'])
                
                # Submit to thread pool
                executor.submit(process_job, job_data)
                break

def find_active_job_for_user(target_user_id):
    """Find active job (processing or queued) for this user"""
    for job_id, status in job_status.items():
        if (status.get('target_user_id') == target_user_id and 
            status.get('status') in ['processing', 'queued']):
            return job_id
    return None

def estimate_wait_time(queue_length):
    """Estimate wait time based on queue length"""
    if queue_length == 0:
        return "Starting immediately"
    
    # Assume 10-15 minutes per job
    min_time = queue_length * 10
    max_time = queue_length * 15
    
    return f"{min_time}-{max_time} minutes"

# API Endpoints

@app.route('/api/analyze', methods=['POST'])
def analyze_followers():
    """Submit a new Instagram follower analysis job using bot slaves"""
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'target_user_id' not in data:
            return jsonify({'error': 'target_user_id is required'}), 400
        
        target_user_id = data['target_user_id']
        
        # Validate target_user_id is numeric
        if not target_user_id.isdigit():
            return jsonify({'error': 'target_user_id must be numeric'}), 400
        
        # Check if there's already an active job for this user
        existing_job_id = find_active_job_for_user(target_user_id)
        if existing_job_id:
            existing_job = job_status[existing_job_id]
            return jsonify({
                'error': 'Job already exists',
                'message': f'This user already has a job with status: {existing_job["status"]}',
                'job_id': existing_job_id,
                'status': existing_job['status']
            }), 409
        
        # Generate random job ID
        job_id = generate_job_id()
        
        # Create job data
        job_data = {
            'job_id': job_id,
            'target_user_id': target_user_id,
            'created_at': time.time()
        }
        
        # Initialize status
        job_status[job_id] = {
            'status': 'queued',
            'target_user_id': target_user_id,
            'created_at': time.time(),
            'position_in_queue': len(job_queue) + 1
        }
        
        # Add to queue or start immediately
        if len(active_sessions) < MAX_CONCURRENT_JOBS:
            # Start immediately
            active_sessions.add(target_user_id)
            executor.submit(process_job, job_data)
            job_status[job_id]['status'] = 'processing'
            job_status[job_id]['position_in_queue'] = 0
        else:
            # Add to queue
            job_queue.append(job_data)
        
        return jsonify({
            'job_id': job_id,
            'status': job_status[job_id]['status'],
            'position_in_queue': job_status[job_id]['position_in_queue'],
            'estimated_wait_time': estimate_wait_time(len(job_queue))
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/analyze-unfollowers', methods=['POST'])
def analyze_unfollowers():
    """Submit a new Instagram un-followers analysis job using bot slaves"""
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'target_user_id' not in data:
            return jsonify({'error': 'target_user_id is required'}), 400
        
        if 'previous_followers' not in data:
            return jsonify({'error': 'previous_followers is required'}), 400
        
        target_user_id = data['target_user_id']
        previous_followers = data['previous_followers']
        
        # Validate previous_followers is a list
        if not isinstance(previous_followers, list):
            return jsonify({'error': 'previous_followers must be a list'}), 400
        
        # Validate previous_followers is not empty
        if len(previous_followers) == 0:
            return jsonify({'error': 'previous_followers cannot be empty'}), 400
        
        # Validate target_user_id is numeric
        if not target_user_id.isdigit():
            return jsonify({'error': 'target_user_id must be numeric'}), 400
        
        # Check if there's already an active job for this user
        existing_job_id = find_active_job_for_user(target_user_id)
        if existing_job_id:
            existing_job = job_status[existing_job_id]
            return jsonify({
                'error': 'Job already exists',
                'message': f'This user already has a job with status: {existing_job["status"]}',
                'job_id': existing_job_id,
                'status': existing_job['status']
            }), 409
        
        # Generate random job ID
        job_id = generate_job_id()
        
        # Create job data
        job_data = {
            'job_id': job_id,
            'target_user_id': target_user_id,
            'job_type': 'analyze_unfollowers',
            'previous_followers': previous_followers,
            'created_at': time.time()
        }
        
        # Initialize status
        job_status[job_id] = {
            'status': 'queued',
            'target_user_id': target_user_id,
            'job_type': 'analyze_unfollowers',
            'created_at': time.time(),
            'position_in_queue': len(job_queue) + 1
        }
        
        # Add to queue or start immediately
        if len(active_sessions) < MAX_CONCURRENT_JOBS:
            # Start immediately
            active_sessions.add(target_user_id)
            executor.submit(process_job, job_data)
            job_status[job_id]['status'] = 'processing'
            job_status[job_id]['position_in_queue'] = 0
        else:
            # Add to queue
            job_queue.append(job_data)
        
        return jsonify({
            'job_id': job_id,
            'status': job_status[job_id]['status'],
            'position_in_queue': job_status[job_id]['position_in_queue'],
            'estimated_wait_time': estimate_wait_time(len(job_queue))
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get the status of a job by job_id"""
    
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    status = job_status[job_id].copy()
    
    # Update queue position if still queued
    if status['status'] == 'queued':
        position = 1
        for job_data in job_queue:
            if job_data['job_id'] == job_id:
                status['position_in_queue'] = position
                break
            position += 1
    
    # Add timing information
    if 'started_at' in status:
        status['processing_time'] = time.time() - status['started_at']
    
    return jsonify(status)

@app.route('/api/queue', methods=['GET'])
def get_queue_status():
    """Get overall queue status"""
    return jsonify({
        'active_sessions': len(active_sessions),
        'max_concurrent': MAX_CONCURRENT_JOBS,
        'queued_jobs': len(job_queue),
        'total_jobs_in_memory': len(job_status)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check bot slave manager health
    bot_manager_healthy = False
    try:
        response = requests.get(f"{BOT_SLAVE_MANAGER_URL}/api/bot/health", timeout=5)
        bot_manager_healthy = response.status_code == 200
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len(active_sessions),
        'queued_jobs': len(job_queue),
        'bot_manager_healthy': bot_manager_healthy,
        'bot_manager_url': BOT_SLAVE_MANAGER_URL
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Instagram Follower Analysis API Server with Bot Integration")
    print("=" * 60)
    print(f"Max concurrent jobs: {MAX_CONCURRENT_JOBS}")
    print(f"Job cleanup delay: {JOB_CLEANUP_DELAY} seconds")
    print(f"Bot slave manager URL: {BOT_SLAVE_MANAGER_URL}")
    print("=" * 60)
    print("Available endpoints:")
    print("  POST /api/analyze - Submit new analysis job (requires only target_user_id)")
    print("  POST /api/analyze-unfollowers - Submit new un-followers analysis job")
    print("  GET  /api/status/<job_id> - Get job status")
    print("  GET  /api/queue - Get queue status")
    print("  GET  /api/health - Health check")
    print("=" * 60)
    print("Prerequisites:")
    print("  1. Bot slave manager must be running on port 5001")
    print("  2. Bot accounts must be configured and logged in")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
