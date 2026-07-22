import assert from 'node:assert/strict'
import { test } from 'node:test'

import { VIEWER_ORIENTATION_OPTIONS, formatViewerOrientationMode } from '../src/viewer/orientation.ts'
import {
  formatGeometryBundleSummary,
  formatGeometryCapabilities,
  formatLearnedRuntimeStatus,
  isLearnedGeometryJob,
} from '../src/viewer/geometryBundleHelpers.ts'
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

test('formats learned geometry bundle helper summaries', () => {
  const metadata = fakeGeometryBundle()

  assert.equal(formatGeometryBundleSummary(metadata), '2 mapped frames, 1 primary artifacts, 3 sidecars')
  assert.equal(formatGeometryCapabilities(metadata), 'depth, confidence, pointmap')
  assert.equal(isLearnedGeometryJob('learned_geometry_preflight'), true)
  assert.equal(isLearnedGeometryJob('import_learned_geometry'), true)
  assert.equal(isLearnedGeometryJob('learned_runtime_preflight'), true)
  assert.equal(isLearnedGeometryJob('learned_runtime_smoke'), true)
  assert.equal(isLearnedGeometryJob('reconstruct_splat'), false)
  assert.equal(
    formatLearnedRuntimeStatus({ status: 'blocked_missing_checkpoint', selected_frame_indices: [0, 2, 4], blockers: ['checkpoint'] }),
    'blocked_missing_checkpoint, 3 selected frames, 1 blockers',
  )
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

function fakeGeometryBundle() {
  return {
    project_id: 'project',
    schema_version: 'roomsplat.geometry_bundle.v1',
    artifact_type: 'learned_geometry_bundle',
    mode: 'learned_geometry',
    source_adapter: 'lingbot-map-bss',
    adapter_family: 'feed_forward',
    status: 'complete',
    complete: true,
    is_reconstruction: false,
    not_reconstruction: true,
    frame_count: 2,
    frame_index_map: [
      { bundle_frame_index: 0, source_frame_index: 0, source_frame: 'frames/frame_000001.png' },
      { bundle_frame_index: 1, source_frame_index: 1, source_frame: 'frames/frame_000002.png' },
    ],
    cameras: [],
    intrinsics: [],
    trajectory: [],
    capabilities: { depth: true, confidence: true, mask: false, pointmap: true },
    primary_artifacts: [
      {
        relative_path: 'reconstruction/learned-point-cloud.ply',
        artifact_type: 'predicted_point_cloud_ply',
        role: 'primary',
        description: 'Predicted point cloud.',
      },
    ],
    sidecars: [
      { relative_path: 'metadata/learned/source/.complete.json', sidecar_type: 'metadata', required: true, description: 'Completion marker.' },
      { relative_path: 'metadata/learned/source/depth/000000.exr', sidecar_type: 'depth', required: true, description: 'Depth.' },
      { relative_path: 'metadata/learned/source/points/000000.exr', sidecar_type: 'pointmap', required: true, description: 'Pointmap.' },
    ],
    quality: { status: 'needs_review', notes: 'Inspect visually.' },
    warnings: [],
    generated_data_rules: {
      local_only: true,
      no_auto_downloads: true,
      contained_under_project: true,
      ignored_by_git: true,
      notes: 'Generated files stay local.',
    },
    generated_at: null,
  }
}
