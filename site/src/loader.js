/* =========================================================
   LOADER — the dome assembles panel by panel as % climbs,
   then dissolves into the live scene.
   ========================================================= */
import { DROPCITY } from "./config.js";

export function createLoader() {
  const root = document.getElementById("loader");
  const g = document.getElementById("loaderDome");
  const numEl = document.getElementById("loaderNum");
  const fillEl = document.getElementById("loaderFill");

  const cx = 50, cy = 80, R = 38, rings = 4, segs = 11;
  const pt = (i, j) => {
    const rad = (R * i) / rings, ang = Math.PI * (j / segs);
    return [cx + Math.cos(ang) * rad, cy - Math.sin(ang) * rad];
  };
  const panels = [];
  for (let i = 0; i < rings; i++) {
    for (let j = 0; j < segs; j++) {
      const a = pt(i, j), b = pt(i, j + 1), c = pt(i + 1, j + 1), d = pt(i + 1, j);
      [[a, b, c], [a, c, d]].forEach((tri) => {
        const poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        poly.setAttribute("points", tri.map((p) => p.join(",")).join(" "));
        poly.setAttribute("fill", DROPCITY[panels.length % DROPCITY.length]);
        poly.setAttribute("fill-opacity", "0.22");
        poly.style.opacity = "0";
        poly.style.transition = "opacity .35s cubic-bezier(.16,1,.3,1)";
        g.appendChild(poly);
        panels.push(poly);
      });
    }
  }
  const base = document.createElementNS("http://www.w3.org/2000/svg", "line");
  base.setAttribute("x1", cx - R); base.setAttribute("y1", cy);
  base.setAttribute("x2", cx + R); base.setAttribute("y2", cy);
  g.appendChild(base);

  let shown = 0;
  function set(pct) {
    pct = Math.max(0, Math.min(100, pct));
    numEl.textContent = Math.round(pct);
    fillEl.style.width = pct + "%";
    const want = Math.floor((pct / 100) * panels.length);
    for (; shown < want; shown++) panels[shown].style.opacity = "1";
  }
  function done() {
    for (; shown < panels.length; shown++) panels[shown].style.opacity = "1";
    root.classList.add("is-done");
    setTimeout(() => { root.style.display = "none"; }, 1000);
  }
  return { set, done };
}
