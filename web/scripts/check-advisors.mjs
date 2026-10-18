// Advisors' debate room (components/debate, api/app/routers/debate.py). A new account convenes
// the advisors on one stock, in English and in Arabic: screenshots of every stage while it runs
// (1440 px) and of every stage replayed from Past sessions (1440 and 390 px), plus checks on the
// screen: disclaimer, citations, no advice words in the verdict, no sideways scroll, the time taken.
//
//   BASE_URL=http://localhost:3201 node scripts/check-advisors.mjs        # beta through the tunnel (everyone is Pro)
//   BASE_URL=http://localhost:3110 LOCKED=1 node scripts/check-advisors.mjs   # an API with BILLING_OPEN: the Free preview
//   BASE_URL=https://alphacouncil.tech VISITOR=1 node scripts/check-advisors.mjs  # signed out: no account, no session
//   BASE_URL=https://alphacouncil.tech EMAIL=... node scripts/check-advisors.mjs   # an existing Pro account (billing open)
//     EMAIL signs in instead of signing up (PASSWORD defaults to the checks' test password); on production the
//     account needs Pro first: `python -m app.billing grant <email> 1` (docs/production.md, Pro billing).
//
// Test accounts are advisors-<locale>-<time>@example.com (no email is sent to example.com).
import { mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3201";
const OUT = process.env.OUT ?? "../docs/screenshots/advisors";
const TICKER = process.env.TICKER ?? "2222";
const LOCALES = (process.env.LOCALES ?? "en,ar").split(",");
const QUESTIONS = {
  en: "Is the dividend covered by earnings, and how safe is it?",
  ar: "هل تغطي الأرباح التوزيعات، وما مدى أمانها؟",
};
const STAGES = ["brief", "openings", "faultlines", "debate", "vote", "verdict"];
const ADVICE = { en: /\b(buy|sell|hold)\b/i, ar: /(اشتر|بيع السهم|احتفظ|شراء السهم)/ };

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ channel: "chrome" });
const failures = [];
const report = [];
const check = (ok, label) => {
  const line = `${ok ? "PASS" : "FAIL"}  ${label}`;
  console.log(line);
  report.push(line);
  if (!ok) failures.push(label);
};
const note = (line) => {
  console.log(line);
  report.push(line);
};

async function context(width, storageState) {
  return browser.newContext({
    viewport: { width, height: width < 768 ? 844 : 900 },
    ...(width < 768 ? { isMobile: true, hasTouch: true } : {}),
    ...(storageState ? { storageState } : {}),
  });
}

async function signUp(page, email) {
  await page.goto(`${BASE_URL}/signup?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(email);
  await page.locator("input[type=password]:visible").fill("a long test password");
  await page.locator("input[type=checkbox]:visible").check();
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 });
}

const prefix = (locale) => (locale === "ar" ? "/ar" : "");

/** The room's own checks, on whatever it shows now. */
async function screenChecks(page, label) {
  const r = await page.evaluate(() => {
    const scroller = document.querySelector("[data-debate-room]")?.closest(".overflow-y-auto");
    return {
      sideways: Math.max(document.scrollingElement.scrollWidth - innerWidth, scroller ? scroller.scrollWidth - scroller.clientWidth : 0),
      disclaimer: document.querySelector("[data-debate-disclaimer]")?.textContent ?? "",
      cites: [...document.querySelectorAll("[data-cite]")].map((e) => e.textContent.trim()),
    };
  });
  check(r.sideways <= 0, `${label}: no sideways scroll (${r.sideways}px)`);
  check(/caricature|كاريكاتير/.test(r.disclaimer), `${label}: disclaimer on screen`);
  check(r.cites.every((c) => /^P\d$/.test(c)), `${label}: citation chips name a dataset (${r.cites.length})`);
}

/** A screenshot; `whole` grows the window to the room's height first (the app scrolls an inner pane, not the page). */
async function shot(page, name, whole = false) {
  const file = `${OUT}/${name}.png`;
  const size = page.viewportSize();
  if (whole) {
    const extra = await page.evaluate(() => {
      const scroller = document.querySelector("[data-debate-room]")?.closest(".overflow-y-auto");
      return scroller ? scroller.scrollHeight - scroller.clientHeight : 0;
    });
    if (extra > 0) await page.setViewportSize({ width: size.width, height: Math.min(size.height + extra, 9000) });
    await page.waitForTimeout(300);
  }
  await page.screenshot({ path: file, fullPage: whole });
  if (whole) await page.setViewportSize(size);
  console.log(`  ${file}`);
}

async function signIn(page, email, password) {
  await page.goto(`${BASE_URL}/login?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(email);
  await page.locator("input[type=password]:visible").fill(password);
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 });
}

