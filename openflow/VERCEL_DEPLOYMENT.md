# Quick Vercel Deployment for Testing

⚠️ **WARNING**: This guide sets up an INSECURE deployment for testing only. No authentication or security is configured. Implement proper security before production use!

## 5-Minute Quick Start

### 1. Setup Free Services (2 minutes)

#### Get a Free Postgres Database

**Option A: Neon (Recommended - Easiest)**
1. Go to [neon.tech](https://neon.tech)
2. Sign up (free)
3. Create a new project
4. Copy the **"Pooled connection"** string
5. Make sure it uses port **5432** (not 5433)
6. Format: `postgresql+asyncpg://user:pass@host.region.neon.tech:5432/dbname`

**Option B: Vercel Postgres**
1. In Vercel Dashboard → Your Project → Storage
2. Click "Create Database" → Select "Postgres"
3. Copy the connection string

#### Get Free Redis

1. Go to [console.upstash.com/redis](https://console.upstash.com/redis)
2. Sign up (free)
3. Create a new database
4. Copy the connection URL (starts with `rediss://`)

### 2. Deploy to Vercel (3 minutes)

#### Connect Your Repository

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. Configure project:
   - **Root Directory**: `openflow`
   - **Framework Preset**: Other
   - **Build Command**: (leave empty)
   - **Install Command**: `pip install -r requirements-vercel.txt`

#### Set Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables, add these 3 variables:

```bash
SERVERLESS=true
DATABASE_URL=<your-neon-or-vercel-postgres-url>
REDIS_URL=<your-upstash-redis-url>
```

Make sure to set them for **all environments** (Production, Preview, Development).

#### Deploy

Click "Deploy" and wait ~2 minutes.

### 3. Test Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.vercel.app/health

# Root endpoint
curl https://your-app.vercel.app/

# Web interface (open in browser)
https://your-app.vercel.app/web

# Static files
https://your-app.vercel.app/static/js/app.js
```

## That's It!

Your app should be running. The frontend is accessible at `/web` and all API endpoints work without authentication.

---

## Troubleshooting

### "502 Bad Gateway" or "Function Timeout"

- **Cause**: Cold start taking too long or database connection issues
- **Fix**: Check function logs in Vercel Dashboard → Deployments → Function Logs
- **Fix**: Verify DATABASE_URL is correct and uses connection pooling

### "Connection refused" to database

- **Cause**: Wrong database URL or SSL required
- **Fix**: Use the **pooled connection** string from Neon (not direct)
- **Fix**: Add `?sslmode=require` to the end of DATABASE_URL if needed

### Static files return 404

- **Cause**: Routing issue
- **Fix**: Check `vercel.json` routes are configured correctly
- **Fix**: Verify files exist in `/openflow/web/static/`

### CORS errors in browser

- **Cause**: Origin not allowed
- **Fix**: Add your domain to `CORS_ORIGINS` in Vercel env variables
- **Fix**: Or set `CORS_ORIGINS=["*"]` for testing (insecure!)

### Module import errors

- **Cause**: Missing dependencies
- **Fix**: Check `requirements-vercel.txt` includes all needed packages
- **Fix**: Redeploy after updating requirements

---

## Next Steps

### Before Production Use

1. ❌ **Implement Authentication**: Currently ALL endpoints are public
2. ❌ **Add Authorization**: Implement role-based access control
3. ❌ **Set DEBUG=false**: Disable debug mode
4. ❌ **Use Production Environment**: Change `ENVIRONMENT=production`
5. ❌ **Generate Secret Key**: Create strong `SECRET_KEY` for JWT tokens
6. ❌ **Configure CORS Properly**: Restrict to your actual domains
7. ❌ **Enable HTTPS Only**: Vercel does this automatically
8. ❌ **Add Rate Limiting**: Prevent abuse
9. ❌ **Setup Monitoring**: Use Vercel Analytics or Sentry
10. ❌ **Database Backups**: Configure automated backups

### Optional Enhancements

- **Custom Domain**: Add in Vercel Dashboard → Project Settings → Domains
- **Preview Deployments**: Automatic for each PR
- **Environment-Specific Config**: Different settings for prod/preview/dev
- **Vercel Cron**: For scheduled tasks (replaces Celery)

---

## What's Working

✅ FastAPI backend running serverless
✅ Vanilla JavaScript frontend (no build needed)
✅ Static file serving via Vercel routes
✅ JSON-RPC API (`/jsonrpc`)
✅ REST API (`/api/v1/*`)
✅ Database connections (via pooling)
✅ Redis caching
✅ Fast cold starts (~1-3s)

## What's NOT Working

❌ Authentication/Authorization (disabled for testing)
❌ Celery background tasks (use Vercel Cron instead)
❌ Module system (disabled for faster cold starts)
❌ File uploads > 4.5MB (Vercel limit)
❌ Long-running requests > 10s (Hobby tier limit)

---

## Free Tier Limits

**Vercel (Hobby)**:
- 100GB-hours compute/month
- 10s function timeout
- 100GB bandwidth/month
- Unlimited deployments

**Neon (Free)**:
- 512MB storage
- 1 project
- Unlimited queries

**Upstash (Free)**:
- 10,000 commands/day
- 256MB storage
- Global edge caching

---

## Viewing Logs

### Via Vercel Dashboard
1. Go to your project
2. Click "Deployments"
3. Click on a deployment
4. Click "View Function Logs"

### Via Vercel CLI
```bash
npm i -g vercel
vercel logs <deployment-url>
```

---

## Local Testing with Serverless Mode

Test locally before deploying:

```bash
cd openflow

# Copy env template
cp .env.vercel.example .env

# Edit .env with your database and Redis URLs
nano .env

# Make sure these are set:
# SERVERLESS=true
# DATABASE_URL=<your-db-url>
# REDIS_URL=<your-redis-url>

# Run locally
poetry run uvicorn openflow.server.main:app --reload

# Test
curl http://localhost:8000/health
open http://localhost:8000/web
```

Or use Vercel dev server:

```bash
npm i -g vercel
cd openflow
vercel dev
```

---

## When to Use Traditional Hosting Instead

Consider Railway, Render, or Fly.io if you need:

- Celery/background workers
- WebSocket connections
- Large file uploads
- Long-running processes (>60s)
- Persistent filesystem
- Always-warm instances

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Neon Docs**: https://neon.tech/docs
- **Upstash Docs**: https://docs.upstash.com

**Remember**: This is for testing only. Implement security before production!
