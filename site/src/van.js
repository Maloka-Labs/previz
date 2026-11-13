/* =========================================================
   VAN — a psychedelic VW Type-2 combi (GaiA, the camper).
   Canvas two-tone paint (Magical-Mystery-Tour swirl), split
   windshield, round headlights (emissive), whitewall wheels,
   a surfboard. Faces +X. world.js parks it beside the dome.
   ========================================================= */
import * as THREE from "three";

const RAINBOW = ["#ff4d6d", "#ff9e3d", "#f4d03f", "#4fd18b", "#3fa9ff", "#8a5cff"];

export function buildVan() {
  const van = new THREE.Group();
  const L = 9, H = 3.3, W = 4.1, wheelR = 0.98, bodyY = wheelR + 0.35;

  const paintFront = texMat(drawFront(512, 512));
  const paintBack = texMat(drawBack(512, 512));
  const paintSide = texMat(drawSide(1024, 512));
  const paintSideR = texMat(drawSide(1024, 512, true));
  const roofMat = new THREE.MeshStandardMaterial({ color: 0xf3eee2, roughness: 0.5, metalness: 0.1 });
  const floorMat = new THREE.MeshStandardMaterial({ color: 0x20161f, roughness: 0.9 });
  const chrome = new THREE.MeshStandardMaterial({ color: 0xdfe6ee, roughness: 0.22, metalness: 1.0 });
  const rubber = new THREE.MeshStandardMaterial({ color: 0x14131a, roughness: 0.85 });
  const whitewall = new THREE.MeshStandardMaterial({ color: 0xeceae0, roughness: 0.5 });

  const bodyMats = [paintFront, paintBack, roofMat, floorMat, paintSide, paintSideR];
  const lower = new THREE.Mesh(rounded(L, H * 0.9, W, 0.35), bodyMats);
  lower.position.y = bodyY + H * 0.45; lower.castShadow = true; lower.receiveShadow = true;
  van.add(lower);

  const cap = new THREE.Mesh(rounded(L * 0.9, H * 0.22, W * 0.9, 0.28), new THREE.MeshStandardMaterial({ color: 0xf3eee2, roughness: 0.5 }));
  cap.position.set(0, bodyY + H * 0.9 + H * 0.08, 0); cap.castShadow = true; van.add(cap);

  const frontX = L / 2;
  const bumperF = new THREE.Mesh(rounded(0.5, 0.5, W * 1.02, 0.2), chrome);
  bumperF.position.set(frontX - 0.05, bodyY + 0.35, 0); van.add(bumperF);
  const bumperR = bumperF.clone(); bumperR.position.x = -frontX + 0.05; van.add(bumperR);

  const headlights = [];
  for (const s of [-1, 1]) {
    const hl = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.22, 20),
      new THREE.MeshStandardMaterial({ color: 0xfff6d0, emissive: 0xffdf8a, emissiveIntensity: 1.4, roughness: 0.3 }));
    hl.rotation.z = Math.PI / 2; hl.position.set(frontX + 0.02, bodyY + 1.15, s * (W * 0.28));
    van.add(hl); headlights.push(hl);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.09, 8, 20), chrome);
    ring.position.copy(hl.position); ring.rotation.y = Math.PI / 2; van.add(ring);
  }
  for (const s of [-1, 1]) {
    const stalk = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.7), chrome);
    stalk.rotation.z = Math.PI / 2.4; stalk.position.set(frontX - 0.2, bodyY + H * 0.75, s * (W / 2 + 0.25)); van.add(stalk);
    const gl = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.4, 0.28), chrome);
    gl.position.set(frontX - 0.35, bodyY + H * 0.75 + 0.28, s * (W / 2 + 0.42)); van.add(gl);
  }

  const wheels = [];
  const wx = L * 0.32, wz = W / 2 + 0.02;
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    const wheel = new THREE.Group();
    const tire = new THREE.Mesh(new THREE.CylinderGeometry(wheelR, wheelR, 0.55, 24), rubber);
    tire.rotation.x = Math.PI / 2; tire.castShadow = true;
    const ww = new THREE.Mesh(new THREE.CylinderGeometry(wheelR * 0.72, wheelR * 0.72, 0.57, 24), whitewall); ww.rotation.x = Math.PI / 2;
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(wheelR * 0.34, wheelR * 0.34, 0.6, 16), chrome); hub.rotation.x = Math.PI / 2;
    wheel.add(tire, ww, hub);
    wheel.position.set(sx * wx, wheelR, sz * wz); van.add(wheel); wheels.push(wheel);
  }

  const board = new THREE.Group();
  const boardMesh = new THREE.Mesh(boardShape(), texMat(drawBoard(256, 64))); boardMesh.castShadow = true;
  board.add(boardMesh);
  for (const s of [-1, 1]) {
    const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, W * 0.7), chrome);
    rail.rotation.x = Math.PI / 2; rail.position.set(s * L * 0.22, bodyY + H * 1.02, 0); van.add(rail);
  }
  board.position.set(-0.5, bodyY + H * 1.06, 0.3); board.rotation.y = 0.06; van.add(board);

  van.userData = { wheels, headlights, height: bodyY };
  return van;
}

