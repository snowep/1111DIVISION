/**
 * ORION Memory & Knowledge System (TypeScript)
 * 
 * Token-efficient, section-based retrieval from .md files.
 * Mirrors the Python Retriever with identical semantics.
 */

import fs from "node:fs/promises";
import path from "node:path";
import type { OrionEvent } from "./types";

export type BudgetTier = "micro" | "standard" | "deep" | "full";

export interface RetrievalSection {
  store: "memory" | "knowledge" | "experience";
  file: string;
  heading: string;
  content: string;
  lineRange: [number, number];
  tokenEstimate: number;
  relevanceScore?: number;
  truncated?: boolean;
}

export interface RetrievalResult {
  memory: RetrievalSection[];
  knowledge: RetrievalSection[];
  experience: RetrievalSection[];
  totalTokens: number;
  gaps: string[];
}

export interface MemoryWriteRequest {
  path: string;
  content: string;
  type: "memory" | "knowledge" | "experience";
}

const BUDGETS: Record<BudgetTier, number> = {
  micro: 500,
  standard: 2000,
  deep: 4000,
  full: 8000,
};

const STOP_WORDS = new Set([
  "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
  "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being",
  "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
  "may", "might", "must", "can", "this", "that", "these", "those", "i", "you",
  "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
]);

function getRootPath(): string {
  return process.env.ORION_WORKSPACE_ROOT
    ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
    : process.cwd();
}

function getOrionDir(): string {
  return path.join(getRootPath(), ".agent", "orion");
}

function getStoreDir(store: "memory" | "knowledge" | "experience"): string {
  return path.join(getOrionDir(), store);
}

function getSharedDir(store: "memory" | "knowledge"): string {
  return path.join(getRootPath(), ".agent", "shared", store);
}

function getPersonaDir(persona: string, store: "memory" | "knowledge" | "experience"): string {
  return path.join(getRootPath(), ".agent", "orion", "personas", "definitions", persona, store);
}

function extractQueryTerms(objective: string, keywords: string[]): string[] {
  const terms = new Set(keywords);
  const words = objective.toLowerCase().match(/\b\w+\b/g) || [];
  for (const w of words) {
    if (w.length > 2 && !STOP_WORDS.has(w)) {
      terms.add(w);
    }
  }
  return Array.from(terms);
}

function isRelevant(text: string, queryTerms: string[]): boolean {
  const lower = text.toLowerCase();
  return queryTerms.some(term => lower.includes(term));
}

