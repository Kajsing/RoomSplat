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
  return jobType === 'learned_geometry_preflight' || jobType === 'import_learned_geometry'
}
