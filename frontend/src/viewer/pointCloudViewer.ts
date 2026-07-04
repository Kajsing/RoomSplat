export type Point = {
  x: number
  y: number
  z: number
  color: string
}

export type PointCloud = {
  points: Point[]
}

export type PointCloudView = {
  rotationY: number
  zoom: number
}

const MAX_PREVIEW_POINTS = 50000

export function parseAsciiPly(source: string): PointCloud {
  const lines = source.split(/\r?\n/)
  const endHeaderIndex = lines.findIndex((line) => line.trim() === 'end_header')
  if (endHeaderIndex < 0) throw new Error('PLY header is missing end_header')

  const vertexLine = lines.slice(0, endHeaderIndex).find((line) => line.startsWith('element vertex '))
  const vertexCount = vertexLine ? Number(vertexLine.split(/\s+/)[2]) : 0
  if (!Number.isFinite(vertexCount) || vertexCount <= 0) throw new Error('PLY has no vertices')
  if (vertexCount > MAX_PREVIEW_POINTS) {
    throw new Error(`PLY preview is limited to ${MAX_PREVIEW_POINTS.toLocaleString()} vertices. Download the artifact for full inspection.`)
  }

  const points: Point[] = []
  for (const line of lines.slice(endHeaderIndex + 1, endHeaderIndex + 1 + vertexCount)) {
    const parts = line.trim().split(/\s+/).map(Number)
    if (parts.length < 3 || parts.some((value) => Number.isNaN(value))) continue
    const [x, y, z, red = 255, green = 255, blue = 255] = parts
    points.push({
      x,
      y,
      z,
      color: `rgb(${clampColor(red)}, ${clampColor(green)}, ${clampColor(blue)})`,
    })
  }

  if (points.length === 0) throw new Error('PLY did not contain readable vertices')
  return { points }
}

export function renderPointCloud(canvas: HTMLCanvasElement, pointCloud: PointCloud, view: PointCloudView) {
  const context = canvas.getContext('2d')
  if (!context) return

  const width = canvas.width
  const height = canvas.height
  context.clearRect(0, 0, width, height)
  context.fillStyle = '#0f1720'
  context.fillRect(0, 0, width, height)

  const bounds = boundsFor(pointCloud.points)
  const centerX = (bounds.minX + bounds.maxX) / 2
  const centerY = (bounds.minY + bounds.maxY) / 2
  const centerZ = (bounds.minZ + bounds.maxZ) / 2
  const span = Math.max(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY, bounds.maxZ - bounds.minZ, 1)
  const scale = (Math.min(width, height) * 0.72 * view.zoom) / span
  const angle = (view.rotationY * Math.PI) / 180
  const sin = Math.sin(angle)
  const cos = Math.cos(angle)

  const projected = pointCloud.points
    .map((point) => {
      const x = point.x - centerX
      const y = point.y - centerY
      const z = point.z - centerZ
      const rotatedX = x * cos - z * sin
      const rotatedZ = x * sin + z * cos
      return {
        x: width / 2 + rotatedX * scale,
        y: height / 2 - y * scale,
        z: rotatedZ,
        color: point.color,
      }
    })
    .sort((a, b) => a.z - b.z)

  for (const point of projected) {
    context.fillStyle = point.color
    context.fillRect(point.x - 1.5, point.y - 1.5, 3, 3)
  }
}

function boundsFor(points: Point[]) {
  return points.reduce(
    (bounds, point) => ({
      minX: Math.min(bounds.minX, point.x),
      maxX: Math.max(bounds.maxX, point.x),
      minY: Math.min(bounds.minY, point.y),
      maxY: Math.max(bounds.maxY, point.y),
      minZ: Math.min(bounds.minZ, point.z),
      maxZ: Math.max(bounds.maxZ, point.z),
    }),
    {
      minX: Number.POSITIVE_INFINITY,
      maxX: Number.NEGATIVE_INFINITY,
      minY: Number.POSITIVE_INFINITY,
      maxY: Number.NEGATIVE_INFINITY,
      minZ: Number.POSITIVE_INFINITY,
      maxZ: Number.NEGATIVE_INFINITY,
    },
  )
}

function clampColor(value: number) {
  return Math.max(0, Math.min(255, Math.round(value)))
}
