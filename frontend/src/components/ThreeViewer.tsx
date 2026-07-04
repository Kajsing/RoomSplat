import { useEffect, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js'
import { PLYLoader } from 'three/addons/loaders/PLYLoader.js'
import type { Artifact, DebugFrameCloudMetadata, ReconstructionMetadata } from '../api'
import { formatBytes, formatViewerArtifactType } from '../viewer/viewerHelpers'

type ColorMode = 'vertex' | 'solid' | 'height'
type CameraPreset = 'default' | 'front' | 'side' | 'top'

type ViewerStats = {
  framePlaneCount?: number
  inputFrameCount?: number
  meshCount?: number
  pointCount?: number
  registeredFrameCount?: number
  sparsePointCount?: number
}

type LoadedArtifact = {
  object: THREE.Object3D
  splatObject?: { update?: () => void; dispose?: () => void }
  stats: ViewerStats
  status: string
  warning?: string
}

type ThreeViewerProps = {
  artifact: Artifact
  debugFrameCloudMetadata: DebugFrameCloudMetadata | null
  reconstructionMetadata: ReconstructionMetadata | null
  sourceUrl: string
}

export default function ThreeViewer({ artifact, debugFrameCloudMetadata, reconstructionMetadata, sourceUrl }: ThreeViewerProps) {
  const mountRef = useRef<HTMLDivElement | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null)
  const controlsRef = useRef<OrbitControls | null>(null)
  const artifactRootRef = useRef<THREE.Group | null>(null)
  const gridRef = useRef<THREE.GridHelper | null>(null)
  const axesRef = useRef<THREE.AxesHelper | null>(null)
  const splatObjectsRef = useRef<Array<{ update?: () => void; dispose?: () => void }>>([])
  const [pointSize, setPointSize] = useState(0.035)
  const [colorMode, setColorMode] = useState<ColorMode>('vertex')
  const [showGrid, setShowGrid] = useState(true)
  const [showAxes, setShowAxes] = useState(true)
  const [showFrameMarkers, setShowFrameMarkers] = useState(true)
  const [isLargeView, setIsLargeView] = useState(false)
  const [screenshotMessage, setScreenshotMessage] = useState<string | null>(null)
  const [status, setStatus] = useState('Loading artifact...')
  const [warning, setWarning] = useState<string | null>(null)
  const [viewerStats, setViewerStats] = useState<ViewerStats>({})

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf6f8fa)
    const camera = new THREE.PerspectiveCamera(55, 1, 0.01, 1000)
    camera.position.set(2.6, 1.8, 3.2)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setSize(mount.clientWidth, mount.clientHeight)
    mount.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.08
    controls.target.set(0, 0, 0)

    const root = new THREE.Group()
    scene.add(root)
    const grid = new THREE.GridHelper(6, 24, 0x7d8590, 0xd0d7de)
    scene.add(grid)
    const axes = new THREE.AxesHelper(1.4)
    axes.position.set(-2.6, 0.02, -2.6)
    scene.add(axes)
    scene.add(new THREE.HemisphereLight(0xffffff, 0x8c959f, 1.8))
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.2)
    keyLight.position.set(3, 4, 2)
    scene.add(keyLight)

    rendererRef.current = renderer
    cameraRef.current = camera
    controlsRef.current = controls
    artifactRootRef.current = root
    gridRef.current = grid
    axesRef.current = axes

    const resize = () => {
      const width = Math.max(1, mount.clientWidth)
      const height = Math.max(1, mount.clientHeight)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }
    resize()

    const resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(mount)
    let animationFrame = 0
    const animate = () => {
      animationFrame = window.requestAnimationFrame(animate)
      controls.update()
      for (const splatObject of splatObjectsRef.current) {
        splatObject.update?.()
      }
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      window.cancelAnimationFrame(animationFrame)
      resizeObserver.disconnect()
      controls.dispose()
      clearArtifactRoot(root)
      grid.geometry.dispose()
      axes.geometry.dispose()
      renderer.dispose()
      renderer.domElement.remove()
      rendererRef.current = null
      cameraRef.current = null
      controlsRef.current = null
      artifactRootRef.current = null
      gridRef.current = null
      axesRef.current = null
      splatObjectsRef.current = []
    }
  }, [])

  useEffect(() => {
    if (gridRef.current) gridRef.current.visible = showGrid
  }, [showGrid])

  useEffect(() => {
    if (axesRef.current) axesRef.current.visible = showAxes
  }, [showAxes])

  useEffect(() => {
    const root = artifactRootRef.current
    if (!root) return
    let cancelled = false
    setStatus('Loading artifact...')
    setWarning(null)
    setViewerStats({})
    clearArtifactRoot(root)
    splatObjectsRef.current = []

    loadArtifact(artifact, sourceUrl, pointSize, colorMode)
      .then((result) => {
        if (cancelled) {
          disposeObject(result.object)
          result.splatObject?.dispose?.()
          return
        }
        root.add(result.object)
        const framePlanes = getFramePlanes(debugFrameCloudMetadata)
        if (artifact.artifact_type === 'debug_frame_cloud_ply' && framePlanes.length > 0 && showFrameMarkers) {
          root.add(createFrameMarkers(debugFrameCloudMetadata))
        }
        if (result.splatObject) splatObjectsRef.current = [result.splatObject]
        fitCameraToObject(result.object, cameraRef.current, controlsRef.current)
        setStatus(result.status)
        setWarning(result.warning ?? null)
        setViewerStats({
          ...result.stats,
          framePlaneCount: framePlanes.length || undefined,
          inputFrameCount: reconstructionMetadata?.input_frame_count,
          registeredFrameCount: reconstructionMetadata?.registered_frame_count,
          sparsePointCount: reconstructionMetadata?.sparse_point_count,
        })
      })
      .catch((reason: Error) => {
        if (!cancelled) {
          setStatus('Artifact could not be loaded.')
          setWarning(reason.message)
        }
      })

    return () => {
      cancelled = true
    }
  }, [artifact, debugFrameCloudMetadata, reconstructionMetadata, showFrameMarkers, sourceUrl, pointSize, colorMode])

  function handleResetCamera() {
    const camera = cameraRef.current
    const controls = controlsRef.current
    if (!camera || !controls) return
    camera.position.set(2.6, 1.8, 3.2)
    controls.target.set(0, 0, 0)
    controls.update()
  }

  function handleFitToArtifact() {
    const root = artifactRootRef.current
    fitCameraToObject(root?.children[0], cameraRef.current, controlsRef.current)
  }

  function handleCameraPreset(preset: CameraPreset) {
    const root = artifactRootRef.current
    setCameraPreset(preset, root?.children[0], cameraRef.current, controlsRef.current)
  }

  function handleScreenshot() {
    const renderer = rendererRef.current
    if (!renderer) return
    const link = document.createElement('a')
    link.download = `${artifact.name.replace(/\.[^.]+$/, '')}-viewer.png`
    link.href = renderer.domElement.toDataURL('image/png')
    link.click()
    setScreenshotMessage(`Screenshot generated: ${link.download}`)
  }

  return (
    <div style={isLargeView ? largeContainerStyle : containerStyle}>
      <div style={toolbarStyle}>
        <button onClick={() => setIsLargeView((current) => !current)} style={buttonStyle} type="button" title="Toggle large viewer">
          {isLargeView ? 'Close large view' : 'Large view'}
        </button>
        <button onClick={handleResetCamera} style={buttonStyle} type="button" title="Reset camera">
          Reset camera
        </button>
        <button onClick={handleFitToArtifact} style={buttonStyle} type="button" title="Fit camera to artifact">
          Fit
        </button>
        <button onClick={() => handleCameraPreset('default')} style={buttonStyle} type="button" title="Default orbit camera">
          Default
        </button>
        <button onClick={() => handleCameraPreset('front')} style={buttonStyle} type="button" title="Front camera">
          Front
        </button>
        <button onClick={() => handleCameraPreset('side')} style={buttonStyle} type="button" title="Side camera">
          Side
        </button>
        <button onClick={() => handleCameraPreset('top')} style={buttonStyle} type="button" title="Top camera">
          Top
        </button>
        <button onClick={handleScreenshot} style={buttonStyle} type="button" title="Save viewer screenshot">
          Screenshot
        </button>
        <label style={controlLabelStyle}>
          Point size
          <button onClick={() => setPointSize((current) => Math.max(0.005, current - 0.005))} style={smallButtonStyle} type="button">
            -
          </button>
          <input
            max={0.12}
            min={0.005}
            onChange={(event) => setPointSize(Number(event.target.value))}
            step={0.005}
            style={rangeStyle}
            type="range"
            value={pointSize}
          />
          <button onClick={() => setPointSize((current) => Math.min(0.12, current + 0.005))} style={smallButtonStyle} type="button">
            +
          </button>
        </label>
        <label style={controlLabelStyle}>
          Color
          <select onChange={(event) => setColorMode(event.target.value as ColorMode)} style={selectStyle} value={colorMode}>
            <option value="vertex">Vertex RGB</option>
            <option value="height">Height</option>
            <option value="solid">Solid</option>
          </select>
        </label>
        <label style={checkLabelStyle}>
          <input checked={showGrid} onChange={(event) => setShowGrid(event.target.checked)} type="checkbox" />
          Grid
        </label>
        <label style={checkLabelStyle}>
          <input checked={showAxes} onChange={(event) => setShowAxes(event.target.checked)} type="checkbox" />
          Axes
        </label>
        {artifact.artifact_type === 'debug_frame_cloud_ply' && getFramePlanes(debugFrameCloudMetadata).length > 0 ? (
          <label style={checkLabelStyle}>
            <input checked={showFrameMarkers} onChange={(event) => setShowFrameMarkers(event.target.checked)} type="checkbox" />
            Frame markers
          </label>
        ) : null}
      </div>
      <div ref={mountRef} style={isLargeView ? largeCanvasHostStyle : canvasHostStyle} />
      <div style={statsStyle}>
        <span>Type: {formatViewerArtifactType(artifact.artifact_type)}</span>
        <span>Size: {formatBytes(artifact.size_bytes)}</span>
        {viewerStats.pointCount !== undefined ? <span>Points: {viewerStats.pointCount.toLocaleString()}</span> : null}
        {viewerStats.inputFrameCount !== undefined ? <span>Input frames: {viewerStats.inputFrameCount.toLocaleString()}</span> : null}
        {viewerStats.registeredFrameCount !== undefined ? (
          <span>Registered frames: {viewerStats.registeredFrameCount.toLocaleString()}</span>
        ) : null}
        {viewerStats.sparsePointCount !== undefined ? <span>Sparse points: {viewerStats.sparsePointCount.toLocaleString()}</span> : null}
        {viewerStats.meshCount !== undefined ? <span>Meshes: {viewerStats.meshCount.toLocaleString()}</span> : null}
        {viewerStats.framePlaneCount !== undefined ? <span>Frame planes: {viewerStats.framePlaneCount.toLocaleString()}</span> : null}
        {debugFrameCloudMetadata?.params ? (
          <span>
            Params: {debugFrameCloudMetadata.params.max_points.toLocaleString()} pts, step {debugFrameCloudMetadata.params.frame_step},{' '}
            {debugFrameCloudMetadata.params.arc_degrees} deg, width {debugFrameCloudMetadata.params.plane_width}
          </span>
        ) : null}
      </div>
      <div style={statusStyle}>
        <strong>{formatViewerArtifactType(artifact.artifact_type)}</strong>
        <span>{status}</span>
      </div>
      {warning ? <p style={warningStyle}>{warning}</p> : null}
      {debugFrameCloudMetadata?.not_reconstruction ? (
        <p style={warningStyle}>Debug frame planes are flat video frames placed in 3D for inspection only. This is not reconstruction.</p>
      ) : null}
      {artifact.artifact_type === 'point_cloud_ply' && reconstructionMetadata?.is_reconstruction ? (
        <p style={realOutputStyle}>Real sparse point-cloud reconstruction from COLMAP. This is conventional point geometry, not Gaussian splat data.</p>
      ) : null}
      {artifact.artifact_type === 'point_cloud_ply' && reconstructionMetadata?.quality?.warning ? (
        <p style={warningStyle}>{reconstructionMetadata.quality.warning}</p>
      ) : null}
      {screenshotMessage ? <p style={successStyle}>{screenshotMessage}</p> : null}
    </div>
  )
}

