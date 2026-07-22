export const DEFAULT_BASE_URL =
  import.meta.env.VITE_ROOMSPLAT_API_URL || import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

export type HealthResponse = {
  status: string
  app: string
  version: string
}

export type Project = {
  id: string
  name: string
  created_at: string
  path: string
}

export type VideoImport = {
  project_id: string
  original_filename: string
  stored_filename: string
  source_video: string
  size_bytes: number
  content_type: string | null
  imported_at: string
}

export type FrameExtraction = {
  project_id: string
  source_video: string
  frames_dir: string
  fps: number
  frame_count: number
  extracted_frame_count: number
  extraction_stride: number
  width: number
  height: number
  extracted_at: string
}

export type FrameExtractionOptions = {
  source_video?: string
  stride: number
  max_frames?: number
}

export type JobType =
  | 'frame_extraction'
  | 'reconstruction_spike'
  | 'debug_frame_cloud'
  | 'reconstruct_point_cloud'
  | 'reconstruct_splat'
  | 'learned_geometry_preflight'
  | 'import_learned_geometry'
export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed'

export type Job = {
  id: string
  project_id: string
  job_type: JobType
  status: JobStatus
  params: Record<string, unknown>
  created_at: string
  updated_at: string
  started_at: string | null
  finished_at: string | null
  result: Record<string, unknown> | null
  error: string | null
  log_path: string
}

export type ArtifactType =
  | 'debug_frame_cloud_ply'
  | 'point_cloud_ply'
  | 'predicted_point_cloud_ply'
  | 'splat_ply'
  | 'mesh_glb'
  | 'learned_geometry_bundle'
  | 'debug_report'
  | 'unsupported'

export type Artifact = {
  id: string
  project_id: string
  name: string
  relative_path: string
  artifact_type: ArtifactType
  viewer_supported: boolean
  size_bytes: number
  modified_at: string
  download_url: string
  description: string
}

export type DebugFramePlane = {
  frame_index: number
  source_frame: string
  position: { x: number; y: number; z: number }
  angle_degrees: number
  point_count: number
  image_width: number
  image_height: number
  plane_width: number
  plane_height: number
}

export type DebugFrameCloudMetadata = {
  project_id: string
  artifact_type: 'debug_frame_cloud_ply'
  mode: 'debug'
  not_reconstruction: boolean
  generated_at?: string
  source_metadata?: string
  frames_dir?: string
  source_frame_count?: number
  frame_count: number
  sampled_points: number
  max_points: number
  params?: {
    max_points: number
    frame_step: number
    arc_degrees: number
    plane_width: number
  }
  frame_planes: DebugFramePlane[]
  output_path?: string
  warning?: string
}

export type ReconstructionCamera = {
  camera_id: number
  model: string
  width: number
  height: number
  params: number[]
}

export type ReconstructionRegisteredImage = {
  image_id: number
  camera_id: number
  name: string
  qvec: [number, number, number, number]
  tvec: [number, number, number]
  center: { x: number; y: number; z: number }
}

export type ReconstructionCameraPathPoint = {
  image_id: number
  name: string
  position: { x: number; y: number; z: number }
}

export type ReconstructionMetadata = {
  project_id: string
  artifact_type: 'point_cloud_ply'
  mode: 'reconstruction'
  reconstruction_type: 'sparse_point_cloud'
  is_reconstruction: boolean
  not_reconstruction: boolean
  debug: boolean
  placeholder: boolean
  adapter: string
  generated_at?: string
  source_metadata?: string
  frames_dir?: string
  input_frame_count: number
  source_frame_count?: number
  registered_frame_count: number
  sparse_point_count: number
  ply_point_count: number
  cameras?: ReconstructionCamera[]
  registered_images?: ReconstructionRegisteredImage[]
  camera_path?: ReconstructionCameraPathPoint[]
  trajectory_bounds?: {
    min: { x: number; y: number; z: number }
    max: { x: number; y: number; z: number }
  } | null
  quality?: {
    status: 'inspectable' | 'too_sparse'
    warning: string | null
  }
  params?: {
    preset?: 'quick' | 'balanced' | 'detail'
    matcher: 'exhaustive' | 'sequential'
    use_gpu: boolean
    recommended_frame_stride?: number
    recommended_max_frames?: number
    description?: string
  }
  colmap?: {
    executable: string
    command_count: number
    workspace: string
  }
  output_path?: string
  warning?: string | null
}

