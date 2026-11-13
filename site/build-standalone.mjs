/* Inlines CSS + bundle into single double-click-able HTML files.
   Usage:  node build-standalone.mjs   (after `npm run build`) */
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));
const read = (p) => fs.readFileSync(path.join(dir, p), "utf8");

const PAGES = [
  { html: "index.html", css: "styles/main.css", js: "dist/maloka.bundle.js", jsRef: "./dist/maloka.bundle.js", cssRef: "./styles/main.css", out: "Maloka-Dome.html" },
  { html: "camper.html", css: "styles/camper.css", js: "dist/camper.bundle.js", jsRef: "./dist/camper.bundle.js", cssRef: "./styles/camper.css", out: "Magical-Mystery-Tour.html" },
];

for (const p of PAGES) {
  let html = read(p.html);
  const css = read(p.css);
  const js = read(p.js).split("</script>").join("<\\/script>");
  html = html.replace(`<link rel="stylesheet" href="${p.cssRef}" />`, () => `<style>\n${css}\n</style>`);
  html = html.replace(`<script src="${p.jsRef}"></script>`, () => `<script>\n${js}\n</script>`);
  fs.writeFileSync(path.join(dir, p.out), html);
  console.log("wrote", p.out, "(" + (Buffer.byteLength(html) / 1024).toFixed(0) + " KB)");
}
