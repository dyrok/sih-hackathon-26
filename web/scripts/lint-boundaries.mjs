#!/usr/bin/env bun
/**
 * Architectural lint. These rules are the ones that would be expensive to catch
 * in review and catastrophic to get wrong, so they run in CI:
 *
 *  1. Role isolation (design-client-apps.md §6) — an app may import only its own
 *     role's API client. The commander build importing `@saarthi/api/counsellor`
 *     is exactly the leak ADR-0003 exists to prevent.
 *  2. No individual-row component in the commander app (F07 definition of done).
 *  3. TrendLine (personal 90-day trend) exists only in apps/jawan.
 *  4. No hardcoded OKLCH outside @saarthi/tokens (design.md §2).
 *  5. No user-facing string literals in JSX — everything through i18n keys.
 *  6. en/hi key parity — a missing translation must fail the build, not fall
 *     back to English silently in the field.
 *  7. Contrast floors (design.md §9): 4.5:1 for text, 3:1 for a focus ring or
 *     any other meaningful non-text UI. A design system that states a floor and
 *     does not measure it drifts below it in one sprint — this one measured
 *     2.03:1 on the amber care chip before anybody looked.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const web = join(dirname(fileURLToPath(import.meta.url)), "..");
const problems = [];
const fail = (file, rule, detail) =>
  problems.push(`${relative(web, file)}: [${rule}] ${detail}`);

function walk(dir, out = []) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const name of entries) {
    if (name === "node_modules" || name === ".next" || name === "dist") continue;
    const full = join(dir, name);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (/\.(ts|tsx|mjs|css)$/.test(name)) out.push(full);
  }
  return out;
}

const ROLE_OF_APP = { jawan: "jawan", counsellor: "counsellor", commander: "commander" };
const ALL_ROLES = Object.values(ROLE_OF_APP);

// --- 1 + 2 + 3: per-app rules -------------------------------------------------
for (const [app, ownRole] of Object.entries(ROLE_OF_APP)) {
  const root = join(web, "apps", app);
  for (const file of walk(root)) {
    const src = readFileSync(file, "utf8");
    for (const role of ALL_ROLES) {
      if (role === ownRole) continue;
      if (src.includes(`@saarthi/api/${role}`)) {
        fail(file, "role-isolation", `imports @saarthi/api/${role} inside apps/${app}`);
      }
    }
    if (app === "commander") {
      // The firewall is a routing and component guarantee too, not only a
      // server rule: nothing in this build may address a person.
      for (const marker of ["pseudonym_id", "PersonRow", "IndividualRow", "legal_name", "personnel_id"]) {
        if (src.includes(marker)) {
          fail(file, "commander-no-individual", `mentions "${marker}" — the commander build has no individual shape`);
        }
      }
    }
    if (app !== "jawan" && /\bTrendLine\b/.test(src)) {
      fail(file, "trendline-jawan-only", "the personal TrendLine renders only in apps/jawan");
    }
  }
}

// --- 4: tokens are the only source of colour ---------------------------------
for (const file of walk(join(web, "apps")).concat(walk(join(web, "packages")))) {
  if (file.includes(join("packages", "tokens"))) continue;
  const src = readFileSync(file, "utf8");
  if (/oklch\(/i.test(src)) fail(file, "tokens-only", "hardcoded oklch() outside @saarthi/tokens");
}

// --- 5: no user-facing literals in JSX ---------------------------------------
// A literal that is pure punctuation, digits, or a known non-linguistic symbol
// is fine; a word is not.
// Heuristic: `>Word words<` with no operators between. Code expressions carry
// `=`, `(`, `;` or quotes, so excluding those keeps false positives near zero.
const JSX_TEXT = />(\s*[A-Za-z][^<>{}()=;"'`]{2,})</g;
const ALLOW = /^(?:[\s\d·×—–—.,:%/|()+-]|&[a-z]+;)*$/;
for (const file of walk(join(web, "apps")).concat(walk(join(web, "packages")))) {
  if (!file.endsWith(".tsx")) continue;
  const src = readFileSync(file, "utf8");
  for (const m of src.matchAll(JSX_TEXT)) {
    const text = m[1].trim();
    if (!text || ALLOW.test(text)) continue;
    // Comments and imports are not JSX text.
    if (text.startsWith("//") || text.startsWith("*")) continue;
    fail(file, "i18n-keys-only", `literal JSX text ${JSON.stringify(text.slice(0, 40))}`);
  }
}

// --- 7: contrast floors -------------------------------------------------------
// Ratios are computed from the hex FALLBACKS in tokens.json, which is what an
// older Android browser without oklch() actually paints.
function relLuminance(hex) {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt(h.slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a, b) {
  const [x, y] = [relLuminance(a), relLuminance(b)];
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
function tint(fg, bg, pct) {
  const [f, b] = [fg, bg].map((h) => h.replace("#", ""));
  return (
    "#" +
    [0, 2, 4]
      .map((i) => {
        const v = Math.round(parseInt(f.slice(i, i + 2), 16) * pct + parseInt(b.slice(i, i + 2), 16) * (1 - pct));
        return v.toString(16).padStart(2, "0");
      })
      .join("")
  );
}

const tokens = JSON.parse(readFileSync(join(web, "packages/tokens/src/tokens.json"), "utf8"));
const C = tokens.color;
const RAISED = C.surface.raised.fallback;
const BASE = C.surface.base.fallback;
const SOFT = C.brand.oliveSoft.fallback;

const TEXT_PAIRS = [
  ["ink on paper", C.ink.primary.fallback, BASE],
  ["secondary ink on paper", C.ink.secondary.fallback, BASE],
  ["secondary ink on card", C.ink.secondary.fallback, RAISED],
  ["olive on paper", C.brand.olive.fallback, BASE],
  ["olive on its own tint", C.brand.olive.fallback, SOFT],
  ["card text on olive", RAISED, C.brand.olive.fallback],
  ["text on the saffron CTA", C.accent.saffronInk.fallback, C.accent.saffron.fallback],
];
for (const [name, fg, bg] of ["green", "amber", "red", "critical"].map((s) => [
  `${s} care-chip label`,
  C.stateInk[s].fallback,
  tint(C.state[s].fallback, RAISED, s === "green" || s === "amber" ? 0.15 : 0.12),
])) {
  TEXT_PAIRS.push([name, fg, bg]);
}
for (const [name, fg, bg] of TEXT_PAIRS) {
  const r = contrast(fg, bg);
  if (r < 4.5) problems.push(`contrast: ${name} is ${r.toFixed(2)}:1, below the 4.5:1 text floor (design.md §9)`);
}

const NON_TEXT_PAIRS = [
  ["focus ring on a card", C.focus.fallback, RAISED],
  ["focus ring on paper", C.focus.fallback, BASE],
  ["focus ring on the olive tint", C.focus.fallback, SOFT],
  ...["green", "amber", "red", "critical"].map((s) => [
    `${s} care-chip border`,
    C.stateInk[s].fallback,
    RAISED,
  ]),
];
for (const [name, fg, bg] of NON_TEXT_PAIRS) {
  const r = contrast(fg, bg);
  if (r < 3) problems.push(`contrast: ${name} is ${r.toFixed(2)}:1, below the 3:1 non-text floor (design.md §6)`);
}

// --- 6: en/hi parity ----------------------------------------------------------
const en = JSON.parse(readFileSync(join(web, "packages/i18n/src/en.json"), "utf8"));
const hi = JSON.parse(readFileSync(join(web, "packages/i18n/src/hi.json"), "utf8"));
for (const k of Object.keys(en)) if (!(k in hi)) problems.push(`i18n: "${k}" missing from hi.json`);
for (const k of Object.keys(hi)) if (!(k in en)) problems.push(`i18n: "${k}" missing from en.json`);

// --- 7: every t("key") resolves ----------------------------------------------
// en.json and hi.json have one owner, so an app that needs a new string declares
// it in packages/i18n/src/pending/<app>.json ({key: {en, hi}}) and the owner
// merges it. A pending key is declared, not missing — anything absent from both
// is a typo and still fails.
const pendingDir = join(web, "packages/i18n/src/pending");
const pending = new Set();
let pendingFiles = [];
try {
  pendingFiles = readdirSync(pendingDir).filter((f) => f.endsWith(".json"));
} catch {
  // No pending directory means nothing is waiting to be merged.
}
for (const file of pendingFiles) {
  const entries = JSON.parse(readFileSync(join(pendingDir, file), "utf8"));
  for (const [key, value] of Object.entries(entries)) {
    if (typeof value?.en !== "string" || typeof value?.hi !== "string") {
      problems.push(`i18n pending/${file}: "${key}" needs both an en and a hi string`);
      continue;
    }
    if (key in en) problems.push(`i18n pending/${file}: "${key}" is already in en.json`);
    pending.add(key);
  }
}

const KEY_CALL = /\bt\(\s*"([a-zA-Z0-9._-]+)"/g;
const seen = new Set();
for (const file of walk(join(web, "apps")).concat(walk(join(web, "packages")))) {
  const src = readFileSync(file, "utf8");
  for (const m of src.matchAll(KEY_CALL)) {
    if (!(m[1] in en) && !pending.has(m[1])) fail(file, "unknown-i18n-key", m[1]);
    seen.add(m[1]);
  }
}

if (problems.length) {
  console.error(`\n✖ ${problems.length} boundary violation(s):\n`);
  for (const p of problems) console.error("  " + p);
  console.error("");
  process.exit(1);
}
console.log(
  `✓ boundaries clean — ${TEXT_PAIRS.length + NON_TEXT_PAIRS.length} contrast pairs, ${Object.keys(en).length} i18n keys (+${pending.size} pending), ${seen.size} referenced statically`,
);
