# Decision 0001: Local Web App, Windows Native First

## Status

Accepted.

## Context

The primary user is a technical Windows user. Android devices are capture devices in v1, not the main runtime.

## Decision

Build a local hosted web app that runs on a Windows PC. Use a Python FastAPI backend, a React/Vite browser UI, and local project folders for storage.

## Consequences

- The app can be used from a browser while heavy processing stays on the PC.
- Setup and validation must stay Windows-friendly.
- Docker, WSL, and cloud processing are fallback or future options, not v1 requirements.
