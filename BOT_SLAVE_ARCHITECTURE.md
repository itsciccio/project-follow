# Instagram Bot Slave Architecture

## Overview

This document describes the bot slave architecture that integrates with your existing Instagram API server. The bot slaves act as "session providers" that maintain persistent Instagram logins and provide session data to your main API server.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING API SERVER                         │
│                    (Port 5000)                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Job Queue     │  │  Job Processor  │  │  API Endpoints  │ │
│  │                 │  │                 │  │                 │ │
│  │ - Queues jobs   │  │ - Processes     │  │ - /api/analyze  │ │
│  │ - Manages       │  │   jobs          │  │ - /api/status   │ │
│  │   concurrency   │  │ - Requests bot  │  │ - /api/queue    │ │
│  │                 │  │   sessions      │  │ - /api/health   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP Requests
                                │ (Request/Release Bot Sessions)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BOT SLAVE MANAGER                             │
│                    (Port 5001)                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Bot Pool       │  │  Session        │  │  Health         │ │
│  │  Manager        │  │  Manager        │  │  Monitor        │ │
│  │                 │  │                 │  │                 │ │
│  │ - Manages bot   │  │ - Provides      │  │ - Monitors bot  │ │
│  │   availability  │  │   session data  │  │   health        │ │
│  │ - Load balances │  │ - Refreshes     │  │ - Auto-refresh  │ │
│  │   requests      │  │   sessions      │  │   sessions      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Manages
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BOT SLAVES                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Bot 1     │  │   Bot 2     │  │   Bot 3     │  │   ...   │ │
│  │             │  │             │  │             │  │         │ │
│  │ - Selenium  │  │ - Selenium  │  │ - Selenium  │  │         │ │
│  │   Browser   │  │   Browser   │  │   Browser   │  │         │ │
│  │ - Instagram │  │ - Instagram │  │ - Instagram │  │         │ │
│  │   Session   │  │   Session   │  │   Session   │  │         │ │
│  │ - Cookies   │  │ - Cookies   │  │ - Cookies   │  │         │ │
│  │   Storage   │  │   Storage   │  │   Storage   │  │         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Existing API Server (Port 5000)
- **Job Queue**: Manages incoming analysis requests
- **Job Processor**: Processes jobs using bot sessions
- **API Endpoints**: Provides REST API for users

### 2. Bot Slave Manager (Port 5001)
- **Bot Pool Manager**: Manages available bot slaves
- **Session Manager**: Provides session data to API server
- **Health Monitor**: Monitors bot health and refreshes sessions

### 3. Bot Slaves
- **Selenium Browsers**: Each bot runs a Chrome browser instance
- **Instagram Sessions**: Maintains logged-in Instagram sessions
- **Cookie Storage**: Persists session cookies between restarts

## Data Flow

### 1. User Request
```
User → POST /api/analyze {"target_user_id": "123456789"}
```

### 2. Job Creation
```
API Server → Creates job → Adds to queue
```

### 3. Bot Session Request
```
Job Processor → POST /api/bot/request → Bot Slave Manager
```

### 4. Bot Session Response
```
Bot Slave Manager → Returns bot session data → Job Processor
```

### 5. Analysis Execution
```
Job Processor → Uses bot session → Instagram API → Analysis
```

### 6. Bot Session Release
```
Job Processor → POST /api/bot/release → Bot Slave Manager
```

## Key Benefits

### 1. **Separation of Concerns**
- API server handles job management
- Bot manager handles session management
- Bot slaves handle Instagram interactions

### 2. **Scalability**
- Multiple bot slaves can be added
- Load balancing across bots
- Independent scaling of components

### 3. **Reliability**
- Bot health monitoring
- Automatic session refresh
- Graceful error handling

### 4. **Maintainability**
- Clear component boundaries
- Independent deployment
- Easy debugging and monitoring

## API Integration

### Bot Slave Manager Endpoints

#### Request Bot Session
```http
POST /api/bot/request
Response: {
  "success": true,
  "bot_data": {
    "bot_id": "bot_1",
    "csrf_token": "...",
    "session_id": "...",
    "user_id": "123456789",
    "cookies": [...],
    "last_login": "2024-01-15T10:30:00"
  }
}
```

#### Release Bot Session
```http
POST /api/bot/release
Body: {"bot_id": "bot_1"}
Response: {"success": true}
```

#### Get Bot Status
```http
GET /api/bot/status
Response: {
  "total_bots": 3,
  "available_bots": 2,
  "bots": {
    "bot_1": {
      "is_logged_in": true,
      "is_busy": false,
      "is_healthy": true,
      "last_activity": "2024-01-15T10:30:00"
    }
  }
}
```

## Deployment

### 1. Start Bot Slave Manager
```bash
python3 setup_bot_slaves.py
# Add bot slaves and start server
```

### 2. Start Main API Server
```bash
python3 instagram_api_server_with_bots.py
```

### 3. Test Integration
```bash
curl -X POST http://localhost:5000/api/analyze \
     -H 'Content-Type: application/json' \
     -d '{"target_user_id": "123456789"}'
```

## Configuration

### Bot Slave Manager Configuration
- **Port**: 5001 (configurable)
- **Bot Config Directory**: `bot_config/`
- **Health Check Interval**: 30 minutes
- **Session Timeout**: 24 hours

### Main API Server Configuration
- **Port**: 5000 (configurable)
- **Bot Manager URL**: `http://localhost:5001`
- **Max Concurrent Jobs**: 5
- **Job Cleanup Delay**: 30 minutes

## Monitoring

### Health Checks
- Bot slave manager health: `GET /api/bot/health`
- Main API server health: `GET /api/health`
- Bot status: `GET /api/bot/status`

### Logging
- Bot login/logout events
- Session refresh events
- Job processing events
- Error handling and recovery

## Security Considerations

### Bot Account Security
- Dedicated Instagram accounts
- Strong passwords
- Regular password rotation
- Account monitoring

### Network Security
- Internal communication between services
- Firewall rules
- HTTPS in production
- Access logging

### Data Protection
- Session data encryption
- Secure cookie storage
- No user credential storage
- Regular security audits

## Troubleshooting

### Common Issues

1. **No Available Bots**
   - Check bot login status
   - Verify bot health
   - Check session validity

2. **Bot Login Failures**
   - Verify credentials
   - Check account restrictions
   - Monitor Instagram changes

3. **Session Expiration**
   - Check health monitoring
   - Verify refresh logic
   - Monitor session age

4. **Communication Issues**
   - Check network connectivity
   - Verify service URLs
   - Check firewall rules

## Future Enhancements

### 1. **Database Integration**
- Persistent job storage
- Bot performance metrics
- User analytics

### 2. **Advanced Monitoring**
- Prometheus metrics
- Grafana dashboards
- Alerting system

### 3. **Load Balancing**
- Multiple bot managers
- Geographic distribution
- Auto-scaling

### 4. **Enhanced Security**
- OAuth integration
- Rate limiting
- DDoS protection

## Conclusion

This bot slave architecture provides a robust, scalable solution for maintaining persistent Instagram sessions while integrating seamlessly with your existing API server. The separation of concerns allows for independent scaling and maintenance of each component, while the HTTP API provides a clean interface for communication between services.

The system is designed to be production-ready with proper monitoring, error handling, and security considerations built in from the start.