async function loadArtifact(artifact: Artifact, sourceUrl: string, pointSize: number, colorMode: ColorMode): Promise<LoadedArtifact> {
  if (artifact.artifact_type === 'mesh_glb') {
    return loadGlb(sourceUrl)
  }
  if (artifact.artifact_type === 'splat_ply') {
    try {
      return await loadSplat(sourceUrl)
    } catch (reason) {
      const fallback = await loadPlyPoints(sourceUrl, pointSize, colorMode)
      return {
        ...fallback,
        status: 'Splat loader could not read this file; displayed as point cloud fallback.',
        warning: `GaussianSplats3D rejected this PLY (${reason instanceof Error ? reason.message : 'unknown reason'}). Displayed as a point cloud fallback; the file may be conventional PLY or missing Gaussian splat attributes.`,
      }
    }
  }
  if (artifact.artifact_type === 'debug_frame_cloud_ply' || artifact.artifact_type === 'point_cloud_ply') {
    const result = await loadPlyPoints(sourceUrl, pointSize, colorMode)
    if (artifact.artifact_type === 'debug_frame_cloud_ply') {
      return {
        ...result,
        status: 'Debug frame planes loaded for viewer inspection.',
        warning: 'Debug frame planes are sampled from extracted frames and are not reconstruction.',
      }
    }
    return result
  }
  throw new Error('This artifact type is not a 3D viewer artifact.')
}

