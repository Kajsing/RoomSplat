import { useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { extractFrames, FrameExtraction, Project, uploadVideo, VideoImport } from '../api'

type UploadPanelProps = {
  project: Project | null
}

export default function UploadPanel({ project }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null)
  const [stride, setStride] = useState(1)
  const [maxFrames, setMaxFrames] = useState('')
  const [importedVideo, setImportedVideo] = useState<VideoImport | null>(null)
  const [extraction, setExtraction] = useState<FrameExtraction | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isExtracting, setIsExtracting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!project || !file) return
    setError(null)
    setIsUploading(true)
    setExtraction(null)

    try {
      const result = await uploadVideo(project.id, file)
      setImportedVideo(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  async function handleExtract() {
    if (!project || !importedVideo) return
    setError(null)
    setIsExtracting(true)

    try {
      const result = await extractFrames(project.id, {
        source_video: importedVideo.source_video,
        stride,
        max_frames: maxFrames ? Number(maxFrames) : undefined,
      })
      setExtraction(result)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Frame extraction failed')
    } finally {
      setIsExtracting(false)
    }
  }

  return (
    <section style={sectionStyle}>
      <div>
        <h2 style={headingStyle}>Video</h2>
        <p style={mutedStyle}>{project ? project.name : 'Select a project'}</p>
      </div>

      <form onSubmit={handleUpload} style={formStyle}>
        <label style={labelStyle} htmlFor="video-file">
          Source file
        </label>
        <input
          id="video-file"
          type="file"
          accept=".mp4,.mov,.avi,.mkv,.webm,.gif,video/*,image/gif"
          disabled={!project || isUploading}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          style={inputStyle}
        />
        <button disabled={!project || !file || isUploading} style={buttonStyle} type="submit">
          {isUploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>

      {importedVideo ? (
        <div style={statusStyle}>
          <strong>{importedVideo.original_filename}</strong>
          <span>{formatBytes(importedVideo.size_bytes)}</span>
          <code style={codeStyle}>{importedVideo.stored_filename}</code>
        </div>
      ) : null}

      <div style={controlsStyle}>
        <label style={labelStyle} htmlFor="stride">
          Stride
        </label>
        <input
          id="stride"
          type="number"
          min={1}
          value={stride}
          onChange={(event) => setStride(Math.max(1, Number(event.target.value) || 1))}
          style={numberInputStyle}
        />
        <label style={labelStyle} htmlFor="max-frames">
          Max frames
        </label>
        <input
          id="max-frames"
          type="number"
          min={1}
          value={maxFrames}
          onChange={(event) => setMaxFrames(event.target.value)}
          style={numberInputStyle}
        />
        <button disabled={!project || !importedVideo || isExtracting} onClick={handleExtract} style={buttonStyle} type="button">
          {isExtracting ? 'Extracting...' : 'Extract frames'}
        </button>
      </div>

      {extraction ? (
        <dl style={metadataStyle}>
          <div>
            <dt>Frames</dt>
            <dd>
              {extraction.extracted_frame_count} of {extraction.frame_count}
            </dd>
          </div>
          <div>
            <dt>Resolution</dt>
            <dd>
              {extraction.width} x {extraction.height}
            </dd>
          </div>
          <div>
            <dt>FPS</dt>
            <dd>{extraction.fps.toFixed(2)}</dd>
          </div>
        </dl>
      ) : null}

      {error ? <p style={errorStyle}>{error}</p> : null}
    </section>
  )
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
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
  gap: 10,
  marginBottom: 16,
} satisfies CSSProperties

const labelStyle = {
  fontWeight: 600,
} satisfies CSSProperties

const inputStyle = {
  maxWidth: 520,
} satisfies CSSProperties

const buttonStyle = {
  justifySelf: 'start',
  padding: '10px 14px',
  border: 0,
  borderRadius: 6,
  background: '#1f883d',
  color: '#ffffff',
  fontWeight: 700,
} satisfies CSSProperties

const statusStyle = {
  display: 'grid',
  gap: 4,
  border: '1px solid #d8dee4',
  borderRadius: 6,
  padding: 12,
  marginBottom: 16,
} satisfies CSSProperties

const codeStyle = {
  color: '#57606a',
  fontSize: 12,
  overflowWrap: 'anywhere',
} satisfies CSSProperties

const controlsStyle = {
  display: 'flex',
  alignItems: 'end',
  gap: 10,
  flexWrap: 'wrap',
  marginBottom: 16,
} satisfies CSSProperties

const numberInputStyle = {
  width: 96,
  padding: '9px 10px',
  border: '1px solid #d0d7de',
  borderRadius: 6,
} satisfies CSSProperties

const metadataStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
  gap: 12,
  margin: 0,
} satisfies CSSProperties

const errorStyle = {
  color: '#b42318',
  margin: '0 0 16px',
} satisfies CSSProperties
