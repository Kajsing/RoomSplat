import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { Artifact, artifactUrl, DEFAULT_BASE_URL, Job, listArtifacts, Project } from '../api'
import { glbPreviewMessage, parseGlbInfo } from '../viewer/glbViewer'
import { parseAsciiPly, PointCloud, renderPointCloud } from '../viewer/pointCloudViewer'

type ViewerPanelProps = {
  project: Project | null
  activeJob: Job | null
}

export default function ViewerPanel({ project, activeJob }: ViewerPanelProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null)
  const [pointCloud, setPointCloud] = useState<PointCloud | null>(null)
  const [debugText, setDebugText] = useState<string | null>(null)
  const [glbText, setGlbText] = useState<string | null>(null)
  const [rotationY, setRotationY] = useState(25)
  const [zoom, setZoom] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    if (!project) {
      setArtifacts([])
      setSelectedArtifactId(null)
      return
    }
    refreshArtifacts(project.id)
  }, [project])

  useEffect(() => {
    if (project && activeJob?.status === 'succeeded') {
      refreshArtifacts(project.id)
    }
  }, [activeJob?.status, project])

  const selectedArtifact = artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null

  useEffect(() => {
    setPointCloud(null)
    setDebugText(null)
    setGlbText(null)
    setError(null)
    if (!selectedArtifact) return

    if (selectedArtifact.artifact_type === 'point_cloud_ply' || selectedArtifact.artifact_type === 'splat_ply') {
      fetch(artifactUrl(selectedArtifact))
        .then((response) => {
          if (!response.ok) throw new Error('Could not load PLY artifact')
          return response.text()
        })
        .then((text) => setPointCloud(parseAsciiPly(text)))
        .catch((reason: Error) => setError(reason.message))
    } else if (selectedArtifact.artifact_type === 'debug_report') {
      fetch(artifactUrl(selectedArtifact))
        .then((response) => {
          if (!response.ok) throw new Error('Could not load debug report')
          return response.text()
        })
        .then((text) => setDebugText(text))
        .catch((reason: Error) => setError(reason.message))
    } else if (selectedArtifact.artifact_type === 'mesh_glb') {
      fetch(artifactUrl(selectedArtifact))
        .then((response) => {
          if (!response.ok) throw new Error('Could not load GLB artifact')
          return response.arrayBuffer()
        })
        .then((buffer) => setGlbText(glbPreviewMessage(parseGlbInfo(buffer))))
        .catch((reason: Error) => setError(reason.message))
    }
  }, [selectedArtifact])

  useEffect(() => {
    if (!pointCloud || !canvasRef.current) return
    renderPointCloud(canvasRef.current, pointCloud, { rotationY, zoom })
  }, [pointCloud, rotationY, zoom])

  function refreshArtifacts(projectId: string) {
    setError(null)
    listArtifacts(projectId)
      .then((loadedArtifacts) => {
        setArtifacts(loadedArtifacts)
        setSelectedArtifactId((currentId) => currentId ?? loadedArtifacts[0]?.id ?? null)
      })
      .catch((reason: Error) => setError(reason.message))
  }

  return (
    <section style={sectionStyle}>
      <div style={headerStyle}>
        <div>
          <h2 style={headingStyle}>Viewer</h2>
          <p style={mutedStyle}>{project ? project.name : 'Select a project'}</p>
        </div>
        <button disabled={!project} onClick={() => project && refreshArtifacts(project.id)} style={secondaryButtonStyle} type="button">
          Refresh
        </button>
      </div>

      {artifacts.length === 0 ? <p style={mutedStyle}>No result artifacts yet.</p> : null}

      {artifacts.length > 0 ? (
        <div style={layoutStyle}>
          <ul style={listStyle}>
            {artifacts.map((artifact) => (
              <li key={artifact.id}>
                <button
                  onClick={() => setSelectedArtifactId(artifact.id)}
                  style={artifact.id === selectedArtifactId ? selectedArtifactStyle : artifactButtonStyle}
                  type="button"
                >
                  <strong>{artifact.name}</strong>
                  <span>{formatArtifactType(artifact.artifact_type)}</span>
                </button>
              </li>
            ))}
          </ul>

          <div style={viewerStyle}>
            {selectedArtifact ? (
              <>
                <div style={artifactHeaderStyle}>
                  <strong>{selectedArtifact.name}</strong>
                  <span>{selectedArtifact.description}</span>
                  <a href={`${DEFAULT_BASE_URL}${selectedArtifact.download_url}`} style={linkStyle}>
                    Download
                  </a>
                </div>

                {selectedArtifact.artifact_type === 'point_cloud_ply' || selectedArtifact.artifact_type === 'splat_ply' ? (
                  <div style={canvasWrapStyle}>
                    <canvas ref={canvasRef} width={720} height={420} style={canvasStyle} />
                    <div style={controlsStyle}>
                      <label>
                        Rotate
                        <input
                          max={180}
                          min={-180}
                          onChange={(event) => setRotationY(Number(event.target.value))}
                          type="range"
                          value={rotationY}
                        />
                      </label>
                      <label>
                        Zoom
                        <input
                          max={3}
                          min={0.3}
                          onChange={(event) => setZoom(Number(event.target.value))}
                          step={0.1}
                          type="range"
                          value={zoom}
                        />
                      </label>
                    </div>
                    {selectedArtifact.artifact_type === 'splat_ply' ? (
                      <p style={mutedStyle}>Displayed as a debug point preview; splat shading is not simulated here.</p>
                    ) : null}
                  </div>
                ) : null}

                {selectedArtifact.artifact_type === 'mesh_glb' && glbText ? <p style={mutedStyle}>{glbText}</p> : null}
                {selectedArtifact.artifact_type === 'debug_report' && debugText ? <pre style={preStyle}>{debugText}</pre> : null}
              </>
            ) : null}
          </div>
        </div>
      ) : null}

      {error ? <p style={errorStyle}>{error}</p> : null}
    </section>
  )
}

