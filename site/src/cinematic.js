/* =========================================================
   CINEMATIC — optional AI-video layer. Reads
   assets/video/manifest.json and blends Kling/Higgsfield
   clips over the WebGL at chosen scroll ranges. No-op when
   the manifest is empty.
   ========================================================= */
export async function initCinematic() {
  const root = document.getElementById("cinematic");
  let cfgs = [];
  try {
    const r = await fetch("./assets/video/manifest.json", { cache: "no-store" });
    if (r.ok) cfgs = (await r.json()).layers || [];
  } catch (e) { /* no manifest → no-op */ }

  const layers = cfgs.map((cfg) => {
    const v = document.createElement("video");
    v.src = cfg.src; v.muted = true; v.loop = true; v.playsInline = true;
    v.setAttribute("playsinline", ""); v.setAttribute("muted", ""); v.preload = "auto";
    v.style.mixBlendMode = cfg.blend || "normal";
    const L = { v, range: cfg.range || [0, 1], max: cfg.max ?? 0.85, ok: false };
    v.addEventListener("canplay", () => { L.ok = true; }, { once: true });
    v.addEventListener("error", () => { L.ok = false; });
    root.appendChild(v);
    return L;
  });

  function update(p) {
    for (const L of layers) {
      if (!L.ok) continue;
      const [a, b] = L.range;
      const mid = (a + b) / 2, half = Math.max(1e-4, (b - a) / 2);
      const o = (p >= a && p <= b) ? Math.max(0, 1 - Math.abs(p - mid) / half) : 0;
      L.v.style.opacity = (o * L.max).toFixed(3);
      if (o > 0.02) { if (L.v.paused) L.v.play().catch(() => {}); }
      else if (!L.v.paused) L.v.pause();
    }
  }
  return { update, active: layers.length > 0 };
}
