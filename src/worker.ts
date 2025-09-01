/**
 * Cloudflare Worker for Tawnia Healthcare Analytics
 * Routes requests between frontend and containerized Python backend
 */

export interface Env {
  BACKEND: Fetcher;
  UPLOADS_BUCKET: R2Bucket;
  REPORTS_BUCKET: R2Bucket;
  CACHE_KV: KVNamespace;
  ANALYTICS_DATA: KVNamespace;
  SESSION_MANAGER: DurableObjectNamespace;
  ANALYTICS: AnalyticsEngineDataset;
  ENVIRONMENT: string;
  DEBUG: string;
  ENABLE_CACHING: string;
  ENABLE_CIRCUIT_BREAKER: string;
  API_VERSION: string;
  MAX_FILE_SIZE: string;
}

// CORS headers
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  'Access-Control-Max-Age': '86400',
};

// Security headers
const securityHeaders = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
};

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Add analytics
    ctx.waitUntil(
      env.ANALYTICS.writeDataPoint({
        blobs: [url.pathname, request.method],
        doubles: [Date.now()],
        indexes: [env.ENVIRONMENT],
      })
    );

    try {
      // Route based on path
      if (url.pathname.startsWith('/api/')) {
        return await handleAPIRequest(request, env, ctx);
      } else if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/reports/')) {
        return await handleStaticFiles(request, env);
      } else {
        return await handleFrontend(request, env);
      }
    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ 
        error: 'Internal server error',
        message: env.DEBUG === 'true' ? error.message : 'Something went wrong'
      }), {
        status: 500,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders,
          ...securityHeaders
        }
      });
    }
  }
};

async function handleAPIRequest(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
  const url = new URL(request.url);
  
  // Rate limiting check
  const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
  const rateLimitKey = `rate_limit:${clientIP}`;
  
  if (env.ENABLE_CIRCUIT_BREAKER === 'true') {
    const currentCount = await env.CACHE_KV.get(rateLimitKey);
    if (currentCount && parseInt(currentCount) > 100) {
      return new Response(JSON.stringify({ 
        error: 'Rate limit exceeded',
        retry_after: 60
      }), {
        status: 429,
        headers: { 
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
  }

  // Check cache for GET requests
  if (request.method === 'GET' && env.ENABLE_CACHING === 'true') {
    const cacheKey = `cache:${url.pathname}:${url.search}`;
    const cached = await env.CACHE_KV.get(cacheKey);
    if (cached) {
      return new Response(cached, {
        headers: {
          'Content-Type': 'application/json',
          'X-Cache': 'HIT',
          ...corsHeaders,
          ...securityHeaders
        }
      });
    }
  }

  // Forward to backend container
  const backendURL = new URL(request.url);
  backendURL.pathname = url.pathname.replace('/api', ''); // Remove /api prefix
  
  const backendRequest = new Request(backendURL.toString(), {
    method: request.method,
    headers: request.headers,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
  });

  const response = await env.BACKEND.fetch(backendRequest);
  
  // Cache successful GET responses
  if (response.ok && request.method === 'GET' && env.ENABLE_CACHING === 'true') {
    const responseClone = response.clone();
    const responseText = await responseClone.text();
    const cacheKey = `cache:${url.pathname}:${url.search}`;
    
    ctx.waitUntil(
      env.CACHE_KV.put(cacheKey, responseText, { expirationTtl: 3600 }) // 1 hour cache
    );
  }

  // Update rate limit counter with proper increment logic
  if (env.ENABLE_CIRCUIT_BREAKER === 'true') {
    ctx.waitUntil(
      (async () => {
        const currentCount = await env.CACHE_KV.get(rateLimitKey);
        const newCount = currentCount ? parseInt(currentCount) + 1 : 1;
        await env.CACHE_KV.put(rateLimitKey, newCount.toString(), { expirationTtl: 60 });
      })()
    );
  }

  // Add headers and return response
  const newResponse = new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: {
      ...Object.fromEntries(response.headers),
      'X-Cache': 'MISS',
      ...corsHeaders,
      ...securityHeaders
    }
  });

  return newResponse;
}

async function handleStaticFiles(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  
  // Determine which bucket to use
  let bucket: R2Bucket;
  let key: string;
  
  if (url.pathname.startsWith('/reports/')) {
    bucket = env.REPORTS_BUCKET;
    key = url.pathname.replace('/reports/', '');
  } else {
    // Default to uploads bucket for other static files
    bucket = env.UPLOADS_BUCKET;
    key = url.pathname.replace('/static/', '');
  }

  const object = await bucket.get(key);
  
  if (!object) {
    return new Response('File not found', { 
      status: 404,
      headers: corsHeaders
    });
  }

  const headers = new Headers({
    'Content-Type': object.httpMetadata?.contentType || 'application/octet-stream',
    'Content-Length': object.size.toString(),
    'Cache-Control': 'public, max-age=3600',
    ...corsHeaders,
    ...securityHeaders
  });

  return new Response(object.body, { headers });
}

async function handleFrontend(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  
  // For SPA routing, serve index.html for non-API routes
  let key = url.pathname === '/' ? 'index.html' : url.pathname.substring(1);
  
  // If the path doesn't have an extension, assume it's a SPA route
  if (!key.includes('.') && key !== 'index.html') {
    key = 'brainsait-enhanced.html';
  }

  const object = await env.UPLOADS_BUCKET.get(`frontend/${key}`);
  
  if (!object) {
    // Fallback to main HTML file for SPA routing
    const fallback = await env.UPLOADS_BUCKET.get('frontend/brainsait-enhanced.html');
    if (!fallback) {
      return new Response('Frontend not found', { 
        status: 404,
        headers: corsHeaders
      });
    }
    
    return new Response(fallback.body, {
      headers: {
        'Content-Type': 'text/html',
        ...corsHeaders,
        ...securityHeaders
      }
    });
  }

  const contentType = getContentType(key);
  
  return new Response(object.body, {
    headers: {
      'Content-Type': contentType,
      'Cache-Control': contentType.includes('html') ? 'no-cache' : 'public, max-age=31536000',
      ...corsHeaders,
      ...securityHeaders
    }
  });
}

function getContentType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  
  const mimeTypes: Record<string, string> = {
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'json': 'application/json',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'ico': 'image/x-icon',
    'pdf': 'application/pdf',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'csv': 'text/csv',
  };

  return mimeTypes[ext || ''] || 'application/octet-stream';
}

// Durable Object for session management
export class SessionManager {
  private state: DurableObjectState;
  private sessions: Map<string, any> = new Map();

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const sessionId = url.searchParams.get('sessionId');

    if (!sessionId) {
      return new Response('Session ID required', { status: 400 });
    }

    switch (request.method) {
      case 'GET':
        const session = this.sessions.get(sessionId);
        return new Response(JSON.stringify(session || {}), {
          headers: { 'Content-Type': 'application/json' }
        });

      case 'POST':
        const data = await request.json();
        this.sessions.set(sessionId, { 
          ...this.sessions.get(sessionId), 
          ...data,
          lastUpdated: Date.now()
        });
        return new Response('OK');

      case 'DELETE':
        this.sessions.delete(sessionId);
        return new Response('OK');

      default:
        return new Response('Method not allowed', { status: 405 });
    }
  }
}