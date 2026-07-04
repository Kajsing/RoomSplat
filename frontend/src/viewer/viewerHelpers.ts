import type { Artifact, ArtifactType } from '../api'

export function formatViewerArtifactType(type: ArtifactType) {
  const labels = {
    debug_frame_cloud_ply: 'Debug frame planes',
    point_cloud_ply: 'Point cloud PLY',
    splat_ply: 'Splat PLY',
    mesh_glb: 'GLB scene',
    debug_report: 'Debug report',
    unsupported: 'Unsupported',
  }
  return labels[type]
}

export function isThreeViewerArtifact(type: ArtifactType) {
  return type === 'debug_frame_cloud_ply' || type === 'point_cloud_ply' || type === 'splat_ply' || type === 'mesh_glb'
}

export function formatBytes(sizeBytes: number) {
  if (sizeBytes < 1024) return `${sizeBytes} B`
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
}

export function sortArtifactsForViewer(artifacts: Artifact[]) {
  return [...artifacts].sort((left, right) => artifactPriority(left) - artifactPriority(right) || left.relative_path.localeCompare(right.relative_path))
}

export function artifactPriority(artifact: Pick<Artifact, 'artifact_type' | 'relative_path'>) {
  const name = artifact.relative_path.split('/').pop()?.toLowerCase() ?? ''
  const isPlaceholder = artifact.relative_path.startsWith('exports/') && name.startsWith('placeholder-')
  if (isPlaceholder) return 90
  if (artifact.relative_path === 'reconstruction/sparse-point-cloud.ply') return 0
  const ranks: Record<ArtifactType, number> = {
    point_cloud_ply: 10,
    splat_ply: 20,
    mesh_glb: 30,
    debug_frame_cloud_ply: 60,
    debug_report: 70,
    unsupported: 100,
  }
  return ranks[artifact.artifact_type]
}
