export type PointBounds = {
  min: { x: number; y: number; z: number }
  max: { x: number; y: number; z: number }
  pointCount: number
}

type Point = {
  x: number
  y: number
  z: number
}

export function fullPointBoundsFromFlatPositions(positions: ArrayLike<number>, itemSize = 3): PointBounds | null {
  const points = finitePointsFromFlatPositions(positions, itemSize)
  return boundsForPoints(points)
}

export function robustPointBoundsFromFlatPositions(
  positions: ArrayLike<number>,
  itemSize = 3,
  keepRatio = 0.85,
  maxSamples = 50_000,
): PointBounds | null {
  const points = finitePointsFromFlatPositions(positions, itemSize, maxSamples)
  if (points.length < 4) return boundsForPoints(points)

  const median = {
    x: medianValue(points.map((point) => point.x)),
    y: medianValue(points.map((point) => point.y)),
    z: medianValue(points.map((point) => point.z)),
  }
  const ranked = points
    .map((point) => ({
      point,
      distanceSquared:
        (point.x - median.x) * (point.x - median.x) +
        (point.y - median.y) * (point.y - median.y) +
        (point.z - median.z) * (point.z - median.z),
    }))
    .sort((left, right) => left.distanceSquared - right.distanceSquared)
  const boundedKeepRatio = Math.max(0.05, Math.min(1, keepRatio))
  const keepCount = Math.max(1, Math.floor(ranked.length * boundedKeepRatio))
  return boundsForPoints(ranked.slice(0, keepCount).map((entry) => entry.point))
}

function finitePointsFromFlatPositions(positions: ArrayLike<number>, itemSize: number, maxSamples = Number.POSITIVE_INFINITY) {
  const points: Point[] = []
  const count = Math.floor(positions.length / itemSize)
  const step = Math.max(1, Math.ceil(count / maxSamples))
  for (let index = 0; index < count; index += step) {
    const offset = index * itemSize
    const x = positions[offset]
    const y = positions[offset + 1]
    const z = positions[offset + 2]
    if (Number.isFinite(x) && Number.isFinite(y) && Number.isFinite(z)) {
      points.push({ x, y, z })
    }
  }
  return points
}

function boundsForPoints(points: Point[]): PointBounds | null {
  if (points.length === 0) return null
  const bounds: PointBounds = {
    min: { x: Number.POSITIVE_INFINITY, y: Number.POSITIVE_INFINITY, z: Number.POSITIVE_INFINITY },
    max: { x: Number.NEGATIVE_INFINITY, y: Number.NEGATIVE_INFINITY, z: Number.NEGATIVE_INFINITY },
    pointCount: points.length,
  }
  for (const point of points) {
    bounds.min.x = Math.min(bounds.min.x, point.x)
    bounds.min.y = Math.min(bounds.min.y, point.y)
    bounds.min.z = Math.min(bounds.min.z, point.z)
    bounds.max.x = Math.max(bounds.max.x, point.x)
    bounds.max.y = Math.max(bounds.max.y, point.y)
    bounds.max.z = Math.max(bounds.max.z, point.z)
  }
  return bounds
}

function medianValue(values: number[]) {
  const sorted = [...values].sort((left, right) => left - right)
  const middle = Math.floor(sorted.length / 2)
  if (sorted.length % 2 === 1) return sorted[middle]
  return (sorted[middle - 1] + sorted[middle]) / 2
}
