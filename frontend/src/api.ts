const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

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

export type JobType = 'frame_extraction' | 'reconstruction_spike'
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

type ProjectListResponse = {
  projects: Project[]
}

type JobListResponse = {
  jobs: Job[]
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

function readErrorMessage(text: string) {
  try {
    const payload = JSON.parse(text) as { detail?: string }
    return payload.detail || text
  } catch {
    return text
  }
}
