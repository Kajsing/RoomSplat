import type { ArtifactType } from '../api'

export function formatViewerArtifactType(type: ArtifactType) {
  const labels = {
    debug_frame_cloud_ply: 'Frame Room Cloud',
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
