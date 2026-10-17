// "Forgot password?" on a running site: English and Arabic, 1440px and 390px, with screenshots.
//   - /login links to the request page; both new forms post (method="post")
//   - asking for a link answers "Check your email" (for any address: the API never says which exist)
//   - /reset-password without its token, or with a used or expired one, says so and offers a new link
//   - the new password must be typed twice the same
//   - with RESET_MINT: a fresh test account sets a new password through a real link. That browser
//     is signed in, the account's other session is ended, the old password is refused, and the
//     link is refused a second time.
//
//   BASE_URL=http://localhost:3201 RESET_MINT="<command>" node scripts/check-reset.mjs [folder]
//
// RESET_MINT is a command that prints a reset token for the @example.com test account given as
// its last argument, by writing one row in that server's password_resets table (the link's email
// itself is not needed). Without it the real-link part is skipped. Screenshots go to
// docs/screenshots/<folder> (default password-reset).
import { execSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const MINT = process.env.RESET_MINT;
const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(here, "../../docs/screenshots", process.argv[2] ?? "password-reset");
const httpCredentials = process.env.STAGING_AUTH
  ? (([username, ...rest]) => ({ username, password: rest.join(":") }))(process.env.STAGING_AUTH.split(":"))
  : undefined;
const text = Object.fromEntries(
  await Promise.all(
    ["en", "ar"].map(async (l) => [l, JSON.parse(await readFile(path.join(here, "../messages", `${l}.json`), "utf8")).auth]),
  ),
);

const failures = [];
const check = (ok, label, detail = "") => {
  console.log(`${ok ? "PASS" : "FAIL"}  ${label}${!ok && detail ? `\n        ${detail}` : ""}`);
  if (!ok) failures.push(label);
};
const attempt = async (label, fn) => {
  try {
    await fn();
    check(true, label);
  } catch (e) {
    check(false, label, String(e.message).split("\n")[0].slice(0, 200));
  }
};

// Through the tunnel there is no nginx, so every browser would count as one visitor (127.0.0.1)
// in the API's rate limits. Each context claims its own documentation address (RFC 5737).
let visitor = 10;
const contextFor = (viewport, phone) =>
  browser.newContext({
    viewport,
    deviceScaleFactor: 1,
    isMobile: phone,
    hasTouch: phone,
    httpCredentials,
    extraHTTPHeaders: { "X-Real-IP": `198.51.100.${visitor++}` },
  });
// Next keeps the page it left mounted but hidden (React <Activity>): only visible elements count.
const shown = (locator) => locator.filter({ visible: true });
const input = (p, name) => shown(p.locator(`input[name="${name}"]`));
const stamp = Date.now();
const OLD = "the old test password";
const NEW = "the new test password";

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });

