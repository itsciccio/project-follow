# Instagram Bot Deployment Guide

This guide explains how to deploy and maintain Instagram bot accounts for persistent session management on your remote server.

## Overview

The bot system provides:
- **Persistent Instagram sessions** using browser automation
- **Automatic session refresh** and cookie management
- **Simplified API** that only requires target user IDs
- **Session health monitoring** and automatic recovery
- **Production-ready deployment** with systemd services

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   End User      │    │   Bot API Server │    │  Instagram Bot  │
│                 │    │                  │    │     Account     │
│ - Provides      │───▶│ - Manages bot    │───▶│ - Always logged │
│   user_id only  │    │   sessions       │    │   in            │
│                 │    │ - Handles API    │    │ - No followers  │
│                 │    │   requests       │    │ - Dedicated     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements
- **Python 3.7+**
- **Chrome browser** installed
- **ChromeDriver** in PATH or auto-managed
- **Linux server** (Ubuntu 20.04+ recommended)
- **Minimum 2GB RAM** and 1 CPU core

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Setup Bot Account
```bash
python3 setup_bot_account.py
```

This interactive script will:
- Guide you through bot account creation
- Test login functionality
- Configure session monitoring
- Generate startup scripts

### 2. Start the Bot Server
```bash
python3 instagram_bot_api_server.py
```

### 3. Test the API
```bash
# Submit analysis job (only need target user ID)
curl -X POST http://localhost:5000/api/analyze \
     -H 'Content-Type: application/json' \
     -d '{"target_user_id": "123456789"}'

# Check job status
curl http://localhost:5000/api/status/<job_id>
```

## Production Deployment

### 1. VPS Setup

**Recommended VPS Providers:**
- **DigitalOcean**: $5/month (1GB RAM, 1 CPU)
- **Vultr**: $5/month (1GB RAM, 1 CPU)
- **Linode**: $5/month (1GB RAM, 1 CPU)
- **Hetzner**: €3.29/month (2GB RAM, 1 CPU)

**Server Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable -y

# Install ChromeDriver
sudo apt install chromium-chromedriver -y
```

### 2. Application Deployment

```bash
# Clone your repository
git clone <your-repo-url>
cd project-follow

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup bot account
python3 setup_bot_account.py

# Test the setup
python3 instagram_bot_api_server.py
```

### 3. Systemd Service

The setup script creates a systemd service file. Install it:

```bash
# Copy service file
sudo cp instagram-bot-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable instagram-bot-api
sudo systemctl start instagram-bot-api

# Check status
sudo systemctl status instagram-bot-api

# View logs
sudo journalctl -u instagram-bot-api -f
```

### 4. Nginx Reverse Proxy (Optional)

For production with HTTPS:

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/instagram-bot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/instagram-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL with Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Bot Account Management

### Creating Bot Accounts

**Best Practices:**
- Use dedicated Instagram accounts
- Accounts should have no followers (or very few)
- Use strong, unique passwords
- Don't use your main personal account
- Consider using business accounts

**Setup Process:**
```bash
python3 setup_bot_account.py
```

### Multiple Bot Accounts

You can run multiple bot accounts for load balancing:

```bash
# Add additional bot accounts via API
curl -X POST http://localhost:5000/api/bot/accounts \
     -H 'Content-Type: application/json' \
     -d '{
       "username": "bot_account_2",
       "password": "secure_password",
       "account_name": "secondary_bot"
     }'

# Login the account
curl -X POST http://localhost:5000/api/bot/accounts/secondary_bot/login
```

### Session Monitoring

The system automatically:
- Checks session health every 30 minutes
- Refreshes expired sessions
- Logs session status and issues
- Handles login failures gracefully

## API Usage

### Simplified API Endpoints

**Submit Analysis Job:**
```bash
curl -X POST http://localhost:5000/api/analyze \
     -H 'Content-Type: application/json' \
     -d '{"target_user_id": "123456789"}'
