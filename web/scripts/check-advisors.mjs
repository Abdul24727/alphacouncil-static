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
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { chromium } from "playwright-core";

import { ADVICE } from "./lib/advice.mjs";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3201";
const OUT = process.env.OUT ?? "../docs/screenshots/advisors";
const TICKER = process.env.TICKER ?? "2222";
const LOCALES = (process.env.LOCALES ?? "en,ar").split(",");
// QUESTION_EN / QUESTION_AR ask something else, so one run can be a `choice` session and the next an `open` one;
// MODE says which the brief is expected to be, and the brief is checked against it (engine.MODES).
const QUESTIONS = {
  en: process.env.QUESTION_EN ?? "Is the dividend covered by earnings, and how safe is it?",
  ar: process.env.QUESTION_AR ?? "هل تغطي الأرباح التوزيعات، وما مدى أمانها؟",
};
const MODE = process.env.MODE ?? null;
const STAGES = ["brief", "openings", "faultlines", "debate", "final", "verdict"];
// What counts as advice on screen, with the sentences it was measured on: scripts/lib/advice.mjs
// What the Chair is asked for (engine.CHAIR_WORDS), and what round one is REPORTED against. The reporting
// threshold is deliberately looser than the 200-300 the seats are asked for: the room writes about a fifth
// past whatever ceiling it is given, so at 200-300 this line named 5 or 6 of 6 every single run and would
// have hidden a real change, and raising the ask instead simply moved the writing up with it
// (docs/beta-advisors-2026-10-27.md, F-2). An answer outside it is kept whole and reported, never cut.
const ANSWER_REPORT = [200, 400];
const CHAIR_WORDS = [200, 350];

// Each seat is answerable for part of the pack (advisors/<id>.md, `owns`), and round one is the
// only step where a seat writes without replying to anyone, so it is the step where citing none of
// your own datasets means your part of the evidence went unread. Reported, never failed: a seat may
// honestly find its evidence absent for this company, and saying so covers the mandate.
const MANDATES = Object.fromEntries(
  await Promise.all(
    (await readdir("../api/app/advisors"))
      .filter((f) => f.endsWith(".md") && f !== "README.md" && f !== "chair.md")
      .map(async (f) => {
        const text = await readFile(`../api/app/advisors/${f}`, "utf8");
        const owns = /^owns:\s*(.+)$/m.exec(text)?.[1] ?? "";
        return [f.replace(/\.md$/, ""), owns.split(",").map((t) => t.trim()).filter(Boolean)];
      }),
  ),
);

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

/**
 * The three-round format on screen (PROJECT.md Step 23): round 1 full answers, round 2 challenges,
 * round 3 final words with "what changed", and the Chair's complete answer. Reads each stage's own tab.
 */
