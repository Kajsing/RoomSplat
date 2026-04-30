export async function fetchHealth(baseUrl = 'http://127.0.0.1:8000') {
  const response = await fetch(`${baseUrl}/health`)
  if (!response.ok) throw new Error('Failed to fetch health')
  return response.json() as Promise<{status:string;app:string;version:string}>
}
