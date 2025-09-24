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
    POST /api/analyze-not-following-back - Submit new not-following-back analysis job
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

# Removed unused InstagramBotAnalyzerAPI class - all analysis is delegated to bot manager

def submit_job_to_bot_manager(job_data: dict) -> dict:
    """
    Submit a job to the bot manager queue system.
    
    Args:
        job_data: Dictionary containing job information
        
    Returns:
        dict: Job submission result with job_id and queue position
    """
    try:
        response = requests.post(f"{BOT_SLAVE_MANAGER_URL}/api/job/submit", 
                               json=job_data, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to submit job: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error submitting job: {e}")
        return None

def get_job_status_from_bot_manager(job_id: str) -> dict:
    """
    Get job status from the bot manager.
    
    Args:
        job_id: Job identifier
        
    Returns:
        dict: Job status information
    """
    try:
        response = requests.get(f"{BOT_SLAVE_MANAGER_URL}/api/job/status/{job_id}", timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get job status: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting job status: {e}")
        return None

def complete_job_in_bot_manager(job_id: str):
    """
    Mark a job as completed in the bot manager.
    
    Args:
        job_id: Job identifier
    """
    try:
        response = requests.post(f"{BOT_SLAVE_MANAGER_URL}/api/job/complete", 
                               json={'job_id': job_id}, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to complete job: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error completing job: {e}")

# Bot session management is now handled entirely by the bot manager
# The API server only submits jobs and receives results

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
        # Job is already submitted to bot manager queue
        # The bot manager will handle bot assignment and processing internally
        logger.info(f"[{job_id}] Job submitted to bot manager queue")
        
        # Poll bot manager for job status and completion
        max_wait_time = 300  # 5 minutes max wait
        wait_start = time.time()
        processing_started = False
        
        while time.time() - wait_start < max_wait_time:
            # Check job status in bot manager
            bot_status = get_job_status_from_bot_manager(job_id)
            logger.info(f"[{job_id}] Bot manager status: {bot_status}")
            
            if bot_status:
                bot_status_type = bot_status.get('status')
                
                # Update local status based on bot manager status
                if bot_status_type == 'queued':
                    job_status[job_id]['status'] = 'queued'
                    job_status[job_id]['position_in_queue'] = bot_status.get('position_in_queue', 0)
                    job_status[job_id]['estimated_wait_time'] = bot_status.get('estimated_wait_time', 0)
                elif bot_status_type == 'processing' and not processing_started:
                    # Job just started processing
                    job_status[job_id]['status'] = 'processing'
                    job_status[job_id]['started_at'] = time.time()
                    job_status[job_id]['assigned_bot'] = bot_status.get('assigned_bot')
                    processing_started = True
                    logger.info(f"[{job_id}] Job started processing by bot {bot_status.get('assigned_bot')}")
                elif bot_status_type in ['completed', 'failed']:
                    if bot_status_type == 'completed':
                        result = bot_status.get('result', {})
                        logger.info(f"[{job_id}] Job completed by bot manager")
                    else:
                        error_msg = bot_status.get('error', 'Unknown error')
                        logger.error(f"[{job_id}] Job failed in bot manager: {error_msg}")
                        raise ValueError(f"Bot manager error: {error_msg}")
                    break
            
            time.sleep(2)  # Wait 2 seconds before checking again
        else:
            raise ValueError("Job did not complete within timeout period")
        
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
        # Mark job as completed in bot manager
        complete_job_in_bot_manager(job_id)
        
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
        previous_followers = data.get('previous_followers', None)  # Optional
        
        # Validate target_user_id is numeric
        if not target_user_id.isdigit():
            return jsonify({'error': 'target_user_id must be numeric'}), 400
        
        # Validate previous_followers if provided
        if previous_followers is not None:
            if not isinstance(previous_followers, list):
                return jsonify({'error': 'previous_followers must be a list'}), 400
            
            if len(previous_followers) == 0:
                return jsonify({'error': 'previous_followers cannot be empty'}), 400
        
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
            'job_type': 'analyze',
            'created_at': time.time()
        }
        
        # Add optional previous_followers if provided
        if previous_followers is not None:
            job_data['previous_followers'] = previous_followers
        
        # Submit job to bot manager queue
        bot_manager_result = submit_job_to_bot_manager(job_data)
        if not bot_manager_result:
            return jsonify({'error': 'Failed to submit job to bot manager'}), 500
        
        # Initialize status in API server
        job_status[job_id] = {
            'status': 'queued',
            'target_user_id': target_user_id,
            'job_type': 'analyze',
            'created_at': time.time(),
            'position_in_queue': bot_manager_result.get('position_in_queue', 1)
        }
        
        # Add to local queue and process next job if capacity available
        job_queue.append(job_data)
        process_next_queued_job()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'position_in_queue': bot_manager_result.get('position_in_queue', 1),
            'estimated_wait_time': bot_manager_result.get('estimated_wait_time', 0)
        })
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/analyze-not-following-back', methods=['POST'])
def analyze_not_following_back():
    """Submit a new Instagram not-following-back analysis job using bot slaves"""
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
            'job_type': 'analyze_not_following_back',
            'created_at': time.time()
        }
        
        # Submit job to bot manager queue
        bot_manager_result = submit_job_to_bot_manager(job_data)
        if not bot_manager_result:
            return jsonify({'error': 'Failed to submit job to bot manager'}), 500
        
        # Initialize status in API server
        job_status[job_id] = {
            'status': 'queued',
            'target_user_id': target_user_id,
            'job_type': 'analyze_not_following_back',
            'created_at': time.time(),
            'position_in_queue': bot_manager_result.get('position_in_queue', 1)
        }
        
        # Add to local queue and process next job if capacity available
        job_queue.append(job_data)
        process_next_queued_job()
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'position_in_queue': bot_manager_result.get('position_in_queue', 1),
            'estimated_wait_time': bot_manager_result.get('estimated_wait_time', 0)
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
    """Get overall queue status from bot manager"""
    try:
        # Get real status from bot manager
        response = requests.get(f"{BOT_SLAVE_MANAGER_URL}/api/queue/status", timeout=5)
        if response.status_code == 200:
            bot_manager_status = response.json()
            return jsonify({
                'active_sessions': bot_manager_status.get('active_jobs', 0),
                'max_concurrent': MAX_CONCURRENT_JOBS,
                'queued_jobs': bot_manager_status.get('queue_length', 0),
                'total_jobs_in_memory': len(job_status),
                'available_bots': bot_manager_status.get('available_bots', 0),
                'total_bots': bot_manager_status.get('total_bots', 0)
            })
        else:
            # Fallback to local status if bot manager is unavailable
            return jsonify({
                'active_sessions': len(active_sessions),
                'max_concurrent': MAX_CONCURRENT_JOBS,
                'queued_jobs': len(job_queue),
                'total_jobs_in_memory': len(job_status),
                'error': 'Bot manager unavailable'
            })
    except Exception as e:
        # Fallback to local status if bot manager is unavailable
        return jsonify({
            'active_sessions': len(active_sessions),
            'max_concurrent': MAX_CONCURRENT_JOBS,
            'queued_jobs': len(job_queue),
            'total_jobs_in_memory': len(job_status),
            'error': f'Bot manager connection failed: {str(e)}'
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
    print("  POST /api/analyze - Submit new follower analysis job")
    print("  POST /api/analyze-not-following-back - Submit new not-following-back analysis job")
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
