const https = require('https');
const fs = require('fs');
const path = require('path');

// Cloudflare API deployment script
const CLOUDFLARE_API = 'https://api.cloudflare.com/client/v4';
const EMAIL = 'dr.mf.12298@gmail.com';
const API_TOKEN = process.env.CLOUDFLARE_API_TOKEN; // Set this in environment

async function deployWorker() {
  const workerScript = fs.readFileSync('src/worker.js', 'utf8');
  
  const options = {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/javascript'
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(`${CLOUDFLARE_API}/accounts/{account_id}/workers/scripts/tawnia-healthcare-analytics`, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(workerScript);
    req.end();
  });
}

async function deployPages() {
  // Upload public directory to Pages
  console.log('Upload public/ directory to Cloudflare Pages manually or use Pages API');
}

// Run deployment
if (API_TOKEN) {
  deployWorker().then(result => {
    console.log('Worker deployed:', result.success);
    deployPages();
  }).catch(console.error);
} else {
  console.log('Set CLOUDFLARE_API_TOKEN environment variable');
}