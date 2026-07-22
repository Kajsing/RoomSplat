import type { Artifact, ArtifactType } from '../api'

export function formatViewerArtifactType(type: ArtifactType) {
  const labels = {
    debug_frame_cloud_ply: 'Debug frame planes',
    point_cloud_ply: 'Point cloud PLY',
    predicted_point_cloud_ply: 'Predicted point cloud PLY',
    splat_ply: 'Splat PLY',
    mesh_glb: 'GLB scene',
    learned_geometry_bundle: 'Geometry bundle',
    debug_report: 'Debug report',
    unsupported: 'Unsupported',
  }
  return labels[type]
}

export function isThreeViewerArtifact(type: ArtifactType) {
  return (
    type === 'debug_frame_cloud_ply' ||
    type === 'point_cloud_ply' ||
    type === 'predicted_point_cloud_ply' ||
    type === 'splat_ply' ||
    type === 'mesh_glb'
  )
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
  if (artifact.relative_path === 'reconstruction/splat.ply') return 0
  if (artifact.relative_path === 'reconstruction/sparse-point-cloud.ply') return 10
  const ranks: Record<ArtifactType, number> = {
    splat_ply: 20,
    predicted_point_cloud_ply: 25,
    point_cloud_ply: 30,
    mesh_glb: 40,
    debug_frame_cloud_ply: 60,
    learned_geometry_bundle: 65,
    debug_report: 70,
    unsupported: 100,
  }
  return ranks[artifact.artifact_type]
}
