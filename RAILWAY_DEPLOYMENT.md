# Railway Deployment Guide - Enhanced Reading Practice Platform

## Overview

This guide covers deploying the Enhanced Reading Practice Platform to Railway.app. The deployment includes a Django REST API backend, React TypeScript frontend, PostgreSQL database, and Redis cache.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code must be in a GitHub repository
3. **Railway CLI** (optional): Install with `npm install -g @railway/cli`

## Quick Deployment (Recommended)

### Option 1: Deploy Button (One-Click)

1. **Fork this repository** to your GitHub account
2. **Click Deploy to Railway**: [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
3. **Connect your GitHub** account and select the forked repository
4. **Configure environment variables** (see section below)
5. **Deploy** - Railway will automatically build and deploy your application

### Option 2: Manual Deployment

#### Step 1: Create Railway Project

1. Visit [railway.app/new](https://railway.app/new)
2. Connect your GitHub account
3. Select the "Enhanced Reading Practice Platform" repository
4. Railway will automatically detect the Django application

#### Step 2: Add Database Services

1. **Add PostgreSQL**:
   - In your Railway project dashboard
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create `DATABASE_URL` environment variable

2. **Add Redis** (optional but recommended):
   - Click "New" → "Database" → "Add Redis"
   - Railway will create `REDIS_URL` environment variable

#### Step 3: Configure Environment Variables

In your Railway project settings, add these environment variables:

```bash
# Required
DEBUG=False
SECRET_KEY=your_super_secure_secret_key_here_minimum_50_characters
ALLOWED_HOSTS=your-app-name.railway.app

# Database (automatically set by Railway when you add PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Redis (automatically set by Railway when you add Redis)
REDIS_URL=redis://host:port

# Optional Security Settings
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_SSL_REDIRECT=True
```

#### Step 4: Deploy

1. Click **"Deploy"** in your Railway dashboard
2. Railway will automatically:
   - Install Python dependencies
   - Run database migrations
   - Collect static files
   - Start the Gunicorn server

#### Step 5: Verify Deployment

1. **Check deployment logs** for any errors
2. **Visit health check**: `https://your-app.railway.app/health/`
3. **Test API endpoints**: `https://your-app.railway.app/api/auth/`
4. **Access admin panel**: `https://your-app.railway.app/admin/`

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Django debug mode | `False` |
| `SECRET_KEY` | Django secret key | `your_50_character_secret_key` |
| `ALLOWED_HOSTS` | Allowed host domains | `your-app.railway.app,custom-domain.com` |

### Database Variables (Auto-configured)

| Variable | Description | Auto-Set by Railway |
|----------|-------------|---------------------|
| `DATABASE_URL` | PostgreSQL connection URL | ✅ Yes |
| `REDIS_URL` | Redis connection URL | ✅ Yes |

### Optional Security Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECURE_HSTS_SECONDS` | HTTPS Strict Transport Security | `31536000` |
| `SECURE_SSL_REDIRECT` | Force HTTPS redirect | `True` |
| `SESSION_COOKIE_SECURE` | Secure session cookies | `True` |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookies | `True` |

### Optional Feature Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_HOST` | SMTP server for notifications | Not set |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | Not set |
| `EMAIL_HOST_PASSWORD` | SMTP password | Not set |

## Post-Deployment Setup

### 1. Create Superuser

Using Railway CLI:

```bash
railway login
railway link [your-project-id]
railway run python backend/manage.py createsuperuser
```

Or via Railway dashboard:
1. Go to your service → "Variables" tab
2. Add a temporary variable: `CREATE_SUPERUSER=yes`
3. Redeploy the service
4. Remove the variable after superuser is created

### 2. Load Sample Data (Optional)

```bash
# Via Railway CLI
railway run python backend/manage.py loaddata sample_data.json

# Or create sample data
railway run python backend/create_sample_data.py
```

### 3. Configure Custom Domain (Optional)

1. In Railway dashboard → "Settings" tab
2. Add your custom domain in "Domains" section
3. Update DNS records as instructed
4. Add domain to `ALLOWED_HOSTS` environment variable

## Frontend Deployment Options

### Option A: Separate Frontend Service (Recommended)

1. **Create new service** in same Railway project
2. **Set build command**: `cd frontend && npm run build`
3. **Set start command**: `cd frontend && npm start`
4. **Configure environment variables**:
   ```
   REACT_APP_API_URL=https://your-backend.railway.app/api
   REACT_APP_ENVIRONMENT=production
   ```

### Option B: Integrated Frontend (Django serves React)

The current configuration serves the React frontend through Django using WhiteNoise:

1. React build files are served at `/static/`
2. API endpoints available at `/api/`
3. Admin interface at `/admin/`

## Monitoring and Maintenance

### Health Checks

Railway automatically monitors these endpoints:
- **Basic Health**: `/health/`
- **Detailed Health**: `/health/detailed/`
- **Readiness Probe**: `/health/ready/`
- **Liveness Probe**: `/health/live/`

### Logs and Debugging

Access logs via:
1. **Railway Dashboard**: "Deployments" tab → View logs
2. **Railway CLI**: `railway logs`
3. **Real-time logs**: `railway logs --follow`

### Performance Monitoring

The application includes built-in monitoring:
- **Request performance tracking**
- **Database query monitoring**
- **Security event logging**
- **System health metrics**

### Scaling

Railway automatically scales your application:
- **Horizontal scaling**: Add more instances during high load
- **Vertical scaling**: Increase memory/CPU as needed
- **Database scaling**: PostgreSQL automatically scales

## Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

**Problem**: CSS/JS files return 404 errors

**Solution**:
```bash
# Via Railway CLI
railway run python backend/manage.py collectstatic --noinput
```

#### 2. Database Connection Issues

**Problem**: Application can't connect to database

**Solution**:
1. Verify `DATABASE_URL` is set in environment variables
2. Check PostgreSQL service is running in Railway dashboard
3. Ensure database migrations completed: `railway run python backend/manage.py migrate`

#### 3. Import/Module Errors

**Problem**: Python module import errors

**Solution**:
1. Check all dependencies are in `requirements.txt`
2. Verify Python version compatibility
3. Redeploy with clean build: Delete deployment and redeploy

#### 4. CORS Issues

**Problem**: Frontend can't connect to backend API

**Solution**:
1. Update `ALLOWED_HOSTS` with correct domains
2. Check CORS settings in Django settings
3. Verify API URLs in frontend configuration

### Debug Commands

```bash
# Check service status
railway status

# Run Django shell
railway run python backend/manage.py shell

# Run database migrations
railway run python backend/manage.py migrate

# Create superuser
railway run python backend/manage.py createsuperuser

# Run security audit
railway run python backend/manage.py security_audit

# Check Django deployment
railway run python backend/manage.py check --deploy
```

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Database migrations completed
- [ ] Superuser account created
- [ ] Health check endpoints responding
- [ ] Security audit passed
- [ ] SSL certificate working
- [ ] Custom domain configured (if applicable)
- [ ] Email notifications configured (if needed)
- [ ] Monitoring and logging verified
- [ ] Backup strategy implemented

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Railway       │    │   Railway       │    │   Railway       │
│   Frontend      │────│   Backend       │────│   PostgreSQL    │
│   (React)       │    │   (Django)      │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Railway       │
                       │   Redis Cache   │
                       └─────────────────┘
```

## Support

For deployment issues:
- **Railway Documentation**: [docs.railway.com](https://docs.railway.com)
- **Railway Discord**: [railway.community](https://railway.community)
- **Project Issues**: Check the project's GitHub issues page

---

The Enhanced Reading Practice Platform is optimized for Railway deployment with automatic scaling, monitoring, and production-ready configurations. 🚀