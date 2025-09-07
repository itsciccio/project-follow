#!/usr/bin/env python3
"""
Instagram Follower Analysis API Server

A Flask API that processes Instagram follower analysis jobs.
Supports multiple concurrent users with one job per session.

Usage:
    python instagram_api_server.py

Endpoints:
    POST /api/analyze - Submit new analysis job
    GET /api/status/<job_id> - Get job status
    GET /api/queue - Get queue status
    GET /api/health - Health check
"""

from flask import Flask, request, jsonify
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
import sys
import os

# Import our existing Instagram scraper
from instagram_api_scraper import InstagramAPIScraper

app = Flask(__name__)

# Configuration
MAX_CONCURRENT_JOBS = 5
JOB_CLEANUP_DELAY = 1800  # 30 minutes in seconds

# Global state management
active_sessions = set()  # Track which session_ids are currently being processed
job_status = {}  # Track job statuses
job_queue = []  # Queue for jobs waiting to start
executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_JOBS)

def generate_job_id():
    """Generate a random UUID for the job ID"""
    return str(uuid.uuid4())

class InstagramAnalyzerAPI:
    def __init__(self, csrf_token, session_id):
        self.csrf_token = csrf_token
        self.session_id = session_id
    
    def analyze(self, job_id):
        """Run the Instagram follower analysis"""
        try:
            # Extract user_id from session_id
            user_id = self.extract_user_id_from_session(self.session_id)
            
            if not user_id:
                raise ValueError("Could not extract user_id from session")
            
            # Create scraper instance
            scraper = InstagramAPIScraper(
                user_id=user_id,
                csrf_token=self.csrf_token,
                cookies=f"sessionid={self.session_id}"
            )
            
            # Fetch followers and following
            print(f"[{job_id}] Starting follower analysis...")
            followers = scraper.get_followers()
            
            print(f"[{job_id}] Starting following analysis...")
            following = scraper.get_following()
            
            # Extract usernames
            follower_usernames = scraper.extract_usernames(followers)
            following_usernames = scraper.extract_usernames(following)
            
            # Find users not following back
            follower_set = set(follower_usernames)
            following_set = set(following_usernames)
            unfollowers = list(following_set - follower_set)
            
            result = {
                'followers_count': len(followers),
                'following_count': len(following),
                'unfollowers_count': len(unfollowers),
                'unfollowers': unfollowers,
                'analysis_completed_at': datetime.now().isoformat()
            }
            
            print(f"[{job_id}] Analysis completed: {len(unfollowers)} unfollowers found")
            return result
            
        except Exception as e:
            print(f"[{job_id}] Analysis failed: {str(e)}")
            raise e
    
    @staticmethod
    def extract_user_id_from_session(session_id):
        """Extract user ID from session ID (everything before the first %)"""
        try:
            user_id = session_id.split('%')[0]
            if user_id.isdigit():
                return user_id
            else:
                return None
        except:
            return None

def process_job(job_data):
    """Process a single job - runs in worker thread"""
    job_id = job_data['job_id']
    session_id = job_data['session_id']
    
    try:
        # Update status to processing
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['started_at'] = time.time()
        
        # Create analyzer and run
        analyzer = InstagramAnalyzerAPI(
            job_data['csrf_token'], 
            job_data['session_id']
        )
        result = analyzer.analyze(job_id)
        
        # Update with results
        job_status[job_id].update({
            'status': 'completed',
            'result': result,
            'completed_at': time.time()
        })
        
    except Exception as e:
        job_status[job_id].update({
            'status': 'failed',
            'error': str(e),
            'failed_at': time.time()
        })
    
    finally:
        # Remove from active sessions
        active_sessions.discard(session_id)
        
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
            print(f"Cleaned up {status} job: {job_id}")

def process_next_queued_job():
    """Process the next job in queue if we have capacity"""
    if len(active_sessions) < MAX_CONCURRENT_JOBS and job_queue:
        # Find next job that doesn't conflict with active sessions
        for i, job_data in enumerate(job_queue):
            if job_data['session_id'] not in active_sessions:
                # Remove from queue and start processing
                job_data = job_queue.pop(i)
                active_sessions.add(job_data['session_id'])
                
                # Submit to thread pool
                executor.submit(process_job, job_data)
                break

def find_active_job_for_session(session_id):
    """Find active job (processing or queued) for this session"""
    for job_id, status in job_status.items():
        if (status.get('session_id') == session_id and 
            status.get('status') in ['processing', 'queued']):
            return job_id
    
    return None

