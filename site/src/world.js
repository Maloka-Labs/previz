/* =========================================================
   WORLD — the Three.js stage. Meadow + dome + pollen + sky +
   footer particles, a scroll-scrubbed camera, bloom + velocity
   chromatic aberration. A mobile quality tier keeps iOS Safari
   from running out of GPU memory. v2.5 opts: withVan, cameraPath,
   rainbow, portal (Telegram).
   ========================================================= */
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { RGBShiftShader } from "three/addons/shaders/RGBShiftShader.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

import { PALETTE, FACETS } from "./config.js";
import { SKY, POLLEN } from "./shaders.js";
import { buildDome } from "./dome.js";
import { buildMeadow } from "./meadow.js";
import { buildParticles } from "./particles.js";
import { buildVan } from "./van.js";

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;

export function createWorld(container, opts = {}) {
  const onFacet = opts.onFacet || (() => {});

  // ---------- quality tier — mobile Safari is GPU-memory constrained ----------
  const ua = navigator.userAgent || "";
  const iOS = /iP(hone|od|ad)/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const coarse = !!(window.matchMedia && matchMedia("(pointer: coarse)").matches);
  const small = Math.min(innerWidth, innerHeight) < 820;
  const MOBILE = iOS || /Android/i.test(ua) || (coarse && small);
  const Q = Object.assign(
    MOBILE
      ? { pix: 1.5, aa: false, shadows: false, grass: 2200, flowers: 800, pollen: 650, shadowMap: 1024 }
      : { pix: 2, aa: true, shadows: true, grass: 7000, flowers: 2200, pollen: 1500, shadowMap: 2048 },
    opts.quality || {}
  );

  const renderer = new THREE.WebGLRenderer({ antialias: Q.aa, powerPreference: "high-performance" });
  renderer.setSize(innerWidth, innerHeight);
  const PIX = Math.min(devicePixelRatio || 1, Q.pix);
  renderer.setPixelRatio(PIX);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = Q.shadows;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);
  renderer.domElement.addEventListener("webglcontextlost", (e) => { e.preventDefault(); (opts.onLost || (() => {}))(); }, false);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 3000);
  camera.position.set(0, 9, 96);

  const uniforms = { uTime: { value: 0 }, uCosmic: { value: 0 }, uReveal: { value: 0 } };
  const sunDir = new THREE.Vector3(-0.55, 0.42, -0.72).normalize();

  const sky = new THREE.Mesh(new THREE.SphereGeometry(1400, 48, 32), new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { uTime: uniforms.uTime, uCosmic: uniforms.uCosmic, uSun: { value: sunDir.clone() } },
    vertexShader: SKY.vertex, fragmentShader: SKY.fragment,
  }));
  scene.add(sky);
  scene.fog = new THREE.FogExp2(0xcfe0ff, 0.0034);

  const dir = new THREE.DirectionalLight(0xfff0d2, 2.4);
  dir.position.copy(sunDir).multiplyScalar(160);
  dir.castShadow = Q.shadows; dir.shadow.mapSize.set(Q.shadowMap, Q.shadowMap);
  const sc = dir.shadow.camera; sc.near = 10; sc.far = 400; sc.left = -70; sc.right = 70; sc.top = 70; sc.bottom = -70;
  scene.add(dir, dir.target);
  const hemi = new THREE.HemisphereLight(0xbfe3ff, 0x46662c, 0.7); scene.add(hemi);
  const amb = new THREE.AmbientLight(0x2a2546, 0.25); scene.add(amb);

  const meadow = buildMeadow(THREE, uniforms, Q);
  scene.add(meadow.group);
  const dome = buildDome(THREE, PALETTE);
  scene.add(dome);
  const gems = dome.userData.gems;
  const pollen = buildPollen(uniforms, PIX, Q.pollen);
  scene.add(pollen);
  const particles = buildParticles(THREE, uniforms);
  particles.points.scale.setScalar(12); particles.points.position.set(0, 18, 30);
  particles.points.material.uniforms.uPix.value = PIX;
  scene.add(particles.points);

  let van = null;
  const vanParked = new THREE.Vector3(22, 0, 18);
  if (opts.withVan) {
    van = buildVan(); van.position.copy(vanParked); van.rotation.y = -0.12; van.scale.setScalar(1.22);
    scene.add(van);
  }
  let rainbow = null;
  if (opts.rainbow) { rainbow = buildRainbow(); scene.add(rainbow); }
  let portal = null;
  const portalPos = new THREE.Vector3(120, 10, 6);
  if (opts.portal) { portal = buildPortal(); portal.position.copy(portalPos); scene.add(portal); }

  const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
  const defPos = [[0, 9, 96], [-34, 7, 62], [44, 13, 41], [-46, 18, 23], [7, 15, 34], [0, 13, 12.5], [0, 14, -1.5], [0, 25, 76]];
  const defLook = [[0, 11, 0], [0, 10, 0], [0, 11, 0], [0, 12, 0], [0, 12, 0], [0, 13, -6], [0, 17, -34], [0, 14, 0]];
  const posCurve = new THREE.CatmullRomCurve3((opts.cameraPath?.pos || defPos).map(V), false, "centripetal");
  const lookCurve = new THREE.CatmullRomCurve3((opts.cameraPath?.look || defLook).map(V), false, "centripetal");

  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.6, 0.7, 0.62);
  composer.addPass(bloom);
  const rgb = new ShaderPass(RGBShiftShader); rgb.uniforms.amount.value = 0.0;
  composer.addPass(rgb);
  composer.addPass(new OutputPass());

  const ray = new THREE.Raycaster();
  const pointer = new THREE.Vector2(-2, -2), parallax = new THREE.Vector2(0, 0), pPar = new THREE.Vector2(0, 0);
  let hoverIdx = -1, activeIdx = -1;
  addEventListener("pointermove", (e) => { pointer.x = (e.clientX / innerWidth) * 2 - 1; pointer.y = -(e.clientY / innerHeight) * 2 + 1; parallax.set(pointer.x, pointer.y); });
  addEventListener("pointerleave", () => pointer.set(-2, -2));
  function pickFacet() {
    if (pointer.x < -1.5) return -1;
    ray.setFromCamera(pointer, camera);
    const hits = ray.intersectObjects(gems, false);
    return hits.length ? hits[0].object.userData.index : -1;
  }
  function setActive(idx) {
    if (idx === activeIdx) return;
    activeIdx = idx;
    gems.forEach((g, i) => { g.userData.target = i === idx ? 1.35 : 0.18; });
    onFacet(idx >= 0 ? { index: idx, facet: FACETS[idx] } : null);
  }

  let progress = 0, vel = 0;
  const facetBand = opts.facetBand || [0.3, 0.74];
  const cosmicBand = opts.cosmicBand || [0.48, 0.9];
  const api = {
    renderer, scene, camera, particles, van,
    setProgress(p) { progress = clamp(p, 0, 1); },
    setVelocity(v) { vel = v; },
    focusFacet(i) { setActive(i); },
    resize, start,
  };

  const clock = new THREE.Clock();
  function tick() {
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = uniforms.uTime.value += dt;
    const tp = clamp(progress, 0, 1);

    pPar.x += (parallax.x - pPar.x) * Math.min(1, dt * 4);
    pPar.y += (parallax.y - pPar.y) * Math.min(1, dt * 4);
    const p = posCurve.getPoint(tp), l = lookCurve.getPoint(tp);
    const bob = Math.sin(t * 0.6) * 0.25;
    camera.position.set(p.x + pPar.x * 2.2, p.y + bob + pPar.y * 1.2, p.z);
    camera.lookAt(l); camera.updateMatrixWorld();

    const cosmic = smooth(cosmicBand[0], cosmicBand[1], tp);
    uniforms.uCosmic.value = cosmic;
    uniforms.uReveal.value = smooth(0.84, 0.965, tp);
    dir.intensity = lerp(2.6, 0.12, cosmic);
    hemi.intensity = lerp(0.75, 0.18, cosmic);
    amb.intensity = lerp(0.22, 0.5, cosmic);
    dir.color.setRGB(lerp(1, 0.5, cosmic), lerp(0.94, 0.55, cosmic), lerp(0.82, 0.8, cosmic));
    scene.fog.color.setRGB(lerp(0.81, 0.04, cosmic), lerp(0.88, 0.02, cosmic), lerp(1.0, 0.09, cosmic));
    scene.fog.density = lerp(0.0034, 0.0016, cosmic);
    dome.userData.winMat.emissiveIntensity = lerp(0.15, 1.5, cosmic);
    bloom.strength = lerp(0.5, 0.85, cosmic);

    dome.updateMatrixWorld(true);
    hoverIdx = pickFacet();
    if (hoverIdx >= 0) setActive(hoverIdx);
    else if (tp > facetBand[0] && tp < facetBand[1]) setActive(clamp(Math.floor(((tp - facetBand[0]) / (facetBand[1] - facetBand[0])) * FACETS.length), 0, FACETS.length - 1));
    else setActive(-1);
    for (const g of gems) {
      const u = g.userData;
      u.baseEmissive += (u.target - u.baseEmissive) * Math.min(1, dt * 6);
      g.material.emissiveIntensity = u.baseEmissive;
      g.scale.setScalar(lerp(2.0, 2.7, clamp((u.baseEmissive - 0.18) / 1.2, 0, 1)));
      g.rotateOnAxis(u.dir, dt * u.spin);
    }
    dome.rotation.y += dt * 0.02;
    particles.update(dt, t);

    if (van) {
      const driveT = smooth(0.72, 1.0, tp);
      van.position.x = vanParked.x + driveT * 82;
      van.position.z = vanParked.z - driveT * 10;
      van.position.y = vanParked.y + (1 - driveT) * Math.sin(t * 1.6) * 0.06;
      const spin = driveT * 46;
      for (const w of van.userData.wheels) w.rotation.z -= (0.15 + spin) * dt;
      for (const hl of van.userData.headlights) hl.material.emissiveIntensity = 1.2 + cosmic * 2.0 + driveT * 1.5;
    }
    if (rainbow) rainbow.material.opacity = 0.12 + (1 - cosmic) * 0.4;
    if (portal) {
      const app = smooth(0.7, 1.0, tp);
      portal.visible = app > 0.01;
      const pulse = 0.8 + 0.2 * Math.sin(t * 3.0);
      portal.scale.setScalar(0.35 + app * 0.7);
      portal.userData.ring.material.emissiveIntensity = (1.0 + app * 1.4) * pulse;
      portal.userData.disc.material.opacity = app * 0.42 * pulse;
      portal.rotation.z += dt * 0.2;
    }

    const target = clamp(Math.abs(vel) * 0.00018, 0, 0.006);
    rgb.uniforms.amount.value += (target - rgb.uniforms.amount.value) * 0.1;
    vel *= 0.9;

    composer.render();
    requestAnimationFrame(tick);
  }
  function start() { clock.start(); tick(); }
  function resize() {
    camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); bloom.setSize(innerWidth, innerHeight);
  }
  addEventListener("resize", resize);
  return api;
}

