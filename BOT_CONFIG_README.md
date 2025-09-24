# Bot Configuration System

## Overview

The Instagram bot manager uses a YAML configuration file to manage bot accounts. This provides better security, easier management, and more flexibility than hardcoded credentials.

## Quick Start

### 1. Create Configuration File

```bash
# Copy the example configuration
cp bot_config.yaml.example bot_config.yaml

# Edit the configuration file with your bot credentials
nano bot_config.yaml  # or use your preferred editor
```

### 2. Start Bot Manager

```bash
python3 instagram_bot_manager.py
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
```

## Bot Account Configuration

### **Required Fields**
- `id`: Unique identifier for the bot
- `username`: Instagram username
- `password`: Instagram password
- `description`: Human-readable description
- `enabled`: Whether the bot is active

### **Example Configuration**
```yaml
bots:
  - id: "bot_1"
    username: "my_bot_account_1"
    password: "secure_password_123"
    description: "Primary bot account"
    enabled: true
  - id: "bot_2"
    username: "my_bot_account_2"
    password: "secure_password_456"
    description: "Secondary bot account"
    enabled: true
```

## Manager Settings

### **Port Configuration**
```yaml
manager:
  port: 5001  # Bot manager API port
```

### **Health Monitoring**
```yaml
manager:
  health_check_interval: 1800  # Check every 30 minutes
  session_timeout: 86400        # 24 hour session timeout
```

### **Concurrency Settings**
```yaml
manager:
  max_concurrent_bots: 10  # Maximum concurrent bot sessions
```

### **Browser Settings**
```yaml
manager:
  headless: true  # Run Chrome in headless mode (recommended)
```

## Logging Configuration

### **Log Levels**
- `DEBUG`: Detailed debugging information
- `INFO`: General information (recommended)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only

### **Log Output**
```yaml
logging:
  level: "INFO"
  file: "bot_manager.log"  # Log to file
  console: true            # Also log to console
```

## Security Best Practices

### **Configuration Security**
- Never commit `bot_config.yaml` to Git
- Use strong passwords for bot accounts
- Keep configuration files secure
- Use environment variables for sensitive data

### **Bot Account Security**
- Use dedicated Instagram accounts (not personal)
- Enable 2FA on bot accounts if possible
- Monitor bot account activity regularly
- Rotate bot accounts if needed

## Advanced Configuration

### **Multiple Bot Managers**
```yaml
# Primary bot manager
manager:
  port: 5001
  bots: [...]

# Secondary bot manager
manager:
  port: 5002
  bots: [...]
```

### **Custom Chrome Options**
```yaml
manager:
  chrome_options:
    - "--no-sandbox"
    - "--disable-dev-shm-usage"
    - "--disable-gpu"
```

## Troubleshooting

### **Configuration Issues**
- **Invalid YAML**: Check syntax with YAML validator
- **Missing credentials**: Ensure all required fields are present
- **Port conflicts**: Change port if 5001 is already in use

### **Bot Account Issues**
- **Login failures**: Check credentials and account status
- **Session expired**: Bot manager will automatically refresh
- **Rate limiting**: Use multiple bot accounts for load balancing

### **Health Monitoring**
```bash
# Check bot manager status
curl http://localhost:5001/api/bot/health

# Get detailed bot status
curl http://localhost:5001/api/bot/status
```

## Production Deployment

### **Environment Variables**
```bash
export BOT_CONFIG_PATH="/path/to/bot_config.yaml"
export BOT_MANAGER_PORT="5001"
export BOT_HEADLESS="true"
```

### **Docker Configuration**
```yaml
version: '3.8'
services:
  bot-manager:
    build: .
    ports:
      - "5001:5001"
    volumes:
      - ./bot_config.yaml:/app/bot_config.yaml
    environment:
      - BOT_HEADLESS=true
```

### **Monitoring**
- Set up health checks for bot manager
- Monitor bot account status
- Track API usage and performance
- Implement proper logging and alerting