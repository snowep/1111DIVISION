/**
 * JARVIS NIM bridge — zero-dependency Node HTTP server.
 *
 *   GET  /api/health  → verifies NIM connectivity by listing /models
 *   GET  /api/fs/root → filesystem sandbox status (configured, root)
 *   GET  /api/fs/list → list a directory inside the sandbox (?path=rel)
 *   GET  /api/fs/read → read a file inside the sandbox (?path=rel)
 *   POST /api/chat    → forwards OpenAI-style messages, streams NIM SSE back
 *                       with auto-routing: if the requested model is
 *                       unavailable, the bridge retries the same request on
 *                       the next model in the fallback chain. Supports
 *                       @file(rel/path) expansion: the file's content is
 *                       injected into the user message before sending.
 *   static serve      → serves ui/dist if it was built (single-server mode)
 *
 * Config comes from environment (node --env-file-if-exists=.env server.js):
 *   NIM_API_KEY          required
 *   NIM_BASE_URL         default https://integrate.api.nvidia.com/v1
 *   NIM_MODEL            default nvidia/llama-3.1-8b-instruct (primary)
 *   NIM_FALLBACK_MODELS  comma-separated ordered list of fallback model IDs
 *   NIM_ROUTER           "off" disables auto-routing (default on)
 *   FS_ROOT              absolute path of the folder JARVIS may read
 *                        (read-only sandbox; omit or leave blank to disable)
 *   PORT                 default 3001
 *
 * Auto-routing rules:
 *   - Only triggers on *availability* failures (upstream HTTP error,
 *     network error, timeout) BEFORE the stream starts.
 *   - A stream that started and then dies is reported to the client as-is;
 *     it is NOT transparently swapped mid-response.
 *   - The client is told which model served the reply via a `meta` SSE
 *     event emitted ahead of the first chunk.
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FSRoom } from './fsroom.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const config = {
  port: Number(process.env.PORT || 3001),
  nimBaseUrl: (process.env.NIM_BASE_URL || 'https://integrate.api.nvidia.com/v1').replace(/\/+$/, ''),
  nimModel: process.env.NIM_MODEL || 'nvidia/llama-3.1-8b-instruct',
  nimApiKey: process.env.NIM_API_KEY || '',
  fallbackModels: (process.env.NIM_FALLBACK_MODELS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean),
  routerEnabled: process.env.NIM_ROUTER !== 'off',
  fsRoot: process.env.FS_ROOT || '',
};

const fsroom = new FSRoom(config.fsRoot);

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

/**
 * Build the ordered candidate list for a request: the requested/primary model
 * first, then configured fallbacks — deduplicated, empties removed.
 */
function buildCandidates(primary) {
  const seen = new Set();
  const out = [];
  for (const m of [primary, ...(config.routerEnabled ? config.fallbackModels : [])]) {
    if (m && !seen.has(m)) {
      seen.add(m);
      out.push(m);
    }
  }
  return out;
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

async function handleFsRoot(res) {
  return json(res, 200, fsroom.rootInfo());
}

async function handleFsList(req, res) {
  try {
    const rel = new URL(req.url, 'http://localhost').searchParams.get('path') || '';
    return json(res, 200, fsroom.list(rel));
  } catch (err) {
    return json(res, err.status || 500, { error: err.message, code: err.code || 'FS_ERROR' });
  }
}

async function handleFsRead(req, res) {
  try {
    const rel = new URL(req.url, 'http://localhost').searchParams.get('path') || '';
    return json(res, 200, fsroom.read(rel));
  } catch (err) {
    return json(res, err.status || 500, { error: err.message, code: err.code || 'FS_ERROR' });
  }
}

/**
 * Expand @file(rel/path) into actual file content before sending to NIM.
 * Always leaves a visible breadcrumb so the model knows the tool ran.
 */
function expandFileRefs(content) {
  if (!fsroom.configured) return { content, injections: [] };
  const injections = [];
  const expanded = String(content).replace(/@file\(([^)]+)\)/g, (_m, rel) => {
    try {
      const file = fsroom.read(rel.trim());
      if (file.binary) {
        return `[@file(${file.path}) — binary file, not included]`;
      }
      const body = `\n\n<file path="${file.path.replace(/&/g, '&amp;').replace(/"/g, '&quot;')}" size="${file.size}"${file.truncated ? ' truncated="true"' : ''}>\n${file.content}\n</file>\n`;
      injections.push({ path: file.path, size: file.size, truncated: file.truncated });
      return body;
    } catch (err) {
      return `[@file(${rel}) — ${err.message}]`;
    }
  });
  return { content: expanded, injections };
}

