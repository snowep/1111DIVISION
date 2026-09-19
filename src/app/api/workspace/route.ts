import { NextResponse } from "next/server";
import { scanWorkspace } from "@/lib/workspace";

export async function GET() {
  try {
    return NextResponse.json(await scanWorkspace());
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Workspace scan failed" },
      { status: 500 }
    );
  }
}
