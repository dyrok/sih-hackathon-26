#!/usr/bin/env bun
/**
 * Browser end-to-end smoke across all three surfaces.
 *
 * Everything here is a property a unit test cannot reach, because it needs a
 * real browser, a real network toggle, or the rendered DOM:
 *
 *   - a check-in completes in <= 3 taps with the network OFF, and the write
 *     lands in the IndexedDB outbox (ADR-0005, TC-601);
 *   - the outbox drains on reconnect and leaves nothing behind (TC-601);
 *   - the receipt screen shows a real audit event (FR-15, TC-404);
 *   - a counsellor cannot enter the commander console, and vice versa;
 *   - **no individual appears anywhere in the commander DOM**, on any screen —
 *     and the personnel-lookup trap answers 403 to a live, signed-in commander
 *     session, which is the attack a judge actually runs (ADR-0003, TC-401);
 *   - the app reflows at 320px and renders in Hindi.
 *
 * Prerequisites (the script checks and tells you):
 *   make seed && make api          # :8000
 *   make jawan / counsellor / commander   # :3100 / :3200 / :3300
 *
 * Run: `make e2e` (or `bun e2e/smoke.mjs`). Screenshots land in e2e/shots/.
 */
import { chromium } from "playwright-core";
import { existsSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const SHOTS = join(HERE, "shots");
mkdirSync(SHOTS, { recursive: true });

const API = process.env.SAARTHI_API ?? "http://127.0.0.1:8000";
const JAWAN = "http://127.0.0.1:3100";
const COUNSELLOR = "http://127.0.0.1:3200";
const COMMANDER = "http://127.0.0.1:3300";

function chromePath() {
  const cache = `${process.env.HOME}/Library/Caches/ms-playwright`;
  if (!existsSync(cache)) return null;
  const dir = readdirSync(cache).find((d) => d.startsWith("chromium-"));
  if (!dir) return null;
  for (const rel of [
    "chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    "chrome-mac/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
    "chrome-linux/chrome",
  ]) {
    const p = join(cache, dir, rel);
    if (existsSync(p)) return p;
  }
  return null;
}

const fails = [];
const ok = (name, cond, detail = "") => {
  console.log(`${cond ? "  ok  " : " FAIL "} ${name}${detail ? "  — " + detail : ""}`);
  if (!cond) fails.push(name);
};

async function reachable(url) {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    return res.ok || res.status < 500;
  } catch {
    return false;
  }
}

for (const [name, url] of [
  ["API", `${API}/health`],
  ["jawan", `${JAWAN}/login`],
  ["counsellor", `${COUNSELLOR}/login`],
  ["commander", `${COMMANDER}/login`],
]) {
  if (!(await reachable(url))) {
    console.error(`\n${name} is not answering at ${url}.\nStart everything first — see the header of this file.\n`);
    process.exit(2);
  }
}

const exe = chromePath();
if (!exe) {
  console.error("\nNo Playwright Chromium found. Install it with:  bunx playwright install chromium\n");
  process.exit(2);
}

const browser = await chromium.launch({ executablePath: exe });

/** Collect page errors, ignoring the ones this script deliberately causes. */
function watch(page, ignore = []) {
  const seen = [];
  const keep = (text) => !ignore.some((re) => re.test(text));
  page.on("console", (m) => {
    if (m.type() === "error" && keep(m.text())) seen.push(m.text());
  });
  page.on("pageerror", (e) => {
    if (keep(e.message)) seen.push("pageerror: " + e.message);
  });
  page.on("response", (r) => {
    const line = `${r.status()} ${r.url()}`;
    if (r.status() >= 400 && keep(line)) seen.push(line);
  });
  return seen;
}

const login = async (page, base, user) => {
  await page.goto(`${base}/login`, { waitUntil: "networkidle" });
  await page.locator('input[autocomplete="username"]').first().fill(user);
  await page.locator('input[type="password"]').first().fill("saarthi");
  await page.click('button[type="submit"]');
};

