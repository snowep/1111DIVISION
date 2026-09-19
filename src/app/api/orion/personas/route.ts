import { NextRequest, NextResponse } from "next/server";
import { getPersonaRouter } from "@/lib/orion-persona";
import type { PersonaDefinition, PersonaActivationResult } from "@/lib/orion-persona";
import fs from "node:fs/promises";
import path from "node:path";

export async function GET() {
  try {
    const router = getPersonaRouter();
    await router.loadDefinitionsAsync();
    const personas = router.getAvailablePersonas();
    
    // Convert to array with summary info
    const personaList = Object.entries(personas).map(([name, def]) => ({
      name,
      role: def.role,
      purpose: def.purpose,
      level: def.level,
      tools: def.tools.length,
      knowledgeDomains: def.knowledge.length,
      skills: def.skills.length,
    }));
    
    return NextResponse.json({ personas: personaList });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to list personas" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;
    const router = getPersonaRouter();
    await router.loadDefinitionsAsync();

    if (action === "select") {
      const selection = router.selectPersona(params.objective, params.context || {});
      return NextResponse.json({ selection });
    }

    if (action === "activate") {
      const context = await router.activatePersona(params.personaName);
      if (!context) {
        return NextResponse.json(
          { error: `Persona '${params.personaName}' not found` },
          { status: 404 }
        );
      }
      const estimateTokens = (ctx: any) => {
        const totalChars = [
          ctx.identityContent,
          ctx.memoryContent,
          ctx.knowledgeContent,
          ctx.skillsContent,
          ctx.experienceContent,
          ctx.sharedMemory,
          ctx.sharedKnowledge,
        ].join("").length;
        return Math.ceil(totalChars / 4);
      };
      return NextResponse.json({ 
        context: router.getContextSummary(context),
        personaName: params.personaName,
        activated: true,
        contextTokensEstimate: estimateTokens(context),
      });
    }

    if (action === "route") {
      const result: PersonaActivationResult = await router.routeTask(
        params.objective,
        params.context || {}
      );
      return NextResponse.json(result);
    }

    if (action === "deactivate") {
      router.deactivatePersona();
      return NextResponse.json({ ok: true });
    }

    if (action === "getActive") {
      const context = router.getActivePersona();
      if (!context) {
        return NextResponse.json({ active: false });
      }
      return NextResponse.json({
        active: true,
        personaName: context.persona.name,
        summary: router.getContextSummary(context),
        tokensEstimate: router.estimateTokens(context),
      });
    }

    if (action === "create") {
      // Create a new persona definition
      const { name, role, purpose, boundaries, style, tools, knowledge, skills, evaluationCriteria, level } = params;
      
      if (!name || !role || !purpose) {
        return NextResponse.json(
          { error: "name, role, and purpose are required" },
          { status: 400 }
        );
      }

      const rootPath = process.env.ORION_WORKSPACE_ROOT
        ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
        : process.cwd();
      const personasDir = path.join(rootPath, ".agent", "orion", "personas", "definitions");
      const personaDir = path.join(personasDir, name);
      
      await fs.mkdir(personasDir, { recursive: true });
      await fs.mkdir(personaDir, { recursive: true });
      await fs.mkdir(path.join(personaDir, "memory"), { recursive: true });
      await fs.mkdir(path.join(personaDir, "knowledge"), { recursive: true });
      await fs.mkdir(path.join(personaDir, "experience"), { recursive: true });
      await fs.mkdir(path.join(personaDir, "skills"), { recursive: true });
      
      const markdown = `# Persona: ${name}

## Role
${role}

## Purpose
${purpose}

## Boundaries
${(boundaries || []).map((b: string) => `- ${b}`).join("\n")}

## Style
${style || "Helpful, concise, accurate"}

## Tools
${(tools || []).map((t: string) => `- ${t}`).join("\n")}

## Memory
[Auto-loaded from memory/ directory]

## Knowledge
${(knowledge || []).map((k: string) => `- ${k}`).join("\n")}

## Skills
${(skills || []).map((s: string) => `- ${s}`).join("\n")}

## Experience
[Auto-loaded from experience/ directory]

## Evaluation Criteria
${(evaluationCriteria || []).map((c: string) => `- ${c}`).join("\n")}

## Level
${level || 1}
`;
      
      await fs.writeFile(
        path.join(personasDir, `${name}.md`),
        markdown,
        "utf-8"
      );
      
      // Reload definitions
      await router.loadDefinitionsAsync();
      
      return NextResponse.json({ ok: true, name });
    }

    return NextResponse.json(
      { error: "Invalid action. Use 'select', 'activate', 'route', 'deactivate', 'getActive', or 'create'" },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Operation failed" },
      { status: 500 }
    );
  }
}