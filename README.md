# Instagram Follower Analysis API

A production-ready REST API server for analyzing Instagram followers and finding users who don't follow you back. Built with Flask and bot session management.

## 🎯 What This Tool Does

### **Bot-Powered Analysis:**
1. **Persistent bot sessions** - Bot accounts stay logged in automatically
2. **Simplified user experience** - Users only need to provide target user ID
3. **Concurrent processing** - Handle multiple users simultaneously
4. **Job management** - Track status, queue, and results
5. **Production ready** - Built with Flask and proper MVC architecture

## 🚀 Quick Start

### **1. Start Bot Manager**
```bash
# Start the bot slave manager (handles Instagram sessions)
python instagram_bot_manager.py
```

### **2. Start API Server**
```bash
# Start the main API server
python instagram_api_server.py
```

### **3. Submit Analysis Job**
```bash
# Basic follower analysis (with optional unfollower detection)
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"target_user_id": "123456789", "previous_followers": ["user1", "user2", ...]}'

# Not-following-back analysis (only target_user_id needed!)
curl -X POST http://localhost:5000/api/analyze-not-following-back \
  -H "Content-Type: application/json" \
  -d '{"target_user_id": "123456789"}'
```

## 📁 Project Structure

### **Core API Files:**
- **`instagram_api_server.py`** - Main Flask REST API server
- **`instagram_bot_manager.py`** - Bot session management service
- **`instagram_api_scraper.py`** - Core Instagram data collection
- **`requirements.txt`** - Python dependencies

### **Configuration:**
- **`bot_config.yaml`** - Bot account configuration
- **`bot_config/`** - Bot session data storage
- **`Instagram_API_Postman_Collection.json`** - Postman collection for testing

### **Documentation:**
- **`README.md`** - This comprehensive guide
- **`SECURITY.md`** - Security guidelines and best practices

## 🔒 Security & Privacy Features

### **Automatic Data Protection**
- **`.gitignore`** file automatically prevents sensitive data from being committed
- **Instagram credentials** are never tracked in version control
- **Collected user data** is automatically excluded from Git
- **Session information** and cookies are kept private

### **What's Protected (Never Committed):**
- `bot_config.yaml` - Bot account configuration
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
   - `target_user_id` - Instagram user ID to analyze
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

### **Bot System:**
```bash
# Start bot manager (handles Instagram sessions)
python instagram_bot_manager.py

# Start API server (handles user requests)
python instagram_api_server.py
```

### **API Server:**
```bash
# Start server
python instagram_api_server.py

# Submit job
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"target_user_id": "123456789"}'

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