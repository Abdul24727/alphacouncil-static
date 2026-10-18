// Accounts brought over from the old site (api/app/import_old.py) on a running site: English and
// Arabic, 1440px and 390px, with screenshots (docs/account-import.md).
//   - /login tells old-site members to choose "Forgot password?" once
//   - an imported account signs in with no password at all until one is set
//   - its new-password page asks for the registration acceptance, refuses to save without it,
//     then saves, signs this browser in and the new password works; name and language came along
//   - an account that brought its old acceptance is not asked again
//
//   BASE_URL=http://localhost:3201 RESET_MINT="<command>" IMPORTED=<prefix> node scripts/check-imported.mjs [folder]
//
// IMPORTED is the prefix given to scripts/made-up-old-accounts.py, whose accounts were imported
// with scripts/old-accounts.sh. RESET_MINT prints a reset token for the @example.com account given
// as its last argument (scripts/old-accounts.sh <site> mint), so no email is sent.
import { execSync } from "node:child_process";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3100";
const { RESET_MINT: MINT, IMPORTED } = process.env;
if (!MINT || !IMPORTED) {
  console.error("set RESET_MINT and IMPORTED (see the top of this file)");
  process.exit(2);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(here, "../../docs/screenshots", process.argv[2] ?? "account-import");
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

// Each context claims its own documentation address (RFC 5737) for the API's rate limits.
let visitor = 40;
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
const mint = (email) => execSync(`${MINT} ${email}`, { encoding: "utf8" }).trim().split("\n").pop();
const NEW = "the new test password";

const browser = await chromium.launch({ channel: "chrome" });
await mkdir(outDir, { recursive: true });

const runs = [
  ...["en", "ar"].flatMap((locale) => ["1440", "390"].map((width) => ({ locale, width, email: `${IMPORTED}-${locale}-${width}@example.com` }))),
  { locale: "en", width: "1440", email: `${IMPORTED}-accepted@example.com`, accepted: true },
];

for (const { locale, width, email, accepted } of runs) {
  const t = text[locale];
  const prefix = locale === "ar" ? "/ar" : "";
  const tag = `${locale} ${width}px${accepted ? " (old acceptance)" : ""}`;
  const name = accepted ? "accepted" : "imported";
  const viewport = width === "1440" ? { width: 1440, height: 900 } : { width: 390, height: 844 };
  const context = await contextFor(viewport, width === "390");
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message.slice(0, 140)));
  const shot = async (n) => {
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outDir, `${n}-${locale}-${width}.png`) });
  };
  const login = (password) =>
    page.request.post(`${BASE_URL}/api/v1/auth/login`, { data: { email, password }, headers: { Origin: BASE_URL } }).then((r) => r.status());
  const me = async () => (await (await page.request.get(`${BASE_URL}/api/v1/auth/me`)).json()).user;

  if (!accepted)
    await attempt(`${tag}: /login says "${t.oldSite}"`, async () => {
      await page.goto(`${BASE_URL}${prefix}/login`, { waitUntil: "networkidle" });
      await shown(page.getByText(t.oldSite)).waitFor();
      await shot("login");
    });

  await attempt(`${tag}: the imported account has no password that signs in`, async () => {
    for (const password of ["", "a guessed password", NEW]) {
      const status = await login(password);
      if (status !== 403) throw new Error(`sign-in answered ${status}`);
    }
  });

  await attempt(
    accepted
      ? `${tag}: the new-password page does not ask for the acceptance again; the password saves`
      : `${tag}: the new-password page asks for the acceptance, refuses without it, then saves`,
    async () => {
      await page.goto(`${BASE_URL}${prefix}/reset-password#token=${mint(email)}`, { waitUntil: "networkidle" });
      await input(page, "password").fill(NEW);
      await input(page, "confirm").fill(NEW);
      const box = input(page, "accept");
      if (accepted) {
        if (await box.count()) throw new Error("the acceptance is asked again");
      } else {
        await box.waitFor({ timeout: 15000 });
        await shot(`${name}-reset-form`);
        await page.getByRole("button", { name: t.reset.cta }).click();
        await shown(page.getByText(t.errors.terms)).waitFor();
        await shot(`${name}-reset-terms`);
        await box.check();
      }
      await page.getByRole("button", { name: t.reset.cta }).click();
      await page.getByRole("heading", { name: t.reset.doneTitle }).waitFor({ timeout: 15000 });
      await shot(`${name}-reset-done`);
    },
  );

  await attempt(`${tag}: signed in as the account, with its old name and language; the new password works`, async () => {
    const user = await me();
    if (user?.email !== email) throw new Error("this browser is not signed in as the account");
    if (user.display_name !== "Check Account" || user.locale !== locale)
      throw new Error(`name ${JSON.stringify(user.display_name)}, language ${user.locale}`);
    const status = await login(NEW);
    if (status !== 200) throw new Error(`sign-in with the new password answered ${status}`);
  });

  check(errors.length === 0, `${tag}: no page errors`, errors.slice(0, 3).join(" | "));
  await context.close();
}

await browser.close();
console.log(`\nscreenshots: ${path.relative(process.cwd(), outDir)}`);
console.log(failures.length ? `\nImported accounts: ${failures.length} check(s) failed` : "\nImported accounts: all checks passed");
process.exit(failures.length ? 1 : 0);