function buildPollen(uniforms, PIX, count = 1500) {
  const N = count;
  const pos = new Float32Array(N * 3), seed = new Float32Array(N), size = new Float32Array(N), color = new Float32Array(N * 3);
  const warm = [[1.0, 0.85, 0.55], [1.0, 0.95, 0.8], [1.0, 0.7, 0.5], [0.95, 0.9, 1.0]];
  for (let i = 0; i < N; i++) {
    const j = i * 3, a = Math.random() * Math.PI * 2, r = 20 + Math.random() * 150;
    pos[j] = Math.cos(a) * r; pos[j + 1] = 2 + Math.random() * 70; pos[j + 2] = Math.sin(a) * r;
    seed[i] = Math.random(); size[i] = 1 + Math.random() * 3;
    const c = warm[i % warm.length]; color[j] = c[0]; color[j + 1] = c[1]; color[j + 2] = c[2];
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1));
  geo.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  geo.setAttribute("aColor", new THREE.BufferAttribute(color, 3));
  const mat = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: uniforms.uTime, uCosmic: uniforms.uCosmic, uPix: { value: PIX } },
    vertexShader: POLLEN.vertex, fragmentShader: POLLEN.fragment,
  });
  const pts = new THREE.Points(geo, mat); pts.frustumCulled = false;
  return pts;
}

