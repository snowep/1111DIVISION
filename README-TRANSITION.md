# ORION TypeScript + MUI Transition

Transition layer from the existing Python ORION prototype to a TypeScript runtime with a live Material UI interface.

## Stack

- Next.js 16.3.5
- React 19.3.0
- TypeScript 5.9.2
- Material UI 9.4.0
- Emotion
- Node.js filesystem APIs

MUI 9 is the current stable major. This implementation intentionally uses standard MUI components and the default MUI visual system. No custom theme, Tailwind, CSS modules, styled-components, or custom design system.

## Local Markdown / filesystem integration

Set `ORION_WORKSPACE_ROOT=D:\Project\1111DIVISION`.

The Next.js server reads that directory directly.

- `GET /api/workspace` — scan workspace
- `GET /api/workspace/file?path=AGENT.md` — read a file
- `POST /api/memory` — append to a Markdown file

All filesystem paths are constrained beneath `ORION_WORKSPACE_ROOT`.

## Run

```bash
npm install
npm run typecheck
npm run dev
```

Open `http://localhost:3000`.

## Next

Replace the transition event generator with the real ORION orchestrator; then connect Markdown retrieval, persona routing, permissions, tools, evaluator/correction, LLM provider, task sessions, and evolution to the same event bus.
