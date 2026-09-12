/**
 * fsroom.js — sandboxed, read-only access to a single local folder.
 *
 * Zero-dependency. Design rules:
 *   - READ ONLY. No write, rename, delete, mkdir. Ever.
 *   - A single explicit root (set via FS_ROOT). Nothing outside it is reachable.
 *   - Path traversal is impossible by construction: every result is re-verified
 *     against the realpath of the root (also defeats symlink escapes).
 *   - Secrets are blocked outright: .env*, *.key, *.pem, *.p12, *.pfx, *.ppk.
 *   - Reads are size-capped (MAX_READ_BYTES) and binary files are detected,
 *     never dumped as text.
 *   - Listings are capped and sorted directories-first.
 */

import fs from 'node:fs';
import path from 'node:path';

export const MAX_READ_BYTES = 256 * 1024; // 256 KiB
const MAX_LIST_ENTRIES = 500;

const SECRET_BLOCKLIST = /(^|[\\/])\.env([^\\/]*)?(\.[^\\/]+)?$|\.(key|pem|p12|pfx|ppk|p8|p7b|jks|keystore)$/i;

// Noise directories: hidden from listings AND blocked from direct read.
const NOISE_DIRS = new Set([
  'node_modules',
  'dist',
  'build',
  '.git',
  '.next',
  '.cache',
  'venv',
  '.venv',
  '__pycache__',
  '.pytest_cache',
  '.mypy_cache',
  '.ruff_cache',
  '.idea',
  '.vscode',
  'coverage',
]);

function sandboxError(status, code, message) {
  const err = new Error(message);
  err.status = status;
  err.code = code;
  return err;
}

function isSecretPath(relPath) {
  return SECRET_BLOCKLIST.test(relPath.replace(/\\/g, '/'));
}

function isBinary(buf) {
  const sample = buf.subarray(0, 1024);
  if (sample.includes(0)) return true;
  let printable = 0;
  for (const b of sample) {
    if (b === 9 || b === 10 || b === 13 || (b >= 32 && b <= 126)) printable += 1;
  }
  return sample.length > 0 && printable / sample.length < 0.9;
}

export class FSRoom {
  /** @param {string|null} root absolute path (forward slashes fine on Windows) */
  constructor(root) {
    this.root = root ? path.resolve(String(root)) : null;
  }

  get configured() {
    return Boolean(this.root) && fs.existsSync(this.root);
  }

  rootInfo() {
    if (!this.root) return { configured: false, reason: 'FS_ROOT is not set' };
    if (!fs.existsSync(this.root)) {
      return { configured: false, root: this.root, reason: 'FS_ROOT does not exist' };
    }
    return { configured: true, root: this.root };
  }

  /** Resolve a relative path inside the sandbox; throws on any escape. */
  resolve(rel) {
    if (!this.root) throw sandboxError(503, 'FS_NOT_CONFIGURED', 'Filesystem sandbox not configured — set FS_ROOT in server/.env and restart.');
    if (!fs.existsSync(this.root)) throw sandboxError(503, 'FS_ROOT_MISSING', 'FS_ROOT does not exist.');

    const r = rel == null || rel === '' ? '' : String(rel).replace(/\\/g, '/').replace(/^\/+/, '');
    const target = path.resolve(this.root, r);

    // Lexical containment
    if (target !== path.resolve(this.root) && !target.startsWith(path.resolve(this.root) + path.sep)) {
      throw sandboxError(403, 'FS_ESCAPE', 'Path escapes the sandbox root.');
    }

    // Real containment (symlinks / junctions cannot escape)
    let realTarget;
    let realRoot;
    try {
      realTarget = fs.realpathSync(target);
      realRoot = fs.realpathSync(this.root);
    } catch {
      throw sandboxError(404, 'FS_NOT_FOUND', 'Path does not exist.');
    }
    if (realTarget !== realRoot && !realTarget.startsWith(realRoot + path.sep)) {
      throw sandboxError(403, 'FS_ESCAPE', 'Path escapes the sandbox root (resolved).');
    }
    return realTarget;
  }

  /** List the contents of a directory inside the sandbox. */
  list(rel) {
    const dir = this.resolve(rel);
    if (!fs.statSync(dir).isDirectory()) {
      throw sandboxError(400, 'FS_NOT_DIR', 'Not a directory.');
    }

    const entries = fs.readdirSync(dir, { withFileTypes: true });
    const out = [];
    for (const ent of entries) {
      if (ent.isDirectory() && NOISE_DIRS.has(ent.name)) continue;
      if (isSecretPath(ent.name)) continue;

      const relPath = path.posix.join(this._rel(dir), ent.name);
      let stat = null;
      try {
        stat = fs.statSync(path.join(dir, ent.name));
      } catch {
        continue; // vanished or unreadable — skip silently
      }
      out.push({
        name: ent.name,
        type: ent.isDirectory() ? 'dir' : 'file',
        size: stat.size,
        modified: stat.mtimeMs,
        path: relPath,
      });
      if (out.length >= MAX_LIST_ENTRIES) {
        out.truncated = true;
        break;
      }
    }

    out.sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name) : a.type === 'dir' ? -1 : 1));
    return { path: this._rel(dir) || '/', entries: out, truncated: out.truncated === true };
  }

  /** Read a text file inside the sandbox (size-capped, binary-safe). */
  read(rel) {
    const file = this.resolve(rel);
    const stat = fs.statSync(file);
    if (stat.isDirectory()) throw sandboxError(400, 'FS_IS_DIR', 'Path is a directory — list it instead.');

    const relPath = this._rel(file);
    if (isSecretPath(relPath)) {
      throw sandboxError(403, 'FS_BLOCKED', 'This file is blocked (secret file).');
    }

    const fd = fs.openSync(file, 'r');
    const buf = Buffer.alloc(Math.min(stat.size, MAX_READ_BYTES) + 1); // +1 to detect truncation
    const bytesRead = fs.readSync(fd, buf, 0, buf.length, 0);
    fs.closeSync(fd);

    const truncated = bytesRead > MAX_READ_BYTES || stat.size > MAX_READ_BYTES;
    const data = buf.subarray(0, Math.min(stat.size, MAX_READ_BYTES));

    if (isBinary(data)) {
      return {
        path: relPath,
        name: path.basename(file),
        size: stat.size,
        binary: true,
        truncated,
        hint: 'Binary file — content not returned.',
      };
    }

    return {
      path: relPath,
      name: path.basename(file),
      size: stat.size,
      truncated,
      content: data.toString('utf8').replace(/^\uFEFF/, ''), // strip BOM
    };
  }

  /** Relative posix path of an absolute sandbox path ('' for root). */
  _rel(absPath) {
    const root = path.resolve(this.root);
    const abs = path.resolve(absPath);
    if (abs === root) return '';
    return abs.slice(root.length + 1).replace(/\\/g, '/');
  }
}