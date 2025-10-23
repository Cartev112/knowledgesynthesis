// High-level controller for the 3D graph viewer (P0)
import * as THREE from 'https://esm.sh/three@0.160.0';
import { Text } from 'https://esm.sh/troika-three-text@0.49.0?deps=three@0.160.0';
import { RenderEngine3D } from './render-engine.js';
import { state } from '../../state.js';

export class Graph3D {
  constructor(container, config = {}) {
    if (!container) throw new Error('Graph3D: container is required');
    this.container = container;
    this.config = config || {};
    this.engine = new RenderEngine3D(container, config);
    this.data = { nodes: [], relationships: [] };
    this.nodeIndexById = new Map();
    this.positions = null;
    this.colors = null;
    this.pointsMesh = null;
    this.edgesLine = null;
    this.hoverIndex = -1;
    this.selected = new Set();
    this.raycaster = new THREE.Raycaster();
    this.raycaster.params.Points = { threshold: 6 };
    this.mouseNDC = new THREE.Vector2();
    this._interactionsSetup = false;
    this.labelMeshes = new Map();
    this._frameCount = 0;
    this._rafId = null;
    this._fogEnabled = !!(config.render && config.render.fogEnabled);
    this.layoutWorker = null;
    this.forceLayoutRunning = false;
    if (this.engine && typeof this.engine.setOnFrame === 'function') {
      this.engine.setOnFrame(() => this._onFrame());
    } else {
      const tick = () => {
        this._onFrame();
        this._rafId = requestAnimationFrame(tick);
      };
      this._rafId = requestAnimationFrame(tick);
    }
  }

  setData(data) {
    this.data = data || { nodes: [], relationships: [] };
    this._renderNodesAsPoints();
    this._renderEdges();
    this._setupInteractions();
  }

  setConfig(config) {
    this.config = { ...this.config, ...config };
    // Future: apply runtime render/layout changes
  }

  applySelection(ids) {
    const baseColor = new THREE.Color(0x9aa6ff);
    const selectColor = new THREE.Color(0x10b981);
    this.selected.clear();
    if (Array.isArray(ids)) {
      for (const id of ids) {
        const idx = this.nodeIndexById.get(id);
        if (idx != null) this.selected.add(idx);
      }
    }
    if (this.colors && this.pointsMesh) {
      const N = this.colors.length / 3;
      for (let i = 0; i < N; i++) {
        const col = this.selected.has(i) ? selectColor : baseColor;
        this.colors[i * 3 + 0] = col.r;
        this.colors[i * 3 + 1] = col.g;
        this.colors[i * 3 + 2] = col.b;
      }
      this.pointsMesh.geometry.attributes.color.needsUpdate = true;
    }
    this._sync2DSelectionFromSet();
  }

  animateToView(view) {
    // Future: smoothly move camera to a saved viewpoint
    if (!view) return;
    const { position, target } = view;
    if (position) this.engine.camera.position.set(position.x, position.y, position.z);
    if (target) this.engine.controls.target.set(target.x, target.y, target.z);
  }

  destroy() {
    // Dispose labels
    for (const m of this.labelMeshes.values()) {
      if (m && m.parent) m.parent.remove(m);
      if (m && m.dispose) m.dispose();
    }
    this.labelMeshes.clear();
    if (this._rafId) cancelAnimationFrame(this._rafId);
    this._rafId = null;
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
      this.nodeIndexById.set(nodes[i].id, i);
    }

    const baseColor = new THREE.Color(0x9aa6ff);
    const colors = new Float32Array(N * 3);
    for (let i = 0; i < N; i++) {
      colors[i * 3 + 0] = baseColor.r;
      colors[i * 3 + 1] = baseColor.g;
      colors[i * 3 + 2] = baseColor.b;
    }

