import { useEffect, useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { createProject, listProjects, Project } from '../api'

type ProjectListProps = {
  selectedProjectId?: string
  onSelectProject: (project: Project) => void
}

export default function ProjectList({ selectedProjectId, onSelectProject }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    listProjects()
      .then((loadedProjects) => {
        if (isMounted) setProjects(loadedProjects)
      })
      .catch((reason: Error) => {
        if (isMounted) setError(reason.message)
      })
      .finally(() => {
        if (isMounted) setIsLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsCreating(true)

    try {
      const project = await createProject(name)
      setProjects((currentProjects) => [project, ...currentProjects])
      onSelectProject(project)
      setName('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not create project')
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <section style={sectionStyle}>
      <div>
        <h2 style={headingStyle}>Projects</h2>
        <p style={mutedStyle}>Create a local project folder before importing video.</p>
      </div>

      <form onSubmit={handleSubmit} style={formStyle}>
        <label style={labelStyle} htmlFor="project-name">
          Project name
        </label>
        <div style={rowStyle}>
          <input
            id="project-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Living room scan"
            style={inputStyle}
          />
          <button disabled={isCreating || !name.trim()} style={buttonStyle} type="submit">
            {isCreating ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>

      {error ? <p style={errorStyle}>{error}</p> : null}
      {isLoading ? <p style={mutedStyle}>Loading projects...</p> : null}
      {!isLoading && projects.length === 0 ? <p style={mutedStyle}>No projects yet.</p> : null}

      <ul style={listStyle}>
        {projects.map((project) => (
          <li key={project.id} style={itemStyle}>
            <strong>{project.name}</strong>
            <span style={metaStyle}>{new Date(project.created_at).toLocaleString()}</span>
            <code style={codeStyle}>{project.id}</code>
            <button
              type="button"
              onClick={() => onSelectProject(project)}
              style={project.id === selectedProjectId ? selectedButtonStyle : secondaryButtonStyle}
            >
              {project.id === selectedProjectId ? 'Selected' : 'Select'}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

const sectionStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 8,
  padding: 20,
  maxWidth: 760,
} satisfies CSSProperties

const headingStyle = {
  fontSize: 22,
  margin: '0 0 8px',
} satisfies CSSProperties

const mutedStyle = {
  color: '#57606a',
  margin: '0 0 16px',
} satisfies CSSProperties

const formStyle = {
  display: 'grid',
  gap: 8,
  marginBottom: 16,
} satisfies CSSProperties

const labelStyle = {
  fontWeight: 600,
} satisfies CSSProperties

const rowStyle = {
  display: 'flex',
  gap: 8,
  flexWrap: 'wrap',
} satisfies CSSProperties

const inputStyle = {
  flex: '1 1 260px',
  minWidth: 0,
  padding: '10px 12px',
  border: '1px solid #d0d7de',
  borderRadius: 6,
} satisfies CSSProperties

const buttonStyle = {
  padding: '10px 14px',
  border: 0,
  borderRadius: 6,
  background: '#1f883d',
  color: '#ffffff',
  fontWeight: 700,
} satisfies CSSProperties

const secondaryButtonStyle = {
  justifySelf: 'start',
  padding: '8px 12px',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  background: '#ffffff',
  color: '#24292f',
  fontWeight: 700,
} satisfies CSSProperties

const selectedButtonStyle = {
  ...secondaryButtonStyle,
  borderColor: '#1f883d',
  color: '#1f883d',
} satisfies CSSProperties

const errorStyle = {
  color: '#b42318',
  margin: '0 0 16px',
} satisfies CSSProperties

const listStyle = {
  display: 'grid',
  gap: 8,
  listStyle: 'none',
  padding: 0,
  margin: 0,
} satisfies CSSProperties

const itemStyle = {
  display: 'grid',
  gap: 4,
  border: '1px solid #d8dee4',
  borderRadius: 6,
  padding: 12,
} satisfies CSSProperties

const metaStyle = {
  color: '#57606a',
  fontSize: 14,
} satisfies CSSProperties

const codeStyle = {
  color: '#57606a',
  fontSize: 12,
  overflowWrap: 'anywhere',
} satisfies CSSProperties
