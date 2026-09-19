export type WorkspaceFile = {
  path: string;
  kind: "markdown" | "code" | "config" | "other";
  size: number;
};

export type WorkspaceSnapshot = {
  root: string;
  files: WorkspaceFile[];
  markdown: WorkspaceFile[];
  agentFiles: WorkspaceFile[];
  scannedAt: string;
};

export type OrionEvent = {
  id: string;
  time: string;
  stage: string;
  message: string;
  status: "running" | "complete" | "info" | "error" | "warning";
};
