# Instagram Follower Analysis API

A production-ready REST API server for analyzing Instagram followers and finding users who don't follow you back. Built with Flask and proper MVC architecture.

## 🚀 Quick Start

### **Local Development:**
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python instagram_api_server.py
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:5000/api/health
   ```


## 🏗️ Architecture

### **MVC Pattern:**
- **Model**: `InstagramAPIScraper` - Data access layer for Instagram API
- **Controller**: `InstagramAnalyzerAPI` - Business logic orchestration
- **View**: Flask endpoints - HTTP request/response handling

### **Key Features:**
- **Dependency Injection** - Clean, testable code
- **Concurrent Processing** - Handle multiple users simultaneously
- **Job Management** - Track status, queue, and results
- **Error Handling** - Comprehensive error management
- **Security** - No sensitive data exposure in API responses

## 📡 API Endpoints

### **Submit Analysis Job**
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
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "queued",
    "position_in_queue": 2,
    "estimated_wait_time": "Starting in ~4 minutes"
}
```

### **Check Job Status**
```bash
GET /api/status/{job_id}
```

**Response**:
```json
{
    "status": "completed",
    "result": {
        "followers_count": 1250,
        "following_count": 890,
        "unfollowers_count": 45,
        "unfollowers": ["user1", "user2", "user3"],
        "analysis_completed_at": "2024-01-15T10:30:00"
    },
    "created_at": 1705312200,
    "processing_time": 45.2
}
```

### **Get Queue Status**
```bash
GET /api/queue
```

**Response**:
```json
{
    "active_sessions": 2,
    "max_concurrent": 5,
    "queued_jobs": 3,
    "total_jobs_in_memory": 8
}
```

### **Health Check**
```bash
GET /api/health
```

**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "active_jobs": 2,
    "queued_jobs": 3
}
```

### **Delete Job**
```bash
DELETE /api/job/{job_id}
```

**Response**:
```json
{
    "message": "Job deleted successfully",
    "deleted_job_status": "completed",
    "remaining_jobs": 7
}
```

### **Debug Job (Development)**
```bash
GET /api/debug/{job_id}
```

**Response**:
```json
{
    "status": "processing",
    "created_at": 1705312200,
    "position_in_queue": 0,
    "processing_time": 25.3
}
```

### **List All Jobs (Development)**
```bash
GET /api/jobs
```

**Response**:
```json
{
    "jobs": {
        "job1": {
            "status": "completed",
            "created_at": 1705312200,
            "position_in_queue": 0
        }
    },
    "total_jobs": 1,
    "active_sessions_count": 2,
    "queue_length": 3
}
```

## 🔧 Configuration

Edit these variables in `instagram_api_server.py`:

```python
MAX_CONCURRENT_JOBS = 5        # Maximum concurrent Instagram sessions
JOB_CLEANUP_DELAY = 1800       # Job cleanup delay in seconds (30 minutes)
```

## 🔑 Getting Instagram Credentials

### **Required Values:**
- **CSRF Token** - Your CSRF token from Instagram cookies
- **Session ID** - Your session ID from Instagram cookies

### **How to Find:**
1. Go to Instagram → Your Profile → Followers
2. Open Developer Tools (F12) → Application tab
3. Go to Cookies → instagram.com
4. Look for:
   - `csrf_token` - Your CSRF token
   - `sessionid` - Your session ID

## 📋 Job Lifecycle

1. **Submit Job** → Job gets queued or starts immediately
2. **Processing** → Instagram data is collected and analyzed
3. **Completed** → Results are available via status endpoint
4. **Cleanup** → Job is automatically removed after 30 minutes

## 🚨 Error Handling

### **Common Error Responses:**

**400 - Bad Request:**
```json
{
    "error": "csrf_token is required"
}
```

**404 - Not Found:**
```json
{
    "error": "Job not found"
}
```

**409 - Conflict:**
```json
{
    "error": "Job already exists",
    "message": "This account already has a job with status: completed",
    "job_id": "existing-job-id",
    "status": "completed"
}
```

**500 - Internal Server Error:**
```json
{
    "error": "Internal server error: Connection timeout"
}
```

## 🧪 Testing

### **Using Postman:**
1. Import `Instagram_API_Postman_Collection.json`
2. Set variables in collection:
   - `base_url`: `http://localhost:5000`
   - `csrf_token`: Your CSRF token
   - `session_id`: Your session ID
   - `job_id`: Job ID from analyze response

### **Using curl:**
```bash
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
```


## 🔒 Security Features

- **No sensitive data exposure** - Credentials never returned in API responses
- **One job per session** - Prevents duplicate processing
- **Automatic cleanup** - Jobs removed after completion
- **Input validation** - All inputs validated before processing
- **Error sanitization** - Error messages don't expose internal details

## 📊 Monitoring

### **Health Check:**
```bash
curl http://localhost:5000/api/health
```

### **Queue Status:**
```bash
curl http://localhost:5000/api/queue
```

### **Debug Information:**
```bash
curl http://localhost:5000/api/jobs
```

## ⚠️ Important Notes

- **One job per session** - Each Instagram account can only have one active job
- **Job cleanup** - Completed jobs are automatically removed after 30 minutes
- **Rate limiting** - Built-in delays to respect Instagram's API
- **Session management** - Instagram sessions are tracked to prevent conflicts
- **Error handling** - Comprehensive error management with detailed logging

## 🐛 Troubleshooting

### **Common Issues:**

**"Job not found"**
- Job may have been cleaned up (30-minute timeout)
- Check if job_id is correct
- Use debug endpoint to see all current jobs

**"Job already exists"**
- Only one job per Instagram session allowed
- Delete existing job or wait for completion

**"Validation error"**
- Check your credentials format
- Ensure session_id contains valid user ID

**"Unexpected error"**
- Check server logs for details
- Verify Instagram credentials are valid
- Check network connectivity

## 📚 Additional Resources

- **Main README** - Complete project overview
- **Postman Collection** - Import for easy testing
- **Security Guidelines** - Best practices for deployment
