import { NextRequest, NextResponse } from "next/server";
import { getExpManager } from "@/lib/orion-exp";

export async function GET() {
  try {
    const manager = getExpManager();
    const progress = manager.getProgress();
    const records = manager.getRecords();
    return NextResponse.json({ progress, records });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to get EXP progress" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;
    const manager = getExpManager();

    if (action === "award") {
      const result = await manager.award(
        params.taskId,
        params.evaluation,
        params.event,
        params.outcome,
        params.lesson,
        params.metadata
      );
      return NextResponse.json({ result, progress: manager.getProgress() });
    }

    if (action === "reset") {
      await manager.reset();
      return NextResponse.json({ ok: true, progress: manager.getProgress() });
    }

    return NextResponse.json(
      { error: "Invalid action. Use 'award' or 'reset'" },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Operation failed" },
      { status: 500 }
    );
  }
}