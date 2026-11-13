/* =========================================================
   MEADOW — hyper-real lush summer. Rolling terrain, instanced
   wind grass, glowing wildflowers. Counts scale down on mobile
   (quality.grass / quality.flowers).
   ========================================================= */
import * as THREE from "three";
import { PALETTE } from "./config.js";

const FLOWER_COLORS = [PALETTE.magenta, PALETTE.gold, PALETTE.tangerine, PALETTE.violet, PALETTE.sky, 0xffffff, PALETTE.amber];

export function terrainHeight(x, z) {
  const flat = smoothstep(0, 46, Math.hypot(x, z));
  const h = 1.7 * Math.sin(x * 0.03) * Math.cos(z * 0.025) + 1.2 * Math.sin((x + z) * 0.018) + 0.6 * Math.sin(x * 0.07 + z * 0.05);
  return h * flat;
}

export function buildMeadow(THREE_, uniforms, quality = {}) {
  const group = new THREE.Group();
  const GRASS = quality.grass ?? 7000;
  const FLOWERS = quality.flowers ?? 2200;

  const groundGeo = new THREE.PlaneGeometry(900, 900, 150, 150);
  groundGeo.rotateX(-Math.PI / 2);
  const gp = groundGeo.getAttribute("position");
  for (let i = 0; i < gp.count; i++) gp.setY(i, terrainHeight(gp.getX(i), gp.getZ(i)));
  groundGeo.computeVertexNormals();
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x4f7a3a, roughness: 0.95, metalness: 0.0 });
  injectNight(groundMat, uniforms, 0.45);
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.receiveShadow = true;
  group.add(ground);

  const blade = new THREE.PlaneGeometry(0.32, 2.4, 1, 3);
  blade.translate(0, 1.2, 0);
  const grassMat = new THREE.MeshStandardMaterial({ color: 0x6fae4a, roughness: 1.0, metalness: 0.0, side: THREE.DoubleSide });
  injectWind(grassMat, uniforms, 1.0); injectNight(grassMat, uniforms, 0.5);
  const grass = new THREE.InstancedMesh(blade, grassMat, GRASS);
  scatter(grass, GRASS, 16, 170, (m, x, z) => {
    const s = 0.7 + Math.random() * 1.2;
    m.makeRotationY(Math.random() * Math.PI); m.scale(new THREE.Vector3(s, s, s));
    m.setPosition(x, terrainHeight(x, z), z);
  });
  grass.castShadow = false;
  group.add(grass);

  const bloom = new THREE.IcosahedronGeometry(0.55, 0);
  bloom.scale(1, 0.5, 1); bloom.translate(0, 2.4, 0);
  const wc = new Float32Array(bloom.getAttribute("position").count * 3).fill(1);
  bloom.setAttribute("color", new THREE.Float32BufferAttribute(wc, 3));   // USE_COLOR → vColor carries instanceColor
  const flowerMat = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 0.5, metalness: 0.1, flatShading: true,
    emissive: new THREE.Color(0x000000), emissiveIntensity: 1.0,
  });
  injectWind(flowerMat, uniforms, 1.2);
  const flowers = new THREE.InstancedMesh(bloom, flowerMat, FLOWERS);
  const col = new THREE.Color();
  scatter(flowers, FLOWERS, 20, 150, (m, x, z, i) => {
    const s = 0.8 + Math.random() * 1.4;
    m.makeRotationY(Math.random() * Math.PI); m.scale(new THREE.Vector3(s, s, s));
    m.setPosition(x, terrainHeight(x, z), z);
    col.setHex(FLOWER_COLORS[i % FLOWER_COLORS.length]); flowers.setColorAt(i, col);
  });
  flowers.material.onBeforeCompile = chainEmissiveFromInstanceColor(flowers.material.onBeforeCompile, uniforms);
  flowers.instanceColor.needsUpdate = true;
  group.add(flowers);

  return { group, ground, grass, flowers };
}

function scatter(mesh, count, rMin, rMax, place) {
  const m = new THREE.Matrix4();
  for (let i = 0; i < count; i++) {
    const a = Math.random() * Math.PI * 2, r = rMin + Math.sqrt(Math.random()) * (rMax - rMin);
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    m.identity(); place(m, x, z, i); mesh.setMatrixAt(i, m);
  }
  mesh.instanceMatrix.needsUpdate = true;
}
function injectWind(mat, uniforms, amount) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = uniforms.uTime;
    sh.vertexShader = "uniform float uTime;\n" + sh.vertexShader;
    sh.vertexShader = sh.vertexShader.replace("#include <begin_vertex>", /* glsl */`#include <begin_vertex>
       vec4 wp = instanceMatrix * vec4(0.0,0.0,0.0,1.0);
       float ph = wp.x*0.35 + wp.z*0.35;
       float sway = sin(uTime*1.5 + ph) + 0.4*sin(uTime*3.1 + ph*1.7);
       float hgt = max(position.y, 0.0);
       transformed.x += sway * ${amount.toFixed(2)} * 0.16 * hgt;
       transformed.z += cos(uTime*1.2 + ph) * ${amount.toFixed(2)} * 0.12 * hgt;`);
  };
}
function injectNight(mat, uniforms, strength) {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh) => {
    if (prev) prev(sh);
    sh.uniforms.uCosmic = uniforms.uCosmic;
    sh.fragmentShader = "uniform float uCosmic;\n" + sh.fragmentShader;
    sh.fragmentShader = sh.fragmentShader.replace("#include <dithering_fragment>", /* glsl */`#include <dithering_fragment>
       gl_FragColor.rgb *= (1.0 - uCosmic*${strength.toFixed(2)});`);
  };
}
function chainEmissiveFromInstanceColor(prev, uniforms) {
  return (sh) => {
    if (prev) prev(sh);
    sh.uniforms.uCosmic = uniforms.uCosmic;
    sh.fragmentShader = "uniform float uCosmic;\n" + sh.fragmentShader;
    sh.fragmentShader = sh.fragmentShader.replace("#include <emissivemap_fragment>", /* glsl */`#include <emissivemap_fragment>
       totalEmissiveRadiance += vColor * (0.12 + uCosmic*0.72);`);
  };
}
function smoothstep(a, b, x) { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); }
