import assert from 'node:assert/strict'
import { test } from 'node:test'

import { gaussianPointStyleFromAttributes } from '../src/viewer/gaussianFallback.ts'

test('creates bounded point sprite style from Gaussian scale and opacity attributes', () => {
  const style = gaussianPointStyleFromAttributes(
    [
      Math.log(0.01), Math.log(0.02), Math.log(0.03),
      Math.log(0.02), Math.log(0.03), Math.log(0.04),
      Math.log(10), Math.log(20), Math.log(30),
    ],
    [-4, 0, 8],
    3,
  )

  assert.ok(style)
  assert.equal(style.size.length, 3)
  assert.equal(style.alpha.length, 3)
  assert.ok(style.size[0] >= 0.45)
  assert.ok(style.size[2] <= 3.2)
  assert.ok(style.alpha[0] < 0.03)
  assert.ok(style.alpha[2] <= 0.95)
})

test('returns null when Gaussian attributes do not match point count', () => {
  assert.equal(gaussianPointStyleFromAttributes([1, 2, 3], [1], 2), null)
})
