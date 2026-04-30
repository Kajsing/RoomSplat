# Project Documentation and Status

## Current status
Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented.
Current milestone: Milestone 1 — Minimal local hosted web app.

## Latest completed milestone
- Milestone 0 — Repository scaffold and docs.

## Decisions made
| Date | Decision | Reason |
|---|---|---|
| 2026-04-30 | Local hosted web app | Keeps Android as capture device and avoids mobile performance constraints. |
| 2026-04-30 | Windows-native first | Matches primary user environment. |
| 2026-04-30 | Gaussian Splatting / NeRF first | Project owner selected splat/NeRF direction over traditional-only point cloud reconstruction. |
| 2026-04-30 | Video import before stream | Reduces MVP complexity and creates reproducible test inputs. |

## Known issues
- No reconstruction pipeline selected yet.
- `.ply` may mean point cloud or splat data depending on pipeline stage.
- `.glb` export path is uncertain until representation is known.

## Commands run
- python --version
- node --version
- python -m pytest backend/tests pipeline/tests
- npm --prefix frontend run build
