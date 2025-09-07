# Instagram Follower Analysis API

A Flask API server that processes Instagram follower analysis jobs with support for multiple concurrent users.

## Features

- **Multi-user support**: Process multiple Instagram accounts simultaneously
- **Session-based concurrency**: One job per Instagram session to avoid rate limiting
- **Queue management**: Jobs are queued when server is at capacity
- **Automatic cleanup**: Completed jobs are cleaned up after 5 minutes
- **Real-time status**: Track job progress and queue position
- **Instagram-safe**: Respects Instagram's rate limits and anti-bot measures
- **Deterministic job IDs**: Job IDs are generated from your credentials, so you never lose access to your job
- **Credential-based access**: Access your job using your csrf_token and session_id instead of remembering job IDs

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements_api.txt
   ```

2. **Start the server**:
   ```bash
   python instagram_api_server.py
   ```

3. **Server will start on**: `http://localhost:5000`

## API Endpoints

### Submit Analysis Job
```bash
POST /api/analyze
Content-Type: application/json

{
    "csrf_token": "your_csrf_token",
    "session_id": "your_session_id"
}
```

**Response**:
```json
{
    "job_id": "uuid",
    "status": "queued|processing",
    "position_in_queue": 0,
    "estimated_wait_time": "Starting immediately"
}
```


### Check Job Status
```bash
GET /api/status/{job_id}
```

**Note**: The `job_id` is generated from your credentials using the formula: `SHA256(csrf_token + ":" + session_id)[:16]`

You can generate your job_id using this Python code:
```python
import hashlib
csrf_token = "your_csrf_token"
session_id = "your_session_id"
job_id = hashlib.sha256(f"{csrf_token}:{session_id}".encode()).hexdigest()[:16]
```

**Response**:
```json
{
    "status": "queued|processing|completed|failed",
    "session_id": "session_id",
    "user_id": "user_id",
    "created_at": 1234567890,
    "position_in_queue": 0,
    "result": {
        "followers_count": 1000,
        "following_count": 500,
        "unfollowers_count": 50,
        "unfollowers": ["user1", "user2", ...],
        "analysis_completed_at": "2024-01-01T12:00:00"
    }
}
```

### Queue Status
```bash
GET /api/queue
```

**Response**:
```json
{
    "active_sessions": 2,
    "max_concurrent": 5,
    "queued_jobs": 3,
    "active_session_ids": ["session1", "session2"],
    "total_jobs_in_memory": 5
}
```

### Health Check
```bash
GET /api/health
```

### List All Jobs (Debug)
```bash
GET /api/jobs
```

### Cleanup Completed Jobs
```bash
POST /api/cleanup
```

### Delete Job by Job ID
```bash
DELETE /api/job/{job_id}
```

### Delete Job by Credentials (Recommended)
```bash
DELETE /api/job
Content-Type: application/json

{
    "csrf_token": "your_csrf_token",
    "session_id": "your_session_id"
}
```

**Response**:
```json
{
    "message": "Job deleted successfully",
    "deleted_job_status": "completed",
    "remaining_jobs": 2
}
```

## Testing

Use the provided test script:

```bash
python test_api.py
```

Or test manually with curl:

```bash
# Health check
curl http://localhost:5000/api/health

# Submit job
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "csrf_token": "your_token",
    "session_id": "your_session"
  }'

# Check status using the job_id from the analyze response
curl http://localhost:5000/api/status/your-job-id

# Delete job by job ID
curl -X DELETE http://localhost:5000/api/job/job-uuid-here

# Delete job by credentials (recommended)
curl -X DELETE http://localhost:5000/api/job \
  -H "Content-Type: application/json" \
  -d '{
    "csrf_token": "your_token",
    "session_id": "your_session"
  }'
```

## Configuration

Edit these variables in `instagram_api_server.py`:

- `MAX_CONCURRENT_JOBS = 5`: Maximum concurrent jobs
- `JOB_CLEANUP_DELAY = 300`: Cleanup delay in seconds (5 minutes)

## Getting Instagram Credentials

You'll need to extract these from your browser:

1. **CSRF Token**: From Instagram's cookies or headers
2. **Session ID**: From Instagram's sessionid cookie (user_id will be extracted automatically)

Use the existing `get_instagram_credentials.py` script to help extract these.

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (missing fields)
- `409`: Conflict (session already processing)
- `404`: Job not found
- `500`: Internal server error

## Security Notes

- This API is designed for local testing
- For production, add authentication, HTTPS, and proper security measures
- Never expose Instagram credentials in logs or responses
- Consider rate limiting and request validation

## Troubleshooting

1. **"Job not found"**: Job may have been cleaned up (5+ minutes old)
2. **"Already being processed"**: Session has an active job
3. **Analysis fails**: Check Instagram credentials and network connection
4. **Server won't start**: Check if port 5000 is available

## Architecture

- **Single-threaded per session**: Each Instagram session gets one dedicated thread
- **Concurrent sessions**: Multiple different sessions can run simultaneously
- **Queue system**: Jobs wait in queue when server is at capacity
- **Automatic cleanup**: Prevents memory bloat from old jobs
