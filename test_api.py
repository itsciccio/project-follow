#!/usr/bin/env python3
"""
Test script for Instagram API Server

This script helps you test the API endpoints locally.
"""

import requests
import json
import time
import sys

API_BASE_URL = "http://localhost:5000"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_queue_status():
    """Test the queue status endpoint"""
    print("\nTesting queue status...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/queue")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def submit_test_job():
    """Submit a test job"""
    print("\nSubmitting test job...")
    
    # You'll need to replace these with real values
    test_data = {
        "csrf_token": "YOUR_CSRF_TOKEN_HERE",
        "session_id": "YOUR_SESSION_ID_HERE"
    }
    
    print("Test data (replace with real values):")
    print(json.dumps(test_data, indent=2))
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            job_id = response.json().get('job_id')
            return job_id
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_job_status(job_id):
    """Check the status of a job"""
    print(f"\nChecking status for job: {job_id}")
    try:
        response = requests.get(f"{API_BASE_URL}/api/status/{job_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def list_all_jobs():
    """List all current jobs"""
    print("\nListing all jobs...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/jobs")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def cleanup_jobs():
    """Clean up completed jobs"""
    print("\nCleaning up completed jobs...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/cleanup")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("Instagram API Server Test Script")
    print("=" * 50)
    
    # Test basic endpoints
    if not test_health():
        print("Health check failed. Is the server running?")
        return
    
    test_queue_status()
    list_all_jobs()
    
    # Interactive job submission
    print("\n" + "=" * 50)
    print("To submit a real job, you need to:")
    print("1. Get your Instagram credentials (csrf_token, session_id, user_id)")
    print("2. Replace the values in the test_data in submit_test_job()")
    print("3. Run the job submission")
    print("=" * 50)
    
    # Ask if user wants to submit a test job
    response = input("\nDo you want to submit a test job? (y/n): ").lower().strip()
    if response == 'y':
        job_id = submit_test_job()
        if job_id:
            print(f"\nJob submitted successfully! Job ID: {job_id}")
            print("You can check the status with:")
            print(f"curl {API_BASE_URL}/api/status/{job_id}")
            
            # Monitor job status
            print("\nMonitoring job status (press Ctrl+C to stop)...")
            try:
                while True:
                    status = check_job_status(job_id)
                    if status and status.get('status') in ['completed', 'failed']:
                        print(f"\nJob finished with status: {status.get('status')}")
                        break
                    time.sleep(10)  # Check every 10 seconds
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