// ---------------------------------------------------------------------------
console.log("\njawan — offline-first, the receipt, Hindi, 320px");
// ---------------------------------------------------------------------------
{
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
    hasTouch: true,
  });
  const page = await ctx.newPage();
  // The offline phase below is deliberate, so its network noise is not a defect.
  const problems = watch(page, [/ERR_INTERNET_DISCONNECTED/, /Failed to fetch/]);
  const shot = (n) => page.screenshot({ path: join(SHOTS, `jawan-${n}.png`), fullPage: true });

  await login(page, JAWAN, "jawan.demo");
  await page.waitForURL(/\/roster/, { timeout: 20000 });
  await page.waitForTimeout(1500);
  await shot("01-roster");

  const home = await page.locator("body").innerText();
  ok("roster home renders HR data, not a mock note", /Next duty|Leave balance/.test(home));
  ok("no raw i18n key on the home screen", !/\b(home|roster|nav)\.[a-z]+\./i.test(home));

  await ctx.setOffline(true);
  const taps = [];
  await page.click("text=Start");
  await page.waitForTimeout(600);
  await shot("02-checkin-offline");
  await page.getByRole("button", { name: /Light$/ }).first().click();
  taps.push("emoji");
  const agree = page.locator('input[type="checkbox"]').first();
  if ((await agree.count()) && !(await agree.isChecked())) {
    await agree.check();
    taps.push("consent");
  }
  await page.getByRole("button", { name: /^Save$/ }).first().click();
  taps.push("save");
  await page.waitForTimeout(1200);
  await shot("03-saved-offline");

  const saved = await page.locator("body").innerText();
  ok("TC-601 · a check-in completes with zero network", /Saved|Checked in today/i.test(saved), `${taps.length} taps`);
  ok("F02 · the check-in is at most 3 taps", taps.length <= 3);
  ok("ADR-0005 · queued data is never error-styled", !/failed|error/i.test(saved));

  const readQueue = () =>
    page.evaluate(
      () =>
        new Promise((resolve) => {
          const req = indexedDB.open("saarthi-offline");
          req.onsuccess = () => {
            const tx = req.result.transaction("queue", "readonly").objectStore("queue").getAll();
            tx.onsuccess = () => resolve(tx.result.map((i) => i.table));
            tx.onerror = () => resolve(["<error>"]);
          };
          req.onerror = () => resolve(["<open-failed>"]);
        }),
    );
  const queued = await readQueue();
  ok("the offline write is in the IndexedDB outbox", queued.includes("checkin"), JSON.stringify(queued));

  await ctx.setOffline(false);
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForTimeout(4000);
  const left = await readQueue();
  ok("TC-601 · the outbox drains on reconnect", left.length === 0, `${left.length} left`);
  await shot("04-after-sync");

  await page.goto(`${JAWAN}/me/receipts`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await shot("05-receipts");
  const receipts = await page.locator("body").innerText();
  ok("FR-15 · the receipt header is the promise", /Your data\. Your right\./.test(receipts));
  ok("FR-15 · a real access event, or an honest empty state", /Counsellor|Welfare officer|No one has opened/.test(receipts));

  await page.goto(`${JAWAN}/me/consent`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await shot("06-consent");
  const consent = await page.locator("body").innerText();
  ok("FR-17 · every scope is separate", /Daily 10-second check-in/.test(consent) && /Battle buddy status/.test(consent));
  ok("FR-17 · withdrawal is stated as silent", /Command will not see it/.test(consent));

  await page.goto(`${JAWAN}/welfare/trend`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await shot("07-trend");
  ok("the personal trend says it is private", /Only you see this/.test(await page.locator("body").innerText()));

  await page.goto(`${JAWAN}/me/settings`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  const hindi = page.getByRole("radio", { name: /Hindi/i }).first();
  if (await hindi.count()) await hindi.click();
  await page.goto(`${JAWAN}/roster`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await shot("08-hindi");
  ok("TC-607 · Hindi renders across the home screen", /Aaj kaisa laga|Suvidhayein|Kalyan/.test(await page.locator("body").innerText()));

  await page.setViewportSize({ width: 320, height: 700 });
  await page.waitForTimeout(600);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  ok("no horizontal overflow at 320px", overflow <= 1, `${overflow}px`);
  await shot("09-320px");

  ok("no console errors or failed requests", problems.length === 0, problems.slice(0, 3).join(" | "));
  await ctx.close();
}

// ---------------------------------------------------------------------------
console.log("\ncounsellor — the door, the queue, the case");
// ---------------------------------------------------------------------------
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
  const page = await ctx.newPage();
  const problems = watch(page, [/\b40[13]\b/]);
  const shot = (n) => page.screenshot({ path: join(SHOTS, `counsellor-${n}.png`), fullPage: true });

  await login(page, COUNSELLOR, "jawan.demo");
  await page.waitForTimeout(1500);
  ok(
    "a jawan token cannot enter the counsellor console",
    /different console/i.test(await page.locator("body").innerText()) &&
      !(await page.evaluate(() => localStorage.getItem("saarthi.token"))),
  );
  await shot("01-wrongrole");

  await login(page, COUNSELLOR, "counsellor.a");
  await page.waitForURL(`${COUNSELLOR}/`, { timeout: 20000 });
  await page.waitForTimeout(2500);
  await shot("02-queue");
  const queue = await page.locator("body").innerText();
  ok("the queue renders cases or the honest empty state", /Case|No open cases/.test(queue));
  ok("the queue is never a bare score", !/^\s*\d{1,3}\s*$/m.test(queue));

  const firstCase = page.locator("a[href^='/case/']").first();
  if (await firstCase.count()) {
    await firstCase.click();
    await page.waitForTimeout(2500);
    await shot("03-case");
    const detail = await page.locator("body").innerText();
    ok("the case leads with evidence, not a number", /Why this case is here|Contributing factors/i.test(detail));
    ok("the name is hidden until two people unlock it", /hidden until two people/i.test(detail));
  } else {
    ok("a case exists to open", false, "the queue was empty — re-seed with `make reset`");
  }

  ok("no console errors or unexpected failed requests", problems.length === 0, problems.slice(0, 3).join(" | "));
  await ctx.close();
}

// ---------------------------------------------------------------------------
console.log("\ncommander — the firewall, from the browser's side");
// ---------------------------------------------------------------------------
{
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 } });
  const page = await ctx.newPage();
  // The two probes at the end are supposed to be refused.
  const problems = watch(page, [/\b40[13]\b/, /welfare\/personnel/, /\/risk\//]);
  const shot = (n) => page.screenshot({ path: join(SHOTS, `commander-${n}.png`), fullPage: true });

  await login(page, COMMANDER, "counsellor.a");
  await page.waitForTimeout(1500);
  ok(
    "a counsellor token cannot enter the commander console",
    /different console/i.test(await page.locator("body").innerText()) &&
      !(await page.evaluate(() => localStorage.getItem("saarthi.token"))),
  );
  await shot("01-wrongrole");

  await login(page, COMMANDER, "commander.3bn");
  await page.waitForURL(`${COMMANDER}/`, { timeout: 20000 });
  await page.waitForTimeout(2500);

  const INDIVIDUAL = ["ps_demo01", "ps_3bn", "ps_tiny", "CR-DEMO-01", "Demo Constable"];
  for (const path of ["/", "/morale", "/indicators", "/simulator", "/forecast", "/checkin"]) {
    await page.goto(COMMANDER + path, { waitUntil: "networkidle" });
    await page.waitForTimeout(1800);
    const html = await page.content();
    const found = INDIVIDUAL.filter((m) => html.includes(m));
    ok(`ADR-0003 · no individual in the DOM of ${path}`, found.length === 0, found.join(","));
    await shot("s" + path.replace(/\W/g, "_"));
  }

  await page.goto(`${COMMANDER}/simulator`, { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);
  const run = page.getByRole("button", { name: /Run projection/i }).first();
  if (await run.count()) {
    await run.click();
    await page.waitForTimeout(2500);
  }
  await shot("03-simulator");
  const sim = await page.locator("body").innerText();
  ok("ADR-0001 · the simulator says it is rules, not a model", /not a prediction model/i.test(sim));
  ok("the simulator shows its assumptions beside the result", /Assumptions used/i.test(sim));

  await page.goto(`${COMMANDER}/`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  const heat = await page.locator("body").innerText();
  ok("the heatmap states its data age", /Data as of/i.test(heat));
  ok("the firewall promise is on screen", /no screen, route or export/i.test(heat));

  // The attack a judge runs, from the console the commander is signed into.
  const probe = async (path) =>
    page.evaluate(async ([api, p]) => {
      const res = await fetch(api + p, {
        headers: { Authorization: "Bearer " + localStorage.getItem("saarthi.token") },
      });
      return res.status;
    }, [API, path]);
  ok("TC-401 · the personnel-lookup trap answers 403 to a live session", (await probe("/welfare/personnel/CR-DEMO-01")) === 403);
  ok("an individual score is refused to a live session", (await probe("/risk/ps_demo01")) === 403);
  ok("the case queue is refused to a live session", (await probe("/interventions/queue")) === 403);

  ok("no console errors or unexpected failed requests", problems.length === 0, problems.slice(0, 3).join(" | "));
  await ctx.close();
}

await browser.close();
console.log(
  fails.length === 0
    ? `\n✓ browser E2E clean — screenshots in ${SHOTS}\n`
    : `\n✖ ${fails.length} failed: ${fails.join(", ")}\n`,
);
process.exit(fails.length === 0 ? 0 : 1);