async function formatChecks(page, locale, standIn) {
  const open = async (stage) => {
    await page.locator(`[data-stage-tab=${stage}]`).click();
    await page.locator(`[data-stage-view=${stage}]`).waitFor();
    await page.waitForTimeout(250);
  };
  const words = (s) => s.replace(/\[(?:P\d+|DB)\]/g, " ").split(/\s+/).filter(Boolean).length;
  // A seat whose reply could not be used three times is marked absent and the room carries on without it
  // (engine.turn). Every round is meant to be a full answer from everyone, so an absence is reported
  // here rather than counted as an answer: the turn card is there either way.
  const roundTurns = async (stage) => {
    const present = [];
    const away = [];
    for (const card of await page.locator(`[data-turn^="${stage}:"]`).all()) {
      const seat = ((await card.getAttribute("data-turn")) ?? ":").split(":")[1];
      const absent = card.locator("[data-absent]");
      if (await absent.count()) away.push(`${seat}: ${await absent.first().getAttribute("data-absent")}`);
      else {
        const text = await card.innerText();
        present.push([seat, words(text), [...new Set([...text.matchAll(/\[(P\d+|DB)\]/g)].map((m) => m[1]))]]);
      }
    }
    return { present, away, total: present.length + away.length };
  };
  const answered = (stage, { away, total }) => {
    check(total >= 3, `${locale}: ${stage} is a turn from each advisor (${total})`);
    check(away.length === 0, `${locale}: every advisor answered ${stage}${away.length ? ` — away: ${away.join("; ")}` : ""}`);
  };

  // The brief's mode, off the "On the table" card (Stage.tsx OnTheTable): `choice` lists the readings with
  // each one's count of final leans, `open` lists the things the room must weigh instead. Not the transcript
  // panel — `data-stage-view` is Transcript.tsx, which carries neither.
  const options = await page.locator("[data-on-table] [data-option]").count();
  const mode = options ? "choice" : "open";
  note(`INFO  ${locale}: the brief is a \`${mode}\` session (${options} options)`);
  if (MODE) check(mode === MODE, `${locale}: the brief is a \`${MODE}\` session as asked (${mode})`);
  if (mode === "choice") {
    check(options >= 2 && options <= 4, `${locale}: a choice session frames two to four options (${options})`);
    // Where a choice session lands is the engine's arithmetic (engine.count_leans), never a model's say-so:
    // each option carries its own tally of the advisors who leaned to it, so read them off the screen.
    const counted = await Promise.all(
      (await page.locator("[data-on-table] [data-option] [data-tally]").all()).map(async (e) =>
        Number(await e.getAttribute("data-tally")),
      ),
    );
    check(
      counted.length === options && counted.some((n) => n > 0),
      `${locale}: every option carries its count of final leans (${counted.join(", ")})`,
    );
  } else {
    const focus = await page.locator("[data-on-table] [data-focus-list] li").count();
    check(focus >= 2 && focus <= 4, `${locale}: an open session lists the two to four things to weigh (${focus})`);
  }

  await open("openings");
  const r1 = await roundTurns("openings");
  answered("round 1", r1);
  const lengths = r1.present.map(([, n]) => n);
  // The stand-in writes one sentence per seat on purpose, so only a model's answers can be full ones.
  if (standIn) note(`INFO  ${locale}: stand-in room, so round 1 lengths are not checked (${lengths.join(", ")} words)`);
  else
    check(
      lengths.length > 0 && lengths.every((n) => n >= 120),
      `${locale}: round 1 answers are full, not openings (${lengths.join(", ")} words)`,
    );
  // Over the band is kept whole and reported, never cut (Step 23's rule): name the seats so a prompt that
  // runs long in one language shows up as that, rather than as a number with no owner.
  const outside = r1.present.filter(([, n]) => n < ANSWER_REPORT[0] || n > ANSWER_REPORT[1]);
  note(
    `INFO  ${locale}: round 1 answers outside ${ANSWER_REPORT.join("–")} words: ${outside.length} of ${r1.present.length}` +
      (outside.length ? ` (${outside.map(([s, n]) => `${s} ${n}`).join(", ")})` : ""),
  );
  // Mandate coverage, per seat and then for the room. A seat that cited none of its own datasets is
  // named; the room's line says which parts of the evidence no seat reached for at all, which is the
  // thing a room of seven seats arguing from the same three figures would show up as.
  const uncovered = r1.present
    .map(([seat, , tags]) => [seat, (MANDATES[seat] ?? []).filter((t) => !tags.includes(t))])
    .filter(([, missing]) => missing.length);
  note(
    `INFO  ${locale}: round 1 seats not citing their own datasets: ${uncovered.length} of ${r1.present.length}` +
      (uncovered.length ? ` (${uncovered.map(([s, m]) => `${s} missing ${m.join("/")}`).join(", ")})` : ""),
  );
  const reached = new Set(r1.present.flatMap(([, , tags]) => tags));
  const owned = [...new Set(r1.present.flatMap(([seat]) => MANDATES[seat] ?? []))];
  const unread = owned.filter((t) => !reached.has(t));
  note(
    `INFO  ${locale}: datasets some seat is answerable for that round 1 never cited: ` +
      (unread.length ? unread.join(", ") : "none") + ` (of ${owned.length} owned)`,
  );

  await open("debate");
  const r2 = await roundTurns("debate");
  answered("round 2", r2);
  note(`INFO  ${locale}: advisors who conceded a point: ${await page.locator("[data-concedes]").count()}`);

  await open("final");
  const r3 = await roundTurns("final");
  answered("round 3", r3);
  const changed = await page.locator('[data-turn^="final:"] [data-changed]').count();
  check(
    changed === r3.present.length,
    `${locale}: every final word says what changed (${changed} of ${r3.present.length})`,
  );
  check((await page.locator("[data-vote-table]").count()) === 0, `${locale}: the final word carries no scores`);

  await open("verdict");
  const answer = (await page.locator("[data-answer]").textContent()) ?? "";
  check(answer.trim().length > 0, `${locale}: the Chair wrote the room's complete answer`);
  note(`INFO  ${locale}: the Chair's answer is ${words(answer)} words (asked for ${CHAIR_WORDS.join("–")})`);
  // DebateText splits a text on blank lines into paragraphs, so a long answer in one block is a wall of
  // text. It happened once: a system-prompt line reading "use no line breaks" flattened every long text
  // (2026-10-27). Reported, never failed — a short answer may honestly be one paragraph.
  const paras = await page.locator("[data-answer] p").count();
  note(`INFO  ${locale}: the Chair's answer is ${paras} paragraph(s)`);
  check(!ADVICE[locale].test(answer), `${locale}: the Chair's answer is an assessment, not advice`);
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
  // The stand-in room (no model key) answers in one sentence and in a second: some checks below are a model's.
  const standIn = (await (await ctx.request.get(`${BASE_URL}/api/v1/debate/status`)).json()).stand_in === true;
  if (standIn) note(`INFO  ${locale}: the room is the labelled stand-in, not a model`);
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
      failed:
        document.querySelector("[data-round-card]")?.getAttribute("data-room-status") === "failed" ||
        /stopped|توقفت/i.test(document.querySelector("[data-round-card]")?.textContent ?? ""),
      writing: document.querySelectorAll("[data-seat][data-writing]").length,
      speaking: [...document.querySelectorAll("[data-seat][data-speaking]")].map((e) => e.getAttribute("data-seat")),
    }));
    if (state.speaking.length > 1) check(false, `${locale}: one speaker at a time (${state.speaking.join(", ")})`);
    for (const s of state.speaking) {
      if (s !== "chair" && ![...speakers].some((x) => x !== "chair")) await shot(page, `speaking-${locale}-1440`);
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
  const verdict = page.locator("[data-verdict]");
  const arrived = (await verdict.count()) === 1;
  check(arrived, `${locale}: the verdict arrived (${seconds.toFixed(0)} s on screen)`);
  // A session can fail (a seat unreachable, the Chair unusable) and the room says so on screen. Report it with
  // what the room shows and move on: everything below reads the verdict, and waiting for one that will never
  // come threw an uncaught timeout that killed the whole run and lost the other locale's findings too
  // (F-9, 2026-10-27). Same lesson as F-4 — do not assume the happy path.
  if (!arrived) {
    const said = ((await page.locator("[data-round-card]").textContent()) ?? "").replace(/\s+/g, " ").trim();
    note(`INFO  ${locale}: the session did not finish, so the checks below it were skipped — the room says: ${said.slice(0, 200)}`);
    await shot(page, `failed-${locale}-1440`);
    await ctx.close();
    return null; // the caller skips the replay: there is no finished session to replay
  }
  // A stand-in session is over in about a second, so nothing can be caught mid-round: only a model's can.
  if (standIn) note(`INFO  ${locale}: stand-in room, so the live rounds are not followed (${seconds.toFixed(0)} s)`);
  else {
    check(speakers.size >= 3, `${locale}: lines played in turn (${[...speakers].join(", ")})`);
    check(seen.size >= 4, `${locale}: saw the stages live (${[...seen].join(", ")})`);
  }
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

  await formatChecks(page, locale, standIn);

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
  if (state) await replayPhone(locale, state);
}

await browser.close();
await writeFile(`${OUT}/check-${process.env.VISITOR ? "visitor" : process.env.LOCKED ? "locked" : "sessions"}.txt`, report.join("\n") + "\n");
console.log(failures.length ? `\n${failures.length} FAILED` : "\nall passed");
process.exit(failures.length ? 1 : 0);
