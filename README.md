# Instagram Follower Analysis Tool

A comprehensive tool for analyzing Instagram followers and finding users who don't follow you back. Available as both a **command-line tool** and a **REST API server**.

## 🎯 What This Tool Does

### **Command-Line Tool:**
1. **Collects your complete Instagram data** using Instagram's internal API
2. **Compares followers vs following** to find users who don't follow you back
3. **Generates a clean text file** with the list of non-followers

### **REST API Server:**
1. **Server-side processing** - Submit jobs via HTTP API
2. **Concurrent processing** - Handle multiple users simultaneously
3. **Job management** - Track status, queue, and results
4. **Production ready** - Built with Flask and proper MVC architecture

## 🚀 Quick Start

### **Option 1: Command-Line Tool (Local)**
```bash
# Complete automated workflow
python run_instagram_analysis.py
```

### **Option 2: API Server (Production)**
```bash
# Start the API server
python instagram_api_server.py

# Submit analysis job via API
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"csrf_token": "your_token", "session_id": "your_session"}'
```

## 📁 Project Structure

### **Command-Line Tools:**
- **`run_instagram_analysis.py`** - Complete automated workflow runner
- **`get_instagram_credentials.py`** - Simplified credentials input (only 2 values!)
- **`instagram_api_scraper.py`** - Core Instagram data collection
- **`compare_followers.py`** - Data comparison and analysis

### **API Server:**
- **`instagram_api_server.py`** - Flask REST API server with MVC architecture
- **`requirements.txt`** - Python dependencies
- **`API_README.md`** - Complete API documentation
- **`Instagram_API_Postman_Collection.json`** - Postman collection for testing

### **Configuration & Documentation:**
- **`.gitignore`** - Comprehensive security patterns
- **`SECURITY.md`** - Security guidelines and best practices

## 🔒 Security & Privacy Features

### **Automatic Data Protection**
- **`.gitignore`** file automatically prevents sensitive data from being committed
- **Instagram credentials** are never tracked in version control
- **Collected user data** is automatically excluded from Git
- **Session information** and cookies are kept private

### **What's Protected (Never Committed):**
- `instagram_curl.txt` - Generated curl command with your credentials
- `instagram_data/` - All collected follower/following data
- Any files containing API keys, tokens, or personal data

### **What's Safe to Commit:**
- Source code (`.py` files)
- Documentation (`.md` files)
- API collections (`.json` files)
- Configuration templates

## 🔑 Getting Your Instagram Credentials

### **Simplified Credentials Input (Only 2 Values!)**
The tool only asks you for **2 values** and automatically extracts the rest:

**🔑 Required:**
- **CSRF Token** - Your CSRF token from cookies
- **Session ID** - Your session ID from cookies

**✨ Automatically Extracted:**
- **User ID** - Extracted from your session ID (everything before the first `%`)

### **How to Find These Values:**
1. **Go to Instagram** → Your Profile → Followers
2. **Open Developer Tools** (F12) → Application tab
3. **Go to Cookies** → instagram.com
4. **Look for these two cookies:**
   - `csrf_token` - Your CSRF token
   - `sessionid` - Your session ID (contains your user ID)

## 🖥️ API Server Features

### **Production-Ready Architecture:**
- **MVC Pattern** - Clean separation of concerns
- **Dependency Injection** - Testable and maintainable code
- **Concurrent Processing** - Handle multiple users simultaneously
- **Job Management** - Track status, queue, and results
- **Error Handling** - Comprehensive error management
- **Security** - No sensitive data exposure in API responses

### **API Endpoints:**
- **`POST /api/analyze`** - Submit new analysis job
- **`GET /api/status/{job_id}`** - Get job status
- **`GET /api/queue`** - Get queue status
- **`GET /api/health`** - Health check
- **`DELETE /api/job/{job_id}`** - Delete specific job

### **Key Features:**
- **One job per session** - Prevents duplicate processing
- **Automatic cleanup** - Jobs removed after 30 minutes
- **Queue management** - Handles concurrent requests
- **Debug endpoints** - Troubleshooting and monitoring

## 📊 Output

### **Command-Line Tool:**
- **`instagram_data/followers.txt`** - List of your followers
- **`instagram_data/following.txt`** - List of users you follow
- **`users_not_following_back.txt`** - Users who don't follow you back

### **API Server:**
- **JSON responses** with structured data
- **Job status tracking** with timestamps
- **Queue position** and estimated wait times
- **Detailed error messages** for troubleshooting

## 🔧 Installation

### **Command-Line Tool:**
```bash
pip install requests
```

### **API Server:**
```bash
pip install -r requirements.txt
```

## 📖 Usage Examples

### **Command-Line Tool:**
```bash
# Complete automated workflow (recommended)
python run_instagram_analysis.py

# Manual step-by-step
python get_instagram_credentials.py
python instagram_api_scraper.py --curl-file instagram_curl.txt
python compare_followers.py
```

### **API Server:**
```bash
# Start server
python instagram_api_server.py

# Submit job
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"csrf_token": "your_token", "session_id": "your_session"}'

# Check status
curl http://localhost:5000/api/status/your-job-id
```


## 🚨 Troubleshooting

### **Command-Line Tool:**
- **"Input file not found"** → Create `curl_input.txt` with your curl command
- **"Missing credentials"** → Check your curl command is complete
- **"Error fetching batch"** → Your session may have expired
- **"Permission denied"** → Instagram may have blocked access

### **API Server:**
- **"Job not found"** → Check job_id or job may have been cleaned up
- **"Job already exists"** → Only one job per session allowed
- **"Validation error"** → Check your credentials format
- **"Unexpected error"** → Check server logs for details

## 📚 Documentation

- **`API_README.md`** - Complete API documentation with examples
- **`SECURITY.md`** - Security guidelines and best practices
- **`Instagram_API_Postman_Collection.json`** - Import into Postman for testing

## ⚠️ Important Notes

- **Respect Instagram's terms of service**
- **Use responsibly** and don't abuse the API
- **Sessions expire** - refresh your Instagram login if needed
- **Rate limiting** is built-in (2 second delays between requests)
- **One job per session** - API prevents duplicate processing

## 📄 License

For educational and personal use only. Respect Instagram's terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

- Check the troubleshooting section above
- Review the API documentation
- Open an issue for bugs or feature requests