function buildRainbow() {
  const bands = 6, cols = [0xff4d6d, 0xff9e3d, 0xf4d03f, 0x4fd18b, 0x3fa9ff, 0x8a5cff];
  const group = new THREE.Group();
  const g = new THREE.TorusGeometry(60, bands * 0.9, 8, 80, Math.PI);
  const pos = g.getAttribute("position"), colAttr = new Float32Array(pos.count * 3), c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const band = Math.floor(((pos.getZ(i) + bands) / (2 * bands)) * bands);
    c.setHex(cols[Math.min(bands - 1, Math.max(0, band))]);
    colAttr[i * 3] = c.r; colAttr[i * 3 + 1] = c.g; colAttr[i * 3 + 2] = c.b;
  }
  g.setAttribute("color", new THREE.Float32BufferAttribute(colAttr, 3));
  const mat = new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.4, fog: false });
  const arc = new THREE.Mesh(g, mat); arc.position.set(-6, 0, -40);
  group.add(arc); group.material = mat;
  return group;
}

function buildPortal() {
  const group = new THREE.Group(), TG = 0x2aabee;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(9, 1.1, 16, 48),
    new THREE.MeshStandardMaterial({ color: TG, emissive: TG, emissiveIntensity: 2.0, roughness: 0.3, metalness: 0.4 }));
  const disc = new THREE.Mesh(new THREE.CircleGeometry(8.4, 48),
    new THREE.MeshBasicMaterial({ color: 0xbfe9ff, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, fog: false }));
  const plane = new THREE.Mesh(planeGlyph(), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 1.2, roughness: 0.4 }));
  plane.scale.setScalar(2.2);
  group.add(disc, ring, plane);
  group.userData = { ring, disc, plane };
  group.rotation.y = -Math.PI / 2;
  return group;
}
function planeGlyph() {
  const s = new THREE.Shape();
  s.moveTo(-3, 0); s.lineTo(3, 1.6); s.lineTo(0.2, 0); s.lineTo(3, -1.6); s.closePath();
  return new THREE.ExtrudeGeometry(s, { depth: 0.3, bevelEnabled: false });
}
