# Cloudflare Deployment Guide

## Account: dr.mf.12298@gmail.com

### Prerequisites
1. Install Node.js (18+)
2. Install Wrangler CLI: `npm install -g wrangler`
3. Login to Cloudflare: `wrangler login`

### Deploy Worker (Backend)
```bash
cd "v:\NCCI Rejection\Khamis-hnh.jisr\July 2025\Tawnia-Analysis"
wrangler publish
```

### Deploy Pages (Frontend)
1. Go to Cloudflare Dashboard → Pages
2. Connect to Git or upload files
3. Upload `public/` directory
4. Set build command: `npm run build:frontend`
5. Set output directory: `public`

### Required Environment Variables
```
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-32-char-encryption-key
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=900000
```

### KV Namespaces to Create
1. `ANALYTICS_DATA` - for caching analytics data
2. `USER_SESSIONS` - for session management

### R2 Buckets to Create
1. `tawnia-analytics-files` - for file storage

### Custom Domain Setup
1. Add domain: `analytics.tawnia.com`
2. Configure DNS: CNAME to worker subdomain
3. Enable SSL/TLS

### Post-Deployment
1. Test endpoints: `/api/health`, `/api/analytics`
2. Verify file upload functionality
3. Check security headers
4. Monitor performance metrics