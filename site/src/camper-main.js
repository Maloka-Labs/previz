/* =========================================================
   CAMPER MAIN — Magical Mystery Tour (v2.5) boot.
   ========================================================= */
import { createLoader } from "./loader.js";
import { createWorld } from "./world.js";
import { initScroll } from "./scroll.js";
import { initCinematic } from "./cinematic.js";
import { initReveals, initScramble, setYear } from "./ui.js";
import { initParallax } from "./parallax.js";
import { SEATS, ACCESS, TELEGRAM_URL } from "./camper-content.js";

["navJump", "heroJump", "finaleJump", "fbJump"].forEach((id) => {
  const el = document.getElementById(id); if (el) el.href = TELEGRAM_URL;
});
setYear();
renderSeats();
renderAccess();

const camperPath = {
  pos: [[34, 7, 34], [30, 6, 26], [10, 12, 34], [-26, 15, 24], [-34, 18, -6], [24, 12, 34], [44, 13, 38], [64, 15, 30]],
  look: [[18, 4, 16], [20, 4, 16], [6, 8, 8], [0, 11, 0], [0, 12, 0], [26, 8, 14], [84, 8, 9], [104, 7, 7]],
};

function noWebGL2() { return typeof window.WebGL2RenderingContext === "undefined"; }
function showFallback() {
  const l = document.getElementById("loader"); if (l) l.style.display = "none";
  const fb = document.getElementById("fallback"); if (fb) fb.hidden = false;
}

boot().catch((err) => { console.error("Camper boot failed:", err); showFallback(); });

async function boot() {
  if (noWebGL2()) { showFallback(); return; }
  const loader = createLoader();
  loader.set(6);
  await raf2();
  loader.set(26);
  let world;
  try {
    world = createWorld(document.getElementById("webgl"), {
      withVan: true, rainbow: true, portal: true, cameraPath: camperPath,
      cosmicBand: [0.55, 0.92], facetBand: [0.42, 0.62], onFacet: () => {}, onLost: showFallback,
    });
  } catch (e) { console.error("WebGL init failed:", e); showFallback(); return; }
  loader.set(64);
  const cinematic = await initCinematic();
  initScroll(world, { onProgress: (p) => cinematic.update(p) });
  initReveals(); initScramble(); initParallax(); revealSeats();
  loader.set(88);
  world.start();
  await frames(6);
  loader.set(100);
  setTimeout(() => loader.done(), 360);
}

function renderSeats() {
  const grid = document.getElementById("seatsGrid"); if (!grid) return;
  grid.innerHTML = "";
  for (const s of SEATS) {
    const card = document.createElement("article");
    card.className = "seat" + (s.shotgun ? " seat--shotgun" : "");
    card.innerHTML =
      `<div class="seat__seat">${s.shotgun ? "Shotgun · launches first" : "Seat " + s.seat}</div>` +
      `<h3 class="seat__vert">${s.vertical}</h3>` +
      `<p class="seat__note">${s.note}</p>`;
    grid.appendChild(card);
  }
}
function revealSeats() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
  }, { threshold: 0.15 });
  document.querySelectorAll(".seat").forEach((el, i) => { el.style.transitionDelay = (i % 5) * 60 + "ms"; io.observe(el); });
}
function renderAccess() {
  const wrap = document.getElementById("accessLadder"); if (!wrap) return;
  const mod = ["rung--gate", "rung--floor", "rung--ceiling"];
  wrap.innerHTML = "";
  ACCESS.forEach((a, i) => {
    const r = document.createElement("div");
    r.className = "rung " + (mod[i] || "");
    r.setAttribute("data-reveal", "");
    r.innerHTML =
      `<div><div class="rung__who">${a.who}</div><div class="rung__meets">meets · ${a.meets} · <span style="color:var(--muted)">${a.tier}</span></div></div>` +
      `<div class="rung__why">${a.why}</div>`;
    wrap.appendChild(r);
  });
}
function raf2() { return new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))); }
function frames(n) { return new Promise((res) => { let i = 0; (function go() { i++ < n ? requestAnimationFrame(go) : res(); })(); }); }
