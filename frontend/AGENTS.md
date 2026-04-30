# Frontend Agent Instructions

This directory contains the local browser UI.

## Rules

- Use React + TypeScript + Vite.
- Keep API access in `src/api.ts`.
- Keep rendering/viewer logic in `src/viewer/`.
- Keep components small and milestone-focused.
- The UI must support a local workflow: project list, video import, job status, result viewer, export links.
- Prefer robust simple UI over visual polish.
- Avoid adding large UI libraries unless needed.

## Validation

Run frontend checks before considering frontend changes complete:

```bash
npm --prefix frontend install
npm --prefix frontend run build
```
