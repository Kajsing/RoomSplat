export type ViewerOrientationMode = 'source' | 'flip-x' | 'flip-y' | 'flip-z' | 'z-up-to-y-up' | 'y-up-to-z-up'

export type ViewerOrientationOption = {
  value: ViewerOrientationMode
  label: string
}

export const VIEWER_ORIENTATION_OPTIONS: ViewerOrientationOption[] = [
  { value: 'source', label: 'Source' },
  { value: 'flip-x', label: 'Flip X' },
  { value: 'flip-y', label: 'Flip Y' },
  { value: 'flip-z', label: 'Flip Z' },
  { value: 'z-up-to-y-up', label: 'Z-up to Y-up' },
  { value: 'y-up-to-z-up', label: 'Y-up to Z-up' },
]

export function formatViewerOrientationMode(value: ViewerOrientationMode) {
  return VIEWER_ORIENTATION_OPTIONS.find((option) => option.value === value)?.label ?? 'Source'
}
