# Direct Cloudflare API Deployment

## Get API Token
1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Create token with permissions:
   - Zone:Zone:Read
   - Zone:Zone Settings:Edit
   - Account:Cloudflare Workers:Edit
   - Account:Page:Edit

## Set Environment Variable
```cmd
set CLOUDFLARE_API_TOKEN=your-token-here
```

## Deploy
```cmd
node deploy-api.js
```

## Alternative: Use Cloudflare Dashboard
1. **Workers**: Copy `src/worker.js` → Workers & Pages → Create
2. **Pages**: Upload `public/` folder → Pages → Upload assets

## Account ID Required
Find at: https://dash.cloudflare.com → Right sidebar