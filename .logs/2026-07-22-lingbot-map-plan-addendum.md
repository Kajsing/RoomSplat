# LingBot-Map plan addendum

Date: 2026-07-22

## Context

Reviewed the local reference copy at `C:\project\lingbot-map` as inspiration for RoomSplat after the user noted that similar work now exists elsewhere.

## Findings

- LingBot-Map is useful as inspiration for feed-forward / learned reconstruction contracts.
- The most relevant ideas are per-frame depth/confidence/points, camera pose and intrinsic outputs, trajectory metadata, completion markers, and viewer controls such as confidence filtering and current/all-frame modes.
- RoomSplat should not directly absorb LingBot-Map as a core dependency right now.

## Risks

- Large `.pt` checkpoints can be unsafe if loaded with pickle-based `torch.load` from untrusted sources.
- Default model/data/sky-mask downloads would conflict with RoomSplat's local-only assumptions.
- CUDA 12.8, FlashInfer, Kaolin, and custom CUDA extensions are heavy and likely fragile on Windows.
- Some LingBot-Map viewers bind to `0.0.0.0` and allow user-selected output paths; RoomSplat should keep localhost-only binding and strict project path containment.

## Decision

Added Milestone 9, `Learned Geometry Adapter Readiness`, to `PLAN.md`.

The milestone prepares RoomSplat for learned geometry adapters through a RoomSplat-native geometry bundle contract and safety rules before any specific model runtime is integrated.

## Validation

Documentation-only change. Run:

```bash
git diff --check
git status --short
```
