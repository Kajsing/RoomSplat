import assert from 'node:assert/strict'
import { test } from 'node:test'

import { VIEWER_ORIENTATION_OPTIONS, formatViewerOrientationMode } from '../src/viewer/orientation.ts'
import { artifactPriority, formatBytes, formatViewerArtifactType, isThreeViewerArtifact, sortArtifactsForViewer } from '../src/viewer/viewerHelpers.ts'

test('formats viewer artifact labels', () => {
  assert.equal(formatViewerArtifactType('debug_frame_cloud_ply'), 'Debug frame planes')
  assert.equal(formatViewerArtifactType('point_cloud_ply'), 'Point cloud PLY')
  assert.equal(formatViewerArtifactType('predicted_point_cloud_ply'), 'Predicted point cloud PLY')
  assert.equal(formatViewerArtifactType('splat_ply'), 'Splat PLY')
  assert.equal(formatViewerArtifactType('mesh_glb'), 'GLB scene')
  assert.equal(formatViewerArtifactType('learned_geometry_bundle'), 'Geometry bundle')
  assert.equal(formatViewerArtifactType('debug_report'), 'Debug report')
})

test('identifies Three.js viewer artifact modes', () => {
  assert.equal(isThreeViewerArtifact('debug_frame_cloud_ply'), true)
  assert.equal(isThreeViewerArtifact('point_cloud_ply'), true)
  assert.equal(isThreeViewerArtifact('predicted_point_cloud_ply'), true)
  assert.equal(isThreeViewerArtifact('splat_ply'), true)
  assert.equal(isThreeViewerArtifact('mesh_glb'), true)
  assert.equal(isThreeViewerArtifact('learned_geometry_bundle'), false)
  assert.equal(isThreeViewerArtifact('debug_report'), false)
  assert.equal(isThreeViewerArtifact('unsupported'), false)
})

test('formats artifact sizes for stats panel', () => {
  assert.equal(formatBytes(512), '512 B')
  assert.equal(formatBytes(1536), '1.5 KB')
  assert.equal(formatBytes(2 * 1024 * 1024), '2.0 MB')
})

test('sorts real artifacts before debug and placeholder artifacts', () => {
  const artifacts = [
    fakeArtifact('exports/placeholder-reconstruction-spike-1234.ply', 'point_cloud_ply'),
    fakeArtifact('metadata/reconstruction_spike.json', 'debug_report'),
    fakeArtifact('metadata/geometry_bundle.json', 'learned_geometry_bundle'),
    fakeArtifact('reconstruction/debug-frame-room.ply', 'debug_frame_cloud_ply'),
    fakeArtifact('reconstruction/learned-point-cloud.ply', 'predicted_point_cloud_ply'),
    fakeArtifact('reconstruction/splat.ply', 'splat_ply'),
    fakeArtifact('reconstruction/sparse-point-cloud.ply', 'point_cloud_ply'),
  ]

  assert.deepEqual(
    sortArtifactsForViewer(artifacts).map((artifact) => artifact.relative_path),
    [
      'reconstruction/splat.ply',
      'reconstruction/sparse-point-cloud.ply',
      'reconstruction/learned-point-cloud.ply',
      'reconstruction/debug-frame-room.ply',
      'metadata/geometry_bundle.json',
      'metadata/reconstruction_spike.json',
      'exports/placeholder-reconstruction-spike-1234.ply',
    ],
  )
  assert.equal(artifactPriority(artifacts[0]), 90)
})

test('provides viewer orientation presets for imported artifacts', () => {
  assert.deepEqual(
    VIEWER_ORIENTATION_OPTIONS.map((option) => option.value),
    ['source', 'flip-x', 'flip-y', 'flip-z', 'z-up-to-y-up', 'y-up-to-z-up'],
  )
  assert.equal(formatViewerOrientationMode('source'), 'Source')
  assert.equal(formatViewerOrientationMode('flip-y'), 'Flip Y')
})

function fakeArtifact(relativePath, artifactType) {
  return {
    id: relativePath,
    project_id: 'project',
    name: relativePath.split('/').pop(),
    relative_path: relativePath,
    artifact_type: artifactType,
    viewer_supported: true,
    size_bytes: 1,
    modified_at: '2026-07-04T00:00:00+00:00',
    download_url: '/download',
    description: '',
  }
}