function formatArtifactType(type: Artifact['artifact_type']) {
  const labels = {
    point_cloud_ply: 'Point cloud PLY',
    splat_ply: 'Splat PLY',
    mesh_glb: 'GLB',
    debug_report: 'Debug report',
    unsupported: 'Unsupported',
  }
  return labels[type]
}

const sectionStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 8,
  padding: 20,
  maxWidth: 1000,
} satisfies CSSProperties

const headerStyle = {
  alignItems: 'start',
  display: 'flex',
  gap: 16,
  justifyContent: 'space-between',
} satisfies CSSProperties

const headingStyle = {
  fontSize: 22,
  margin: '0 0 8px',
} satisfies CSSProperties

const mutedStyle = {
  color: '#57606a',
  margin: '0 0 16px',
} satisfies CSSProperties

const layoutStyle = {
  display: 'grid',
  gap: 16,
  gridTemplateColumns: 'minmax(180px, 260px) minmax(0, 1fr)',
} satisfies CSSProperties

const listStyle = {
  display: 'grid',
  gap: 8,
  listStyle: 'none',
  margin: 0,
  padding: 0,
} satisfies CSSProperties

const artifactButtonStyle = {
  background: '#ffffff',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  color: '#24292f',
  display: 'grid',
  gap: 4,
  padding: 10,
  textAlign: 'left',
  width: '100%',
} satisfies CSSProperties

const selectedArtifactStyle = {
  ...artifactButtonStyle,
  borderColor: '#1f883d',
} satisfies CSSProperties

const viewerStyle = {
  minWidth: 0,
} satisfies CSSProperties

const artifactHeaderStyle = {
  display: 'grid',
  gap: 4,
  marginBottom: 12,
} satisfies CSSProperties

const canvasWrapStyle = {
  display: 'grid',
  gap: 12,
} satisfies CSSProperties

const canvasStyle = {
  aspectRatio: '12 / 7',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  maxWidth: '100%',
  width: '100%',
} satisfies CSSProperties

const controlsStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 16,
} satisfies CSSProperties

const preStyle = {
  background: '#f6f8fa',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  maxHeight: 420,
  overflow: 'auto',
  padding: 12,
  whiteSpace: 'pre-wrap',
} satisfies CSSProperties

const linkStyle = {
  color: '#0969da',
} satisfies CSSProperties

const secondaryButtonStyle = {
  padding: '8px 12px',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  background: '#ffffff',
  color: '#24292f',
  fontWeight: 700,
} satisfies CSSProperties

const errorStyle = {
  color: '#b42318',
  margin: '12px 0 0',
} satisfies CSSProperties