async function loadMarkdownSections(
  dirPath: string,
  storeName: "memory" | "knowledge" | "experience",
  queryTerms: string[]
): Promise<RetrievalSection[]> {
  const sections: RetrievalSection[] = [];
  
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      
      if (entry.isDirectory()) {
        const subSections = await loadMarkdownSections(fullPath, storeName, queryTerms);
        sections.push(...subSections);
      } else if (entry.name.endsWith(".md")) {
        try {
          const content = await fs.readFile(fullPath, "utf-8");
          const fileSections = extractSections(content, fullPath, storeName, queryTerms);
          sections.push(...fileSections);
        } catch {
          // Skip unreadable files
        }
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return sections;
}

function extractSections(
  content: string,
  filePath: string,
  storeName: "memory" | "knowledge" | "experience",
  queryTerms: string[]
): RetrievalSection[] {
  const sections: RetrievalSection[] = [];
  const lines = content.split("\n");
  let currentHeading = "";
  let sectionStart = 0;
  let sectionLines: string[] = [];
  const rootPath = getRootPath();
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headingMatch = line.match(/^(#+)\s+(.+)$/);
    
    if (headingMatch) {
      // Save previous section
      if (sectionLines.length > 0) {
        const sectionContent = sectionLines.join("\n");
        if (isRelevant(sectionContent, queryTerms) || isRelevant(currentHeading, queryTerms)) {
          const relativePath = path.relative(rootPath, filePath).replaceAll("\\", "/");
          sections.push({
            store: storeName,
            file: relativePath,
            heading: currentHeading,
            content: sectionContent,
            lineRange: [sectionStart + 1, i],
            tokenEstimate: Math.ceil(sectionContent.length / 4),
          });
        }
      }
      currentHeading = headingMatch[2];
      sectionStart = i;
      sectionLines = [line];
    } else {
      sectionLines.push(line);
    }
  }
  
  // Handle last section
  if (sectionLines.length > 0) {
    const sectionContent = sectionLines.join("\n");
    if (isRelevant(sectionContent, queryTerms) || isRelevant(currentHeading, queryTerms)) {
      const relativePath = path.relative(rootPath, filePath).replaceAll("\\", "/");
      sections.push({
        store: storeName,
        file: relativePath,
        heading: currentHeading,
        content: sectionContent,
        lineRange: [sectionStart + 1, lines.length],
        tokenEstimate: Math.ceil(sectionContent.length / 4),
      });
    }
  }
  
  return sections;
}

function rankSections(sections: RetrievalSection[], queryTerms: string[]): RetrievalSection[] {
  for (const s of sections) {
    let score = 0.0;
    const heading = s.heading.toLowerCase();
    const content = s.content.toLowerCase();
    const filePath = s.file.toLowerCase();
    
    const headingHits = queryTerms.filter(t => heading.includes(t)).length;
    score += 0.4 * Math.min(headingHits / Math.max(queryTerms.length, 1), 1.0);
    
    const contentHits = queryTerms.filter(t => content.includes(t)).length;
    score += 0.3 * Math.min(contentHits / Math.max(queryTerms.length, 1), 1.0);
    
    const fileHits = queryTerms.filter(t => filePath.includes(t)).length;
    score += 0.1 * Math.min(fileHits / Math.max(queryTerms.length, 1), 1.0);
    
    // Priority bonuses
    if (filePath.includes("decision") || filePath.includes("preference")) {
      score += 0.1;
    } else if (filePath.includes("pipeline") || filePath.includes("architecture")) {
      score += 0.1;
    }
    
    s.relevanceScore = score;
  }
  
  return sections.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
}

function applyBudget(sections: RetrievalSection[], budget: BudgetTier): RetrievalSection[] {
  const limit = BUDGETS[budget];
  let total = 0;
  const result: RetrievalSection[] = [];
  
  for (const s of sections) {
    const estimate = s.tokenEstimate;
    if (total + estimate <= limit) {
      result.push(s);
      total += estimate;
    } else {
      const remaining = limit - total;
      if (remaining > 100) {
        const truncated = {
          ...s,
          content: s.content.slice(0, remaining * 4) + "\n... [truncated]",
          tokenEstimate: remaining,
          truncated: true,
        };
        result.push(truncated);
        total += remaining;
      }
      break;
    }
  }
  
  return result;
}

function identifyGaps(queryTerms: string[], sections: RetrievalSection[]): string[] {
  const foundTerms = new Set<string>();
  
  for (const s of sections) {
    const combined = (s.heading + " " + s.content).toLowerCase();
    for (const term of queryTerms) {
      if (combined.includes(term)) {
        foundTerms.add(term);
      }
    }
  }
  
  return queryTerms.filter(t => !foundTerms.has(t));
}

/**
 * Main retrieval function — token-budgeted, relevance-ranked, gap-aware.
 */
export async function retrieveForTask(
  objective: string,
  keywords: string[] = [],
  budget: BudgetTier = "standard",
  personaName?: string
): Promise<RetrievalResult> {
  const queryTerms = extractQueryTerms(objective, keywords);
  const allSections: RetrievalSection[] = [];
  
  // 1. Persona-specific stores (highest priority)
  if (personaName) {
    for (const store of ["memory", "knowledge", "experience"] as const) {
      const dir = getPersonaDir(personaName, store);
      const sections = await loadMarkdownSections(dir, store, queryTerms);
      allSections.push(...sections);
    }
  }
  
  // 2. Shared stores (cross-persona commons)
  for (const store of ["memory", "knowledge"] as const) {
    const dir = getSharedDir(store);
    const sections = await loadMarkdownSections(dir, store, queryTerms);
    allSections.push(...sections);
  }
  
  // 3. ORION global stores
  for (const store of ["memory", "knowledge", "experience"] as const) {
    const dir = getStoreDir(store);
    const sections = await loadMarkdownSections(dir, store, queryTerms);
    allSections.push(...sections);
  }
  
  // Rank, budget, gaps
  const ranked = rankSections(allSections, queryTerms);
  const filtered = applyBudget(ranked, budget);
  const gaps = identifyGaps(queryTerms, filtered);
  
  return {
    memory: filtered.filter(s => s.store === "memory"),
    knowledge: filtered.filter(s => s.store === "knowledge"),
    experience: filtered.filter(s => s.store === "experience"),
    totalTokens: filtered.reduce((sum, s) => sum + s.tokenEstimate, 0),
    gaps,
  };
}

/**
 * Write memory/knowledge/experience to .md files.
 * Memory = append-only. Knowledge = replace section or append with confirmation.
 */
export async function writeMemory(request: MemoryWriteRequest): Promise<{ ok: boolean; path: string }> {
  const storeDir = path.join(getOrionDir(), request.type);
  const absolutePath = path.join(storeDir, request.path);
  
  // Security: prevent path traversal
  const resolvedStore = path.resolve(storeDir);
  const resolvedPath = path.resolve(absolutePath);
  if (!resolvedPath.startsWith(resolvedStore + path.sep) && resolvedPath !== resolvedStore) {
    throw new Error("Path escapes ORION memory directory");
  }
  
  await fs.mkdir(path.dirname(resolvedPath), { recursive: true });
  
  const content = request.content.endsWith("\n") ? request.content : request.content + "\n";
  await fs.appendFile(resolvedPath, content, "utf-8");
  
  return { ok: true, path: request.path };
}

/**
 * Read a specific memory file.
 */
export async function readMemoryFile(relativePath: string): Promise<string> {
  const absolutePath = path.join(getOrionDir(), relativePath);
  const resolvedOrion = path.resolve(getOrionDir());
  const resolvedPath = path.resolve(absolutePath);
  
  if (!resolvedPath.startsWith(resolvedOrion + path.sep) && resolvedPath !== resolvedOrion) {
    throw new Error("Path escapes ORION directory");
  }
  
  return fs.readFile(resolvedPath, "utf-8");
}

/**
 * List all memory files in a store.
 */
export async function listMemoryFiles(store: "memory" | "knowledge" | "experience"): Promise<string[]> {
  const dir = getStoreDir(store);
  const files: string[] = [];
  
  async function walk(current: string) {
    try {
      const entries = await fs.readdir(current, { withFileTypes: true });
      for (const entry of entries) {
        const full = path.join(current, entry.name);
        if (entry.isDirectory()) {
          await walk(full);
        } else if (entry.name.endsWith(".md")) {
          const relative = path.relative(dir, full).replaceAll("\\", "/");
          files.push(relative);
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }
  
  await walk(dir);
  return files.sort();
}