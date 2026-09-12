/**
 * JARVIS NIM bridge — zero-dependency Node HTTP server.
 *
 *   GET  /api/health  → verifies NIM connectivity by listing /models
 *   POST /api/chat    → forwards OpenAI-style messages, streams NIM SSE back
 *   static serve      → serves ui/dist if it was built (single-server mode)
 *
 * Config comes from environment (node --env-file-if-exists=.env server.js):
 *   NIM_API_KEY   required
 *   NIM_BASE_URL  default https://integrate.api.nvidia.com/v1
 *   NIM_MODEL     default nvidia/llama-3.1-8b-instruct
 *   PORT          default 3001
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const config = {
  port: Number(process.env.PORT || 3001),
  nimBaseUrl: (process.env.NIM_BASE_URL || 'https://integrate.api.nvidia.com/v1').replace(/\/+$/, ''),
  nimModel: process.env.NIM_MODEL || 'nvidia/llama-3.1-8b-instruct',
  nimApiKey: process.env.NIM_API_KEY || '',
};

const DIST = path.join(__dirname, '..', 'ui', 'dist');

/* ---------------------------------- utils --------------------------------- */

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
  });
  res.end(payload);
}

function safeParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return String(text).slice(0, 500);
  }
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.map': 'application/json',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
};

/* ------------------------------- endpoints -------------------------------- */

async function handleHealth(res) {
  if (!config.nimApiKey) {
    return json(res, 200, {
      ok: false,
      status: 'no-key',
      message: 'NIM_API_KEY is not set. Copy server/.env.example to server/.env and add your key.',
      config: { model: config.nimModel, baseUrl: config.nimBaseUrl },
    });
  }
  try {
    const upstream = await fetch(`${config.nimBaseUrl}/models`, {
      headers: { Authorization: `Bearer ${config.nimApiKey}` },
      signal: AbortSignal.timeout(15000),
    });
    if (!upstream.ok) {
      return json(res, 200, {
        ok: false,
        status: 'nim-rejected',
        httpStatus: upstream.status,
        message: 'NVIDIA NIM rejected the request — check the API key.',
        detail: safeParse(await upstream.text()),
      });
    }
    const data = await upstream.json();
    const ids = (data?.data || []).map((m) => m.id);
    return json(res, 200, {
      ok: true,
      status: 'connected',
      model: config.nimModel,
      modelKnown: ids.includes(config.nimModel),
      modelCount: ids.length,
      sampleModels: ids.slice(0, 20),
    });
  } catch (err) {
    return json(res, 200, {
      ok: false,
      status: 'network-error',
      message: `Could not reach NIM: ${err.message}`,
    });
  }
}

async function handleChat(req, res) {
  let raw = '';
  for await (const chunk of req) raw += chunk;

  let parsed;
  try {
    parsed = JSON.parse(raw || '{}');
  } catch {
    return json(res, 400, { error: 'Invalid JSON body.' });
  }

  const messages = parsed.messages;
  if (!Array.isArray(messages) || messages.length === 0) {
    return json(res, 400, { error: '"messages" must be a non-empty array.' });
  }

  if (!config.nimApiKey) {
    return json(res, 401, { error: 'NIM_API_KEY is not set. Add it to server/.env and restart.' });
  }

  const nimBody = {
    model: parsed.model || config.nimModel,
    messages,
    stream: true,
    temperature: parsed.temperature ?? 0.6,
    max_tokens: parsed.max_tokens ?? 1024,
  };

  try {
    const upstream = await fetch(`${config.nimBaseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${config.nimApiKey}`,
      },
      body: JSON.stringify(nimBody),
      signal: AbortSignal.timeout(120000),
    });

    if (!upstream.ok) {
      return json(res, upstream.status, {
        error: `NIM returned HTTP ${upstream.status}`,
        detail: safeParse(await upstream.text()),
      });
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    });

    const reader = upstream.body.getReader();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value);
    }
    res.end();
  } catch (err) {
    if (!res.headersSent) {
      return json(res, 502, { error: `Upstream error: ${err.message}` });
    }
    res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
    res.end();
  }
}

/* ---------------------------- static file serving ------------------------- */

function serveStatic(req, res) {
  if (!fs.existsSync(DIST)) return false;

  let pathname;
  try {
    pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  } catch {
    return json(res, 400, { error: 'Bad request path.' });
  }
  if (pathname === '/') pathname = '/index.html';

  const filePath = path.resolve(DIST, '.' + pathname);
  if (!filePath.startsWith(DIST + path.sep) && filePath !== DIST) {
    return json(res, 403, { error: 'Forbidden.' });
  }

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    // SPA fallback → index.html (handles client-side routes)
    const index = path.join(DIST, 'index.html');
    if (!fs.existsSync(index)) return false;
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    fs.createReadStream(index).pipe(res);
    return true;
  }

  const ext = path.extname(filePath).toLowerCase();
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filePath).pipe(res);
  return true;
}

/* ---------------------------------- server -------------------------------- */

const server = http.createServer(async (req, res) => {
  let pathname;
  try {
    pathname = new URL(req.url, 'http://localhost').pathname;
  } catch {
    return json(res, 400, { error: 'Bad request path.' });
  }

  try {
    if (req.method === 'GET' && pathname === '/api/health') return await handleHealth(res);
    if (req.method === 'POST' && pathname === '/api/chat') return await handleChat(req, res);
    if (pathname.startsWith('/api/')) return json(res, 404, { error: 'Unknown API route.' });
    if (serveStatic(req, res)) return;

    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end([
      'JARVIS NIM bridge is up.',
      '',
      '  API:   /api/health   /api/chat',
      '  UI:    build it with:  cd ui && npm install && npm run build',
      `  Model: ${config.nimModel}`,
      config.nimApiKey ? '' : '  NOTE:  NIM_API_KEY not set — copy server/.env.example to server/.env',
    ].filter(Boolean).join('\n'));
  } catch (err) {
    console.error('[bridge]', err);
    if (!res.headersSent) json(res, 500, { error: err.message });
    else res.end();
  }
});

server.listen(config.port, () => {
  console.log(`JARVIS NIM bridge  →  http://localhost:${config.port}`);
  console.log(`  model   : ${config.nimModel}`);
  console.log(`  base URL: ${config.nimBaseUrl}`);
  console.log(`  key     : ${config.nimApiKey ? 'set' : 'MISSING (copy .env.example to .env)'}`);
});