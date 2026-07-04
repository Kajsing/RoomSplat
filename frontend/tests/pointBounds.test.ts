import assert from 'node:assert/strict'
import { test } from 'node:test'

import { fullPointBoundsFromFlatPositions, robustPointBoundsFromFlatPositions } from '../src/viewer/pointBounds.ts'

test('full point bounds include every finite position', () => {
  const bounds = fullPointBoundsFromFlatPositions([0, 1, 2, -2, 4, 6, Number.NaN, 99, 99, 3, -1, 5])

  assert.deepEqual(bounds?.min, { x: -2, y: -1, z: 2 })
  assert.deepEqual(bounds?.max, { x: 3, y: 4, z: 6 })
  assert.equal(bounds?.pointCount, 3)
})

test('robust point bounds ignore distant outliers around the median cluster', () => {
  const clusteredPositions = [
    -1, -1, 0,
    -0.5, 0, 0.25,
    0, 0.5, -0.25,
    0.5, 0, 0.2,
    1, 1, 0,
    60, 70, 80,
  ]
  const full = fullPointBoundsFromFlatPositions(clusteredPositions)
  const robust = robustPointBoundsFromFlatPositions(clusteredPositions, 3, 0.84)

  assert.equal(full?.max.x, 60)
  assert.deepEqual(robust?.min, { x: -1, y: -1, z: -0.25 })
  assert.deepEqual(robust?.max, { x: 1, y: 1, z: 0.25 })
})

test('robust point bounds sample large arrays deterministically', () => {
  const positions: number[] = []
  for (let index = 0; index < 100; index += 1) {
    positions.push(index, index * 0.5, 0)
  }

  const bounds = robustPointBoundsFromFlatPositions(positions, 3, 1, 10)

  assert.equal(bounds?.pointCount, 10)
  assert.deepEqual(bounds?.min, { x: 0, y: 0, z: 0 })
  assert.deepEqual(bounds?.max, { x: 90, y: 45, z: 0 })
})