export type SplatReconstructionMetadata = {
  project_id: string
  artifact_type: 'splat_ply'
  mode: 'reconstruction'
  reconstruction_type: 'gaussian_splat'
  adapter: string
  status: 'blocked_missing_dependencies' | 'succeeded' | 'failed' | string
  is_reconstruction: boolean
  not_reconstruction: boolean
  debug: boolean
  placeholder: boolean
  generated_at?: string
  frames_dir?: string
  input_frame_count: number
  source_frame_count?: number
  params?: {
    method: 'splatfacto' | 'splatfacto-big'
    max_iterations?: number | null
  }
  readiness?: {
    status: string
    summary: string
    blockers: string[]
    next_steps: string[]
  }
  commands?: {
    process_data: string[]
    train: string[]
    export: string[]
  }
  output_path?: string | null
  warning?: string | null
}

export type GeometryBundleVector3 = {
  x: number
  y: number
  z: number
}

export type GeometryBundleMetadata = {
  project_id: string
  schema_version: 'roomsplat.geometry_bundle.v1'
  artifact_type: 'learned_geometry_bundle'
  mode: 'learned_geometry'
  source_adapter: string
  adapter_family: 'learned' | 'feed_forward' | 'external' | 'unknown'
  status: 'complete' | 'incomplete' | 'blocked_missing_dependencies' | 'failed'
  complete: boolean
  is_reconstruction: boolean
  not_reconstruction: boolean
  frame_count: number
  frame_index_map: Array<{
    bundle_frame_index: number
    source_frame_index: number
    source_frame: string
  }>
  cameras: Array<{
    frame_index: number
    position: GeometryBundleVector3
    qvec?: [number, number, number, number] | null
    transform?: number[][] | null
  }>
  intrinsics: Array<{
    frame_index: number
    width: number
    height: number
    fx: number
    fy: number
    cx: number
    cy: number
  }>
  trajectory: Array<{
    frame_index: number
    position: GeometryBundleVector3
  }>
  capabilities: {
    depth: boolean
    confidence: boolean
    mask: boolean
    pointmap: boolean
  }
  primary_artifacts: Array<{
    relative_path: string
    artifact_type: 'predicted_point_cloud_ply' | 'mesh_glb' | 'unsupported'
    role: string
    description: string
  }>
  sidecars: Array<{
    relative_path: string
    sidecar_type: 'depth' | 'confidence' | 'mask' | 'pointmap' | 'camera_poses' | 'intrinsics' | 'trajectory' | 'sampling' | 'metadata' | 'other'
    required: boolean
    description: string
  }>
  quality: {
    status: 'unknown' | 'debug' | 'inspectable' | 'needs_review' | 'failed'
    notes: string
  }
  warnings: string[]
  generated_data_rules: {
    local_only: boolean
    no_auto_downloads: boolean
    contained_under_project: boolean
    ignored_by_git: boolean
    notes: string
  }
  generated_at?: string | null
}

export type ExportFormat = 'ply' | 'glb'
export type ExportStatus = 'real' | 'placeholder'

export type ExportResult = {
  id: string
  project_id: string
  source_artifact_id: string
  source_relative_path: string
  export_relative_path: string
  format: ExportFormat
  artifact_type: ArtifactType
  status: ExportStatus
  generated_at: string
  metadata_path: string
  download_url: string
  warning: string | null
}

