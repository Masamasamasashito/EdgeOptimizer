/**
 * ----------------------------------------------------------
 * Edge Optimizer
 * Request Engine for Cloudflare Workers
 *
 * Crafted by Nishi Labo | https://4649-24.com
 * ----------------------------------------------------------
 *
 * Entry point for the Cloudflare Worker.
 * Re-exports the handler from
 * RequestEngine/cloudflare_workers/global/funcfiles/src/_03_cf_worker_handler.ts
 *
 * Build: esbuild (RequestEngine/cloudflare_workers/global/funcfiles/build.mjs)
 * bundles all imports into dist/worker.js
 */

export { default } from "./_03_cf_worker_handler";
