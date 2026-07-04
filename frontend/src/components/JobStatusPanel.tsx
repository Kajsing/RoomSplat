import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { createJob, getJob, Job, listJobs, Project } from '../api'

type ReconstructionPreset = 'quick' | 'balanced' | 'detail'
type ReconstructionMatcher = 'exhaustive' | 'sequential'

type JobStatusPanelProps = {
  project: Project | null
  activeJob: Job | null
  onJobChange: (job: Job | null) => void
}

export default function JobStatusPanel({ project, activeJob, onJobChange }: JobStatusPanelProps) {
  const [jobs, setJobs] = useState<Job[]>([])
  const [preset, setPreset] = useState<ReconstructionPreset>('balanced')
  const [matcher, setMatcher] = useState<ReconstructionMatcher>('exhaustive')
  const [useGpu, setUseGpu] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!project) {
      setJobs([])
      return
    }
    listJobs(project.id).then(setJobs).catch((reason: Error) => setError(reason.message))
  }, [project])

  useEffect(() => {
    if (!project || !activeJob || !['queued', 'running'].includes(activeJob.status)) return

    const intervalId = window.setInterval(() => {
      getJob(project.id, activeJob.id)
        .then((job) => {
          onJobChange(job)
          setJobs((currentJobs) => upsertJob(currentJobs, job))
        })
        .catch((reason: Error) => setError(reason.message))
    }, 750)

    return () => window.clearInterval(intervalId)
  }, [activeJob, onJobChange, project])

  async function handleReconstructionSpike() {
    if (!project) return
    setError(null)
    setIsStarting(true)
    try {
      const job = await createJob(project.id, 'reconstruction_spike', {})
      onJobChange(job)
      setJobs((currentJobs) => upsertJob(currentJobs, job))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not start reconstruction spike')
    } finally {
      setIsStarting(false)
    }
  }

  async function handlePointCloudReconstruction() {
    if (!project) return
    setError(null)
    setIsStarting(true)
    try {
      const job = await createJob(project.id, 'reconstruct_point_cloud', { preset, matcher, use_gpu: useGpu })
      onJobChange(job)
      setJobs((currentJobs) => upsertJob(currentJobs, job))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not start point cloud reconstruction')
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <section style={sectionStyle}>
      <div>
        <h2 style={headingStyle}>Jobs</h2>
        <p style={mutedStyle}>{project ? project.name : 'Select a project'}</p>
      </div>

      <div style={buttonRowStyle}>
        <button disabled={!project || isStarting} onClick={handlePointCloudReconstruction} style={buttonStyle} type="button">
          {isStarting ? 'Starting...' : 'Run point cloud reconstruction'}
        </button>
        <button disabled={!project || isStarting} onClick={handleReconstructionSpike} style={secondaryButtonStyle} type="button">
          Run reconstruction spike
        </button>
      </div>

      <div style={optionsStyle}>
        <label style={inputLabelStyle}>
          Preset
          <select onChange={(event) => setPreset(event.target.value as ReconstructionPreset)} style={selectStyle} value={preset}>
            <option value="quick">Quick</option>
            <option value="balanced">Balanced</option>
            <option value="detail">Detail</option>
          </select>
        </label>
        <label style={inputLabelStyle}>
          Matcher
          <select onChange={(event) => setMatcher(event.target.value as ReconstructionMatcher)} style={selectStyle} value={matcher}>
            <option value="exhaustive">Exhaustive</option>
            <option value="sequential">Sequential</option>
          </select>
        </label>
        <label style={checkLabelStyle}>
          <input checked={useGpu} onChange={(event) => setUseGpu(event.target.checked)} type="checkbox" />
          GPU
        </label>
        <span style={hintStyle}>{presetHint(preset)}</span>
      </div>

      {activeJob ? (
        <div style={activeJobStyle}>
          <strong>{formatJobType(activeJob.job_type)}</strong>
          <span>{activeJob.status}</span>
          {activeJob.error ? <span style={errorStyle}>{activeJob.error}</span> : null}
          {activeJob.result ? <code style={codeStyle}>{summarizeResult(activeJob)}</code> : null}
        </div>
      ) : null}

      {jobs.length > 0 ? (
        <ul style={listStyle}>
          {jobs.slice(0, 5).map((job) => (
            <li key={job.id} style={itemStyle}>
              <strong>{formatJobType(job.job_type)}</strong>
              <span>{job.status}</span>
              <code style={codeStyle}>{job.id}</code>
            </li>
          ))}
        </ul>
      ) : (
        <p style={mutedStyle}>No jobs yet.</p>
      )}

      {error ? <p style={errorStyle}>{error}</p> : null}
    </section>
  )
}

function upsertJob(jobs: Job[], job: Job) {
  const rest = jobs.filter((candidate) => candidate.id !== job.id)
  return [job, ...rest]
}

function formatJobType(jobType: Job['job_type']) {
  const labels = {
    frame_extraction: 'Frame extraction',
    reconstruction_spike: 'Reconstruction spike',
    debug_frame_cloud: 'Debug 3D preview',
    reconstruct_point_cloud: 'Point cloud reconstruction',
  }
  return labels[jobType]
}

function summarizeResult(job: Job) {
  if (job.job_type === 'frame_extraction') {
    return `${job.result?.extracted_frame_count ?? '?'} frames`
  }
  if (job.job_type === 'debug_frame_cloud') {
    return `${job.result?.sampled_points ?? '?'} debug points`
  }
  if (job.job_type === 'reconstruct_point_cloud') {
    const preset = typeof job.result?.params === 'object' && job.result.params ? (job.result.params as Record<string, unknown>).preset : undefined
    return `${job.result?.ply_point_count ?? '?'} points, ${job.result?.registered_frame_count ?? '?'} registered frames${
      preset ? `, ${preset} preset` : ''
    }`
  }
  return String(job.result?.status ?? 'report ready')
}

function presetHint(preset: ReconstructionPreset) {
  const hints = {
    quick: 'Recommended extraction: stride 3, max 24 frames.',
    balanced: 'Recommended extraction: stride 2, max 60 frames.',
    detail: 'Recommended extraction: stride 1, max 120 frames.',
  }
  return hints[preset]
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

const buttonStyle = {
  padding: '10px 14px',
  border: 0,
  borderRadius: 6,
  background: '#1f883d',
  color: '#ffffff',
  fontWeight: 700,
  marginBottom: 16,
} satisfies CSSProperties

const secondaryButtonStyle = {
  ...buttonStyle,
  background: '#ffffff',
  border: '1px solid #d0d7de',
  color: '#24292f',
} satisfies CSSProperties

const buttonRowStyle = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  marginBottom: 8,
} satisfies CSSProperties

const optionsStyle = {
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

const selectStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 6,
  color: '#24292f',
  padding: '7px 8px',
} satisfies CSSProperties

const checkLabelStyle = {
  alignItems: 'center',
  color: '#57606a',
  display: 'flex',
  fontSize: 13,
  gap: 6,
  minHeight: 34,
} satisfies CSSProperties

const hintStyle = {
  color: '#57606a',
  fontSize: 13,
  minHeight: 34,
  paddingTop: 9,
} satisfies CSSProperties

const activeJobStyle = {
  display: 'grid',
  gap: 4,
  border: '1px solid #d8dee4',
  borderRadius: 6,
  padding: 12,
  marginBottom: 16,
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

const codeStyle = {
  color: '#57606a',
  fontSize: 12,
  overflowWrap: 'anywhere',
} satisfies CSSProperties

const errorStyle = {
  color: '#b42318',
  margin: '12px 0 0',
} satisfies CSSProperties
