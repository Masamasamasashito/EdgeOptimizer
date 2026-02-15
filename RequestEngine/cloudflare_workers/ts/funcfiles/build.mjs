// build.mjs
//
// Build pipeline for Cloudflare Workers using esbuild.
// This script compiles TypeScript, bundles dependencies,
// and outputs a single JavaScript file optimized for the
// Cloudflare Workers runtime.

// ----------------------------------------------------------
// Edge Optimizer
// Request Engine for Cloudflare Workers
// 
// Crafted by Nishi Labo | https://4649-24.com
// ----------------------------------------------------------

import { build } from "esbuild";

await build({
  // Entry point for the Worker (TypeScript source file)
  entryPoints: ["src/worker.ts"],

  // Output location for the bundled Worker script
  outfile: "dist/worker.js",

  // Bundle all imported modules into a single file.
  // Cloudflare Workers do not have a filesystem, so bundling is required.
  bundle: true,

  // Output format: Cloudflare Workers use ES Modules.
  format: "esm",

  // Target environment: Workers run on a V8 isolate similar to a browser.
  platform: "browser",

  // JavaScript language target. ES2022 is fully supported by Workers.
  target: "esnext",

  // Disable all minification options.
  // This keeps the output readable and easier to debug.
  minify: false,
  minifyWhitespace: false,
  minifySyntax: false,
  minifyIdentifiers: false,

  // Remove all comments from the output, including license headers.
  // This keeps the final bundle clean and reduces noise.
  legalComments: "none",

  // Do not generate source maps.
  // Workers do not require them, and omitting them keeps the bundle smaller.
  sourcemap: false
});

// Build completion message
console.log("Build finished: dist/worker.js");


