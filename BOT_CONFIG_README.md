# Bot Configuration System

## Overview

The Instagram bot manager now uses a YAML configuration file to manage bot accounts. This provides better security, easier management, and more flexibility than hardcoded credentials.

## Quick Start

### 1. Create Configuration File

```bash
python3 setup_bot_manager.py
# Choose option 1 to create bot configuration
```

### 2. Start Bot Manager

```bash
python3 setup_bot_manager.py
# Choose option 3 to start the bot manager
```

### 3. Start Main API Server

```bash
python3 instagram_api_server.py
```

## Configuration File Structure

The `bot_config.yaml` file contains:

```yaml
# Bot accounts
bots:
  - id: "bot_1"
    username: "your_bot_username"
    password: "your_bot_password"
    description: "Primary bot account"
    enabled: true

# Manager settings
manager:
  port: 5001
  health_check_interval: 1800
  session_timeout: 86400
  max_concurrent_bots: 10
  headless: true

# Logging settings
logging:
  level: "INFO"
  file: "bot_manager.log"

# Security settings
security:
  cookie_encryption: true
  session_rotation: true
```

## Security Best Practices

### 🔒 **Never Commit Credentials**
- `bot_config.yaml` is in `.gitignore`
- Never commit this file to version control
- Use `bot_config.yaml.example` as a template

### 🤖 **Bot Account Security**
- Use dedicated Instagram accounts (not your main account)
- Accounts should have no followers or very few
- Use strong, unique passwords
- Enable 2FA if possible
- Monitor accounts for restrictions

### 🛡️ **File Security**
- Restrict file permissions: `chmod 600 bot_config.yaml`
- Keep the file in a secure location
- Consider using environment variables for production

## Configuration Options

### Bot Configuration
- **id**: Unique identifier for the bot
- **username**: Instagram username
- **password**: Instagram password
- **description**: Human-readable description
- **enabled**: Whether the bot is active (true/false)

### Manager Configuration
- **port**: HTTP API port (default: 5001)
- **health_check_interval**: Health check frequency in seconds (default: 1800)
- **session_timeout**: Session timeout in seconds (default: 86400)
- **max_concurrent_bots**: Maximum concurrent bot usage (default: 10)
- **headless**: Run browsers in headless mode (default: true)

### Logging Configuration
- **level**: Log level (DEBUG, INFO, WARNING, ERROR)
- **file**: Log file path
- **max_size**: Maximum log file size
- **backup_count**: Number of backup log files

### Security Configuration
- **cookie_encryption**: Encrypt stored cookies (default: true)
- **session_rotation**: Rotate sessions periodically (default: true)
- **rotation_interval**: Session rotation interval in seconds (default: 3600)

## Environment Variables (Production)

For production deployments, consider using environment variables:

```bash
# Set environment variables
export BOT_USERNAME_1="your_bot_username"
export BOT_PASSWORD_1="your_bot_password"
export BOT_USERNAME_2="your_bot_username_2"
export BOT_PASSWORD_2="your_bot_password_2"

# Update bot_config.yaml to use environment variables
bots:
  - id: "bot_1"
    username: "${BOT_USERNAME_1}"
    password: "${BOT_PASSWORD_1}"
    enabled: true
```

## Troubleshooting

### Configuration File Issues
- **File not found**: Run `python3 setup_bot_manager.py` to create configuration
- **Invalid YAML**: Check syntax with a YAML validator
- **Missing fields**: Ensure all required fields are present

### Bot Login Issues
- **Invalid credentials**: Verify username/password
- **Account locked**: Check Instagram account status
- **2FA enabled**: Disable 2FA or use app-specific password

### Manager Issues
- **Port in use**: Change port in configuration
- **No bots available**: Check bot status and credentials
- **Session expired**: Bots auto-refresh, check logs

## Monitoring

### Check Bot Status
```bash
curl http://localhost:5001/api/bot/status
```

### Check Manager Health
```bash
curl http://localhost:5001/api/bot/health
```

### View Logs
```bash
tail -f bot_manager.log
```

## Migration from Old System

If you were using the old hardcoded system:

1. **Backup old configuration**: Save any hardcoded credentials
2. **Create new config**: Run `python3 setup_bot_manager.py`
3. **Test configuration**: Verify bots can login
4. **Update deployment**: Use new configuration system

## Example Production Setup

```yaml
# Production bot_config.yaml
bots:
  - id: "primary_bot"
    username: "${BOT_USERNAME_1}"
    password: "${BOT_PASSWORD_1}"
    description: "Primary production bot"
    enabled: true
    
  - id: "backup_bot"
    username: "${BOT_USERNAME_2}"
    password: "${BOT_PASSWORD_2}"
    description: "Backup production bot"
    enabled: true

manager:
  port: 5001
  health_check_interval: 900  # 15 minutes
  session_timeout: 43200      # 12 hours
  max_concurrent_bots: 5
  headless: true

logging:
  level: "WARNING"
  file: "/var/log/instagram_bot_manager.log"
  max_size: "50MB"
  backup_count: 10

security:
  cookie_encryption: true
  session_rotation: true
  rotation_interval: 1800  # 30 minutes
```

This configuration system provides a secure, flexible, and maintainable way to manage your Instagram bot accounts.