async function loadSplat(sourceUrl: string): Promise<LoadedArtifact> {
  const GaussianSplats3D = await import('@mkkellogg/gaussian-splats-3d')
  const splatObject = new GaussianSplats3D.DropInViewer({ gpuAcceleratedSort: false })
  await splatObject.addSplatScene(sourceUrl, {
    format: GaussianSplats3D.SceneFormat.Ply,
    progressiveLoad: false,
    showLoadingUI: false,
    splatAlphaRemovalThreshold: 5,
  })
  return {
    object: splatObject as THREE.Object3D,
    splatObject,
    stats: {},
    status: 'Gaussian splat PLY loaded with splat renderer.',
  }
}

async function loadPlyPoints(sourceUrl: string, pointSize: number, colorMode: ColorMode): Promise<LoadedArtifact> {
  const geometry = await new PLYLoader().loadAsync(sourceUrl)
  geometry.computeBoundingBox()
  const positions = geometry.getAttribute('position')
  if (!positions || positions.count === 0) {
    throw new Error('PLY artifact has no vertex positions to display.')
  }
  applyColorMode(geometry, colorMode)
  const hasVertexColor = colorMode !== 'solid' && Boolean(geometry.getAttribute('color'))
  const material = new THREE.PointsMaterial({
    color: colorMode === 'solid' ? 0x0969da : 0xffffff,
    size: pointSize,
    sizeAttenuation: true,
    vertexColors: hasVertexColor,
  })
  const object = new THREE.Points(geometry, material)
  return {
    object,
    stats: { pointCount: positions.count },
    status: `Point cloud loaded with ${positions.count} points.`,
  }
}

