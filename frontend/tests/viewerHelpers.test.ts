import assert from 'node:assert/strict'
import { test } from 'node:test'

import { artifactPriority, formatBytes, formatViewerArtifactType, isThreeViewerArtifact, sortArtifactsForViewer } from '../src/viewer/viewerHelpers.ts'

test('formats viewer artifact labels', () => {
  assert.equal(formatViewerArtifactType('debug_frame_cloud_ply'), 'Debug frame planes')
  assert.equal(formatViewerArtifactType('point_cloud_ply'), 'Point cloud PLY')
  assert.equal(formatViewerArtifactType('splat_ply'), 'Splat PLY')
  assert.equal(formatViewerArtifactType('mesh_glb'), 'GLB scene')
  assert.equal(formatViewerArtifactType('debug_report'), 'Debug report')
})

test('identifies Three.js viewer artifact modes', () => {
  assert.equal(isThreeViewerArtifact('debug_frame_cloud_ply'), true)
  assert.equal(isThreeViewerArtifact('point_cloud_ply'), true)
  assert.equal(isThreeViewerArtifact('splat_ply'), true)
  assert.equal(isThreeViewerArtifact('mesh_glb'), true)
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
    fakeArtifact('reconstruction/debug-frame-room.ply', 'debug_frame_cloud_ply'),
    fakeArtifact('reconstruction/splat.ply', 'splat_ply'),
    fakeArtifact('reconstruction/sparse-point-cloud.ply', 'point_cloud_ply'),
  ]

  assert.deepEqual(
    sortArtifactsForViewer(artifacts).map((artifact) => artifact.relative_path),
    [
      'reconstruction/splat.ply',
      'reconstruction/sparse-point-cloud.ply',
      'reconstruction/debug-frame-room.ply',
      'metadata/reconstruction_spike.json',
      'exports/placeholder-reconstruction-spike-1234.ply',
    ],
  )
  assert.equal(artifactPriority(artifacts[0]), 90)
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
