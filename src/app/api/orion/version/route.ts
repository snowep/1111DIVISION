import { NextRequest, NextResponse } from "next/server";
import { getVersionManager } from "@/lib/orion-version";

export async function GET() {
  try {
    const manager = getVersionManager();
    const version = manager.getVersion();
    return NextResponse.json({ version });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to get version" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;
    const manager = getVersionManager();

    if (action === "bump") {
      const result = await manager.bumpVersion(params.type);
      return NextResponse.json(result);
    }

    if (action === "milestone") {
      const version = await manager.recordMilestone(params.milestone, params.version);
      return NextResponse.json({ version });
    }

    if (action === "setTier") {
      const version = await manager.setTier(params.tier);
      return NextResponse.json({ version });
    }

    if (action === "reset") {
      const version = await manager.reset();
      return NextResponse.json({ version });
    }

    return NextResponse.json(
      { error: "Invalid action. Use 'bump', 'milestone', 'setTier', or 'reset'" },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Operation failed" },
      { status: 500 }
    );
  }
}