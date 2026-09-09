#!/usr/bin/env bun
/**
 * Generates dist/tokens.css (CSS custom properties with hex fallbacks) and
 * src/index.ts (typed token export) from src/tokens.json.
 * Run: bun run generate
 */
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const pkg = join(here, "..");
const tokens = JSON.parse(readFileSync(join(pkg, "src", "tokens.json"), "utf8"));

const cssVars = [];
const flatten = (node, prefix) => {
  for (const [key, val] of Object.entries(node)) {
    const name = `${prefix}-${toKebab(key)}`;
    if (val && typeof val === "object" && "value" in val) {
      cssVars.push(`  ${name}: ${val.fallback};`);
      cssVars.push(`  ${name}: ${val.value};`);
    } else if (val && typeof val === "object") {
      flatten(val, name);
    } else {
      cssVars.push(`  ${name}: ${val};`);
    }
  }
};
const toKebab = (s) => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();

flatten(tokens, "--sa");

const css = `/* AUTO-GENERATED from src/tokens.json — do not edit by hand.
   First declaration = hex fallback (older Android browsers), second = OKLCH. */
:root {
${cssVars.join("\n")}
}
`;

mkdirSync(join(pkg, "dist"), { recursive: true });
writeFileSync(join(pkg, "dist", "tokens.css"), css);

const ts = `// AUTO-GENERATED from src/tokens.json — do not edit by hand.
import tokensJson from "./tokens.json";
export const tokens = tokensJson;
export type Tokens = typeof tokens;
`;
writeFileSync(join(pkg, "src", "index.ts"), ts);

console.log(`tokens: wrote dist/tokens.css (${cssVars.length} declarations) + src/index.ts`);