def find_job_for_session(session_id):
    """Find any job (any status) for this session"""
    for job_id, status in job_status.items():
        if status.get('session_id') == session_id:
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
    """Submit a new Instagram follower analysis job"""
    try:
        data = request.json
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'csrf_token' not in data:
            return jsonify({'error': 'csrf_token is required'}), 400
        
        if 'session_id' not in data:
            return jsonify({'error': 'session_id is required'}), 400
        
        session_id = data['session_id']
        csrf_token = data['csrf_token']
        
        # Extract user_id from session_id
        user_id = InstagramAnalyzerAPI.extract_user_id_from_session(session_id)
        if not user_id:
            return jsonify({'error': 'Could not extract user_id from session_id'}), 400
        
        # Check if there's already any job for this session (any status)
        existing_job_id = find_job_for_session(session_id)
        if existing_job_id:
            existing_job = job_status[existing_job_id]
            return jsonify({
                'error': 'Job already exists',
                'message': f'This account already has a job with status: {existing_job["status"]}',
                'job_id': existing_job_id,
                'status': existing_job['status']
            }), 409
        
        # Generate random job ID
        job_id = generate_job_id()
        
        # Create job data
        job_data = {
            'job_id': job_id,
            'csrf_token': csrf_token,
            'session_id': session_id,
            'created_at': time.time()
        }
        
        # Initialize status
        job_status[job_id] = {
            'status': 'queued',
            'session_id': session_id,
            'user_id': user_id,  # Store extracted user_id for reference
            'created_at': time.time(),
            'position_in_queue': len(job_queue) + 1
        }
        
        # Add to queue or start immediately
        if len(active_sessions) < MAX_CONCURRENT_JOBS:
            # Start immediately
            active_sessions.add(session_id)
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
    """Get the status of a job by job_id (generated from csrf_token:session_id)"""
    
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    status = job_status[job_id].copy()
    
    # Remove sensitive data
    status.pop('session_id', None)
    status.pop('csrf_token', None)
    
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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_jobs': len(active_sessions),
        'queued_jobs': len(job_queue)
    })

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all current jobs (for debugging)"""
    jobs = {}
    for job_id, status in job_status.items():
        jobs[job_id] = {
            'status': status['status'],
            'created_at': status.get('created_at', 0),
            'position_in_queue': status.get('position_in_queue', 0)
        }
    
    return jsonify({
        'jobs': jobs,
        'total_jobs': len(jobs),
        'active_sessions_count': len(active_sessions),
        'queue_length': len(job_queue)
    })

@app.route('/api/debug/<job_id>', methods=['GET'])
def debug_job(job_id):
    """Debug endpoint to check job status with more details"""
    if job_id not in job_status:
        return jsonify({
            'error': 'Job not found',
            'job_id': job_id,
            'total_jobs': len(job_status),
            'all_job_ids': list(job_status.keys()),
            'active_sessions_count': len(active_sessions),
            'queue_length': len(job_queue)
        }), 404
    
    job_info = job_status[job_id].copy()
    
    # Remove sensitive data
    job_info.pop('session_id', None)
    job_info.pop('csrf_token', None)
    
    if 'started_at' in job_info:
        job_info['processing_time'] = time.time() - job_info['started_at']
    
    return jsonify(job_info)

@app.route('/api/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually clean up completed jobs (for testing)"""
    cleaned_count = 0
    for job_id in list(job_status.keys()):
        status = job_status[job_id]['status']
        if status in ['completed', 'failed']:
            del job_status[job_id]
            cleaned_count += 1
    
    return jsonify({
        'message': f'Cleaned up {cleaned_count} completed jobs',
        'remaining_jobs': len(job_status)
    })

@app.route('/api/job/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a specific job by ID"""
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404
    
    job_info = job_status[job_id]
    job_status_value = job_info['status']
    session_id = job_info.get('session_id')
    
    # Check if job is currently active (processing or queued)
    if job_status_value in ['processing', 'queued']:
        return jsonify({
            'error': 'Cannot delete active job',
            'message': 'Job is currently processing or queued. Wait for completion or stop the job first.',
            'job_status': job_status_value
        }), 409
    
    # Remove from active sessions if it was there
    if session_id in active_sessions:
        active_sessions.discard(session_id)
    
    # Remove from queue if it was there
    for i, queued_job in enumerate(job_queue):
        if queued_job['job_id'] == job_id:
            job_queue.pop(i)
            break
    
    # Delete the job
    del job_status[job_id]
    
    return jsonify({
        'message': f'Job {job_id} deleted successfully',
        'deleted_job_status': job_status_value,
        'remaining_jobs': len(job_status)
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
    print("Instagram Follower Analysis API Server")
    print("=" * 60)
    print(f"Max concurrent jobs: {MAX_CONCURRENT_JOBS}")
    print(f"Job cleanup delay: {JOB_CLEANUP_DELAY} seconds")
    print("=" * 60)
    print("Available endpoints:")
    print("  POST /api/analyze - Submit new analysis job")
    print("  GET  /api/status/<job_id> - Get job status")
    print("  GET  /api/debug/<job_id> - Debug job with detailed info")
    print("  GET  /api/queue - Get queue status")
    print("  GET  /api/health - Health check")
    print("  GET  /api/jobs - List all jobs (debug)")
    print("  POST /api/cleanup - Clean up completed jobs")
    print("  DELETE /api/job/<job_id> - Delete specific job by job_id")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
