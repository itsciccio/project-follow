# Instagram Follower Analysis Tool

A simple tool to collect your Instagram followers/following data using Instagram's internal API and compare them to find users who don't follow you back.

## 🎯 What This Tool Does

1. **Collects your complete Instagram data** using Instagram's internal API
2. **Compares followers vs following** to find users who don't follow you back
3. **Generates a clean text file** with the list of non-followers

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
- Example files (`.example` files)
- Configuration templates

### **Example Files for Reference:**
- `instagram_data_example/` - Shows output data structure
- No real credentials or user data included

### **Simplified Security Model:**
- **Only 2 values needed**: session_id + csrf_token
- **User ID extracted automatically** from session_id
- **No manual curl commands** to copy/paste
- **Reduced risk** of credential exposure

## 🚀 Quick Start

### Complete Automated Workflow (Recommended)
```bash
# Run everything automatically with one command
python run_instagram_analysis.py
```

**Or on Windows, double-click:** `run_instagram_analysis.bat`

**What happens automatically:**
1. **Asks for your credentials** (session_id + csrf_token only)
2. **Extracts your user ID** automatically from session_id
3. **Scrapes your Instagram data** (followers + following)
4. **Compares and analyzes** to find users who don't follow back

### Manual Step-by-Step
```bash
# 1. Get credentials and generate curl command
python get_instagram_credentials.py

# 2. Run the scraper
python instagram_api_scraper.py --curl-file instagram_curl.txt

# 3. Compare followers
python compare_followers.py
```

## 📁 Files You Need

- **`run_instagram_analysis.py`** - **🚀 Complete automated workflow runner**
- **`run_instagram_analysis.bat`** - **Windows batch file for easy execution**
- **`get_instagram_credentials.py`** - **🆕 Simplified credentials input (only 2 values!)**
- **`get_credentials.bat`** - **Windows batch file for credentials input**
- **`instagram_api_scraper.py`** - Collects your Instagram data
- **`compare_followers.py`** - Compares the data and finds non-followers
- **`instagram_curl.txt`** - **Auto-generated complete curl command**
- **`instagram_data/`** - Directory containing your collected data
- **`users_not_following_back.txt`** - Final list of users who don't follow you back

## 🔑 Getting Your Instagram Credentials

### **Simplified Credentials Input (Only Method)**
The tool only asks you for **2 values** and automatically extracts the rest:

**🔑 Required (Only 2 values!):**
- **CSRF Token** - Your CSRF token from cookies
- **Session ID** - Your session ID from cookies

**✨ Automatically Extracted:**
- **User ID** - Extracted from your session ID (everything before the first `%`)

**Example Session ID Format:**
```
410199922%3AA9IF5q64rDBksn%3A9%3AAYfA7EvS4XvKzqbub0EKcaiMW2w61TJFm8ojtHl2xg
     ↑
User ID: 410199922
```

### **How to Find These Values:**
1. **Go to Instagram** → Your Profile → Followers
2. **Open Developer Tools** (F12) → Application tab
3. **Go to Cookies** → instagram.com
4. **Look for these two cookies:**
   - `csrf_token` - Your CSRF token
   - `sessionid` - Your session ID (contains your user ID)

## 📊 Output

The tool creates:
- **`instagram_data/followers.txt`** - List of your followers
- **`instagram_data/following.txt`** - List of users you follow
- **`users_not_following_back.txt`** - Users who don't follow you back

## ⚠️ Important Notes

- **Respect Instagram's terms of service**
- **Use responsibly** and don't abuse the API
- **Sessions expire** - refresh your Instagram login if needed
- **Rate limiting** is built-in (2 second delays between requests)

## 🔧 Installation

```bash
pip install requests
```

## 📖 Usage Examples

### Basic Usage
```bash
# Complete automated workflow (recommended)
python run_instagram_analysis.py
```

### Manual Step-by-Step
```bash
# 1. Get credentials and generate curl command
python get_instagram_credentials.py

# 2. Run the scraper
python instagram_api_scraper.py --curl-file instagram_curl.txt

# 3. Compare followers
python compare_followers.py
```

### Custom Settings
```bash
# Limit number of users collected
python instagram_api_scraper.py --curl-file instagram_curl.txt --max-count 1000

# Adjust rate limiting
python instagram_api_scraper.py --curl-file instagram_curl.txt --delay 3.0
```

## 🚨 Troubleshooting

- **"Input file not found"** → Create `curl_input.txt` with your curl command
- **"Missing credentials"** → Check your curl command is complete
- **"Error fetching batch"** → Your session may have expired
- **"Permission denied"** → Instagram may have blocked access

## 📄 License

For educational and personal use only. Respect Instagram's terms of service. 