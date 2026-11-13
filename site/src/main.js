/* MAIN — boot sequence (Maloka Dome / v2). */
import { createLoader } from "./loader.js";
import { createWorld } from "./world.js";
import { initScroll } from "./scroll.js";
import { initCinematic } from "./cinematic.js";
import { initScramble, initReveals, initFacetUI, initFooterMorph, initSound, setYear } from "./ui.js";

setYear();
function noWebGL2() { return typeof window.WebGL2RenderingContext === "undefined"; }
function showFallback() {
  const l = document.getElementById("loader"); if (l) l.style.display = "none";
  const fb = document.getElementById("fallback"); if (fb) fb.hidden = false;
}

boot().catch((err) => { console.error("Maloka boot failed:", err); showFallback(); });

async function boot() {
  if (noWebGL2()) { showFallback(); return; }
  let world, scroll;
  const loader = createLoader();
  loader.set(6);
  const facetUI = initFacetUI({ onDot: (i) => scroll?.scrollToFacet(i) });
  await raf2();
  loader.set(28);
  try {
    world = createWorld(document.getElementById("webgl"), { onFacet: (payload) => facetUI.update(payload), onLost: showFallback });
  } catch (e) { console.error("WebGL init failed:", e); showFallback(); return; }
  loader.set(64);
  const cinematic = await initCinematic();
  scroll = initScroll(world, { onProgress: (p) => cinematic.update(p) });
  initScramble(); initReveals(); initFooterMorph(world.particles); initSound();
  loader.set(86);
  world.start();
  await frames(6);
  loader.set(100);
  setTimeout(() => loader.done(), 360);
}
function raf2() { return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }
function frames(n) { return new Promise((res) => { let i = 0; (function go() { i++ < n ? requestAnimationFrame(go) : res(); })(); }); }
