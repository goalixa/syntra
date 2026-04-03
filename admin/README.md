# Syntra Admin Panel

A modern web-based admin interface for the Syntra AI DevOps orchestration service.

## Features

- **Authentication**: Secure admin access with token-based authentication
- **Dashboard Overview**: Real-time statistics and activity monitoring
- **Agent Management**: View and monitor AI agent status
- **Configuration**: Configure Syntra settings via web interface
- **Activity Logs**: Track all system activities and events
- **Responsive Design**: Works on desktop and mobile devices

## Access

The admin panel is served directly from the Syntra FastAPI application:

```
http://localhost:8000/admin
```

## Quick Start

### Local Development

1. Start the Syntra service:
   ```bash
   cd /Users/snapp/Desktop/projects/Goalixa/Services/syntra
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Open your browser:
   ```
   http://localhost:8000/admin
   ```

3. Click "Authenticate with Syntra" to access the admin panel

### Docker Deployment

```bash
docker build -t syntra:latest .
docker run -p 8000:8000 syntra:latest
```

Then access: `http://localhost:8000/admin`

## API Endpoints

### Authentication

- `POST /api/admin/auth` - Authenticate and receive access token

### Dashboard Data

- `GET /api/admin/overview` - Get dashboard statistics
- `GET /api/admin/agents` - Get agent status information

### Configuration

- `GET /api/admin/config` - Get current configuration
- `POST /api/admin/config` - Update configuration

### Logs

- `GET /api/admin/logs?limit=50&level=INFO` - Get activity logs with optional filtering

## Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `model` | LLM model to use (claude, gpt-4, gpt-3.5-turbo) | claude |
| `namespace` | Default Kubernetes namespace | production |
| `timeout` | Agent timeout in seconds | 300 |
| `debug` | Enable debug logging | false |
| `systemPrompt` | Custom AI instructions | empty |

## Architecture

```
┌─────────────────────────────────────────┐
│         Browser (Admin Panel)           │
│         /admin/static/                   │
└─────────────────┬───────────────────────┘
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌─────────────────────────────────┐   │
│  │  Static Files (/admin)          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Admin API (/api/admin/*)       │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## File Structure

```
syntra/
├── admin/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Main stylesheet
│   │   ├── js/
│   │   │   └── app.js             # Admin application logic
│   │   └── index.html             # Admin panel HTML
│   └── README.md                   # This file
├── api/
│   ├── admin_routes.py             # Admin API endpoints
│   ├── routes.py                   # Main API routes
│   └── schemas.py                  # Pydantic models
└── main.py                         # FastAPI app entry point
```

## Security Considerations

### Current State (Development)
- Demo authentication (accepts any request)
- Tokens stored in memory
- 24-hour token expiry
- No rate limiting

### Production Recommendations
1. **Integrate with Goalixa Auth Service**
   - Replace demo auth with proper JWT validation
   - Use existing auth service endpoints

2. **Add HTTPS Only**
   - Enforce HTTPS in production
   - Add secure cookie flags

3. **Implement Rate Limiting**
   - Add rate limiting middleware
   - Prevent brute force attacks

4. **Use Persistent Storage**
   - Store configuration in database
   - Persist audit logs

5. **Add RBAC**
   - Role-based access control
   - Different permission levels

## Development

### Modifying the UI

The admin panel uses vanilla JavaScript with no build process:

1. **HTML**: `admin/static/index.html`
2. **CSS**: `admin/static/css/style.css`
3. **JavaScript**: `admin/static/js/app.js`

Simply edit files and refresh your browser (no compilation needed).

### Adding New API Endpoints

1. Add endpoint to `api/admin_routes.py`
2. Add corresponding method in `admin/static/js/app.js`
3. Update the UI to display the new data

### Styling

The admin panel uses CSS custom properties for theming. Modify `:root` in `style.css`:

```css
:root {
  --color-primary: #6366f1;
  --color-bg: #0f172a;
  --color-bg-card: #1e293b;
  /* ... more colors */
}
```

## Troubleshooting

### Admin panel not loading
- Check that the Syntra service is running
- Verify port 8000 is accessible
- Check browser console for errors

### Authentication failing
- Verify admin routes are properly registered in main.py
- Check that `/api/admin/auth` endpoint is accessible
- Review logs for authentication errors

### Configuration not saving
- Check browser console for API errors
- Verify `/api/admin/config` POST endpoint is working
- Check FastAPI logs for errors

## Monitoring

Check admin panel usage via logs:

```bash
# View all admin activity
curl http://localhost:8000/api/admin/logs

# View only errors
curl http://localhost:8000/api/admin/logs?level=ERROR
```

## Contributing

When adding features to the admin panel:

1. Update both frontend (`admin/static/`) and backend (`api/admin_routes.py`)
2. Maintain the existing design system
3. Add proper error handling
4. Document new API endpoints
5. Test authentication flow

## License

Same as parent Syntra project.
