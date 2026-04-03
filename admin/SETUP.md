# Syntra Admin Panel - Setup Guide

## What Was Created

A complete admin panel for Syntra with the following structure:

```
syntra/
├── admin/
│   ├── static/
│   │   ├── index.html          # Main admin interface
│   │   ├── css/
│   │   │   └── style.css       # Modern dark theme styles
│   │   └── js/
│   │       └── app.js          # Frontend application logic
│   ├── README.md               # Full documentation
│   └── SETUP.md                # This file
├── api/
│   ├── __init__.py             # Package initialization
│   └── admin_routes.py         # Admin API endpoints
└── main.py                     # Updated with admin panel
```

## Features Implemented

### Authentication Flow
- Login screen with "Authenticate with Syntra" button
- Token-based authentication (24-hour expiry)
- Automatic logout on token expiry
- Session persistence via localStorage

### Dashboard Views
1. **Overview** - System statistics and recent activity
2. **Agents** - Status and performance of all AI agents
3. **Configuration** - Web-based settings management
4. **Activity Logs** - System event tracking

### Admin API Endpoints
- `POST /api/admin/auth` - Authentication
- `GET /api/admin/overview` - Dashboard data
- `GET /api/admin/agents` - Agent status
- `GET /api/admin/config` - Get configuration
- `POST /api/admin/config` - Update configuration
- `GET /api/admin/logs` - Activity logs

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/snapp/Desktop/projects/Goalixa/Services/syntra
pip install -r requirements.txt
```

### 2. Start the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access Admin Panel
Open browser to: `http://localhost:8000/admin`

## Configuration Options

Configure these settings via the admin UI:

| Setting | Description | Default |
|---------|-------------|---------|
| LLM Model | AI model (claude, gpt-4, gpt-3.5-turbo) | claude |
| Namespace | Kubernetes namespace | production |
| Timeout | Agent timeout (seconds) | 300 |
| Debug Logging | Enable verbose logs | false |
| System Prompt | Custom AI instructions | empty |

## Design System

The admin panel uses a modern dark theme:

- **Colors**: Deep blue-gray background with indigo accents
- **Typography**: Inter font family
- **Layout**: Sidebar navigation with main content area
- **Components**: Cards, buttons, forms, tables

## Tech Stack

- **Frontend**: Vanilla JavaScript (no framework)
- **Backend**: FastAPI
- **Styling**: Custom CSS with CSS custom properties
- **Architecture**: RESTful API + Single Page Application

## Next Steps

### Production Security
Replace the demo authentication with proper auth integration:

```python
# In api/admin_routes.py
async def authenticate(request: AuthRequest):
    # Call Goalixa Auth Service
    # Validate JWT tokens
    # Return proper user data
    pass
```

### Database Integration
Replace in-memory storage with persistent database:

```python
# Store configuration in database
# Persist activity logs
# Cache frequently accessed data
```

### Additional Features
Consider adding:
- Real-time updates via WebSockets
- Agent task management interface
- Kubernetes cluster viewer
- Performance metrics dashboard
- User management (if multi-tenant)

## Troubleshooting

### Port Already in Use
```bash
# Use different port
uvicorn main:app --port 8001
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Admin Panel Not Loading
1. Check server is running: `curl http://localhost:8000/health`
2. Verify static files: `ls -la admin/static/`
3. Check browser console for errors

## File Locations

- **Admin UI**: `syntra/admin/static/`
- **Admin API**: `syntra/api/admin_routes.py`
- **Main App**: `syntra/main.py`
- **Documentation**: `syntra/admin/README.md`

## Support

For issues or questions:
1. Check `syntra/admin/README.md` for detailed documentation
2. Review FastAPI logs for errors
3. Test API endpoints directly with curl

---

**Status**: ✅ Complete and ready to use
**Version**: 1.0.0
**Last Updated**: 2025-04-03
