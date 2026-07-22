import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import {
  Artifact,
  artifactUrl,
  createExport,
  createJob,
  DEFAULT_BASE_URL,
  DebugFrameCloudMetadata,
  ExportFormat,
  ExportResult,
  getDebugFrameCloudMetadata,
  getFrameExtraction,
  getReconstructionMetadata,
  Job,
  listArtifacts,
  listJobs,
  Project,
  ReconstructionMetadata,
} from '../api'
import ThreeViewer from './ThreeViewer'
import { formatViewerArtifactType, isThreeViewerArtifact, sortArtifactsForViewer } from '../viewer/viewerHelpers'

type ViewerPanelProps = {
  project: Project | null
  activeJob: Job | null
  onJobChange: (job: Job) => void
}

export default function ViewerPanel({ project, activeJob, onJobChange }: ViewerPanelProps) {
  const [artifacts, setArtifacts] = useState<Artifact[]>([])
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null)
  const [debugText, setDebugText] = useState<string | null>(null)
  const [debugFrameCloudMetadata, setDebugFrameCloudMetadata] = useState<DebugFrameCloudMetadata | null>(null)
  const [reconstructionMetadata, setReconstructionMetadata] = useState<ReconstructionMetadata | null>(null)
  const [debugPreviewParams, setDebugPreviewParams] = useState({
    max_points: 50000,
    frame_step: 1,
    arc_degrees: 55,
    plane_width: 1.35,
  })
  const [hasExtractedFrames, setHasExtractedFrames] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exportMessage, setExportMessage] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [isCreatingDebugPreview, setIsCreatingDebugPreview] = useState(false)

  useEffect(() => {
    if (!project) {
      setArtifacts([])
      setSelectedArtifactId(null)
      setHasExtractedFrames(false)
      return
    }
    refreshProjectViewerState(project.id)
  }, [project])

  useEffect(() => {
    if (!project || !activeJob) return
    if (activeJob.status === 'succeeded') {
      refreshProjectViewerState(project.id)
    }
  }, [activeJob?.status, project])

  const selectedArtifact = artifacts.find((artifact) => artifact.id === selectedArtifactId) ?? null
  const isThreeArtifact = selectedArtifact ? isThreeViewerArtifact(selectedArtifact.artifact_type) : false

  useEffect(() => {
    setDebugText(null)
    setDebugFrameCloudMetadata(null)
    setReconstructionMetadata(null)
    setError(null)
    if (!project || !selectedArtifact) return

    if (selectedArtifact.artifact_type === 'debug_report') {
      fetch(artifactUrl(selectedArtifact))
        .then((response) => {
          if (!response.ok) throw new Error('Could not load debug report')
          return response.text()
        })
        .then((text) => setDebugText(text))
        .catch((reason: Error) => setError(reason.message))
    }

    if (selectedArtifact.artifact_type === 'debug_frame_cloud_ply') {
      getDebugFrameCloudMetadata(project.id)
        .then(setDebugFrameCloudMetadata)
        .catch((reason: Error) => setError(reason.message))
    }

    if (selectedArtifact.artifact_type === 'point_cloud_ply') {
      getReconstructionMetadata(project.id)
        .then(setReconstructionMetadata)
        .catch(() => setReconstructionMetadata(null))
    }
  }, [project, selectedArtifact])

  function refreshProjectViewerState(projectId: string) {
    setError(null)
    Promise.all([listArtifacts(projectId), listJobs(projectId), getFrameExtraction(projectId).then(() => true).catch(() => false)])
      .then(([loadedArtifacts, jobs, hasFrameMetadata]) => {
        const sortedArtifacts = sortArtifactsForViewer(loadedArtifacts)
        setArtifacts(sortedArtifacts)
        setSelectedArtifactId((currentId) => {
          if (currentId && sortedArtifacts.some((artifact) => artifact.id === currentId)) return currentId
          return sortedArtifacts.find((artifact) => artifact.artifact_type === 'point_cloud_ply')?.id ??
            sortedArtifacts.find((artifact) => artifact.artifact_type === 'debug_frame_cloud_ply')?.id ??
            sortedArtifacts[0]?.id ??
            null
        })
        setHasExtractedFrames(
          hasFrameMetadata ||
          jobs.some((job) => job.job_type === 'frame_extraction' && job.status === 'succeeded') ||
            (activeJob?.job_type === 'frame_extraction' && activeJob.status === 'succeeded'),
        )
      })
      .catch((reason: Error) => setError(reason.message))
  }

  async function handleCreateDebugPreview() {
    if (!project) return
    setError(null)
    setExportMessage(null)
    setIsCreatingDebugPreview(true)
    try {
      const job = await createJob(project.id, 'debug_frame_cloud', debugPreviewParams)
      onJobChange(job)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not create debug frame planes job')
    } finally {
      setIsCreatingDebugPreview(false)
    }
  }

  async function handleExport(format: ExportFormat, allowPlaceholder = false) {
    if (!project || !selectedArtifact) return
    setError(null)
    setExportMessage(null)
    setIsExporting(true)
    try {
      const result = await createExport(project.id, selectedArtifact.id, format, allowPlaceholder)
      setExportMessage(formatExportMessage(result))
      const loadedArtifacts = sortArtifactsForViewer(await listArtifacts(project.id))
      setArtifacts(loadedArtifacts)
      const exportedArtifact = loadedArtifacts.find((artifact) => artifact.relative_path === result.export_relative_path)
      setSelectedArtifactId(exportedArtifact?.id ?? selectedArtifact.id)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Export failed')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <section style={sectionStyle}>
      <div style={headerStyle}>
        <div>
          <h2 style={headingStyle}>Viewer</h2>
          <p style={mutedStyle}>{project ? project.name : 'Select a project'}</p>
        </div>
        <div style={headerActionsStyle}>
          <button
            disabled={!project || !hasExtractedFrames || isCreatingDebugPreview}
            onClick={handleCreateDebugPreview}
            style={secondaryButtonStyle}
            type="button"
          >
            Create debug frame planes
          </button>
          <button disabled={!project} onClick={() => project && refreshProjectViewerState(project.id)} style={secondaryButtonStyle} type="button">
            Refresh
          </button>
        </div>
      </div>

      {project && !hasExtractedFrames ? <p style={mutedStyle}>Extract frames before creating debug frame planes or real point-cloud reconstruction.</p> : null}
      {project && hasExtractedFrames ? (
        <div style={previewOptionsStyle}>
          <label style={inputLabelStyle}>
            Max points
            <input
              max={50000}
              min={1}
              onChange={(event) => setDebugPreviewParams((params) => ({ ...params, max_points: Number(event.target.value) }))}
              style={numberInputStyle}
              type="number"
              value={debugPreviewParams.max_points}
            />
          </label>
          <label style={inputLabelStyle}>
            Frame step
            <input
              min={1}
              onChange={(event) => setDebugPreviewParams((params) => ({ ...params, frame_step: Number(event.target.value) }))}
              style={numberInputStyle}
              type="number"
              value={debugPreviewParams.frame_step}
            />
          </label>
          <label style={inputLabelStyle}>
            Arc
            <input
              max={180}
              min={1}
              onChange={(event) => setDebugPreviewParams((params) => ({ ...params, arc_degrees: Number(event.target.value) }))}
              style={numberInputStyle}
              type="number"
              value={debugPreviewParams.arc_degrees}
            />
          </label>
          <label style={inputLabelStyle}>
            Plane width
            <input
              max={10}
              min={0.1}
              onChange={(event) => setDebugPreviewParams((params) => ({ ...params, plane_width: Number(event.target.value) }))}
              step={0.05}
              style={numberInputStyle}
              type="number"
              value={debugPreviewParams.plane_width}
            />
          </label>
        </div>
      ) : null}
      {artifacts.length === 0 ? <p style={mutedStyle}>No result artifacts yet.</p> : null}

      {artifacts.length > 0 ? (
        <div style={layoutStyle}>
          <ul style={listStyle}>
            {artifacts.map((artifact) => (
              <li key={artifact.id}>
                <button
                  onClick={() => {
                    setSelectedArtifactId(artifact.id)
                    setExportMessage(null)
                  }}
                  style={artifact.id === selectedArtifactId ? selectedArtifactStyle : artifactButtonStyle}
                  type="button"
                >
                  <strong>{artifact.name}</strong>
                  <span>{formatViewerArtifactType(artifact.artifact_type)}</span>
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
                  <div style={exportControlsStyle}>
                    {selectedArtifact.artifact_type === 'point_cloud_ply' ||
                    selectedArtifact.artifact_type === 'predicted_point_cloud_ply' ||
                    selectedArtifact.artifact_type === 'splat_ply' ? (
                      <button disabled={isExporting} onClick={() => handleExport('ply')} style={secondaryButtonStyle} type="button">
                        Export PLY
                      </button>
                    ) : null}
                    {selectedArtifact.artifact_type === 'mesh_glb' ? (
                      <button disabled={isExporting} onClick={() => handleExport('glb')} style={secondaryButtonStyle} type="button">
                        Export GLB
                      </button>
                    ) : null}
                    {selectedArtifact.artifact_type === 'debug_report' ? (
                      <>
                        <button disabled={isExporting} onClick={() => handleExport('ply', true)} style={secondaryButtonStyle} type="button">
                          Export placeholder PLY
                        </button>
                        <button disabled={isExporting} onClick={() => handleExport('glb', true)} style={secondaryButtonStyle} type="button">
                          Export placeholder GLB
                        </button>
                      </>
                    ) : null}
                  </div>
                  {exportMessage ? <span style={successStyle}>{exportMessage}</span> : null}
                </div>

                {isThreeArtifact ? (
                  <ThreeViewer
                    artifact={selectedArtifact}
                    debugFrameCloudMetadata={debugFrameCloudMetadata}
                    reconstructionMetadata={reconstructionMetadata}
                    sourceUrl={`${artifactUrl(selectedArtifact)}?v=${encodeURIComponent(selectedArtifact.modified_at)}`}
                  />
                ) : null}
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

function formatExportMessage(result: ExportResult) {
  if (result.status === 'placeholder') {
    return `Placeholder ${result.format.toUpperCase()} export created: ${result.export_relative_path}`
  }
  return `${result.format.toUpperCase()} export created: ${result.export_relative_path}`
}

const sectionStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 8,
  padding: 20,
  maxWidth: 1120,
} satisfies CSSProperties

const headerStyle = {
  alignItems: 'start',
  display: 'flex',
  gap: 16,
  justifyContent: 'space-between',
} satisfies CSSProperties

const headerActionsStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  justifyContent: 'flex-end',
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

const previewOptionsStyle = {
  alignItems: 'end',
  display: 'flex',
  flexWrap: 'wrap',
  gap: 10,
  marginBottom: 16,
} satisfies CSSProperties

const inputLabelStyle = {
  color: '#57606a',
  display: 'grid',
  fontSize: 13,
  gap: 4,
} satisfies CSSProperties

const numberInputStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 6,
  color: '#24292f',
  maxWidth: 110,
  padding: '7px 8px',
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

const exportControlsStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  marginTop: 8,
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

const successStyle = {
  color: '#1f883d',
  fontWeight: 600,
} satisfies CSSProperties
