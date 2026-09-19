/**
 * ORION Persona System (TypeScript)
 * 
 * Multi-persona support with individual memory/knowledge, merging into shared ORION memory.
 * Ported from Python PersonaRouter with identical semantics.
 */

import fs from "node:fs/promises";
import path from "node:path";

export type PersonaStatus = "inactive" | "standby" | "active" | "paused" | "completed";

export interface PersonaDefinition {
  name: string;
  role: string;
  purpose: string;
  boundaries: string[];
  style: string;
  tools: string[];
  memory: string;
  knowledge: string[];
  skills: string[];
  experience: string[];
  evaluationCriteria: string[];
  level: number;
}

export interface PersonaContext {
  persona: PersonaDefinition;
  identityContent: string;
  memoryContent: string;
  knowledgeContent: string;
  skillsContent: string;
  experienceContent: string;
  sharedMemory: string;
  sharedKnowledge: string;
}

export interface PersonaSelection {
  personaName: string;
  confidence: number;
  reasoning: string;
  requiredKnowledge: string[];
}

export interface PersonaActivationResult {
  selection: PersonaSelection;
  context: PersonaContext | null;
  personaName: string;
  activated: boolean;
  contextTokensEstimate: number;
}

function getRootPath(): string {
  return process.env.ORION_WORKSPACE_ROOT
    ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
    : process.cwd();
}

function getPersonasDir(): string {
  return path.join(getRootPath(), ".agent", "orion", "personas", "definitions");
}

function getSharedDir(): string {
  return path.join(getRootPath(), ".agent", "shared");
}

function getOrionDir(): string {
  return path.join(getRootPath(), ".agent", "orion");
}

