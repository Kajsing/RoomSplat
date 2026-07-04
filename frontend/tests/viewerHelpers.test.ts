import assert from 'node:assert/strict'
import { test } from 'node:test'

import { formatBytes, formatViewerArtifactType, isThreeViewerArtifact } from '../src/viewer/viewerHelpers.ts'

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
