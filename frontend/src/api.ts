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

type ProjectListResponse = {
  projects: Project[]
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `Request failed with ${response.status}`)
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
