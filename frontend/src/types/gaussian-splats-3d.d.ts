declare module '@mkkellogg/gaussian-splats-3d' {
  import { Object3D } from 'three'

  export const SceneFormat: {
    Ply: unknown
    Splat: unknown
    KSplat: unknown
  }

  export class DropInViewer extends Object3D {
    constructor(options?: Record<string, unknown>)
    addSplatScene(path: string, options?: Record<string, unknown>): Promise<void>
    update?: () => void
    dispose?: () => void
  }
}