for (const locale of ["en", "ar"]) {
  for (const [width, viewport] of [["1440", { width: 1440, height: 900 }], ["390", { width: 390, height: 844 }]]) {
    const t = text[locale];
    const prefix = locale === "ar" ? "/ar" : "";
    const tag = `${locale} ${width}px`;
    const context = await contextFor(viewport, width === "390");
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message.slice(0, 140)));
    const shot = async (name) => {
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: path.join(outDir, `${name}-${locale}-${width}.png`) });
    };
    const formPosts = async () => (await shown(page.locator("form")).getAttribute("method")) === "post";

    await attempt(`${tag}: /login links to "${t.forgotLink}", which opens the request page`, async () => {
      await page.goto(`${BASE_URL}${prefix}/login`, { waitUntil: "networkidle" });
      await shot("login");
      await page.getByRole("link", { name: t.forgotLink }).click();
      await page.waitForURL((u) => u.pathname === `${prefix}/forgot-password`, { timeout: 15000 });
      await page.getByRole("heading", { name: t.forgot.title }).waitFor();
      if (!(await formPosts())) throw new Error("the request form does not post");
      await shot("forgot");
    });

    await attempt(`${tag}: asking for a link answers "${t.forgot.sentTitle}"`, async () => {
      await input(page, "email").fill(`nobody-${stamp}@example.com`);
      await page.getByRole("button", { name: t.forgot.cta }).click();
      await page.getByRole("heading", { name: t.forgot.sentTitle }).waitFor({ timeout: 15000 });
      await shot("forgot-sent");
    });

    await attempt(`${tag}: /reset-password without its token says so and offers a new link`, async () => {
      await page.goto(`${BASE_URL}${prefix}/reset-password`, { waitUntil: "networkidle" });
      await shown(page.getByText(t.reset.missing)).waitFor();
      await page.getByRole("link", { name: t.reset.newLink }).waitFor();
      await shot("reset-missing");
    });

    await attempt(`${tag}: passwords that differ are refused; an unknown link is "expired or used"`, async () => {
      await page.goto(`${BASE_URL}${prefix}/reset-password#token=${randomBytes(32).toString("base64url")}`, { waitUntil: "networkidle" });
      if (!(await formPosts())) throw new Error("the new-password form does not post");
      await input(page, "password").fill(NEW);
      await input(page, "confirm").fill(`${NEW}!`);
      await page.getByRole("button", { name: t.reset.cta }).click();
      await shown(page.getByText(t.reset.mismatch)).waitFor();
      await input(page, "confirm").fill(NEW);
      await page.getByRole("button", { name: t.reset.cta }).click();
      await shown(page.getByText(t.reset.expired)).waitFor({ timeout: 15000 });
      await shot("reset-expired");
    });

    if (MINT) {
      const email = `reset-${stamp}-${locale}-${width}@example.com`;
      const other = await contextFor(viewport, width === "390");
      const fresh = await other.newPage();
      fresh.on("pageerror", (e) => errors.push(e.message.slice(0, 140)));
      const api = (p, data) =>
        fresh.request.post(`${BASE_URL}/api/v1/auth/${p}`, { data, headers: { Origin: BASE_URL } }).then((r) => r.status());
      await attempt(`${tag}: a real link sets the new password and ends the account's other session`, async () => {
        // The account and its first session, in the first browser.
        const signup = await page.request.post(`${BASE_URL}/api/v1/auth/signup`, {
          data: { email, password: OLD, accept_terms: true, locale },
          headers: { Origin: BASE_URL },
        });
        if (signup.status() !== 200) throw new Error(`sign-up answered ${signup.status()}`);
        const token = execSync(`${MINT} ${email}`, { encoding: "utf8" }).trim().split("\n").pop();
        await fresh.goto(`${BASE_URL}${prefix}/reset-password#token=${token}`, { waitUntil: "networkidle" });
        await input(fresh, "password").fill(NEW);
        await input(fresh, "confirm").fill(NEW);
        await fresh.evaluate(() => document.fonts.ready);
        await fresh.screenshot({ path: path.join(outDir, `reset-form-${locale}-${width}.png`) });
        await fresh.getByRole("button", { name: t.reset.cta }).click();
        await fresh.getByRole("heading", { name: t.reset.doneTitle }).waitFor({ timeout: 15000 });
        await fresh.evaluate(() => document.fonts.ready);
        await fresh.screenshot({ path: path.join(outDir, `reset-done-${locale}-${width}.png`) });
        const me = async (p) => (await (await p.request.get(`${BASE_URL}/api/v1/auth/me`)).json()).user?.email ?? null;
        if ((await me(fresh)) !== email) throw new Error("the browser that set the password is not signed in");
        if ((await me(page)) !== null) throw new Error("the account's other session is still signed in");
        const [oldLogin, newLogin] = [await api("login", { email, password: OLD }), await api("login", { email, password: NEW })];
        if (oldLogin !== 403 || newLogin !== 200) throw new Error(`sign-in: old password ${oldLogin}, new ${newLogin}`);
        await fresh.goto(`${BASE_URL}${prefix}/forgot-password`, { waitUntil: "domcontentloaded" }); // a fresh page load
        await fresh.goto(`${BASE_URL}${prefix}/reset-password#token=${token}`, { waitUntil: "networkidle" });
        await input(fresh, "password").fill(`${NEW} again`);
        await input(fresh, "confirm").fill(`${NEW} again`);
        await fresh.getByRole("button", { name: t.reset.cta }).click();
        await shown(fresh.getByText(t.reset.expired)).waitFor({ timeout: 15000 });
      });
      await other.close();
    }

    check(errors.length === 0, `${tag}: no page errors`, errors.slice(0, 3).join(" | "));
    await context.close();
  }
}

await browser.close();
console.log(`\nscreenshots: ${path.relative(process.cwd(), outDir)}`);
console.log(failures.length ? `\nForgot password: ${failures.length} check(s) failed` : "\nForgot password: all checks passed");
process.exit(failures.length ? 1 : 0);