    this.positions = positions;
    this.initialPositions = positions.slice(0);
    this.colors = colors;
    this.pointsMesh = this.engine.addPoints(positions, colors);
  }

  _renderEdges() {
    const rels = this.data.relationships || [];
    if (!rels.length || !this.positions) return;
    const segs = new Float32Array(rels.length * 2 * 3);
    let k = 0;
    for (const r of rels) {
      const si = this.nodeIndexById.get(r.source);
      const ti = this.nodeIndexById.get(r.target);
      if (si == null || ti == null) continue;
      const sx = this.positions[si * 3 + 0];
      const sy = this.positions[si * 3 + 1];
      const sz = this.positions[si * 3 + 2];
      const tx = this.positions[ti * 3 + 0];
      const ty = this.positions[ti * 3 + 1];
      const tz = this.positions[ti * 3 + 2];
      segs[k++] = sx; segs[k++] = sy; segs[k++] = sz;
      segs[k++] = tx; segs[k++] = ty; segs[k++] = tz;
    }
    if (k > 0) {
      const filled = (k === segs.length) ? segs : segs.slice(0, k);
      this.edgesLine = this.engine.addEdges(filled, 0x6b7280, 1.0, true, 0.22);
    }
  }

  _computeEdgeIndexPairs() {
    const rels = this.data.relationships || [];
    const pairs = [];
    for (const r of rels) {
      const si = this.nodeIndexById.get(r.source);
      const ti = this.nodeIndexById.get(r.target);
      if (si == null || ti == null) continue;
      pairs.push(si, ti);
    }
    return new Uint32Array(pairs);
  }

  _recomputeEdgeSegmentsFromPositions(pos) {
    const rels = this.data.relationships || [];
    const segs = new Float32Array(rels.length * 2 * 3);
    let k = 0;
    for (const r of rels) {
      const si = this.nodeIndexById.get(r.source);
      const ti = this.nodeIndexById.get(r.target);
      if (si == null || ti == null) continue;
      segs[k++] = pos[si * 3 + 0];
      segs[k++] = pos[si * 3 + 1];
      segs[k++] = pos[si * 3 + 2];
      segs[k++] = pos[ti * 3 + 0];
      segs[k++] = pos[ti * 3 + 1];
      segs[k++] = pos[ti * 3 + 2];
    }
    return k === segs.length ? segs : segs.slice(0, k);
  }

  toggleForceLayout() {
    if (this.forceLayoutRunning) {
      this.stopForceLayout();
    } else {
      this.startForceLayout();
    }
  }

  startForceLayout() {
    if (!this.positions || this.forceLayoutRunning) return;
    const N = (this.positions.length / 3) | 0;
    const edges = this._computeEdgeIndexPairs();
    const workerUrl = '/static/js/viewing/graph3d/layout-worker.js';
    this.layoutWorker = new Worker(workerUrl, { type: 'module' });
    this.forceLayoutRunning = true;

    this.layoutWorker.onmessage = (e) => {
      const msg = e.data;
      if (!msg) return;
      if (msg.type === 'tick' || msg.type === 'done') {
        // Update internal positions and engine
        this.positions.set(msg.positions);
        this.engine.updateNodePositions(this.positions);
        const segs = this._recomputeEdgeSegmentsFromPositions(this.positions);
        this.engine.updateEdgesSegments(segs);
        if (msg.type === 'done') {
          this.forceLayoutRunning = false;
          this.layoutWorker.terminate();
          this.layoutWorker = null;
        }
      }
    };

    const config = { iterations: 800, batch: 3, step: 0.02, repulsion: 180, spring: 0.01, restLength: 42, damping: 0.9 };
    this.layoutWorker.postMessage({
      type: 'start',
      nodes: N,
      positions: this.positions,
      edges,
      config
    });
  }

  stopForceLayout() {
    if (this.layoutWorker) {
      this.layoutWorker.postMessage({ type: 'stop' });
      this.layoutWorker.terminate();
      this.layoutWorker = null;
    }
    this.forceLayoutRunning = false;
  }

  resetLayout() {
    this.stopForceLayout();
    if (!this.positions || !this.initialPositions) return;
    this.positions.set(this.initialPositions);
    this.engine.updateNodePositions(this.positions);
    const segs = this._recomputeEdgeSegmentsFromPositions(this.positions);
    this.engine.updateEdgesSegments(segs);
  }

  _setupInteractions() {
    if (!this.pointsMesh) return;
    if (this._interactionsSetup) return;
    const canvas = this.engine.renderer.domElement;
    const getNDC = (e) => {
      const rect = canvas.getBoundingClientRect();
      this.mouseNDC.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouseNDC.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    };
    const highlight = (idx, color) => {
      if (!this.colors) return;
      this.colors[idx * 3 + 0] = color.r;
      this.colors[idx * 3 + 1] = color.g;
      this.colors[idx * 3 + 2] = color.b;
      this.pointsMesh.geometry.attributes.color.needsUpdate = true;
    };
    const baseColor = new THREE.Color(0x9aa6ff);
    const hoverColor = new THREE.Color(0xf59e0b);
    const selectColor = new THREE.Color(0x10b981);

    const onMove = (e) => {
      getNDC(e);
      this.raycaster.setFromCamera(this.mouseNDC, this.engine.camera);
      const isects = this.raycaster.intersectObject(this.pointsMesh, false);
      const newHover = isects.length ? isects[0].index : -1;
      if (newHover === this.hoverIndex) return;
      if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
        highlight(this.hoverIndex, baseColor);
      }
      this.hoverIndex = newHover;
      if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
        highlight(this.hoverIndex, hoverColor);
      }
    };
    const onLeave = () => {
      if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
        highlight(this.hoverIndex, baseColor);
      }
      this.hoverIndex = -1;
    };
    const onClick = (e) => {
      getNDC(e);
      this.raycaster.setFromCamera(this.mouseNDC, this.engine.camera);
      const isects = this.raycaster.intersectObject(this.pointsMesh, false);
      if (!isects.length) return;
      const idx = isects[0].index;
      if (this.selected.has(idx)) {
        this.selected.delete(idx);
        const col = (this.hoverIndex === idx) ? hoverColor : baseColor;
        highlight(idx, col);
      } else {
        this.selected.add(idx);
        highlight(idx, selectColor);
      }
      this._sync2DSelectionFromSet();
    };
    canvas.addEventListener('mousemove', onMove);
    canvas.addEventListener('mouseleave', onLeave);
    canvas.addEventListener('click', onClick);
    this._interactionsSetup = true;
  }

  _sync2DSelectionFromSet() {
    const ids = [];
    const nodes = this.data.nodes || [];
    for (const idx of this.selected) {
      const id = nodes[idx]?.id;
      if (id != null) ids.push(id);
    }
    state.selectedNodes = new Set(ids);
    if (state.cy) {
      state.cy.nodes().removeClass('multi-selected');
      ids.forEach(id => {
        const n = state.cy.getElementById(id);
        if (n && n.length) n.addClass('multi-selected');
      });
    }
    if (window.viewingManager && window.viewingManager.updateFabVisibility) {
      window.viewingManager.updateFabVisibility();
    }
  }

  _ensureLabel(idx) {
    if (this.labelMeshes.has(idx)) return this.labelMeshes.get(idx);
    const nodes = this.data.nodes || [];
    const n = nodes[idx];
    const text = (n && (n.label || n.name || String(n.id))) || String(idx);
    const label = new Text();
    label.text = text;
    label.fontSize = 3.5;
    label.color = 0xffffff;
    label.outlineWidth = 0.5;
    label.outlineColor = 0x000000;
    label.anchorX = 'left';
    label.anchorY = 'bottom';
    label.sync();
    this.engine.labelsGroup.add(label);
    this.labelMeshes.set(idx, label);
    return label;
  }

  _onFrame() {
    if (!this.positions) return;
    this._frameCount++;
    const camQ = this.engine.camera.quaternion;

    // Hover label
    if (this.hoverIndex !== -1) {
      const li = this._ensureLabel(this.hoverIndex);
      const i = this.hoverIndex;
      li.position.set(
        this.positions[i * 3 + 0] + 1.5,
        this.positions[i * 3 + 1] + 1.5,
        this.positions[i * 3 + 2]
      );
      li.quaternion.copy(camQ);
      li.visible = true;
    }

    // Selected labels
    for (const i of this.selected) {
      const li = this._ensureLabel(i);
      li.position.set(
        this.positions[i * 3 + 0] + 1.5,
        this.positions[i * 3 + 1] + 1.5,
        this.positions[i * 3 + 2]
      );
      li.quaternion.copy(camQ);
      li.visible = true;
    }

    // Hide labels that are neither hovered nor selected every few frames
    if (this._frameCount % 10 === 0) {
      for (const [idx, mesh] of this.labelMeshes.entries()) {
        if (idx !== this.hoverIndex && !this.selected.has(idx)) {
          mesh.visible = false;
        }
      }
    }
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