async function convene(locale) {
  const ctx = await context(1440);
  const page = await ctx.newPage();
  if (process.env.EMAIL) await signIn(page, process.env.EMAIL, process.env.PASSWORD ?? "a long test password");
  else await signUp(page, `advisors-${locale}-${Date.now()}@example.com`);
  await page.goto(`${BASE_URL}${prefix(locale)}/t/${TICKER}/advisors`, { waitUntil: "networkidle" });
  await page.locator("[data-question-form]").waitFor({ timeout: 30000 });
  await page.waitForTimeout(800);
  await shot(page, `idle-${locale}-1440`);
  await screenChecks(page, `${locale} idle`);

  await page.locator("#debate-q").fill(QUESTIONS[locale]);
  const started = Date.now();
  await page.locator("[data-convene]").click();

  // Follow the session: one screenshot as each stage starts (seats writing), until the verdict lands.
  const seen = new Set();
  const speakers = new Set(); // seats that took the floor (Player.tsx), one line at a time
  while (Date.now() - started < 8 * 60_000) {
    const state = await page.evaluate(() => ({
      live: document.querySelector("[data-stage-tab][aria-current=step]")?.getAttribute("data-stage-tab") ?? null,
      done: !!document.querySelector("[data-verdict]"),
      failed: /stopped|توقفت/i.test(document.querySelector("[data-round-card]")?.textContent ?? ""),
      writing: document.querySelectorAll("[data-seat][data-writing]").length,
      speaking: [...document.querySelectorAll("[data-seat][data-speaking]")].map((e) => e.getAttribute("data-seat")),
    }));
    if (state.speaking.length > 1) check(false, `${locale}: one speaker at a time (${state.speaking.join(", ")})`);
    for (const s of state.speaking) {
      if (s !== "chair" && !speakers.size) await shot(page, `speaking-${locale}-1440`);
      speakers.add(s);
    }
    if (state.failed) break;
    if (state.live && !seen.has(state.live) && state.live !== "verdict") {
      seen.add(state.live);
      await page.waitForTimeout(state.live === "brief" ? 1500 : 2500);
      await shot(page, `live-${state.live}-${locale}-1440`);
    }
    if (state.done) break;
    await page.waitForTimeout(700);
  }
  const seconds = (Date.now() - started) / 1000;
  check(speakers.size >= 3, `${locale}: lines played in turn (${[...speakers].join(", ")})`);
  const verdict = page.locator("[data-verdict]");
  check((await verdict.count()) === 1, `${locale}: the verdict arrived (${seconds.toFixed(0)} s on screen)`);
  check(seen.size >= 4, `${locale}: saw the stages live (${[...seen].join(", ")})`);
  await page.waitForTimeout(1000);
  await shot(page, `live-verdict-${locale}-1440`);
  await shot(page, `verdict-${locale}-1440-full`, true);
  await screenChecks(page, `${locale} verdict 1440`);

  const headline = (await page.locator("[data-verdict] .headline").first().textContent()) ?? "";
  check(!ADVICE[locale].test(headline), `${locale}: verdict headline is an assessment, not advice ("${headline.trim()}")`);
  if (locale === "ar") check(/[؀-ۿ]/.test(headline), "ar: the verdict is in Arabic");
  const unverified = await page.locator("[data-unverified]").count();
  note(`INFO  ${locale}: figures marked as not found in the data: ${unverified}`);
  const took = await page.locator("[data-verdict]").textContent();
  note(`INFO  ${locale}: ${(took.match(/(Took|استغرقت) [\d:]+/) ?? ["time not shown"])[0]}`);

  // Every stage replayed at 1440 (whole page), from the stage tabs.
  for (const stage of STAGES) {
    await page.locator(`[data-stage-tab=${stage}]`).click();
    await page.locator(`[data-stage-view=${stage}]`).waitFor();
    await page.waitForTimeout(300);
    await shot(page, `stage-${stage}-${locale}-1440`, true);
  }
  const state = await ctx.storageState();
  await ctx.close();
  return state;
}

