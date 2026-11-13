/* Bundles each entry (+ three, gsap, lenis) into a CDN-free IIFE.
   Usage:  npm i && npm run build  */
import * as esbuild from "esbuild";
import { fileURLToPath } from "node:url";
import path from "node:path";

const dir = path.dirname(fileURLToPath(import.meta.url));
const ENTRIES = [
  { in: "src/entry.js", out: "dist/maloka.bundle.js" },
  { in: "src/camper-entry.js", out: "dist/camper.bundle.js" },
];

for (const e of ENTRIES) {
  await esbuild.build({
    entryPoints: [path.join(dir, e.in)],
    bundle: true, format: "iife", minify: true, target: ["es2019"],
    outfile: path.join(dir, e.out),
    nodePaths: [path.join(dir, "node_modules")],
    alias: { "three/addons": path.join(dir, "node_modules/three/examples/jsm") },
    logLevel: "error",
  });
  console.log("built", e.out);
}
