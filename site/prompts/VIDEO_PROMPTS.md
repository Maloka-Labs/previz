# 🎬 AI Video Prompt Pack (Kling / Higgsfield)

Both pages render their world **procedurally in real time**. This pack lets you layer
real AI-generated film on top. Generate on your own account, drop `.mp4`s in
`assets/video/`, and list them in `assets/video/manifest.json` — the site blends them
over the WebGL at chosen scroll ranges, and is a no-op when the manifest is empty.

## Shared style token — append to every prompt
```
STYLE: hyper-realistic cinematic, 1960s Drop City geodesic dome of hand-painted
rainbow panels, lush hyper-real summer wildflower meadow, golden-hour light, drifting
pollen, an interstellar nebula woven into the sky, anamorphic lens, subtle chromatic
aberration, volumetric god-rays, 35mm grain. 16:9.
NEGATIVE: text, watermark, snow, ice, winter, igloo, cartoon, low-res, distorted geometry.
```
Settings: 16:9, ~5s loopable; Kling *Image-to-Video* for control, Higgsfield slow *Push-in*/*Orbit*.

## Maloka Dome (v2)
- `hero.mp4` `0.00–0.16` `normal` — dome in a summer meadow, slow push-in, golden hour, pollen.
- `facets.mp4` `0.40–0.70` `screen` — extreme close orbit of painted facets, prismatic caustics.
- `cosmos.mp4` `0.78–1.00` `screen` — summer sky dissolving into a magenta/violet/teal nebula, dome glowing.

## Magical Mystery Tour (v2.5 — the camper)
- `van-hero.mp4` `0.00–0.16` `normal` — a psychedelic VW split-screen combi parked beside the rainbow
  geodesic dome in a summer meadow, "Magical Mystery Tour" energy, surfboard on the roof, slow dolly, golden hour.
- `road.mp4` `0.55–0.80` `screen` — POV down a sunlit country road, rainbow light streaks, flowers rushing past.
- `depart.mp4` `0.85–1.00` `screen` — the VW combi driving off toward a glowing Telegram-blue portal on the
  horizon at dusk, headlights blazing, star-trails, a paper-plane of light. Whisking away.

## Wiring
`assets/video/manifest.json`:
```json
{ "layers": [
  { "src": "./assets/video/van-hero.mp4", "range": [0.00,0.16], "blend": "normal", "max": 0.85 },
  { "src": "./assets/video/depart.mp4",   "range": [0.85,1.00], "blend": "screen", "max": 0.90 }
] }
```
Keep clips web-optimized (H.264, ~1080p, < ~6 MB). `screen` blend turns black-background clips into additive light.