```

**Check Job Status:**
```bash
curl http://localhost:5000/api/status/<job_id>
```

**List Bot Accounts:**
```bash
curl http://localhost:5000/api/bot/accounts
```

**Refresh Bot Session:**
```bash
curl -X POST http://localhost:5000/api/bot/accounts/main_bot/refresh
```

### Response Format

**Analysis Result:**
```json
{
  "target_user_id": "123456789",
  "followers_count": 1500,
  "following_count": 800,
  "unfollowers_count": 200,
  "unfollowers": ["user1", "user2", "..."],
  "analysis_completed_at": "2024-01-15T10:30:00",
  "bot_account_used": "main_bot"
}
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check API health
curl http://localhost:5000/api/health

# Check queue status
curl http://localhost:5000/api/queue

# View systemd service status
sudo systemctl status instagram-bot-api
```

### Log Monitoring

```bash
# View application logs
sudo journalctl -u instagram-bot-api -f

# View Chrome browser logs (if needed)
tail -f /var/log/chrome.log
```

### Session Health Monitoring

The system automatically monitors:
- Session validity
- Cookie expiration
- Login status
- API response health

### Troubleshooting

**Common Issues:**

1. **Bot Login Fails:**
   - Check credentials
   - Verify account isn't locked
   - Try manual login first

2. **Session Expires:**
   - System auto-refreshes sessions
   - Check monitoring logs
   - Manually refresh if needed

3. **Chrome/ChromeDriver Issues:**
   - Update Chrome and ChromeDriver
   - Check system resources
   - Verify display settings for headless mode

4. **API Rate Limiting:**
   - Reduce request frequency
   - Use multiple bot accounts
   - Implement proper delays

## Security Considerations

### Bot Account Security
- Use dedicated accounts only
- Strong, unique passwords
- Enable 2FA if possible
- Monitor for restrictions

### Server Security
- Keep system updated
- Use firewall rules
- Implement HTTPS in production
- Monitor access logs
- Use SSH keys instead of passwords

### Data Protection
- Bot credentials stored locally
- Session data encrypted in browser profile
- Don't share credentials
- Regular security audits

## Performance Optimization

### Resource Management
- Monitor memory usage
- Limit concurrent jobs
- Use appropriate delays
- Clean up old sessions

### Scaling
- Multiple bot accounts
- Load balancing
- Database for job persistence
- Caching for repeated requests

## Compliance and Legal

### Instagram Terms of Service
- Be aware of Instagram's ToS
- Use reasonable request rates
- Don't abuse the service
- Monitor for account restrictions

### Data Privacy
- Respect user privacy
- Don't store personal data unnecessarily
- Implement data retention policies
- Follow GDPR/privacy regulations

## Support and Maintenance

### Regular Maintenance
- Update dependencies monthly
- Monitor system resources
- Check bot account health
- Review security logs

### Backup Strategy
- Backup bot configuration
- Backup session data
- Document deployment process
- Test recovery procedures

## Cost Estimation

### VPS Costs
- **Basic**: $5/month (1GB RAM, 1 CPU)
- **Standard**: $10/month (2GB RAM, 1 CPU)
- **Premium**: $20/month (4GB RAM, 2 CPU)

### Additional Costs
- Domain name: $10-15/year
- SSL certificate: Free (Let's Encrypt)
- Monitoring tools: Free (basic) to $20/month

### Total Monthly Cost
- **Basic setup**: $5-10/month
- **Production setup**: $10-25/month

## Conclusion

This bot system provides a robust solution for maintaining persistent Instagram sessions on remote servers. The key benefits are:

1. **Simplified API**: Users only need to provide target user IDs
2. **Persistent Sessions**: Bot accounts stay logged in automatically
3. **Automatic Recovery**: System handles session refresh and failures
4. **Production Ready**: Includes monitoring, logging, and deployment tools
5. **Scalable**: Supports multiple bot accounts and load balancing

The main trade-off is that target accounts cannot be private, but this is often acceptable for public Instagram analysis use cases.
