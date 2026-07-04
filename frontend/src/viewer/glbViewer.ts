export type GlbInfo = {
  version: number
  length: number
}

export function parseGlbInfo(buffer: ArrayBuffer): GlbInfo {
  const view = new DataView(buffer)
  if (buffer.byteLength < 12) throw new Error('GLB header is too short')
  const magic = view.getUint32(0, true)
  if (magic !== 0x46546c67) throw new Error('File is not a GLB binary')
  return {
    version: view.getUint32(4, true),
    length: view.getUint32(8, true),
  }
}

export function glbPreviewMessage(info: GlbInfo) {
  return `GLB loaded: version ${info.version}, ${info.length} bytes. Full mesh rendering is deferred until Three.js GLB viewer support is added.`
}