async function loadGlb(sourceUrl: string): Promise<LoadedArtifact> {
  const gltf = await new GLTFLoader().loadAsync(sourceUrl)
  const object = gltf.scene ?? new THREE.Group()
  let meshCount = 0
  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.castShadow = true
      child.receiveShadow = true
      meshCount += 1
    }
  })
  return {
    object,
    stats: { meshCount },
    status: meshCount > 0 ? 'GLB scene loaded.' : 'GLB loaded, but it did not contain visible mesh nodes.',
    warning: meshCount > 0 ? undefined : 'This GLB has no visible mesh nodes.',
  }
}

function applyColorMode(geometry: THREE.BufferGeometry, colorMode: ColorMode) {
  if (colorMode !== 'height') return
  const positions = geometry.getAttribute('position')
  if (!positions) return
  const colors = new Float32Array(positions.count * 3)
  const box = geometry.boundingBox ?? new THREE.Box3().setFromBufferAttribute(positions as THREE.BufferAttribute)
  const minY = box.min.y
  const rangeY = Math.max(0.0001, box.max.y - box.min.y)
  for (let index = 0; index < positions.count; index += 1) {
    const t = (positions.getY(index) - minY) / rangeY
    colors[index * 3] = 0.1 + t * 0.9
    colors[index * 3 + 1] = 0.35 + (1 - Math.abs(t - 0.5) * 2) * 0.5
    colors[index * 3 + 2] = 0.9 - t * 0.65
  }
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
}

function fitCameraToObject(object: THREE.Object3D | undefined, camera: THREE.PerspectiveCamera | null, controls: OrbitControls | null) {
  if (!object || !camera || !controls) return
  const box = new THREE.Box3().setFromObject(object)
  if (box.isEmpty()) return
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxSize = Math.max(size.x, size.y, size.z, 0.5)
  const fitDistance = maxSize / (2 * Math.tan((camera.fov * Math.PI) / 360))
  camera.position.copy(center).add(new THREE.Vector3(fitDistance * 0.85, fitDistance * 0.55, fitDistance * 1.25))
  camera.near = Math.max(0.001, fitDistance / 100)
  camera.far = Math.max(100, fitDistance * 100)
  camera.updateProjectionMatrix()
  controls.target.copy(center)
  controls.update()
}

function setCameraPreset(
  preset: CameraPreset,
  object: THREE.Object3D | undefined,
  camera: THREE.PerspectiveCamera | null,
  controls: OrbitControls | null,
) {
  if (!camera || !controls) return
  const box = object ? new THREE.Box3().setFromObject(object) : new THREE.Box3()
  const center = box.isEmpty() ? new THREE.Vector3(0, 0, 0) : box.getCenter(new THREE.Vector3())
  const size = box.isEmpty() ? new THREE.Vector3(2, 2, 2) : box.getSize(new THREE.Vector3())
  const distance = Math.max(size.x, size.y, size.z, 1) * 1.8
  const offsets: Record<CameraPreset, THREE.Vector3> = {
    default: new THREE.Vector3(distance * 0.85, distance * 0.55, distance * 1.25),
    front: new THREE.Vector3(0, 0, distance),
    side: new THREE.Vector3(distance, distance * 0.2, 0),
    top: new THREE.Vector3(0, distance, 0.001),
  }
  camera.position.copy(center).add(offsets[preset])
  camera.lookAt(center)
  controls.target.copy(center)
  controls.update()
}

