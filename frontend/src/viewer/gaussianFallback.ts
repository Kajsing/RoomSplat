export type GaussianPointStyle = {
  alpha: Float32Array
  size: Float32Array
}

export function gaussianPointStyleFromAttributes(
  scales: ArrayLike<number>,
  opacities: ArrayLike<number>,
  count: number,
  scaleItemSize = 3,
): GaussianPointStyle | null {
  if (count <= 0 || opacities.length < count || scales.length < count * scaleItemSize) return null

  const rawSizes = new Float32Array(count)
  for (let index = 0; index < count; index += 1) {
    const offset = index * scaleItemSize
    const maxLogScale = Math.max(scales[offset], scales[offset + 1], scales[offset + 2])
    rawSizes[index] = Number.isFinite(maxLogScale) ? Math.exp(maxLogScale) : 0
  }

  const positiveSizes = Array.from(rawSizes).filter((value) => value > 0 && Number.isFinite(value)).sort((left, right) => left - right)
  if (positiveSizes.length === 0) return null
  const medianSize = Math.max(percentile(positiveSizes, 0.5), 0.0001)
  const highSize = Math.max(percentile(positiveSizes, 0.95), medianSize)

  const size = new Float32Array(count)
  const alpha = new Float32Array(count)
  for (let index = 0; index < count; index += 1) {
    const clampedRawSize = Math.max(0.0001, Math.min(rawSizes[index], highSize))
    size[index] = clamp(Math.sqrt(clampedRawSize / medianSize), 0.45, 3.2)
    alpha[index] = clamp(sigmoid(opacities[index]) * 0.92, 0, 0.95)
  }
  return { alpha, size }
}

function sigmoid(value: number) {
  if (!Number.isFinite(value)) return 0
  return 1 / (1 + Math.exp(-value))
}

function percentile(sortedValues: number[], ratio: number) {
  if (sortedValues.length === 0) return 0
  const boundedRatio = clamp(ratio, 0, 1)
  const index = Math.min(sortedValues.length - 1, Math.max(0, Math.floor((sortedValues.length - 1) * boundedRatio)))
  return sortedValues[index]
}

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}
