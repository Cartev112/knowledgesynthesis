// High-level controller for the 3D graph viewer (P0)
import * as THREE from 'https://esm.sh/three@0.160.0';
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
    this.raycaster.params.Points = { threshold: 1.2 };
    this.mouseNDC = new THREE.Vector2();
    this._interactionsSetup = false;
    this._frameCount = 0;
    this._rafId = null;
    this._fogEnabled = !!(config.render && config.render.fogEnabled);
    this.layoutWorker = null;
    this.forceLayoutRunning = false;
    this._lastCamQuat = new THREE.Quaternion();
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
    // Map 2D node 'sources' into 3D data so document interactions work
    if (state.cy && this.data.nodes?.length) {
      const map = new Map();
      state.cy.nodes().forEach(n => {
        map.set(n.id(), n.data()?.sources || []);
      });
      for (const n of this.data.nodes) {
        if (n && n.id != null) n.sources = map.get(n.id) || n.sources || [];
      }
    }
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
      if (newHover !== this.hoverIndex) {
        if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
          highlight(this.hoverIndex, baseColor);
        }
        this.hoverIndex = newHover;
        if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
          highlight(this.hoverIndex, hoverColor);
        }
      }
      if (this.hoverIndex !== -1) {
        this._showNodeTooltip3D(this.hoverIndex, e);
      } else {
        this._hideNodeTooltip3D();
      }
    };
    const onLeave = () => {
      if (this.hoverIndex !== -1 && !this.selected.has(this.hoverIndex)) {
        highlight(this.hoverIndex, baseColor);
      }
      this.hoverIndex = -1;
      this._hideNodeTooltip3D();
    };
    const onClick = (e) => {
      getNDC(e);
      this.raycaster.setFromCamera(this.mouseNDC, this.engine.camera);
      const isects = this.raycaster.intersectObject(this.pointsMesh, false);
      if (!isects.length) return;
      const idx = isects[0].index;
      if (e.shiftKey) {
        // Multi-select toggle
        if (this.selected.has(idx)) {
          this.selected.delete(idx);
          const col = (this.hoverIndex === idx) ? hoverColor : baseColor;
          highlight(idx, col);
        } else {
          this.selected.add(idx);
          highlight(idx, selectColor);
        }
      } else {
        // Single select only
        const baseWas = Array.from(this.selected);
        this.selected.clear();
        // reset colors of previously selected
        for (const si of baseWas) {
          if (si !== idx) highlight(si, baseColor);
        }
        this.selected.add(idx);
        highlight(idx, selectColor);
      }
      this._sync2DSelectionFromSet();
      // Zoom to clicked node
      const id = this.data.nodes?.[idx]?.id;
      if (id != null) this.focusNodeById(id);
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

  _onFrame() {
    if (!this.positions) return;
    this._frameCount++;
    // No per-frame label updates; 3D uses the same DOM tooltips as 2D
  }

  // --- Tooltips (reuse 2D DOM) ---
  _showNodeTooltip3D(idx, evt) {
    const tooltip = document.getElementById('node-tooltip');
    if (!tooltip) return;
    
    // Don't update position if user is hovering over the tooltip (to allow clicking buttons)
    if (tooltip.matches(':hover')) {
      return;
    }
    
    const n = this.data.nodes?.[idx];
    if (!n) return;
    const labelEl = document.getElementById('node-tooltip-label');
    const typeEl = document.getElementById('node-tooltip-type');
    const sigEl = document.getElementById('node-tooltip-significance');
    if (labelEl) labelEl.textContent = n.label || n.id;
    if (typeEl) typeEl.textContent = '';
    if (sigEl) sigEl.textContent = n.significance ? `Significance: ${n.significance}/5` : '';
    const offset = 10;
    const container = document.getElementById('cy-container') || this.container;
    const rect = container.getBoundingClientRect();
    let left = (evt.clientX ?? 0) - rect.left + offset;
    let top = (evt.clientY ?? 0) - rect.top + offset;
    const maxLeft = Math.max(0, rect.width - 320);
    const maxTop = Math.max(0, rect.height - 180);
    left = Math.min(Math.max(8, left), maxLeft);
    top = Math.min(Math.max(8, top), maxTop);
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
    tooltip.classList.remove('hidden');
    tooltip.classList.add('visible');
    if (window.viewingManager) {
      // So the existing Read More button wiring works in 3D as well
      window.viewingManager.currentHoveredNode = n;
    }
  }

  _hideNodeTooltip3D() {
    const tooltip = document.getElementById('node-tooltip');
    if (tooltip) tooltip.classList.remove('visible');
  }

  // --- Index wiring equivalents ---
  highlightNodeById(nodeId, highlight) {
    if (!this.colors || !this.data?.nodes) return;
    const idx = this.nodeIndexById.get(nodeId);
    if (idx == null) return;
    if (this.selected.has(idx)) return; // don't override selected color
    const baseColor = new THREE.Color(0x9aa6ff);
    const hoverColor = new THREE.Color(0xf59e0b);
    const c = highlight ? hoverColor : baseColor;
    this.colors[idx*3+0] = c.r;
    this.colors[idx*3+1] = c.g;
    this.colors[idx*3+2] = c.b;
    if (this.pointsMesh) this.pointsMesh.geometry.attributes.color.needsUpdate = true;
  }
  highlightDocumentEntities(docId, highlight) {
    if (!this.colors || !this.data?.nodes) return;
    const baseColor = new THREE.Color(0x9aa6ff);
    const highlightColor = new THREE.Color(0xf59e0b);
    for (let i = 0; i < this.data.nodes.length; i++) {
      const n = this.data.nodes[i];
      const sources = n.sources || [];
      const hasDoc = sources.some(s => (typeof s === 'object' ? s.id : s) === docId);
      if (hasDoc) {
        const c = highlight ? highlightColor : baseColor;
        this.colors[i*3+0] = c.r;
        this.colors[i*3+1] = c.g;
        this.colors[i*3+2] = c.b;
      }
    }
    if (this.pointsMesh) this.pointsMesh.geometry.attributes.color.needsUpdate = true;
  }

  applyDocumentFilter3D() {
    if (!this.positions || !this.initialPositions || !this.data?.nodes) return;
    const invisible = new Set();
    const allDocs = (state.indexData?.documents || []).length;
    const showAll = state.activeDocuments.size === allDocs;
    for (let i = 0; i < this.data.nodes.length; i++) {
      const n = this.data.nodes[i];
      const sources = n.sources || [];
      const hasActiveDoc = sources.some(s => state.activeDocuments.has(typeof s === 'object' ? s.id : s));
      const visible = showAll || hasActiveDoc;
      if (!visible) invisible.add(i);
    }
    for (let i = 0; i < this.data.nodes.length; i++) {
      const p = i*3;
      if (invisible.has(i)) {
        this.positions[p] = 1e6;
        this.positions[p+1] = 1e6;
        this.positions[p+2] = 1e6;
      } else {
        this.positions[p]   = this.initialPositions[p];
        this.positions[p+1] = this.initialPositions[p+1];
        this.positions[p+2] = this.initialPositions[p+2];
      }
    }
    this.engine.updateNodePositions(this.positions);
    const segs = this._recomputeEdgeSegmentsFromPositionsWithVisibility(this.positions, invisible);
    this.engine.updateEdgesSegments(segs);
  }

  _recomputeEdgeSegmentsFromPositionsWithVisibility(pos, invisibleSet) {
    const rels = this.data.relationships || [];
    const segs = new Float32Array(rels.length * 2 * 3);
    let k = 0;
    for (const r of rels) {
      const si = this.nodeIndexById.get(r.source);
      const ti = this.nodeIndexById.get(r.target);
      if (si == null || ti == null) continue;
      if (invisibleSet.has(si) || invisibleSet.has(ti)) continue;
      segs[k++] = pos[si * 3 + 0];
      segs[k++] = pos[si * 3 + 1];
      segs[k++] = pos[si * 3 + 2];
      segs[k++] = pos[ti * 3 + 0];
      segs[k++] = pos[ti * 3 + 1];
      segs[k++] = pos[ti * 3 + 2];
    }
    return k === segs.length ? segs : segs.slice(0, k);
  }

  focusNodeById(nodeId) {
    const idx = this.nodeIndexById.get(nodeId);
    if (idx == null || !this.positions) return;
    const x = this.positions[idx*3], y = this.positions[idx*3+1], z = this.positions[idx*3+2];
    const target = new THREE.Vector3(x, y, z);
    this.engine.controls.target.copy(target);
    const cam = this.engine.camera;
    const dir = new THREE.Vector3().subVectors(cam.position, this.engine.controls.target).normalize();
    const distance = 60; // a comfortable distance
    cam.position.copy(target).addScaledVector(dir, distance);
  }

  resetView() {
    if (!this.positions || this.positions.length === 0) return;
    // Compute center and radius of visible nodes (ignore hidden sentinels)
    const center = new THREE.Vector3(0,0,0);
    let count = 0;
    for (let i = 0; i < this.positions.length; i += 3) {
      const x = this.positions[i], y = this.positions[i+1], z = this.positions[i+2];
      if (x > 1e5 || y > 1e5 || z > 1e5) continue;
      center.x += x; center.y += y; center.z += z; count++;
    }
    if (count === 0) return;
    center.multiplyScalar(1 / count);
    let maxR2 = 0;
    for (let i = 0; i < this.positions.length; i += 3) {
      const x = this.positions[i], y = this.positions[i+1], z = this.positions[i+2];
      if (x > 1e5 || y > 1e5 || z > 1e5) continue;
      const dx = x - center.x, dy = y - center.y, dz = z - center.z;
      const r2 = dx*dx + dy*dy + dz*dz;
      if (r2 > maxR2) maxR2 = r2;
    }
    const radius = Math.sqrt(maxR2) || 50;
    this.engine.controls.target.copy(center);
    const cam = this.engine.camera;
    // Position camera back along current view direction
    const dir = new THREE.Vector3().subVectors(cam.position, this.engine.controls.target).normalize();
    const distance = Math.max(radius * 2.2, 120);
    cam.position.copy(center).addScaledVector(dir, distance);
  }

  toggleFog() {
    this._fogEnabled = !this._fogEnabled;
    this.engine.setFogEnabled(this._fogEnabled, this.config?.render || {});
  }

  setPointSize(size) {
    const s = Number(size);
    if (!isNaN(s)) this.engine.setPointSize(s);
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
