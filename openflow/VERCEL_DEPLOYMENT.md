# Vercel Deployment Guide for OpenFlow

This guide walks you through deploying OpenFlow to Vercel with all necessary configurations.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Database with Connection Pooling**: Choose one of:
   - [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres) (Recommended for simplicity)
   - [Neon](https://neon.tech) (Serverless Postgres with built-in pooling)
   - [Supabase](https://supabase.com) (Postgres with connection pooler)
3. **Redis**: [Upstash Redis](https://upstash.com) (Serverless Redis)
4. **Vercel CLI** (optional): `npm i -g vercel`

## Step-by-Step Deployment

### 1. Prepare External Services

#### A. Setup Postgres Database (Choose one)

**Option 1: Vercel Postgres (Easiest)**
```bash
# In your Vercel project dashboard
1. Go to Storage tab
2. Click "Create Database"
3. Select "Postgres"
4. Copy the connection string (it includes pooling)
```

**Option 2: Neon (Recommended)**
```bash
# Visit https://neon.tech
1. Create a new project
2. Get the "Pooled connection" string from dashboard
3. Use port 5432 (not 5433)
4. Format: postgresql+asyncpg://user:pass@host.region.neon.tech:5432/dbname
```

**Option 3: Supabase**
```bash
# Visit https://supabase.com
1. Create a new project
2. Go to Database settings
3. Use "Connection pooling" URL (port 6543)
4. Transaction mode for better performance
```

#### B. Setup Redis (Upstash)

```bash
# Visit https://upstash.com
1. Create a new Redis database
2. Choose region close to your Vercel deployment
3. Copy the connection URL (starts with rediss://)
4. Format: rediss://default:password@redis-host.upstash.io:6379
```

### 2. Configure Vercel Project

#### A. Connect Repository

```bash
# Option 1: Using Vercel Dashboard
1. Go to https://vercel.com/new
2. Import your Git repository
3. Select the repository
4. Set root directory to: openflow

# Option 2: Using Vercel CLI
cd openflow
vercel link
```

#### B. Configure Build Settings

In Vercel Dashboard → Project Settings → General:

```
Framework Preset: Other
Root Directory: openflow
Build Command: (leave empty)
Output Directory: (leave empty)
Install Command: pip install -r requirements-vercel.txt
```

### 3. Set Environment Variables

Go to Vercel Dashboard → Project Settings → Environment Variables

Add all variables from `.env.vercel.example`:

#### Required Variables (Set for all environments: Production, Preview, Development)

```bash
# Generate a secret key first
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Then add these variables:
ENVIRONMENT=production
DEBUG=false
SERVERLESS=true
SECRET_KEY=<your-generated-secret-key>
DATABASE_URL=<your-postgres-connection-string>
REDIS_URL=<your-upstash-redis-url>
```

#### CORS Configuration

```bash
# Add your Vercel domain
CORS_ORIGINS=["https://your-app.vercel.app","https://*.vercel.app"]
```

#### Optional Variables

```bash
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
LOG_LEVEL=INFO
DATABASE_POOL_SIZE=1
DATABASE_MAX_OVERFLOW=0
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_PRE_PING=true
```

### 4. Run Database Migrations

**IMPORTANT**: Run migrations before deploying!

```bash
# Option 1: Locally with production database
cd openflow
export DATABASE_URL="<your-production-database-url>"
poetry run alembic upgrade head

# Option 2: Using a separate migration script
# Create a one-time Vercel function to run migrations
# (Not recommended for production)
```

### 5. Deploy to Vercel

#### Option 1: Automatic Deployment (Recommended)

```bash
# Push to your main branch
git push origin main

# Vercel will automatically deploy
# Check deployment status at https://vercel.com/dashboard
```

#### Option 2: Manual Deployment with CLI

```bash
cd openflow

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### 6. Verify Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.vercel.app/health

# Root endpoint
curl https://your-app.vercel.app/

# Frontend (should load the web client)
curl https://your-app.vercel.app/web

# Static files
curl https://your-app.vercel.app/static/js/app.js
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Symptom**: "connection refused" or "too many connections"

**Solution**:
- Ensure you're using a connection pooler (Neon, Supabase pooler, or PgBouncer)
- Verify `DATABASE_POOL_SIZE=1` and `DATABASE_MAX_OVERFLOW=0` in Vercel
- Check SSL is enabled: add `?sslmode=require` to connection string

#### 2. Static Files Not Loading

**Symptom**: 404 errors for `/static/*` files

**Solution**:
- Verify `vercel.json` routes are correct
- Check files exist in `/web/static/` directory
- Ensure `.vercelignore` doesn't exclude static files

#### 3. CORS Errors

**Symptom**: Browser console shows CORS errors

**Solution**:
- Update `CORS_ORIGINS` to include your Vercel domain
- Use wildcard: `["https://*.vercel.app"]`
- Check that credentials are allowed if using authentication

#### 4. Cold Start Timeout

**Symptom**: First request times out or is very slow

**Solution**:
- Serverless mode is enabled (skips heavy initialization)
- Increase function timeout in `vercel.json` (max 10s for hobby)
- Consider upgrading to Vercel Pro for 60s timeout

#### 5. Module Import Errors

**Symptom**: "No module named X" errors

**Solution**:
- Verify `requirements-vercel.txt` includes all dependencies
- Check Python version compatibility (Vercel uses 3.9)
- Add missing packages to `requirements-vercel.txt`

### Performance Optimization

#### 1. Enable Vercel Edge Caching

Add cache headers to static responses:

```python
# In main.py
@app.get("/health")
async def health_check():
    return Response(
        content='{"status":"healthy"}',
        headers={"Cache-Control": "public, max-age=60"}
    )
```

#### 2. Use Vercel Edge Functions (Advanced)

Convert lightweight endpoints to Edge Functions for global distribution.

#### 3. Optimize Database Queries

- Use connection pooler (Neon, Supabase)
- Add database indexes for frequently queried fields
- Enable query result caching in Redis

## Monitoring and Logs

### View Logs

```bash
# Using Vercel CLI
vercel logs <deployment-url>

# Or in Vercel Dashboard
Project → Deployments → Click deployment → View Function Logs
```

### Setup Monitoring

1. **Vercel Analytics**: Enable in Project Settings → Analytics
2. **Error Tracking**: Integrate Sentry or similar
3. **Database Monitoring**: Use Neon/Supabase built-in monitoring

## Continuous Deployment

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./openflow
```

## Local Testing with Vercel

Test serverless mode locally:

```bash
cd openflow

# Install Vercel CLI
npm i -g vercel

# Set environment variables locally
cp .env.vercel.example .env

# Edit .env with your values
# Make sure SERVERLESS=true

# Run Vercel dev server
vercel dev

# Test endpoints
curl http://localhost:3000/health
curl http://localhost:3000/web
```

## Production Checklist

Before going live, verify:

- [ ] Database connection pooler is configured
- [ ] Redis (Upstash) is set up and connected
- [ ] All environment variables are set in Vercel
- [ ] `SECRET_KEY` is a strong, random value
- [ ] Database migrations are applied
- [ ] `DEBUG=false` in production
- [ ] `SERVERLESS=true` is set
- [ ] CORS origins include your domain
- [ ] Health check endpoint returns 200
- [ ] Frontend loads correctly at `/web`
- [ ] API endpoints respond (test `/jsonrpc`, `/api/v1/...`)
- [ ] Authentication flow works
- [ ] Monitoring/logging is configured

## Cost Considerations

### Free Tier Limits (Vercel Hobby)

- **Functions**: 100GB-hours/month
- **Function Duration**: 10 seconds max
- **Deployments**: Unlimited
- **Bandwidth**: 100GB/month

### Recommended Upgrades

If you exceed free tier:

1. **Vercel Pro** ($20/month): 1000GB-hours, 60s timeout
2. **Neon Pro** ($19/month): Better performance, more storage
3. **Upstash** (Pay-as-you-go): Scales with usage

## Security Best Practices

1. **Never commit secrets**: Use `.env` files locally, environment variables in Vercel
2. **Rotate secrets regularly**: Update `SECRET_KEY` periodically
3. **Use HTTPS only**: Vercel provides automatic HTTPS
4. **Enable rate limiting**: Add rate limiting middleware
5. **Monitor access logs**: Review Vercel function logs regularly
6. **Use strong database passwords**: Generate with password manager
7. **Restrict CORS origins**: Only allow your actual domains

## Support

For issues:

- **Vercel Docs**: https://vercel.com/docs
- **Neon Docs**: https://neon.tech/docs
- **Upstash Docs**: https://docs.upstash.com
- **OpenFlow Issues**: Create issue in GitHub repository

## Next Steps

After successful deployment:

1. Set up custom domain in Vercel Dashboard
2. Configure SSL certificate (automatic with Vercel)
3. Set up monitoring and alerts
4. Create preview deployments for testing
5. Document any custom configurations
6. Set up backup strategy for database

---

**Note**: Serverless deployment has limitations. For production workloads with heavy background processing, consider traditional hosting (Railway, Render, Fly.io).
