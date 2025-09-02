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
- `curl_input.txt` - Your Instagram API credentials
- `instagram_curl.txt` - Formatted credentials
- `instagram_data/` - All collected follower/following data
- Any files containing API keys, tokens, or personal data

### **What's Safe to Commit:**
- Source code (`.py` files)
- Documentation (`.md` files)
- Example files (`.example` files)
- Configuration templates

### **Example Files for Reference:**
- `curl_input.txt.example` - Shows expected curl command format
- `instagram_data_example/` - Shows output data structure
- No real credentials or user data included

## 🚀 Quick Start

### Option 1: Automated Workflow (Recommended)
```bash
# Run everything automatically with one command
python run_instagram_analysis.py
```

**Or on Windows, double-click:** `run_instagram_analysis.bat`

### Option 2: Manual Step-by-Step
1. **Copy your curl command** from Instagram (see instructions below)
2. **Paste it into `curl_input.txt`** file
3. **Run the formatter:**
   ```bash
   python save_curl_and_run.py
   ```
4. **Run the scraper:**
   ```bash
   python instagram_api_scraper.py --curl-file instagram_curl.txt
   ```
5. **Run the comparison:**
   ```bash
   python compare_followers.py
   ```

## 📁 Files You Need

- **`run_instagram_analysis.py`** - **🚀 Complete automated workflow runner**
- **`run_instagram_analysis.bat`** - **Windows batch file for easy execution**
- **`instagram_api_scraper.py`** - Collects your Instagram data
- **`save_curl_and_run.py`** - Reads and formats your curl command
- **`compare_followers.py`** - Compares the data and finds non-followers
- **`curl_input.txt`** - **Put your Instagram curl command here**
- **`instagram_curl.txt`** - **Auto-generated cleaned curl command**
- **`instagram_data/`** - Directory containing your collected data
- **`users_not_following_back.txt`** - Final list of users who don't follow back

## 🔑 Getting Your Instagram Credentials

1. **Log into Instagram** in your browser
2. **Go to your profile** and click "Followers"
3. **Open Developer Tools** (F12) → Network tab
4. **Find the API request** to `/api/v1/friendships/{user_id}/followers/`
5. **Right-click** → "Copy as cURL"
6. **Paste the entire curl command** into `curl_input.txt`
7. **Run** `python save_curl_and_run.py` to format it

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
# 1. Put your curl command in curl_input.txt
# 2. Format the curl command
python save_curl_and_run.py

# 3. Collect data
python instagram_api_scraper.py --curl-file instagram_curl.txt

# 4. Compare data
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