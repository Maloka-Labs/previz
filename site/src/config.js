/* =========================================================
   CONFIG — the one file you edit to make this "yours".
   Each FACET below becomes one illuminated gem on the dome,
   the Wylde-Diamond mechanic: turn the dome, read a facet
   of the business. Add/remove/reorder freely — the dome and
   the side-nav rebuild themselves to match.
   ========================================================= */

export const FACETS = [
  { title: "Worldcraft", blurb: "Generative 3D worlds and spatial previs — turn a prompt into a navigable set for AI filmmakers.", tags: ["3D worlds", "previs", "ComfyUI"], color: "#ff7a3c" },
  { title: "Story Engine", blurb: "Narrative tooling: shot lists, storyboards and screenplay-to-sequence pipelines that keep the soul in the story.", tags: ["narrative", "storyboards", "pipeline"], color: "#ff5d8f" },
  { title: "The Atelier", blurb: "A design studio for brand worlds and immersive web — the place this very dome was grown.", tags: ["design", "brand", "web"], color: "#f4c95d" },
  { title: "Sound & Vision", blurb: "Generative scores, sound design and film — flower-power frequencies tuned for the deep field.", tags: ["music", "film", "audio"], color: "#2ec4b6" },
  { title: "The Greenhouse", blurb: "R&D for the ideas that don't fit a box yet. Experiments, prototypes, and beautiful dead-ends.", tags: ["research", "prototypes", "labs"], color: "#8fc06a" },
  { title: "Living Capital", blurb: "Ventures and an on-chain commons — patient, regenerative capital for builders and dreamers.", tags: ["ventures", "community", "on-chain"], color: "#8a5cff" },
  { title: "The Commons", blurb: "Residencies, open tools and a real community — the front porch of the dome, always unlatched.", tags: ["community", "open-source", "residency"], color: "#67b8ff" },
];

export const PALETTE = {
  ink: 0x0b0a14, haze: 0x1d1830, gold: 0xf4c95d, amber: 0xff9e3d,
  tangerine: 0xff7a3c, magenta: 0xff5d8f, violet: 0x8a5cff, teal: 0x2ec4b6,
  sky: 0x67b8ff, meadow: 0x8fc06a, meadowDeep: 0x37633f, cream: 0xf4efe3,
};

export const DROPCITY = [
  0xff7a3c, 0xff5d8f, 0xf4c95d, 0x2ec4b6, 0x8a5cff,
  0x67b8ff, 0x8fc06a, 0xff9e3d, 0xe85d75, 0x46b1a8,
];

export const DOME = { radius: 18, detail: 3 };
