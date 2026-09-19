import { NextRequest, NextResponse } from "next/server";
import { appendMarkdown } from "@/lib/workspace";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as { path?: string; content?: string };
  if (!body.path || !body.content) {
    return NextResponse.json({ error: "path and content are required" }, { status: 400 });
  }
  try {
    await appendMarkdown(body.path, body.content);
    return NextResponse.json({ ok: true, path: body.path });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Memory write failed" },
      { status: 500 }
    );
  }
}
