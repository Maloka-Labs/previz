/* =========================================================
   SCROLL — Lenis smooth scroll drives camera progress and
   feeds scroll velocity into the chromatic-aberration pass.
   ========================================================= */
import { FACETS } from "./config.js";

const FACET_BAND = [0.3, 0.74];

export function initScroll(world, { onProgress } = {}) {
  const Lenis = window.Lenis;
  const lenis = new Lenis({ smoothWheel: true, lerp: 0.085, wheelMultiplier: 0.9 });

  function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);

  let limit = 1;
  lenis.on("scroll", ({ scroll, limit: lim, velocity }) => {
    limit = lim || 1;
    const p = scroll / limit;
    world.setProgress(p);
    world.setVelocity(velocity);
    if (onProgress) onProgress(p);
  });

  if (window.gsap && window.ScrollTrigger) {
    window.gsap.registerPlugin(window.ScrollTrigger);
    lenis.on("scroll", window.ScrollTrigger.update);
  }

  function scrollToFacet(i) {
    const [b0, b1] = FACET_BAND;
    const p = b0 + ((i + 0.5) / FACETS.length) * (b1 - b0);
    lenis.scrollTo(p * limit, { duration: 1.4 });
  }
  return { lenis, scrollToFacet };
}
