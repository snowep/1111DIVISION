import { NextRequest, NextResponse } from "next/server";
import { 
  EvaluatorEngine, 
  createEvaluatorConfig, 
  type TaskContext, 
  type EvaluationResult 
} from "@/lib/orion-evaluator";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;

    if (action !== "evaluate") {
      return NextResponse.json(
        { error: "Only 'evaluate' action supported" },
        { status: 400 }
      );
    }

    // Validate required fields
    const required = ["task", "verification", "critiqueFindings", "correctionBudgetRemaining"];
    for (const field of required) {
      if (!(field in params)) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        );
      }
    }

    const config = createEvaluatorConfig(params.config);
    const root = process.env.ORION_WORKSPACE_ROOT
      ? require("node:path").resolve(process.env.ORION_WORKSPACE_ROOT)
      : process.cwd();
    
    const engine = new EvaluatorEngine(config, root);
    
    const result: EvaluationResult = engine.evaluate(
      params.task as TaskContext,
      params.verification,
      params.critiqueFindings,
      params.correctionBudgetRemaining,
      params.evaluationCycle || 1
    );

    return NextResponse.json({ result });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Evaluation failed" },
      { status: 500 }
    );
  }
}