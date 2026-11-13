/* =========================================================
   UI — the HTML layer over the WebGL. Text scramble, scroll
   reveals, facet readout/dots, footer morph triggers, and a
   quiet generative ambient pad.
   ========================================================= */
import { FACETS } from "./config.js";

const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&*+=-/<>";

function scramble(el, finalText, dur = 800) {
  const start = performance.now(), len = finalText.length;
  function frame(now) {
    const t = Math.min(1, (now - start) / dur);
    let out = "";
    for (let i = 0; i < len; i++) {
      const ch = finalText[i];
      if (/\s/.test(ch) || ch.charCodeAt(0) === 160) { out += ch; continue; }
      out += t * len > i ? ch : CHARS[(Math.random() * CHARS.length) | 0];
    }
    el.textContent = out;
    if (t < 1) requestAnimationFrame(frame); else el.textContent = finalText;
  }
  requestAnimationFrame(frame);
}

export function initScramble() {
  document.querySelectorAll("[data-scramble]").forEach((el) => {
    const text = el.textContent;
    el.addEventListener("mouseenter", () => scramble(el, text, 500));
  });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { scramble(e.target, e.target.dataset._txt ?? e.target.textContent, 900); io.unobserve(e.target); }
    });
  }, { threshold: 0.6 });
  document.querySelectorAll("[data-scramble-on-view]").forEach((el) => { el.dataset._txt = el.textContent; io.observe(el); });
}

export function initReveals() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("is-in"); });
  }, { threshold: 0.25, rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll("[data-reveal]").forEach((el) => io.observe(el));
}

export function initFacetUI({ onDot } = {}) {
  const card = document.getElementById("facetCard");
  const idxEl = document.getElementById("facetIndex");
  const titleEl = document.getElementById("facetTitle");
  const descEl = document.getElementById("facetDesc");
  const tagsEl = document.getElementById("facetTags");
  const dotsWrap = document.getElementById("facetDots");
  if (!card || !dotsWrap) return { update() {} };

  const dots = FACETS.map((f, i) => {
    const b = document.createElement("button");
    b.title = f.title; b.style.borderColor = f.color;
    b.addEventListener("click", () => onDot && onDot(i));
    dotsWrap.appendChild(b); return b;
  });

  let shown = -1;
  function update(payload) {
    const visible = !!payload;
    card.classList.toggle("is-visible", visible);
    dotsWrap.classList.toggle("is-visible", visible);
    if (!visible) { dots.forEach((d) => d.classList.remove("is-active")); shown = -1; return; }
    const { index, facet } = payload;
    dots.forEach((d, i) => {
      d.classList.toggle("is-active", i === index);
      if (i === index) { d.style.background = facet.color; d.style.boxShadow = `0 0 12px ${facet.color}`; }
      else { d.style.background = "transparent"; d.style.boxShadow = "none"; }
    });
    if (index === shown) return;
    shown = index;
    idxEl.textContent = String(index + 1).padStart(2, "0");
    titleEl.textContent = facet.title;
    descEl.textContent = facet.blurb;
    tagsEl.innerHTML = "";
    facet.tags.forEach((t) => { const li = document.createElement("li"); li.textContent = t; tagsEl.appendChild(li); });
  }
  return { update };
}

export function initFooterMorph(particles) {
  const footer = document.getElementById("contact");
  if (footer) footer.addEventListener("mouseenter", () => particles.setMorph("dome"));
  document.querySelectorAll("[data-morph]").forEach((a) => {
    a.addEventListener("mouseenter", () => particles.setMorph(a.dataset.morph));
    a.addEventListener("focus", () => particles.setMorph(a.dataset.morph));
  });
}

export function initSound() {
  const btn = document.getElementById("soundToggle");
  if (!btn) return;
  btn.classList.add("is-muted");
  let ctx, master, playing = false;
  function build() {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    master = ctx.createGain(); master.gain.value = 0.0;
    const filter = ctx.createBiquadFilter(); filter.type = "lowpass"; filter.frequency.value = 900;
    filter.connect(master); master.connect(ctx.destination);
    [110, 164.81, 220, 277.18].forEach((f, i) => {
      const o = ctx.createOscillator(); o.type = i % 2 ? "sine" : "triangle";
      o.frequency.value = f; o.detune.value = (Math.random() - 0.5) * 8;
      const g = ctx.createGain(); g.gain.value = 0.16 / (i + 1);
      const lfo = ctx.createOscillator(); lfo.frequency.value = 0.05 + i * 0.03;
      const lg = ctx.createGain(); lg.gain.value = 0.06;
      lfo.connect(lg); lg.connect(g.gain); lfo.start();
      o.connect(g); g.connect(filter); o.start();
    });
  }
  btn.addEventListener("click", () => {
    if (!ctx) build();
    ctx.resume(); playing = !playing;
    btn.classList.toggle("is-muted", !playing);
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.linearRampToValueAtTime(playing ? 0.6 : 0.0, ctx.currentTime + 1.2);
  });
}

export function setYear() {
  const y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
}