function createFrameMarkers(metadata: DebugFrameCloudMetadata) {
  const group = new THREE.Group()
  group.name = 'debug-frame-markers'
  const geometry = new THREE.SphereGeometry(0.035, 12, 12)
  const material = new THREE.MeshBasicMaterial({ color: 0xd1242f })
  for (const plane of getFramePlanes(metadata)) {
    const marker = new THREE.Mesh(geometry, material)
    marker.position.set(plane.position.x, plane.position.y, plane.position.z)
    marker.name = `Frame ${plane.frame_index + 1}: ${plane.source_frame}`
    group.add(marker)
  }
  return group
}

function getFramePlanes(metadata: DebugFrameCloudMetadata | null) {
  return Array.isArray(metadata?.frame_planes) ? metadata.frame_planes : []
}

function clearArtifactRoot(root: THREE.Group) {
  for (const child of [...root.children]) {
    root.remove(child)
    disposeObject(child)
  }
}

function disposeObject(object: THREE.Object3D) {
  object.traverse((child) => {
    const disposable = child as THREE.Object3D & { geometry?: THREE.BufferGeometry; material?: THREE.Material | THREE.Material[] }
    disposable.geometry?.dispose()
    if (Array.isArray(disposable.material)) {
      disposable.material.forEach((material) => material.dispose())
    } else {
      disposable.material?.dispose()
    }
    if (child !== object) {
      ;(child as { dispose?: () => void }).dispose?.()
    }
  })
}

const containerStyle = {
  display: 'grid',
  gap: 10,
} satisfies CSSProperties

const largeContainerStyle = {
  ...containerStyle,
  background: '#ffffff',
  inset: 16,
  overflow: 'auto',
  padding: 16,
  position: 'fixed',
  zIndex: 20,
} satisfies CSSProperties

const toolbarStyle = {
  alignItems: 'center',
  display: 'flex',
  flexWrap: 'wrap',
  gap: 10,
} satisfies CSSProperties

const buttonStyle = {
  background: '#ffffff',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  color: '#24292f',
  fontWeight: 700,
  padding: '8px 10px',
} satisfies CSSProperties

const smallButtonStyle = {
  ...buttonStyle,
  minWidth: 30,
  padding: '6px 8px',
} satisfies CSSProperties

const controlLabelStyle = {
  alignItems: 'center',
  color: '#24292f',
  display: 'flex',
  gap: 8,
  fontSize: 14,
} satisfies CSSProperties

const checkLabelStyle = {
  ...controlLabelStyle,
  gap: 5,
} satisfies CSSProperties

const rangeStyle = {
  width: 116,
} satisfies CSSProperties

const selectStyle = {
  border: '1px solid #d0d7de',
  borderRadius: 6,
  padding: '6px 8px',
} satisfies CSSProperties

const canvasHostStyle = {
  aspectRatio: '16 / 9',
  border: '1px solid #d0d7de',
  borderRadius: 6,
  minHeight: 320,
  overflow: 'hidden',
  width: '100%',
} satisfies CSSProperties

const largeCanvasHostStyle = {
  ...canvasHostStyle,
  minHeight: 'calc(100vh - 220px)',
} satisfies CSSProperties

const statsStyle = {
  color: '#57606a',
  display: 'flex',
  flexWrap: 'wrap',
  fontSize: 13,
  gap: 10,
} satisfies CSSProperties

const statusStyle = {
  alignItems: 'center',
  color: '#57606a',
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  fontSize: 14,
} satisfies CSSProperties

const warningStyle = {
  background: '#fff8c5',
  border: '1px solid #d4a72c',
  borderRadius: 6,
  color: '#5d4411',
  margin: 0,
  padding: 10,
} satisfies CSSProperties

const successStyle = {
  color: '#1f883d',
  fontWeight: 600,
  margin: 0,
} satisfies CSSProperties

const realOutputStyle = {
  background: '#dafbe1',
  border: '1px solid #1f883d',
  borderRadius: 6,
  color: '#116329',
  margin: 0,
  padding: 10,
} satisfies CSSProperties
