#!/usr/bin/env bun
/**
 * Merge `packages/i18n/src/pending/*.json` into en.json and hi.json.
 *
 * The three apps are built independently, so they stage new keys in their own
 * pending file rather than all editing the two shared dictionaries — a shared
 * JSON file is the one place parallel work reliably collides. This script folds
 * them in, refuses a key that disagrees with an existing translation, and
 * deletes the pending files once they are merged.
 *
 * Pending shape:  { "my.key": { "en": "English", "hi": "Romanised Hindi" } }
 */
import { existsSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)), "..", "packages", "i18n", "src");
const pendingDir = join(src, "pending");

if (!existsSync(pendingDir)) {
  console.log("no pending/ directory — nothing to merge");
  process.exit(0);
}

const en = JSON.parse(readFileSync(join(src, "en.json"), "utf8"));
const hi = JSON.parse(readFileSync(join(src, "hi.json"), "utf8"));

const problems = [];
let added = 0;
let skipped = 0;

const files = readdirSync(pendingDir).filter((f) => f.endsWith(".json")).sort();
for (const file of files) {
  const entries = JSON.parse(readFileSync(join(pendingDir, file), "utf8"));
  for (const [key, value] of Object.entries(entries)) {
    const enText = typeof value === "string" ? value : value?.en;
    const hiText = typeof value === "string" ? value : value?.hi;
    if (!enText || !hiText) {
      problems.push(`${file}: "${key}" needs both en and hi`);
      continue;
    }
    if (key in en) {
      if (en[key] !== enText) {
        problems.push(
          `${file}: "${key}" already exists with a different English string ` +
            `(${JSON.stringify(en[key])} vs ${JSON.stringify(enText)}) — reuse the existing key or rename yours`,
        );
      } else {
        skipped += 1;
      }
      continue;
    }
    en[key] = enText;
    hi[key] = hiText;
    added += 1;
  }
}

if (problems.length) {
  console.error(`\n✖ ${problems.length} problem(s) merging pending keys:\n`);
  for (const p of problems) console.error("  " + p);
  process.exit(1);
}

const sortKeys = (o) => Object.fromEntries(Object.keys(o).sort().map((k) => [k, o[k]]));
writeFileSync(join(src, "en.json"), JSON.stringify(sortKeys(en), null, 2) + "\n");
writeFileSync(join(src, "hi.json"), JSON.stringify(sortKeys(hi), null, 2) + "\n");
rmSync(pendingDir, { recursive: true, force: true });

console.log(
  `✓ merged ${added} new key(s) from ${files.length} file(s) (${skipped} already present); ` +
    `${Object.keys(en).length} total`,
);
