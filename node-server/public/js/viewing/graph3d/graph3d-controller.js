// High-level controller for the 3D graph viewer (P0)
import { RenderEngine3D } from './render-engine.js';

export class Graph3D {
  constructor(container, config = {}) {
    if (!container) throw new Error('Graph3D: container is required');
    this.container = container;
    this.config = config || {};
    this.engine = new RenderEngine3D(container, config);
    this.data = { nodes: [], relationships: [] };
  }

  setData(data) {
    this.data = data || { nodes: [], relationships: [] };
    this._renderNodesAsPoints();
  }

  setConfig(config) {
    this.config = { ...this.config, ...config };
    // Future: apply runtime render/layout changes
  }

  animateToView(view) {
    // Future: smoothly move camera to a saved viewpoint
    if (!view) return;
    const { position, target } = view;
    if (position) this.engine.camera.position.set(position.x, position.y, position.z);
    if (target) this.engine.controls.target.set(target.x, target.y, target.z);
  }

  destroy() {
    this.engine.dispose();
  }

  // --- Internals ---
  _renderNodesAsPoints() {
    this.engine.clear();
    const nodes = this.data.nodes || [];
    const N = nodes.length;
    if (!N) return;

    // Simple initial layout: place nodes on a sphere using golden spiral
    const positions = new Float32Array(N * 3);
    const phi = Math.PI * (3 - Math.sqrt(5)); // golden angle
    const radius = Math.cbrt(Math.max(N, 1)) * 6 + 30; // grow radius sublinearly with N
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1 || 1)) * 2; // y from 1 to -1
      const r = Math.sqrt(1 - y * y);
      const theta = phi * i;
      const x = Math.cos(theta) * r;
      const z = Math.sin(theta) * r;
      positions[i * 3 + 0] = x * radius;
      positions[i * 3 + 1] = y * radius;
      positions[i * 3 + 2] = z * radius;
    }

    this.engine.addPoints(positions);
  }
}

// Convenience factory
export function initGraph3D(container, data, config) {
  const g = new Graph3D(container, config);
  if (data) g.setData(data);
  return g;
}

// Optional: attach to window for manual testing without bundler
if (typeof window !== 'undefined') {
  window.Graph3D = Graph3D;
  window.initGraph3D = initGraph3D;
}
