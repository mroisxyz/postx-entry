import { copyFileSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

// Authored for the "post-x the agent builds a game" make.fun bounty.
// The destination is configurable, so create it recursively before writing.
// POST.json is optional; a valid placeholder keeps this program crash-free.
// Every message goes to stderr, leaving stdout clean for the harness.
// Only Node's standard library is used - no packages, no network calls.

const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const sourceDir = dirname(process.argv[1] ?? "");
const sourcePost = join(sourceDir, "POST.json");
const targetPost = join(outputDir, "POST.json");

mkdirSync(outputDir, { recursive: true });

if (existsSync(sourcePost)) {
  copyFileSync(sourcePost, targetPost);
  console.error(`[makefun] copied POST.json -> ${targetPost}`);
} else {
  writeFileSync(targetPost, JSON.stringify({ url: "" }) + "\n", "utf8");
  console.error(`[makefun] no POST.json found; wrote placeholder -> ${targetPost}`);
}

function describeOutput(outDir: string): string {
  return `output ready in ${outDir}`;
}

console.error(`[makefun] ${describeOutput(outputDir)}`);
