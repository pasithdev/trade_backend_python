# DigitalOcean App Platform Network Issue Resolution

## Problem
The app shows healthy internal logs but returns `ERR_QUIC_PROTOCOL_ERROR` and connection resets when accessed externally at `https://whale-app-864sn.ondigitalocean.app/`.

## Root Cause Analysis
- Internal health checks (`kube-probe/1.31`) succeed with `200` responses
- External `curl` tests show TLS handshake failures and connection resets
- This indicates a DigitalOcean edge/load balancer networking issue, not an application problem

## Immediate Fixes Applied

### 1. Updated `app.yaml` Configuration
- Removed `preserve_path_prefix` that may interfere with routing
- Added explicit `GUNICORN_CMD_ARGS` environment variable
- Reduced health check `initial_delay_seconds` from 30 to 20
- Added `PYTHONPATH` environment variable for proper module resolution

### 2. Enhanced Health Check Endpoint
- Added timestamp and environment info to `/health` response
- Switched to `jsonify()` for consistent JSON responses
- Added port and worker information for debugging

### 3. Created Diagnostics Script
- Added `diagnose.sh` for internal container debugging
- Includes network binding checks and process monitoring

## Resolution Steps

### Step 1: Deploy Current Changes
```bash
git add .
git commit -m "Fix DigitalOcean App Platform networking issues"
git push origin master
```

### Step 2: DigitalOcean Dashboard Actions
1. Go to **Apps → whale-app-864sn → Settings**
2. Under **Domains**, verify the default domain shows **Certificate: Active**
3. If certificate is "Provisioning" or "Failed", click **Retry**
4. Under **Components → web → Settings**:
   - Verify **HTTP Port** is set to `8080`
   - Check that **Routes** shows `/` as **Active**

### Step 3: Network Configuration Fix
1. In **Settings → Networking**:
   - **Disable HTTP/3 (QUIC)** - This often causes the `ERR_QUIC_PROTOCOL_ERROR`
   - Save settings and redeploy

### Step 4: Force Redeploy
- Click **Actions → Force Rebuild and Deploy**
- This refreshes edge routing and SSL certificates

### Step 5: Test External Access
After deployment completes (5-10 minutes):
```bash
curl -v https://whale-app-864sn.ondigitalocean.app/health
curl -v https://whale-app-864sn.ondigitalocean.app/
```

## Expected Results
- `200 OK` responses with proper HTML/JSON content
- No more connection resets or TLS errors
- External traffic showing in application logs

## If Issues Persist
1. Check DigitalOcean status page for platform issues
2. Try accessing from different networks/devices
3. Contact DigitalOcean support with error details:
   - App ID: whale-app-864sn
   - Error: Connection reset during TLS handshake
   - Internal health checks pass, external access fails

## Next Steps After Resolution
- Monitor application logs for external traffic
- Set up proper environment variables (API keys, etc.)
- Configure custom domain if needed
- Enable auto-scaling if traffic increases