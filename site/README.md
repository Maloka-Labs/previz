# Maloka Labs — Living Dome sites 🌸🛸🚐

Real-time WebGL2 scroll experiences with the visual DNA of [igloo.inc](https://www.igloo.inc/)
(scroll-scrubbed camera, assembling loader, procedural hero object, chromatic-aberration
transitions, morphing particle footer) re-skinned as **Drop City summer × interstellar
flower-power**. Stack: **Three.js · GSAP · Lenis · vanilla ES modules**, bundled locally.

Two pages:

- **`index.html` — The Dome (v2).** A geodesic Drop City dome in a summer meadow that
  dissolves into the cosmos; each gem is a facet of the business (the Wylde-Diamond mechanic).
- **`camper.html` — Magical Mystery Tour (v2.5).** The Camper recruitment narrative: a
  psychedelic **VW combi (GaiA)** parked beside the dome, parallax scrollytelling through the
  story, then the van **drives off to a glowing Telegram portal**. Content in `src/camper-content.js`.

## Run it

Libraries are **bundled locally** (`dist/*.bundle.js`) — no CDN, works offline.

- **Double-click:** open `Maloka-Dome.html` or `Magical-Mystery-Tour.html` (self-contained single files).
- **As a site:** `cd site && python3 -m http.server 8000` → open `http://localhost:8000/` or `/camper.html`.
  (ES-module sites must be served over http — a `file://` multi-file page won't run; the single files above are the exception.)

## Build (after editing `src/`)
```bash
cd site
npm install                 # three, gsap, lenis, esbuild (dev only)
npm run build               # → dist/maloka.bundle.js + dist/camper.bundle.js
node build-standalone.mjs   # → Maloka-Dome.html + Magical-Mystery-Tour.html
```

## Edit the content
- **v2 facets:** `src/config.js` → `FACETS[]`.
- **v2.5 camper copy / seats / CTA:** `src/camper-content.js` (incl. the **Telegram link** — set `TELEGRAM_URL`).

## Mobile
`world.js` detects mobile (iOS/Android, coarse pointer + small viewport) and drops to a light
tier — pixelRatio 1.5, no anti-aliasing, no shadows, fewer instances — so phone GPUs don't
run out of memory. A lost WebGL context falls back to the readable content + CTA.

## Structure (highlights)
```
src/
  world.js      Three.js stage: camera path, lights, bloom + RGB-shift, facets, van/rainbow/portal, quality tier
  van.js        procedural psychedelic VW combi (canvas paint, split screen, whitewalls, surfboard)
  dome.js meadow.js shaders.js particles.js   the summer⇄cosmos world
  main.js entry.js                v2 boot
  camper-main.js camper-entry.js camper-content.js parallax.js   v2.5 boot + scrollytelling
assets/  img (svg marks) · video (drop AI clips + manifest.json)
prompts/VIDEO_PROMPTS.md          ready-to-run Kling/Higgsfield prompts
```

## Optional AI video
Drop Kling/Higgsfield clips in `assets/video/`, list them in `manifest.json` — blended over
the WebGL at chosen scroll ranges. No-op when empty. See `prompts/VIDEO_PROMPTS.md`.

> This `site/` is self-contained and unrelated to the ComfyUI World Labs nodes in the repo root.
