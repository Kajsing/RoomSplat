# Kinect Plugin Notes

Kinect support is not required for v1. It should be added later as an input plugin rather than baked into the core video-first pipeline.

Future plugin interface:

```text
InputProvider
  name
  capabilities
  start_capture()
  stop_capture()
  export_session_to_project()
```

Open questions:

- Is the target Kinect hardware v1 or v2?
- Should depth frames be stored alongside RGB frames?
- Should Kinect capture bypass the video import flow or export a session into the same project format?
