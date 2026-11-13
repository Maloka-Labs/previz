/* =========================================================
   PARTICLES — the interactive footer field. Swirls and
   coalesces into flower → diamond → dome → star, colored
   by velocity (slow=violet, fast=hot gold).
   ========================================================= */
import * as THREE from "three";

const N = 4200;

export function buildParticles(THREE_, uniforms) {
  const shapes = { flower: flower(N), diamond: diamond(N), dome: dome(N), star: star(N) };
  const cur = new Float32Array(shapes.dome);
  const target = new Float32Array(shapes.dome);
  const speed = new Float32Array(N);
  const seed = new Float32Array(N);
  for (let i = 0; i < N; i++) seed[i] = Math.random();

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(cur, 3));
  geo.setAttribute("aSpeed", new THREE.BufferAttribute(speed, 1));
  geo.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1));

  const mat = new THREE.ShaderMaterial({
    uniforms: { uPix: { value: 1 }, uReveal: uniforms.uReveal, uTime: uniforms.uTime },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: /* glsl */`
      attribute float aSpeed; attribute float aSeed;
      varying float vSpeed; uniform float uPix; uniform float uReveal;
      void main(){
        vSpeed = aSpeed;
        vec4 mv = modelViewMatrix * vec4(position,1.0);
        gl_PointSize = (1.6 + aSpeed*38.0) * uPix * (70.0/-mv.z) * (0.4+uReveal);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      precision highp float; varying float vSpeed; uniform float uReveal;
      void main(){
        vec2 uv = gl_PointCoord-0.5; float d=length(uv); if(d>0.5) discard;
        float core = smoothstep(0.5,0.0,d);
        vec3 slow=vec3(0.54,0.36,1.0), midC=vec3(1.0,0.49,0.24), fast=vec3(1.0,0.96,0.86);
        float s=clamp(vSpeed*16.0,0.0,1.0);
        vec3 col=mix(slow,midC,smoothstep(0.0,0.5,s));
        col=mix(col,fast,smoothstep(0.5,1.0,s));
        gl_FragColor=vec4(col, core*uReveal*0.95);
      }`,
  });

  const points = new THREE.Points(geo, mat);
  points.frustumCulled = false;

  let morph = "dome";
  function setMorph(name) { if (shapes[name]) { morph = name; target.set(shapes[name]); } }

  function update(dt, time) {
    const k = 1 - Math.pow(0.001, dt);
    const arr = geo.getAttribute("position").array;
    for (let i = 0; i < N; i++) {
      const j = i * 3;
      const dx = target[j] - arr[j], dy = target[j + 1] - arr[j + 1], dz = target[j + 2] - arr[j + 2];
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
      const sw = Math.min(dist, 0.6) * 0.6;
      const a = time * 0.8 + seed[i] * 6.28;
      arr[j] += dx * k + Math.cos(a) * sw * dt;
      arr[j + 1] += dy * k + Math.sin(a * 1.3) * sw * dt;
      arr[j + 2] += dz * k + Math.sin(a) * sw * dt;
      speed[i] = dist * k / Math.max(dt, 1e-3) * 0.02;
    }
    geo.getAttribute("position").needsUpdate = true;
    geo.getAttribute("aSpeed").needsUpdate = true;
    points.rotation.y = time * 0.06;
  }
  return { points, setMorph, update, get morph() { return morph; } };
}

function flower(n) {
  const a = new Float32Array(n * 3), petals = 6;
  for (let i = 0; i < n; i++) {
    const j = i * 3;
    if (i % 9 === 0) { const r = Math.random() * 0.16, t = Math.random() * Math.PI * 2;
      a[j] = Math.cos(t) * r; a[j + 1] = Math.sin(t) * r; a[j + 2] = (Math.random() - 0.5) * 0.06; continue; }
    const p = i % petals, ang = (p / petals) * Math.PI * 2, u = Math.random();
    const w = (Math.random() - 0.5) * Math.sin(u * Math.PI) * 0.34;
    a[j] = Math.cos(ang) * u - Math.sin(ang) * w;
    a[j + 1] = Math.sin(ang) * u + Math.cos(ang) * w;
    a[j + 2] = (Math.random() - 0.5) * 0.06;
  }
  return a;
}
function diamond(n) {
  const a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const j = i * 3;
    let x = Math.random() * 2 - 1, y = Math.random() * 2 - 1, z = Math.random() * 2 - 1;
    const l = Math.abs(x) + Math.abs(y) + Math.abs(z) || 1; x /= l; y /= l; z /= l;
    a[j] = x * 0.9; a[j + 1] = y * 1.4; a[j + 2] = z * 0.9;
  }
  return a;
}
function dome(n) {
  const a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const j = i * 3;
    let x = Math.random() * 2 - 1, y = Math.random(), z = Math.random() * 2 - 1;
    const l = Math.sqrt(x * x + y * y + z * z) || 1;
    a[j] = x / l; a[j + 1] = (y / l) * 0.92 - 0.1; a[j + 2] = z / l;
  }
  return a;
}
function star(n) {
  const a = new Float32Array(n * 3), outer = 1, inner = 0.45, pts = 5, seg = (Math.PI * 2) / pts;
  for (let i = 0; i < n; i++) {
    const j = i * 3, th = Math.random() * Math.PI * 2, t = (th % seg) / seg;
    const edge = t < 0.5 ? lerp(outer, inner, t / 0.5) : lerp(inner, outer, (t - 0.5) / 0.5);
    const r = Math.sqrt(Math.random()) * edge;
    a[j] = Math.cos(th) * r; a[j + 1] = Math.sin(th) * r; a[j + 2] = (Math.random() - 0.5) * 0.05;
  }
  return a;
}
function lerp(a, b, t) { return a + (b - a) * t; }
