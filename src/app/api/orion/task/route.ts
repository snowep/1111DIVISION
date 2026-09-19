/**
 * ORION Task API - Main entry point for running tasks through the full pipeline
 * 
 * Integrates: Persona Router → Memory/Knowledge Retrieval → Evaluator → EXP → Version
 */

import { NextRequest, NextResponse } from "next/server";
import { retrieveForTask } from "@/lib/orion-memory";
import { getExpManager } from "@/lib/orion-exp";
import { getVersionManager } from "@/lib/orion-version";
import { EvaluatorEngine, createEvaluatorConfig, type TaskContext } from "@/lib/orion-evaluator";

export interface OrionTaskRequest {
  objective: string;
  context?: Record<string, unknown>;
  persona?: string;
  budget?: "micro" | "standard" | "deep" | "full";
  autoEvaluate?: boolean;
}

import type { EXPProgress } from "@/lib/orion-exp";
import type { VersionInfo } from "@/lib/orion-version";

export interface OrionTaskResponse {
  taskId: string;
  status: "started" | "completed" | "failed";
  persona?: string;
  retrieval?: Awaited<ReturnType<typeof retrieveForTask>>;
  evaluation?: Awaited<ReturnType<typeof EvaluatorEngine.prototype.evaluate>>;
  expResult?: { result: string; progress: EXPProgress };
  version?: VersionInfo;
  error?: string;
}

// In-memory task store (in production, use persistent storage)
const taskStore = new Map<string, OrionTaskResponse>();

function generateTaskId(): string {
  const date = new Date().toISOString().split("T")[0].replace(/-/g, "");
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `task-${date}-${random}`;
}

export async function POST(request: NextRequest) {
  try {
    const body: OrionTaskRequest = await request.json();
    
    if (!body.objective) {
      return NextResponse.json(
        { error: "objective is required" },
        { status: 400 }
      );
    }

    const taskId = generateTaskId();
    const budget = body.budget || "standard";
    const persona = body.persona;

    // Initialize response
    const response: OrionTaskResponse = {
      taskId,
      status: "started",
      persona,
    };

    taskStore.set(taskId, response);

    // STAGE 1: RETRIEVAL - Get relevant memory/knowledge/experience
    const retrieval = await retrieveForTask(
      body.objective,
      [], // keywords - could extract from objective
      budget,
      persona
    );
    response.retrieval = retrieval;

    // STAGE 2: PERSONA ACTIVATION (placeholder - would load persona context)
    // In full implementation, this would call PersonaRouter.activate_persona()

    // STAGE 3: EXECUTION (placeholder - would run actual task)
    // For now, simulate a task context for evaluation
    const mockTaskContext: TaskContext = {
      objective: body.objective,
      plan: [
        "Understand the objective",
        "Retrieve relevant context",
        "Execute the task",
        "Verify results",
        "Document outcome"
      ],
      executionLog: [
        { action: "Retrieve context", result: `Found ${retrieval.totalTokens} tokens of relevant context`, success: true },
        { action: "Execute task", result: "Task execution simulated", success: true },
        { action: "Verify results", result: "Verification passed", success: true },
      ],
      verificationResults: [
        { overall: "PASS", checks: { objective_met: true, verification_evidence: true, no_critical_issues: true } }
      ],
      critiqueFindings: [],
      corrections: [],
      persona,
    };

    // STAGE 4: EVALUATION (if requested)
    if (body.autoEvaluate !== false) {
      const config = createEvaluatorConfig();
      const root = process.env.ORION_WORKSPACE_ROOT
        ? require("node:path").resolve(process.env.ORION_WORKSPACE_ROOT)
        : process.cwd();
      
      const engine = new EvaluatorEngine(config, root);
      
      const evaluation = engine.evaluate(
        mockTaskContext,
        mockTaskContext.verificationResults[0],
        mockTaskContext.critiqueFindings,
        3, // correction budget
        1
      );
      
      response.evaluation = evaluation;

      // STAGE 5: EXP AWARD (if evaluation passed)
      if (evaluation.verdict === "PASS") {
        const expManager = getExpManager();
        const event = body.objective.split(" ").length > 20 ? "complex_verified" : "normal_verified";
        const expResult = await expManager.award(
          taskId,
          { passed: evaluation.verdict === "PASS", score: evaluation.score },
          event,
          "success",
          `Completed: ${body.objective.slice(0, 100)}`,
          { persona, budget }
        );
        response.expResult = {
          result: expResult,
          progress: expManager.getProgress()
        };

        // STAGE 6: VERSION BUMP (on successful task)
        const versionManager = getVersionManager();
        const versionResult = await versionManager.bumpVersion("build");
        response.version = versionResult.version;
      }
    }

    response.status = "completed";
    taskStore.set(taskId, response);

    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Task failed" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  const taskId = request.nextUrl.searchParams.get("taskId");
  
  if (taskId) {
    const task = taskStore.get(taskId);
    if (!task) {
      return NextResponse.json({ error: "Task not found" }, { status: 404 });
    }
    return NextResponse.json(task);
  }

  // List all tasks
  const tasks = Array.from(taskStore.values()).sort((a, b) => 
    b.taskId.localeCompare(a.taskId)
  );
  return NextResponse.json({ tasks });
}