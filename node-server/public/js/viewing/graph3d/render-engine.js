// Minimal Three.js render engine for 3D graph viewer (P0)
// ESM imports pinned to specific versions (esm.sh rewrites bare imports)
import * as THREE from 'https://esm.sh/three@0.160.0';
import { OrbitControls } from 'https://esm.sh/three@0.160.0/examples/jsm/controls/OrbitControls.js';
import { Line2 } from 'https://esm.sh/three@0.160.0/examples/jsm/lines/Line2.js';
import { LineMaterial } from 'https://esm.sh/three@0.160.0/examples/jsm/lines/LineMaterial.js';
import { LineGeometry } from 'https://esm.sh/three@0.160.0/examples/jsm/lines/LineGeometry.js';

export class RenderEngine3D {
  constructor(container, config = {}) {
    this.container = container;
    this.config = config;

    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.domElement.classList.add('graph3d-canvas');
    container.appendChild(this.renderer.domElement);

    // Scene
    this.scene = new THREE.Scene();
    const bg = (config.render && config.render.background) || '#0b1020';
    this.scene.background = new THREE.Color(bg);

    // Camera
    const fov = (config.camera && config.camera.fov) || 55;
    this.camera = new THREE.PerspectiveCamera(
      fov,
      Math.max(container.clientWidth, 1) / Math.max(container.clientHeight, 1),
      (config.camera && config.camera.near) || 0.1,
      (config.camera && config.camera.far) || 5000
    );
    this.camera.position.set(0, 0, 100);

    // Controls
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;

    // Lighting (subtle, as we may use unlit materials later)
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 0.6);
    dir.position.set(1, 1, 1);
    this.scene.add(dir);

    // Content groups
    this.root = new THREE.Group();
    this.nodesGroup = new THREE.Group();
    this.edgesGroup = new THREE.Group();
    this.root.add(this.edgesGroup);
    this.root.add(this.nodesGroup);
    this.scene.add(this.root);

    // Resize handling
    this._onResize = () => this.resize();
    window.addEventListener('resize', this._onResize);

    this._raf = null;
    this.start();
  }

  start() {
    if (this._raf) return;
    const loop = () => {
      this._raf = requestAnimationFrame(loop);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    loop();
  }

  stop() {
    if (this._raf) cancelAnimationFrame(this._raf);
    this._raf = null;
  }

  clear() {
    // Remove all children from groups
    for (const g of [this.nodesGroup, this.edgesGroup]) {
      while (g.children.length) {
        const obj = g.children.pop();
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      }
    }
  }

  addPoints(positions, colors) {
    // positions: Float32Array of length 3N
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    if (colors) geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 1.8,
      color: 0x9aa6ff,
      vertexColors: !!colors,
      sizeAttenuation: true
    });

    const points = new THREE.Points(geometry, material);
    this.nodesGroup.add(points);
    return points;
  }

  addEdges(positions, color = 0x9aa6ff, width = 1.2, transparent = true, opacity = 0.25) {
    const geom = new LineGeometry();
    geom.setPositions(Array.from(positions));
    const material = new LineMaterial({
      color,
      linewidth: width,
      transparent,
      opacity,
      depthTest: true,
      depthWrite: true
    });
    material.resolution.set(this.container.clientWidth, this.container.clientHeight);
    const line = new Line2(geom, material);
    line.computeLineDistances();
    this.edgesGroup.add(line);
    return line;
  }

  resize() {
    const w = Math.max(this.container.clientWidth, 1);
    const h = Math.max(this.container.clientHeight, 1);
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    for (const child of this.edgesGroup.children) {
      if (child.material && child.material.resolution) {
        child.material.resolution.set(w, h);
      }
    }
  }

  dispose() {
    this.stop();
    window.removeEventListener('resize', this._onResize);
    this.clear();
    this.renderer.dispose();
    if (this.renderer.domElement && this.renderer.domElement.parentElement === this.container) {
      this.container.removeChild(this.renderer.domElement);
    }
  }
}
