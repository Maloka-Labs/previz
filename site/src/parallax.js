/* =========================================================
   PARALLAX — gentle depth for decorative HTML layers.
   [data-parallax="0.15"] drifts by its distance from the
   viewport centre. Runs its own rAF on native scroll.
   ========================================================= */
export function initParallax() {
  const els = [...document.querySelectorAll("[data-parallax]")].map((el) => ({
    el, speed: parseFloat(el.dataset.parallax) || 0.1,
    rot: parseFloat(el.dataset.parallaxRot || "0"),
  }));
  if (!els.length) return;
  let vh = innerHeight;
  addEventListener("resize", () => { vh = innerHeight; }, { passive: true });
  function frame() {
    for (const o of els) {
      const r = o.el.getBoundingClientRect();
      const center = r.top + r.height / 2 - vh / 2;
      const y = -center * o.speed;
      const rot = o.rot ? center * o.rot : 0;
      o.el.style.transform = `translate3d(0, ${y.toFixed(1)}px, 0)` + (rot ? ` rotate(${rot.toFixed(2)}deg)` : "");
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
