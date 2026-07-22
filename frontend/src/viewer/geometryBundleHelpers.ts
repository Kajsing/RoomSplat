import type { GeometryBundleMetadata, JobType } from '../api'

export function formatGeometryBundleSummary(metadata: GeometryBundleMetadata) {
  return `${metadata.frame_count.toLocaleString()} mapped frames, ${metadata.primary_artifacts.length.toLocaleString()} primary artifacts, ${metadata.sidecars.length.toLocaleString()} sidecars`
}

export function formatGeometryCapabilities(metadata: Pick<GeometryBundleMetadata, 'capabilities'>) {
  const labels = [
    metadata.capabilities.depth ? 'depth' : null,
    metadata.capabilities.confidence ? 'confidence' : null,
    metadata.capabilities.mask ? 'mask' : null,
    metadata.capabilities.pointmap ? 'pointmap' : null,
  ].filter(Boolean)
  return labels.length > 0 ? labels.join(', ') : 'none'
}

export function isLearnedGeometryJob(jobType: JobType) {
  return (
    jobType === 'learned_geometry_preflight' ||
    jobType === 'import_learned_geometry' ||
    jobType === 'learned_runtime_preflight' ||
    jobType === 'learned_runtime_smoke'
  )
}

export function formatLearnedRuntimeStatus(result: Record<string, unknown> | null | undefined) {
  const status = typeof result?.status === 'string' ? result.status : 'pending'
  const selected = Array.isArray(result?.selected_frame_indices) ? result.selected_frame_indices.length : undefined
  const blockers = Array.isArray(result?.blockers) ? result.blockers.length : 0
  const frameText = selected === undefined ? '' : `, ${selected.toLocaleString()} selected frames`
  const blockerText = blockers > 0 ? `, ${blockers.toLocaleString()} blockers` : ''
  return `${status}${frameText}${blockerText}`
}
