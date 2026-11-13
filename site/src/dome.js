/* =========================================================
   DOME — a Drop City geodesic dome. Patchwork shell + glass
   cosmos-windows + golden struts + one interactive gem per FACET.
   ========================================================= */
import * as THREE from "three";
import { DROPCITY, DOME, FACETS } from "./config.js";

export function buildDome(THREE_, palette) {
  const group = new THREE.Group();
  const R = DOME.radius;

  const base = new THREE.IcosahedronGeometry(R, DOME.detail);   // already non-indexed
  const pos = base.getAttribute("position");
  const triCount = pos.count / 3;

  const keepPos = [], keepCol = [], winPos = [];
  const c = new THREE.Color();
  for (let t = 0; t < triCount; t++) {
    const i = t * 9;
    const cyAvg = (pos.array[i + 1] + pos.array[i + 4] + pos.array[i + 7]) / 3;
    if (cyAvg < -R * 0.08) continue;
    const rnd = fract(Math.sin(t * 127.1) * 43758.5453);
    const isWindow = rnd > 0.82 && cyAvg > -R * 0.02;
    const target = isWindow ? winPos : keepPos;
    for (let k = 0; k < 9; k++) target.push(pos.array[i + k]);
    if (!isWindow) {
      c.setHex(DROPCITY[(t * 7) % DROPCITY.length]);
      const v = 0.85 + rnd * 0.3;
      for (let k = 0; k < 3; k++) keepCol.push(c.r * v, c.g * v, c.b * v);
    }
  }

  const shellGeo = new THREE.BufferGeometry();
  shellGeo.setAttribute("position", new THREE.Float32BufferAttribute(keepPos, 3));
  shellGeo.setAttribute("color", new THREE.Float32BufferAttribute(keepCol, 3));
  shellGeo.computeVertexNormals();
  const shell = new THREE.Mesh(shellGeo, new THREE.MeshStandardMaterial({
    vertexColors: true, flatShading: true, roughness: 0.62, metalness: 0.12, side: THREE.DoubleSide,
  }));
  shell.castShadow = true; shell.receiveShadow = true;
  group.add(shell);

  const winGeo = new THREE.BufferGeometry();
  winGeo.setAttribute("position", new THREE.Float32BufferAttribute(winPos, 3));
  winGeo.computeVertexNormals();
  const winMat = new THREE.MeshStandardMaterial({
    color: 0x0a0820, emissive: new THREE.Color(palette.violet), emissiveIntensity: 0.25,
    roughness: 0.1, metalness: 0.0, transparent: true, opacity: 0.55, side: THREE.DoubleSide,
  });
  group.add(new THREE.Mesh(winGeo, winMat));

  const edges = new THREE.EdgesGeometry(shellGeo, 1);
  const struts = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: palette.gold, transparent: true, opacity: 0.35 }));
  struts.scale.setScalar(1.004);
  group.add(struts);

  const gems = [];
  const n = FACETS.length, golden = Math.PI * (3 - Math.sqrt(5));
  const gemGeo = new THREE.OctahedronGeometry(1, 0);
  for (let i = 0; i < n; i++) {
    const f = FACETS[i];
    const y = 0.26 + 0.56 * (n === 1 ? 0.5 : i / (n - 1));
    const az = i * golden, r = Math.sqrt(Math.max(0, 1 - y * y));
    const dir = new THREE.Vector3(Math.cos(az) * r, y, Math.sin(az) * r).normalize();
    const col = new THREE.Color(f.color);
    const gem = new THREE.Mesh(gemGeo, new THREE.MeshStandardMaterial({
      color: col, emissive: col, emissiveIntensity: 0.18, roughness: 0.18, metalness: 0.35, flatShading: true,
    }));
    gem.scale.setScalar(2.0);
    gem.position.copy(dir).multiplyScalar(R * 1.03);
    gem.lookAt(dir.clone().multiplyScalar(R * 2));
    gem.userData = { index: i, facet: f, dir, baseEmissive: 0.18, target: 0.18, spin: 0.2 + Math.random() * 0.3 };
    group.add(gem); gems.push(gem);
  }

  group.userData = { shell, winMat, struts, gems, radius: R };
  return group;
}
function fract(x) { return x - Math.floor(x); }
