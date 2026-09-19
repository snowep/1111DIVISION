import { NextRequest, NextResponse } from "next/server";
import { retrieveForTask, writeMemory, readMemoryFile, listMemoryFiles, type RetrievalResult } from "@/lib/orion-memory";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const objective = searchParams.get("objective");
  const budget = (searchParams.get("budget") as "micro" | "standard" | "deep" | "full") || "standard";
  const persona = searchParams.get("persona") || undefined;
  const keywordsParam = searchParams.get("keywords");
  const keywords = keywordsParam ? keywordsParam.split(",") : [];

  if (!objective) {
    return NextResponse.json(
      { error: "objective query parameter is required" },
      { status: 400 }
    );
  }

  try {
    const result: RetrievalResult = await retrieveForTask(objective, keywords, budget, persona);
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Retrieval failed" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...params } = body;

    if (action === "write") {
      const result = await writeMemory(params);
      return NextResponse.json(result);
    }

    if (action === "read") {
      const content = await readMemoryFile(params.path);
      return NextResponse.json({ content, path: params.path });
    }

    if (action === "list") {
      const files = await listMemoryFiles(params.store);
      return NextResponse.json({ files, store: params.store });
    }

    return NextResponse.json(
      { error: "Invalid action. Use 'write', 'read', or 'list'" },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Operation failed" },
      { status: 500 }
    );
  }
}