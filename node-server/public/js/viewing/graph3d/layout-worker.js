// Simple 3D force-directed layout worker (progressive updates)
// Message protocol:
// { type: 'start', nodes: N, positions: Float32Array(3N), edges: Uint32Array(2M), config: { iterations, step, repulsion, spring, damping } }
// { type: 'stop' }
// Posts back: { type: 'tick', positions: Float32Array(3N), iter }

let positions = null; // Float32Array
let velocities = null; // Float32Array
let edges = null; // Uint32Array of index pairs
let N = 0;
let cfg = null;
let running = false;

function tickOnce() {
  const rep = cfg.repulsion || 200; // repulsive constant
  const spr = cfg.spring || 0.01; // spring constant for edges
  const rest = cfg.restLength || 40; // rest length
  const step = cfg.step || 0.02; // integration step
  const damp = cfg.damping || 0.85; // damping factor

  // Repulsion (naive O(N^2) for N ~ few hundred)
  for (let i = 0; i < N; i++) {
    const ix = i * 3;
    let fx = 0, fy = 0, fz = 0;
    const xi = positions[ix], yi = positions[ix+1], zi = positions[ix+2];
    for (let j = 0; j < N; j++) {
      if (i === j) continue;
      const jx = j * 3;
      let dx = xi - positions[jx];
      let dy = yi - positions[jx+1];
      let dz = zi - positions[jx+2];
      const dist2 = dx*dx + dy*dy + dz*dz + 1e-3;
      const inv = 1.0 / Math.sqrt(dist2);
      const force = rep * inv * inv; // 1/r^2
      fx += dx * force * inv;
      fy += dy * force * inv;
      fz += dz * force * inv;
    }
    velocities[ix] = (velocities[ix] + fx * step) * damp;
    velocities[ix+1] = (velocities[ix+1] + fy * step) * damp;
    velocities[ix+2] = (velocities[ix+2] + fz * step) * damp;
  }

  // Springs along edges
  for (let e = 0; e < edges.length; e += 2) {
    const a = edges[e];
    const b = edges[e+1];
    const ax = a*3, bx = b*3;
    const dx = positions[bx] - positions[ax];
    const dy = positions[bx+1] - positions[ax+1];
    const dz = positions[bx+2] - positions[ax+2];
    const dist = Math.max(Math.sqrt(dx*dx + dy*dy + dz*dz), 1e-3);
    const disp = dist - rest;
    const force = spr * disp;
    const nx = dx / dist, ny = dy / dist, nz = dz / dist;
    velocities[ax] += force * nx * step;
    velocities[ax+1] += force * ny * step;
    velocities[ax+2] += force * nz * step;
    velocities[bx] -= force * nx * step;
    velocities[bx+1] -= force * ny * step;
    velocities[bx+2] -= force * nz * step;
  }

  // Integrate
  for (let i = 0; i < N; i++) {
    const ix = i*3;
    positions[ix] += velocities[ix];
    positions[ix+1] += velocities[ix+1];
    positions[ix+2] += velocities[ix+2];
  }
}

onmessage = (evt) => {
  const msg = evt.data;
  if (msg.type === 'start') {
    N = msg.nodes;
    cfg = msg.config || {};
    positions = new Float32Array(msg.positions); // copy
    velocities = new Float32Array(positions.length);
    edges = msg.edges ? new Uint32Array(msg.edges) : new Uint32Array();
    running = true;

    const iterations = cfg.iterations || 500;
    const batch = cfg.batch || 5; // how many ticks per post

    let iter = 0;
    const loop = () => {
      if (!running) return;
      for (let k = 0; k < batch && iter < iterations; k++, iter++) {
        tickOnce();
      }
      // Post progressive update
      postMessage({ type: 'tick', positions, iter });
      if (iter < iterations) {
        setTimeout(loop, 0);
      } else {
        running = false;
        postMessage({ type: 'done', positions, iter });
      }
    };
    loop();
  } else if (msg.type === 'stop') {
    running = false;
  }
};
