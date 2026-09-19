import { NextRequest, NextResponse } from "next/server";
import { readWorkspaceFile } from "@/lib/workspace";

export async function GET(request: NextRequest) {
  const file = request.nextUrl.searchParams.get("path");
  if (!file) return NextResponse.json({ error: "Missing path" }, { status: 400 });
  try {
    return NextResponse.json({ path: file, content: await readWorkspaceFile(file) });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "File read failed" },
      { status: 500 }
    );
  }
}
