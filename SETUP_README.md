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
curl -X POST http://localhost:5000/api/analyze \
     -H 'Content-Type: application/json' \
     -d '{"target_user_id": "123456789"}'
```

## Bot Account Requirements

- **Dedicated Instagram accounts** (not your main account)
- **No followers** or very few followers
- **Strong passwords**
- **Accounts used only for this purpose**

## Security Notes

- `bot_config.yaml` contains sensitive credentials
- Never commit this file to version control
- Keep the file secure and restrict access
- The file is automatically ignored by git

## Troubleshooting

**Bot login fails:**
- Check username/password in `bot_config.yaml`
- Verify the Instagram account isn't locked
- Try logging in manually first

**No bots available:**
- Check bot status: `curl http://localhost:5001/api/bot/status`
- Verify bots are enabled in configuration
- Check bot manager logs

**API server can't connect:**
- Ensure bot manager is running on port 5001
- Check bot manager health: `curl http://localhost:5001/api/bot/health`
