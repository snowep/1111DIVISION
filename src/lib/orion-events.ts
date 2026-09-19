import type { OrionEvent } from "./types";

export function createTransitionEvents(task: string): OrionEvent[] {
  const now = Date.now();
  const event = (n: number, stage: string, message: string, status: OrionEvent["status"]): OrionEvent => ({
    id: `${now}-${n}`,
    time: new Date(now + n * 400).toLocaleTimeString(),
    stage,
    message,
    status
  });
  return [
    event(1, "REQUEST", task, "complete"),
    event(2, "INSPECT", "Scanning local workspace and .agent state", "complete"),
    event(3, "MEMORY", "Retrieving relevant Markdown memory", "complete"),
    event(4, "KNOWLEDGE", "Retrieving relevant workspace knowledge", "complete"),
    event(5, "PERSONA", "ORION remains primary; persona routing ready", "info"),
    event(6, "EXECUTE", "Transition runtime ready for tool adapter", "running")
  ];
}