function loadMarkdownFiles(dirPath: string): string[] {
  const results: string[] = [];
  
  try {
    const entries = require("node:fs").readdirSync(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      
      if (entry.isDirectory()) {
        results.push(...loadMarkdownFiles(fullPath));
      } else if (entry.name.endsWith(".md")) {
        try {
          const content = require("node:fs").readFileSync(fullPath, "utf-8");
          results.push(content);
        } catch {
          // Skip unreadable files
        }
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return results;
}

async function loadMarkdownFilesAsync(dirPath: string): Promise<string[]> {
  const results: string[] = [];
  
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);
      
      if (entry.isDirectory()) {
        const subResults = await loadMarkdownFilesAsync(fullPath);
        results.push(...subResults);
      } else if (entry.name.endsWith(".md")) {
        try {
          const content = await fs.readFile(fullPath, "utf-8");
          results.push(content);
        } catch {
          // Skip unreadable files
        }
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return results;
}

function parsePersonaMarkdown(content: string, name: string): PersonaDefinition {
  const persona: PersonaDefinition = {
    name,
    role: "",
    purpose: "",
    boundaries: [],
    style: "",
    tools: [],
    memory: "",
    knowledge: [],
    skills: [],
    experience: [],
    evaluationCriteria: [],
    level: 1,
  };
  
  const lines = content.split("\n");
  let currentSection = "";
  let sectionContent: string[] = [];
  
  for (const line of lines) {
    if (line.startsWith("# ")) {
      // Main title - skip
      continue;
    } else if (line.startsWith("## ")) {
      // Save previous section
      if (currentSection && sectionContent.length > 0) {
        const content = sectionContent.join("\n").trim();
        setPersonaField(persona, currentSection, content);
      }
      currentSection = line.slice(3).trim().toLowerCase().replace(/\s+/g, "_");
      sectionContent = [];
      continue;
    }
    
    if (currentSection) {
      sectionContent.push(line);
    }
  }
  
  // Handle last section
  if (currentSection && sectionContent.length > 0) {
    const content = sectionContent.join("\n").trim();
    setPersonaField(persona, currentSection, content);
  }
  
  return persona;
}

function setPersonaField(persona: PersonaDefinition, field: string, content: string): void {
  switch (field) {
    case "role":
      persona.role = content;
      break;
    case "purpose":
      persona.purpose = content;
      break;
    case "boundaries":
      persona.boundaries = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "style":
      persona.style = content;
      break;
    case "tools":
      persona.tools = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "memory":
      persona.memory = content;
      break;
    case "knowledge":
      persona.knowledge = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "skills":
      persona.skills = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "experience":
      persona.experience = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "evaluation_criteria":
      persona.evaluationCriteria = content.split("\n").map(l => l.replace(/^[-*]\s*/, "")).filter(Boolean);
      break;
    case "level":
      persona.level = parseInt(content, 10) || 1;
      break;
  }
}

function keywordSelect(objective: string, definitions: Map<string, PersonaDefinition>): PersonaSelection {
  const objectiveLower = objective.toLowerCase();
  
  const patterns: Record<string, string[]> = {
    engineer: ["code", "python", "implement", "fix", "bug", "debug", "compile", "test", "refactor"],
    researcher: ["research", "investigate", "study", "analyze", "examine", "compare", "survey"],
    architect: ["architecture", "design", "structure", "pattern", "framework", "system"],
    analyst: ["analyze", "review", "audit", "evaluate", "assess", "compare", "metrics"],
    security: ["security", "vulnerability", "attack", "penetration", "auth", "permission", "credential"],
    operations: ["deploy", "release", "production", "run", "execute", "build", "monitor"],
    manager: ["plan", "coordinate", "manage", "organize", "schedule", "prioritize"],
  };
  
  let bestPersona = "default";
  let bestScore = 0.3;
  
  for (const [persona, keywords] of Object.entries(patterns)) {
    const matches = keywords.filter(kw => objectiveLower.includes(kw)).length;
    if (matches > 0) {
      const score = Math.min(0.9, 0.3 + matches * 0.15);
      if (score > bestScore) {
        bestScore = score;
        bestPersona = persona;
      }
    }
  }
  
  // Check if persona exists in definitions
  if (definitions.has(bestPersona)) {
    bestScore = 0.8;
  }
  
  return {
    personaName: bestPersona,
    confidence: bestScore,
    reasoning: `Keyword match: ${bestPersona} (score: ${bestScore.toFixed(2)})`,
    requiredKnowledge: bestPersona !== "default" ? [`knowledge/${bestPersona}`] : [],
  };
}

export class PersonaRouter {
  private definitions: Map<string, PersonaDefinition> = new Map();
  private activePersona: PersonaContext | null = null;

  constructor() {
    this.loadDefinitions();
  }

  private loadDefinitions(): void {
    const dir = getPersonasDir();
    
    try {
      const entries = require("node:fs").readdirSync(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.name.endsWith(".md")) {
          const fullPath = path.join(dir, entry.name);
          const name = entry.name.slice(0, -3);
          try {
            const content = require("node:fs").readFileSync(fullPath, "utf-8");
            const persona = parsePersonaMarkdown(content, name);
            this.definitions.set(name, persona);
          } catch {
            // Skip invalid files
          }
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }

  async loadDefinitionsAsync(): Promise<void> {
    const dir = getPersonasDir();
    
    try {
      await fs.mkdir(dir, { recursive: true });
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.name.endsWith(".md")) {
          const fullPath = path.join(dir, entry.name);
          const name = entry.name.slice(0, -3);
          try {
            const content = await fs.readFile(fullPath, "utf-8");
            const persona = parsePersonaMarkdown(content, name);
            this.definitions.set(name, persona);
          } catch {
            // Skip invalid files
          }
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }

  getAvailablePersonas(): Record<string, PersonaDefinition> {
    const result: Record<string, PersonaDefinition> = {};
    for (const [name, def] of this.definitions) {
      result[name] = def;
    }
    return result;
  }

  selectPersona(objective: string, context: Record<string, unknown> = {}): PersonaSelection {
    return keywordSelect(objective, this.definitions);
  }

  async activatePersona(personaName: string): Promise<PersonaContext | null> {
    const definition = this.definitions.get(personaName);
    if (!definition && personaName !== "default") {
      return null;
    }
    
    const def = definition || {
      name: "default",
      role: "Assistant",
      purpose: "General purpose assistant",
      boundaries: [],
      style: "Helpful, concise, accurate",
      tools: [],
      memory: "",
      knowledge: [],
      skills: [],
      experience: [],
      evaluationCriteria: [],
      level: 1,
    };
    
    const context: PersonaContext = {
      persona: def,
      identityContent: "",
      memoryContent: "",
      knowledgeContent: "",
      skillsContent: "",
      experienceContent: "",
      sharedMemory: "",
      sharedKnowledge: "",
    };
    
    // Load identity
    const identityPath = path.join(getPersonasDir(), personaName, "identity.md");
    try {
      context.identityContent = await fs.readFile(identityPath, "utf-8");
    } catch {
      // No identity file
    }
    
    // Load persona memory
    const personaMemoryDir = path.join(getPersonasDir(), personaName, "memory");
    const personaMemoryParts = await loadMarkdownFilesAsync(personaMemoryDir);
    context.memoryContent = personaMemoryParts.join("\n\n");
    
    // Load ORION global memory
    const orionMemoryDir = path.join(getOrionDir(), "memory");
    const orionMemoryParts = await loadMarkdownFilesAsync(orionMemoryDir);
    context.memoryContent += "\n\n" + orionMemoryParts.join("\n\n");
    
    // Load persona knowledge
    const personaKnowledgeDir = path.join(getPersonasDir(), personaName, "knowledge");
    const personaKnowledgeParts = await loadMarkdownFilesAsync(personaKnowledgeDir);
    context.knowledgeContent = personaKnowledgeParts.join("\n\n");
    
    // Load shared memory
    const sharedMemoryDir = path.join(getSharedDir(), "memory");
    const sharedMemoryParts = await loadMarkdownFilesAsync(sharedMemoryDir);
    context.sharedMemory = sharedMemoryParts.join("\n\n");
    
    // Load shared knowledge
    const sharedKnowledgeDir = path.join(getSharedDir(), "knowledge");
    const sharedKnowledgeParts = await loadMarkdownFilesAsync(sharedKnowledgeDir);
    context.sharedKnowledge = sharedKnowledgeParts.join("\n\n");
    
    this.activePersona = context;
    return context;
  }

  getActivePersona(): PersonaContext | null {
    return this.activePersona;
  }

  deactivatePersona(): void {
    this.activePersona = null;
  }

  async routeTask(objective: string, taskContext: Record<string, unknown> = {}): Promise<PersonaActivationResult> {
    const selection = this.selectPersona(objective, taskContext);
    const context = await this.activatePersona(selection.personaName);
    
    return {
      selection,
      context,
      personaName: selection.personaName,
      activated: context !== null,
      contextTokensEstimate: context ? this.estimateTokens(context) : 0,
    };
  }

  estimateTokens(context: PersonaContext): number {
    const totalChars = [
      context.identityContent,
      context.memoryContent,
      context.knowledgeContent,
      context.skillsContent,
      context.experienceContent,
      context.sharedMemory,
      context.sharedKnowledge,
    ].join("").length;
    return Math.ceil(totalChars / 4);
  }

  getContextSummary(context: PersonaContext): string {
    const parts: string[] = [];
    if (context.identityContent) parts.push("Identity loaded");
    if (context.memoryContent) parts.push(`Memory: ${context.memoryContent.length} chars`);
    if (context.sharedMemory) parts.push(`Shared memory: ${context.sharedMemory.length} chars`);
    if (context.knowledgeContent) parts.push(`Knowledge: ${context.knowledgeContent.length} chars`);
    if (context.experienceContent) parts.push(`Experience: ${context.experienceContent.length} chars`);
    return parts.length > 0 ? parts.join(", ") : "No context loaded";
  }
}

let personaRouterInstance: PersonaRouter | null = null;

export function getPersonaRouter(): PersonaRouter {
  if (!personaRouterInstance) {
    personaRouterInstance = new PersonaRouter();
  }
  return personaRouterInstance;
}