async function replayPhone(locale, state) {
  const ctx = await context(390, state);
  const page = await ctx.newPage();
  await page.goto(`${BASE_URL}${prefix(locale)}/t/${TICKER}/advisors`, { waitUntil: "networkidle" });
  await page.locator("[data-past-toggle]").click();
  await page.locator("[data-past-sessions] li button").first().click();
  await page.locator("[data-verdict]").waitFor({ timeout: 30000 });
  await page.waitForTimeout(800);
  await screenChecks(page, `${locale} 390`);
  // A saved session opens on its last line; "Play the debate" plays it again from the Chair's brief.
  await page.locator("[data-replay]").click();
  await page.waitForTimeout(400);
  const first = await page.locator("[data-seat][data-speaking]").getAttribute("data-seat");
  await page.waitForTimeout(3600);
  const next = await page.locator("[data-seat][data-speaking]").getAttribute("data-seat");
  const typed = (await page.locator("[data-speech-text]").textContent())?.length ?? 0;
  check(first === "chair" && next !== "chair" && typed > 0, `${locale} 390: "Play the debate" replays it in turn (${first}, then ${next}; ${typed} characters typed)`);
  await shot(page, `replay-${locale}-390`);
  for (const stage of STAGES) {
    await page.locator(`[data-stage-tab=${stage}]`).click();
    await page.locator(`[data-stage-view=${stage}]`).waitFor();
    await page.waitForTimeout(300);
    await shot(page, `stage-${stage}-${locale}-390`, true);
  }
  await ctx.close();
}

async function lockedPreview(locale) {
  for (const width of [1440, 390]) {
    const ctx = await context(width);
    const page = await ctx.newPage();
    await signUp(page, `advisors-free-${locale}-${Date.now()}@example.com`);
    await page.goto(`${BASE_URL}${prefix(locale)}/t/${TICKER}/advisors`, { waitUntil: "networkidle" });
    await page.locator("[data-debate-locked=pro]").waitFor({ timeout: 30000 });
    check((await page.locator("[data-convene]").count()) === 0, `${locale} ${width}: Free sees the locked preview, no Convene button`);
    await screenChecks(page, `${locale} locked ${width}`);
    await shot(page, `locked-${locale}-${width}`, width < 768);
    await ctx.close();
  }
}

/** Signed out: the room asks to sign in, the Council tab links to it, /pricing lists it under Pro. */
async function visitor(locale) {
  const status = await (await (await context(1440)).request.get(`${BASE_URL}/api/v1/debate/status`)).json();
  check(
    status.signed_in === false && status.stand_in === false && status.pro_limit === 20,
    `status: models ${status.models.advisors} / ${status.models.chair}, plan ${status.plan}, Pro limit ${status.pro_limit}`,
  );
  for (const width of [1440, 390]) {
    const ctx = await context(width);
    const page = await ctx.newPage();
    await page.goto(`${BASE_URL}${prefix(locale)}/t/${TICKER}/advisors`, { waitUntil: "networkidle" });
    await page.locator("[data-debate-locked]").waitFor({ timeout: 30000 });
    check((await page.locator("[data-convene]").count()) === 0, `${locale} ${width}: signed out, the room is locked`);
    await screenChecks(page, `${locale} visitor ${width}`);
    await shot(page, `visitor-${locale}-${width}`, width < 768);
    await page.goto(`${BASE_URL}${prefix(locale)}/t/${TICKER}/council`, { waitUntil: "networkidle" });
    const callout = page.locator("[data-advisors-callout] a");
    await callout.waitFor({ timeout: 30000 });
    check(!!(await callout.getAttribute("href"))?.endsWith(`/t/${TICKER}/advisors`), `${locale} ${width}: the Council tab links to the room`);
    await shot(page, `council-callout-${locale}-${width}`);
    await ctx.close();
  }
  const ctx = await context(1440);
  const page = await ctx.newPage();
  await page.goto(`${BASE_URL}${prefix(locale)}/pricing`, { waitUntil: "networkidle" });
  const text = (await page.locator("body").textContent()) ?? "";
  check(/advisors' room: 20 sessions|غرفة المستشارين: 20 جلسة/.test(text), `${locale}: /pricing lists the advisors' room under Pro`);
  await ctx.close();
}

for (const locale of LOCALES) {
  if (process.env.VISITOR) {
    await visitor(locale);
    continue;
  }
  if (process.env.LOCKED) {
    await lockedPreview(locale);
    continue;
  }
  const state = await convene(locale);
  await replayPhone(locale, state);
}

await browser.close();
await writeFile(`${OUT}/check-${process.env.VISITOR ? "visitor" : process.env.LOCKED ? "locked" : "sessions"}.txt`, report.join("\n") + "\n");
console.log(failures.length ? `\n${failures.length} FAILED` : "\nall passed");
process.exit(failures.length ? 1 : 0);