/* ------------------------------- endpoints -------------------------------- */

async function handleHealth(res) {
  const route = buildCandidates(config.nimModel);
  if (!config.nimApiKey) {
    return json(res, 200, {
      ok: false,
      status: 'no-key',
      message: 'NIM_API_KEY is not set. Copy server/.env.example to server/.env and add your key.',
      config: { model: config.nimModel, baseUrl: config.nimBaseUrl, route },
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
    const availability = route.map((m) => ({ model: m, available: ids.includes(m) }));
    return json(res, 200, {
      ok: true,
      status: 'connected',
      model: config.nimModel,
      modelKnown: ids.includes(config.nimModel),
      modelCount: ids.length,
      route,
      availability,
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

  // Expand @file(...) references in the last user message.
  const injections = [];
  const last = messages[messages.length - 1];
  if (last && last.role === 'user' && typeof last.content === 'string') {
    const expanded = expandFileRefs(last.content);
    last.content = expanded.content;
    injections.push(...expanded.injections);
  }

  if (!config.nimApiKey) {
    return json(res, 401, { error: 'NIM_API_KEY is not set. Add it to server/.env and restart.' });
  }

  const candidates = buildCandidates(parsed.model || config.nimModel);
  const attempts = [];
  let lastFailure = null;

  for (const [index, model] of candidates.entries()) {
    const nimBody = {
      model,
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
        const detail = safeParse(await upstream.text());
        const reason =
          (typeof detail === 'object' && detail?.error?.message) ||
          `HTTP ${upstream.status}`;
        attempts.push({ model, status: upstream.status, ok: false, reason });
        lastFailure = { status: upstream.status, detail };

        // If the model itself was rejected (404), the reason is often
        // "model not found" — surface the available models to guide.
        if (upstream.status === 404) {
          try {
            const ml = await fetch(`${config.nimBaseUrl}/models`, {
              headers: { Authorization: `Bearer ${config.nimApiKey}` },
              signal: AbortSignal.timeout(10000),
            });
            if (ml.ok) {
              const md = await ml.json();
              lastFailure.availableModels = (md.data || []).map((m) => m.id);
            }
          } catch {
            // best-effort: ignore model-list failure
          }
        }
        continue;
      }

      // Stream headers first, then announce which model is actually serving.
      res.writeHead(200, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no',
      });
      // meta: which model serves this reply. files: what was injected.
      res.write(
        `data: ${JSON.stringify({
          type: 'meta',
          model,
          fallback: index > 0,
          attempts: attempts.length,
        })}\n\n`
      );
      if (injections.length > 0) {
        res.write(`data: ${JSON.stringify({ type: 'files', files: injections })}\n\n`);
      }

      const reader = upstream.body.getReader();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
      res.end();
      return;
    } catch (err) {
      attempts.push({ model, ok: false, reason: `network: ${err.message}` });
      lastFailure = { status: 502, detail: err.message };
      continue;
    }
  }

  return json(res, 503, {
    error: `All ${candidates.length} candidate model(s) failed.`,
    attempts,
    lastFailure,
  });
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
    if (req.method === 'GET' && pathname === '/api/fs/root') return await handleFsRoot(res);
    if (req.method === 'GET' && pathname === '/api/fs/list') return await handleFsList(req, res);
    if (req.method === 'GET' && pathname === '/api/fs/read') return await handleFsRead(req, res);
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
      `  Route: ${buildCandidates(config.nimModel).join('  ->  ')}`,
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
  console.log(`  router  : ${config.routerEnabled ? 'auto (' + config.fallbackModels.length + ' fallback(s))' : 'off'}`);
  console.log(`  route   : ${buildCandidates(config.nimModel).join('  ->  ')}`);
  console.log(`  fsroom  : ${fsroom.configured ? fsroom.root : 'not configured (set FS_ROOT)'}`);
});