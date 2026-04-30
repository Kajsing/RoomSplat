# Decision 0003: Imported Video First, Streams Later

## Status

Accepted.

## Context

The core engine should first prove that it can consume a video and produce a 3D result. Live capture and Android workflows add complexity before the reconstruction path is known.

## Decision

Implement imported video file workflow first. Add phone/webcam stream capture, Android companion workflows, and Kinect plugins later.

## Consequences

- Early tests can use tiny deterministic videos.
- The project can validate frame extraction and reconstruction contracts before adding streaming state.
- Capture devices remain optional inputs rather than core runtime assumptions.
