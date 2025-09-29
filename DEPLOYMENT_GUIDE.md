# DigitalOcean App Platform Deployment Guide

## 📋 Prerequisites

1. **GitHub Repository**: Push your code to a GitHub repository
2. **DigitalOcean Account**: Sign up at [digitalocean.com](https://digitalocean.com)
3. **Binance API Keys**: Get your API keys from [Binance API Management](https://www.binance.com/en/my/settings/api-management)

## 🚀 Deployment Steps

### Step 1: Prepare Repository

Your repository now includes:
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version (3.11.10)
- ✅ `Procfile` - Gunicorn start command
- ✅ `app.yaml` - DigitalOcean configuration (optional)

### Step 2: Create App on DigitalOcean

1. **Go to DigitalOcean Control Panel**
   - Navigate to **Apps** → **Create App**

2. **Connect Repository**
   - **Source**: Choose GitHub
   - **Repository**: Select your crypto trading repository
   - **Branch**: Select `main` or your deployment branch

3. **Configure Service**
   - **Component Type**: Web Service
   - **Environment**: Python (auto-detected)
   - **Run Command**: `gunicorn --bind 0.0.0.0:$PORT src.main:app --timeout 120 --workers 2`
   - **HTTP Port**: 8080

### Step 3: Set Environment Variables

In the DigitalOcean App Platform, add these environment variables:

#### Required Variables:
```
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-this-to-something-secure
BINANCE_API_KEY=your-binance-api-key (mark as SECRET)
BINANCE_SECRET_KEY=your-binance-secret-key (mark as SECRET)
BINANCE_TESTNET=false
```

#### Optional Variables:
```
LOG_LEVEL=INFO
PORT=8080
```

### Step 4: Configure Resources

- **Plan**: Basic ($5/month recommended for testing)
- **Region**: Choose closest to your location
- **Scaling**: 1 instance (can scale later)

### Step 5: Deploy

1. Click **Next** → **Review** → **Create Resources**
2. Wait for deployment (usually 5-10 minutes)
3. Your app will be available at: `https://your-app-name.ondigitalocean.app`

## 🔧 Post-Deployment Configuration

### Configure Binance API

Once deployed, configure your Binance API:

```bash
curl -X POST https://your-app-name.ondigitalocean.app/api/binance/config \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-binance-api-key",
    "api_secret": "your-binance-secret-key", 
    "testnet": false
  }'
```

### Test Webhooks

Your webhook endpoints will be available at:
- `https://your-app-name.ondigitalocean.app/api/binance/state-aware-ma-cross-webhook`
- `https://your-app-name.ondigitalocean.app/api/tradingview/binancebinance/state-aware-ma-cross-webhook`

## 📡 TradingView Integration

Update your TradingView alerts to use the production URL:

**Webhook URL:**
```
https://your-app-name.ondigitalocean.app/api/tradingview/binancebinance/state-aware-ma-cross-webhook
```

**Alert Message:**
```json
{"action": "buy", "symbol": "{{ticker}}", "balance_percentage": "0.20", "leverage": "10", "entry": "{{close}}"}
```

## 🔍 Monitoring & Logs

- **App Logs**: Available in DigitalOcean Control Panel → Apps → Your App → Runtime Logs
- **Metrics**: Monitor CPU, Memory, and Request metrics
- **Health Check**: App Platform automatically monitors your app health

## 🛡️ Security Best Practices

1. **Environment Variables**: Always use environment variables for sensitive data
2. **API Keys**: Mark Binance API keys as "SECRET" in DigitalOcean
3. **HTTPS**: DigitalOcean provides free SSL certificates
4. **IP Whitelist**: Consider whitelisting DigitalOcean's IP ranges in Binance

## 🔄 Updates & Maintenance

- **Auto Deploy**: Enable auto-deploy from your GitHub branch
- **Manual Deploy**: Use DigitalOcean Control Panel to trigger deployments
- **Scaling**: Increase instances or upgrade plan as needed

## 📞 Support

- **DigitalOcean Docs**: [App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- **Community**: [DigitalOcean Community](https://www.digitalocean.com/community/)

## 🎯 Quick Test

After deployment, test your app:

```bash
# Health check
curl https://your-app-name.ondigitalocean.app/

# Test webhook configuration
curl https://your-app-name.ondigitalocean.app/api/binance/test-state-aware-ma-cross
```

Your crypto trading system is now live and ready for automated trading! 🚀
