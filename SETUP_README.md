# Instagram Bot Setup

## Quick Setup

### 1. Install Dependencies

**Install Python packages:**
```bash
pip install -r requirements.txt
```

**Install Google Chrome:**
- Download from: https://www.google.com/chrome/
- Or install via winget: `winget install Google.Chrome`
- Chrome is required for the bot automation

### 2. Configure Bot Accounts
```bash
# Copy the example configuration
cp bot_config.yaml.example bot_config.yaml

# Edit the configuration file with your bot credentials
nano bot_config.yaml  # or use your preferred editor
```

**Update `bot_config.yaml` with your bot credentials:**
```yaml
bots:
  - id: "bot_1"
    username: "your_actual_bot_username"  # Replace this
    password: "your_actual_bot_password"  # Replace this
    description: "Primary bot account"
    enabled: true
```

**That's it!** The bot manager runs on port 5001 with automatic health monitoring.

### 3. Start Bot Manager
```bash
python3 instagram_bot_manager.py
```

### 4. Start Main API Server
```bash
python3 instagram_api_server.py
```

### 5. Test the API
```bash
# Basic follower analysis
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"target_user_id": "123456789"}'

# Not-following-back analysis
curl -X POST http://localhost:5000/api/analyze-not-following-back \
  -H "Content-Type: application/json" \
  -d '{"target_user_id": "123456789"}'
```

## Bot Account Requirements

### **Creating Bot Accounts**
- **Use dedicated Instagram accounts** (not your personal account)
- **Accounts should have minimal followers** to avoid detection
- **Use realistic usernames** and profile information
- **Enable 2FA** if possible for security

### **Bot Account Setup**
1. Create new Instagram accounts
2. Complete profile setup with realistic information
3. Add a few posts to make accounts look legitimate
4. Add the credentials to `bot_config.yaml`
5. Test login through the bot manager

## Configuration Options

### **Bot Manager Settings**
```yaml
manager:
  port: 5001                    # Bot manager API port
  health_check_interval: 1800   # Health check every 30 minutes
  session_timeout: 86400        # Session timeout (24 hours)
  max_concurrent_bots: 10       # Maximum concurrent bot sessions
  headless: true                # Run Chrome in headless mode
```

### **Multiple Bot Accounts**
```yaml
bots:
  - id: "bot_1"
    username: "bot_account_1"
    password: "password1"
    description: "Primary bot account"
    enabled: true
  - id: "bot_2"
    username: "bot_account_2"
    password: "password2"
    description: "Secondary bot account"
    enabled: true
```

## Troubleshooting

### **Common Issues**
- **Chrome not found**: Install Google Chrome and ensure it's in PATH
- **Bot login fails**: Check credentials and account status
- **Session expired**: Bot manager will automatically refresh sessions
- **Rate limiting**: Use multiple bot accounts for load balancing

### **Health Monitoring**
```bash
# Check bot manager health
curl http://localhost:5001/api/bot/health

# Check main API health
curl http://localhost:5000/api/health
```

## Production Deployment

### **Security Considerations**
- Keep `bot_config.yaml` secure and never commit to Git
- Use environment variables for sensitive configuration
- Implement proper authentication for API endpoints
- Monitor bot account health regularly

### **Scaling**
- Add more bot accounts to `bot_config.yaml`
- Use load balancing for multiple bot managers
- Monitor system resources and performance
- Implement proper logging and monitoring