type ProjectListResponse = {
  projects: Project[]
}

type JobListResponse = {
  jobs: Job[]
}

type ArtifactListResponse = {
  artifacts: Artifact[]
}

type ExportListResponse = {
  exports: ExportResult[]
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(readErrorMessage(errorText) || `Request failed with ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function fetchHealth(baseUrl = DEFAULT_BASE_URL) {
  return requestJson<HealthResponse>(`${baseUrl}/health`)
}

export async function listProjects(baseUrl = DEFAULT_BASE_URL) {
  const response = await requestJson<ProjectListResponse>(`${baseUrl}/projects`)
  return response.projects
}

export async function createProject(name: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<Project>(`${baseUrl}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export async function uploadVideo(projectId: string, file: File, baseUrl = DEFAULT_BASE_URL) {
  const params = new URLSearchParams({ filename: file.name })
  return requestJson<VideoImport>(`${baseUrl}/projects/${projectId}/videos/upload?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': file.type || 'application/octet-stream' },
    body: file,
  })
}

export async function extractFrames(projectId: string, options: FrameExtractionOptions, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<FrameExtraction>(`${baseUrl}/projects/${projectId}/frames/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options),
  })
}

export async function getFrameExtraction(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<FrameExtraction>(`${baseUrl}/projects/${projectId}/frames/extraction`)
}

export async function createJob(projectId: string, jobType: JobType, params: Record<string, unknown>, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<Job>(`${baseUrl}/projects/${projectId}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_type: jobType, params }),
  })
}

export async function getJob(projectId: string, jobId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<Job>(`${baseUrl}/projects/${projectId}/jobs/${jobId}`)
}

export async function listJobs(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  const response = await requestJson<JobListResponse>(`${baseUrl}/projects/${projectId}/jobs`)
  return response.jobs
}

export async function listArtifacts(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  const response = await requestJson<ArtifactListResponse>(`${baseUrl}/projects/${projectId}/artifacts`)
  return response.artifacts
}

export function artifactUrl(artifact: Artifact, baseUrl = DEFAULT_BASE_URL) {
  return `${baseUrl}${artifact.download_url}`
}

export async function getDebugFrameCloudMetadata(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<DebugFrameCloudMetadata>(`${baseUrl}/projects/${projectId}/debug-frame-cloud`)
}

export async function getReconstructionMetadata(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<ReconstructionMetadata>(`${baseUrl}/projects/${projectId}/reconstruction`)
}

export async function getSplatReconstructionMetadata(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<SplatReconstructionMetadata>(`${baseUrl}/projects/${projectId}/splat-reconstruction`)
}

export async function getGeometryBundleMetadata(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  return requestJson<GeometryBundleMetadata>(`${baseUrl}/projects/${projectId}/geometry-bundle`)
}

export async function createExport(
  projectId: string,
  sourceArtifactId: string,
  format: ExportFormat,
  allowPlaceholder = false,
  baseUrl = DEFAULT_BASE_URL,
) {
  return requestJson<ExportResult>(`${baseUrl}/projects/${projectId}/exports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_artifact_id: sourceArtifactId,
      format,
      allow_placeholder: allowPlaceholder,
    }),
  })
}

export async function listExports(projectId: string, baseUrl = DEFAULT_BASE_URL) {
  const response = await requestJson<ExportListResponse>(`${baseUrl}/projects/${projectId}/exports`)
  return response.exports
}

function readErrorMessage(text: string) {
  try {
    const payload = JSON.parse(text) as { detail?: unknown }
    if (typeof payload.detail === 'string') return payload.detail
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (item && typeof item === 'object' && 'msg' in item) return String((item as { msg: unknown }).msg)
          return JSON.stringify(item)
        })
        .join('; ')
    }
    if (payload.detail) return JSON.stringify(payload.detail)
    return text
  } catch {
    return text
  }
}