function rounded(w, h, d) {
  const g = new THREE.BoxGeometry(w, h, d, 2, 2, 2);
  const p = g.getAttribute("position"), hh = h / 2, hw = w / 2, hd = d / 2;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const fx = Math.abs(x) > hw * 0.5 ? 1 : 0, fz = Math.abs(z) > hd * 0.5 ? 1 : 0;
    if (Math.abs(y) > hh * 0.5 && (fx || fz)) { x *= 0.94; z *= 0.94; }
    p.setXYZ(i, x, y, z);
  }
  g.computeVertexNormals(); return g;
}
function boardShape() { const g = new THREE.CapsuleGeometry(0.34, 4.4, 4, 12); g.rotateZ(Math.PI / 2); g.scale(1, 0.28, 1); return g; }

function texMat(canvas) {
  const t = new THREE.CanvasTexture(canvas); t.anisotropy = 8; t.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshStandardMaterial({ map: t, roughness: 0.38, metalness: 0.18 });
}
function makeCanvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return { c, x: c.getContext("2d") }; }
function swirl(x, w, h, cx, cy, R) {
  for (let i = 12; i >= 0; i--) { x.beginPath(); x.arc(cx, cy, (R * i) / 12, 0, Math.PI * 2); x.fillStyle = RAINBOW[i % RAINBOW.length]; x.globalAlpha = 0.72; x.fill(); }
  x.globalAlpha = 1;
}
function paintBase(x, w, h) {
  x.fillStyle = "#f3eee2"; x.fillRect(0, 0, w, h);
  x.fillStyle = "#ff4d8d";
  x.beginPath(); x.moveTo(0, h * 0.44); x.bezierCurveTo(w * 0.35, h * 0.42, w * 0.6, h * 0.64, w, h * 0.42);
  x.lineTo(w, h); x.lineTo(0, h); x.closePath(); x.fill();
}
function drawSide(w, h, mirror = false) {
  const { c, x } = makeCanvas(w, h);
  if (mirror) { x.translate(w, 0); x.scale(-1, 1); }
  paintBase(x, w, h);
  for (let i = 0; i < RAINBOW.length; i++) { x.fillStyle = RAINBOW[i]; x.globalAlpha = 0.9; x.fillRect(0, h * 0.5 + i * 6, w, 6); }
  x.globalAlpha = 1;
  swirl(x, w, h, w * 0.24, h * 0.78, h * 0.3); swirl(x, w, h, w * 0.7, h * 0.8, h * 0.24);
  const wy = h * 0.14, wh = h * 0.3;
  [[0.06, 0.16], [0.24, 0.2], [0.46, 0.2], [0.68, 0.24]].forEach(([px, pw]) => glass(x, w * px, wy, w * pw, wh));
  peace(x, w * 0.14, h * 0.76, h * 0.12);
  return c;
}
function drawFront(w, h) {
  const { c, x } = makeCanvas(w, h);
  paintBase(x, w, h);
  x.fillStyle = "#f3eee2";
  x.beginPath(); x.moveTo(w * 0.5, h * 0.72); x.lineTo(0, h * 0.46); x.lineTo(0, h * 0.34);
  x.lineTo(w * 0.5, h * 0.58); x.lineTo(w, h * 0.34); x.lineTo(w, h * 0.46); x.closePath(); x.fill();
  glass(x, w * 0.1, h * 0.1, w * 0.36, h * 0.24); glass(x, w * 0.54, h * 0.1, w * 0.36, h * 0.24);
  const cx = w * 0.5, cy = h * 0.5, r = h * 0.13;
  x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.fillStyle = "#f3eee2"; x.fill();
  x.lineWidth = h * 0.02; x.strokeStyle = "#2a2340"; x.stroke();
  x.fillStyle = "#2a2340"; x.font = `bold ${r * 1.1}px Georgia, serif`; x.textAlign = "center"; x.textBaseline = "middle";
  x.fillText("V", cx, cy - r * 0.28); x.fillText("W", cx, cy + r * 0.34);
  return c;
}
function drawBack(w, h) {
  const { c, x } = makeCanvas(w, h);
  paintBase(x, w, h);
  glass(x, w * 0.2, h * 0.12, w * 0.6, h * 0.24);
  x.strokeStyle = "#2a2340"; x.lineWidth = 6;
  for (let i = 0; i < 6; i++) { x.beginPath(); x.moveTo(w * 0.32, h * 0.62 + i * 14); x.lineTo(w * 0.68, h * 0.62 + i * 14); x.stroke(); }
  peace(x, w * 0.5, h * 0.5, h * 0.09);
  return c;
}
function drawBoard(w, h) {
  const { c, x } = makeCanvas(w, h);
  for (let i = 0; i < w; i++) { x.fillStyle = RAINBOW[Math.floor(i / (w / RAINBOW.length)) % RAINBOW.length]; x.fillRect(i, 0, 1, h); }
  x.strokeStyle = "rgba(255,255,255,.5)"; x.lineWidth = 3; x.beginPath(); x.moveTo(0, h / 2); x.lineTo(w, h / 2); x.stroke();
  return c;
}
function glass(x, gx, gy, gw, gh) {
  const g = x.createLinearGradient(gx, gy, gx + gw, gy + gh);
  g.addColorStop(0, "#2b3a4a"); g.addColorStop(0.5, "#8fb7cf"); g.addColorStop(1, "#33465a");
  roundRect(x, gx, gy, gw, gh, gh * 0.28); x.fillStyle = g; x.fill(); x.lineWidth = 8; x.strokeStyle = "#e9e4d6"; x.stroke();
}
function peace(x, cx, cy, r) {
  x.strokeStyle = "#f3eee2"; x.lineWidth = r * 0.16;
  x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.stroke();
  x.beginPath(); x.moveTo(cx, cy - r); x.lineTo(cx, cy + r);
  x.moveTo(cx, cy); x.lineTo(cx - r * 0.7, cy + r * 0.7); x.moveTo(cx, cy); x.lineTo(cx + r * 0.7, cy + r * 0.7); x.stroke();
}
function roundRect(x, rx, ry, rw, rh, r) {
  x.beginPath(); x.moveTo(rx + r, ry);
  x.arcTo(rx + rw, ry, rx + rw, ry + rh, r); x.arcTo(rx + rw, ry + rh, rx, ry + rh, r);
  x.arcTo(rx, ry + rh, rx, ry, r); x.arcTo(rx, ry, rx + rw, ry, r); x.closePath();
}
