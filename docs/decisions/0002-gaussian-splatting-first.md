# Decision 0002: Gaussian Splatting / NeRF First

## Status

Accepted as project direction; implementation path still needs a spike.

## Context

The project owner selected Gaussian Splatting / NeRF-style reconstruction over a traditional-only photogrammetry or point-cloud project.

## Decision

Pursue Gaussian Splatting / NeRF first, using existing tools where practical. COLMAP, pycolmap, Nerfstudio, gsplat, and Open3D are candidate dependencies or adapters.

## Consequences

- The pipeline must honestly distinguish Gaussian splat data from conventional point clouds and meshes.
- Milestone 4 is a spike to prove the first local Windows-native path.
- The app must not pretend placeholder outputs are real reconstructions.
