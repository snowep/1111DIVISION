import fs from "node:fs/promises";
import path from "node:path";
import type { WorkspaceFile, WorkspaceSnapshot } from "./types";

const IGNORED = new Set([".git", "node_modules", ".next", "__pycache__", ".venv"]);

function rootPath() {
  return process.env.ORION_WORKSPACE_ROOT
    ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
    : process.cwd();
}

function kindFor(filePath: string): WorkspaceFile["kind"] {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".md" || ext === ".mdx") return "markdown";
  if ([".ts", ".tsx", ".js", ".jsx", ".py", ".rs", ".go"].includes(ext)) return "code";
  if ([".json", ".yaml", ".yml", ".toml", ".env"].includes(ext)) return "config";
  return "other";
}

async function walk(current: string, base: string, result: WorkspaceFile[]) {
  const entries = await fs.readdir(current, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORED.has(entry.name)) continue;
    const absolute = path.join(current, entry.name);
    const relative = path.relative(base, absolute).replaceAll("\\", "/");
    if (entry.isDirectory()) {
      await walk(absolute, base, result);
    } else {
      const stat = await fs.stat(absolute);
      result.push({ path: relative, kind: kindFor(absolute), size: stat.size });
    }
  }
}

export async function scanWorkspace(): Promise<WorkspaceSnapshot> {
  const root = rootPath();
  const files: WorkspaceFile[] = [];
  await walk(root, root, files);
  files.sort((a, b) => a.path.localeCompare(b.path));
  return {
    root,
    files,
    markdown: files.filter((file) => file.kind === "markdown"),
    agentFiles: files.filter((file) => file.path.startsWith(".agent/")),
    scannedAt: new Date().toISOString()
  };
}

function safePath(relativePath: string) {
  const root = rootPath();
  const absolute = path.resolve(root, relativePath);
  if (absolute !== root && !absolute.startsWith(root + path.sep)) {
    throw new Error("Path escapes ORION_WORKSPACE_ROOT");
  }
  return absolute;
}

export async function readWorkspaceFile(relativePath: string) {
  return fs.readFile(safePath(relativePath), "utf8");
}

export async function appendMarkdown(relativePath: string, content: string) {
  if (!relativePath.endsWith(".md")) {
    throw new Error("Only Markdown memory writes are allowed in transition mode.");
  }
  const absolute = safePath(relativePath);
  await fs.mkdir(path.dirname(absolute), { recursive: true });
  await fs.appendFile(absolute, content.endsWith("\n") ? content : `${content}\n`, "utf8");
}
