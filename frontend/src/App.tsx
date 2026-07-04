import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { fetchHealth, Job, Project } from './api'
import JobStatusPanel from './components/JobStatusPanel'
import ProjectList from './components/ProjectList'
import UploadPanel from './components/UploadPanel'

export default function App() {
  const [message, setMessage] = useState('Loading backend health...')
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  useEffect(() => {
    fetchHealth().then((h) => setMessage(`${h.app}: ${h.status} (${h.version})`)).catch((e) => setMessage(`Backend unavailable: ${e.message}`))
  }, [])
  return (
    <main style={mainStyle}>
      <header>
        <h1 style={titleStyle}>Local 3D Room Mapper</h1>
        <p style={healthStyle}>{message}</p>
      </header>
      <ProjectList
        selectedProjectId={selectedProject?.id}
        onSelectProject={(project) => {
          setSelectedProject(project)
          setActiveJob(null)
        }}
      />
      <UploadPanel project={selectedProject} onJobChange={setActiveJob} />
      <JobStatusPanel project={selectedProject} activeJob={activeJob} onJobChange={setActiveJob} />
    </main>
  )
}

const mainStyle = {
  display: 'grid',
  gap: 24,
  padding: 32,
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  color: '#24292f',
} satisfies CSSProperties

const titleStyle = {
  fontSize: 32,
  margin: '0 0 8px',
} satisfies CSSProperties

const healthStyle = {
  color: '#57606a',
  margin: 0,
} satisfies CSSProperties
