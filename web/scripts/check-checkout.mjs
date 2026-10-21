// Checkout in Moyasar TEST mode on beta, every case of PROJECT.md Step 16, through the tunnel.
// Beta only, test keys only (it stops unless the checkout hands out a pk_test_ key), Moyasar's
// published test cards only. Needs BILLING_OPEN=true and a MOYASAR_WEBHOOK_SECRET in beta's
// api.env (the runbook: "Pro billing (Moyasar)"), and SSH to the server for the server-side steps:
// confirming test addresses, delivering Moyasar's notifications (beta's password gate keeps
// Moyasar's own webhooks out), running the renewals job, and a test-mode refund.
//
//   BASE_URL=http://localhost:3201 OUT=../docs/screenshots/checkout-test-<date> node scripts/check-checkout.mjs
//
// Accounts: checkout-<case>-<time>@example.com (no email is sent to example.com).
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright-core";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3201";
const OUT = process.env.OUT ?? "../docs/screenshots/checkout-test";
const SSH = process.env.SSH ?? "root@alphacouncil.tech";
const ENV = "/etc/alphacouncil-platform/api.env"; // beta's
const API = "http://127.0.0.1:8200"; // beta's API on the server
const CARDS = { paid: "4111111111111111", declined: "4123120001090000" };

await mkdir(OUT, { recursive: true });
const results = [];
const record = (id, name, ok, evidence) => {
  results.push({ id, name, ok, evidence });
  console.log(`${ok ? "PASS" : "FAIL"}  ${id} ${name}${evidence?.note ? ` — ${evidence.note}` : ""}`);
};

/** Runs on the server; `stdin` is a script for python3 -I -. Secrets stay on the server. */
function server(cmd, stdin) {
  const r = spawnSync("ssh", [SSH, cmd], { input: stdin, encoding: "utf8", timeout: 180000 });
  if (r.status !== 0) throw new Error(`server: ${cmd.slice(0, 60)}: ${(r.stderr || r.stdout).slice(0, 200)}`);
  return r.stdout.trim();
}
const sql = (q) => server(`docker exec acp-postgres psql -U acp -d acp -tAc "${q.replace(/"/g, '\\"')}"`);
const READ_ENV = `
env = {}
for line in open("${ENV}"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.rstrip("\\n").split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
`;
/** Delivers a Moyasar notification to beta's API, as Moyasar would (its secret_token included). */
function webhook(type, paymentId) {
  return server(
    `python3 -I - ${type} ${paymentId}`,
    `import json, sys, urllib.request, urllib.error
${READ_ENV}
body = json.dumps({"type": sys.argv[1], "secret_token": env["MOYASAR_WEBHOOK_SECRET"], "data": {"id": sys.argv[2]}}).encode()
req = urllib.request.Request("${API}/v1/billing/webhook/moyasar", body, {"content-type": "application/json"})
try:
    r = urllib.request.urlopen(req, timeout=60); print(r.status, r.read().decode()[:80])
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode()[:80])
`,
  );
}
/** A full refund in Moyasar's TEST mode (what the owner would do in the dashboard). */
function refund(paymentId) {
  return server(
    `python3 -I - ${paymentId}`,
    `import base64, json, sys, urllib.request, urllib.error
${READ_ENV}
key = env.get("MOYASAR_SECRET_KEY", "")
if not key.startswith("sk_test_"):
    sys.exit("not a test key: refusing")
auth = base64.b64encode((key + ":").encode()).decode()
# Moyasar's edge refuses Python's default user agent (Cloudflare 1010); this is the app's own (app/http.py).
headers = {"content-type": "application/json", "authorization": "Basic " + auth, "user-agent": "AlphaCouncil/1.0 (+https://alphacouncil.tech)"}
req = urllib.request.Request(f"https://api.moyasar.com/v1/payments/{sys.argv[1]}/refund", b"{}", headers, method="POST")
try:
    r = urllib.request.urlopen(req, timeout=60); print(r.status, json.loads(r.read()).get("status"))
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode()[:120])
`,
  );
}
const renewNow = () => {
  server("systemctl start acp-billing.service");
  return server("journalctl -u acp-billing.service -n 20 --no-pager -o cat | grep -E '^reminded=' | tail -1");
};

const browser = await chromium.launch({ channel: "chrome" });
const context = (width) =>
  browser.newContext({ viewport: { width, height: width < 768 ? 844 : 900 }, ...(width < 768 ? { isMobile: true, hasTouch: true } : {}) });
const pre = (locale) => (locale === "ar" ? "/ar" : "");

/** A new account with its address confirmed (test addresses get no email; the database is told). */
async function newAccount(page, tag, locale) {
  const email = `checkout-${tag}-${Date.now()}@example.com`;
  await page.goto(`${BASE_URL}${pre(locale)}/signup?next=/home`, { waitUntil: "networkidle" });
  await page.locator("input[type=email]:visible").fill(email);
  await page.locator("input[type=password]:visible").fill("a long test password");
  await page.locator("input[type=checkbox]:visible").check();
  await page.locator("form:visible button[type=submit]").click();
  await page.waitForURL((u) => u.pathname.endsWith("/home"), { timeout: 30000 }).catch(async () => {
    // Sign-ups share the sign-in limit (10 per 15 minutes per address); the tunnel is one address.
    throw new Error(`sign-up did not finish: ${(await page.locator("form:visible").innerText()).replace(/\s+/g, " ").slice(0, 160)}`);
  });
  const id = sql(`UPDATE users SET email_verified_at = now() WHERE email = '${email}' AND email LIKE '%@example.com' RETURNING id`);
  return { email, id: id.split("\n")[0] };
}
const billing = async (page) => (await page.request.get(`${BASE_URL}/api/v1/billing`)).json();

/** Pays (or tries to) through Moyasar's form. threeDS: "Y" approve, "N" refuse. holdReturn: the browser
 *  "closes" after paying: the return page never loads, so only the notification can start Pro. */
async function pay(page, { locale, card, threeDS = "Y", holdReturn = false, shot }) {
  await page.goto(`${BASE_URL}${pre(locale)}/checkout`, { waitUntil: "networkidle" });
  await page.locator("[data-checkout] input[type=checkbox]").check();
  await page.getByRole("button", { name: /Continue to payment|المتابعة إلى الدفع/ }).click();
  const form = page.locator("[data-moyasar-form]");
  await form.locator("input").first().waitFor({ timeout: 30000 });
  if (shot) await page.screenshot({ path: `${OUT}/${shot}-form.png` });
  // Moyasar returns the browser to beta's public address (its site URL), which is behind the
  // password gate; this browser has no gate login, so the return goes through the tunnel instead.
  // holdReturn: the page never loads at all (the payer closed the browser).
  let held = null;
  await page.route(/\/billing\/return/, (route) => {
    const url = new URL(route.request().url());
    if (holdReturn) {
      held = url.href;
      return route.abort();
    }
    if (url.origin === new URL(BASE_URL).origin) return route.continue();
    return route.fulfill({ status: 302, headers: { location: `${BASE_URL}${url.pathname}${url.search}` } });
  });
  await form.locator("#mysr-cc-name").pressSequentially("Test Card");
  await form.locator("#mysr-cc-number").pressSequentially(card);
  await form.locator("#mysr-cc-exp").pressSequentially("1230");
  await form.locator("#mysr-cc-csc").pressSequentially("123");
  await form.locator("button[type=submit]").click();
  const deadline = Date.now() + 90000;
  while (Date.now() < deadline && !held && !/billing\/return|acs_emulator/.test(page.url())) await page.waitForTimeout(250);
  if (page.url().includes("acs_emulator")) {
    // Moyasar's 3-D Secure emulator stands in for the bank: "(Y)" approves, "(N)" refuses.
    const choice = page.locator("select#auth_result");
    const value = await choice.locator("option", { hasText: `(${threeDS})` }).first().getAttribute("value");
    await choice.selectOption(value);
    await page.getByRole("button", { name: "Submit" }).click();
    while (Date.now() < deadline && !held && !page.url().startsWith(`${BASE_URL}/billing/return`) && !page.url().startsWith(`${BASE_URL}/ar/billing/return`))
      await page.waitForTimeout(250);
  }
  if (holdReturn) {
    if (!held) throw new Error("the return page was never requested");
    return { id: new URL(held).searchParams.get("id"), held: true };
  }
  const id = new URL(page.url()).searchParams.get("id");
  await page
    .locator("[data-pro-started], main p[role=alert]")
    .first()
    .waitFor({ timeout: 60000 })
    .catch(async (e) => {
      await page.screenshot({ path: `${OUT}/${shot ?? "pay"}-stuck.png` });
      throw new Error(`no result on ${page.url()}: ${(await page.locator("body").innerText()).replace(/\s+/g, " ").slice(0, 300)} (${e.message.split("\n")[0]})`);
    });
  const paid = (await page.locator("[data-pro-started]").count()) > 0;
  const message = paid ? null : await page.locator("main p[role=alert]").innerText();
  if (shot) await page.screenshot({ path: `${OUT}/${shot}-return.png` });
  return { id, paid, message };
}

// Beta must hand out test keys, or nothing below runs.
{
  const ctx = await context(1440);
  const page = await ctx.newPage();
  const plans = await (await page.request.get(`${BASE_URL}/api/v1/plans`)).json();
  await newAccount(page, "keycheck", "en");
  const form = await (await page.request.post(`${BASE_URL}/api/v1/billing/checkout`, { data: { accept_terms: true }, headers: { Origin: BASE_URL } })).json();
  await ctx.close();
  const test = String(form.publishable_key ?? "").startsWith("pk_test_");
  record("0", "beta's checkout is open with Moyasar TEST keys", plans.checkout_open === true && test, { note: `checkout_open=${plans.checkout_open}, test key=${test}` });
  if (!test || !plans.checkout_open) {
    await browser.close();
    process.exit(1);
  }
}

// A: English, 1440 — declined card, 3-D Secure refused, then paid; renewal, cancel, refund.
const A = {};
{
  const ctx = await context(1440);
  const page = await ctx.newPage();
  A.account = await newAccount(page, "a", "en");
  const declined = await pay(page, { locale: "en", card: CARDS.declined, shot: "A1-declined-en-1440" });
  let b = await billing(page);
  record("1", "declined card: refused, no Pro", !declined.paid && b.plan === "free", { note: `"${(declined.message ?? "").slice(0, 80)}", plan ${b.plan}`, payment: declined.id });
  const refused = await pay(page, { locale: "en", card: CARDS.paid, threeDS: "N", shot: "A2-3ds-refused-en-1440" });
  b = await billing(page);
  record("2", "3-D Secure refused: not paid, no Pro", !refused.paid && b.plan === "free", { note: `"${(refused.message ?? "").slice(0, 80)}", plan ${b.plan}`, payment: refused.id });
  const paid = await pay(page, { locale: "en", card: CARDS.paid, threeDS: "Y", shot: "A3-paid-en-1440" });
  b = await billing(page);
  A.paid = paid.id;
  A.firstEnd = b.paid_through;
  record("3", "3-D Secure approved: paid, Pro started, card saved, renews", paid.paid && b.plan === "pro" && b.renews && b.card_last4 === "1111", {
    note: `Pro through ${b.paid_through}, ${b.card_brand} ${b.card_last4}, renews=${b.renews}`,
    payment: paid.id,
  });
  // The return page asks Moyasar; the address bar's "status=paid" decides nothing.
  await page.goto(`${BASE_URL}/billing/return?id=${declined.id}&status=paid&message=APPROVED`, { waitUntil: "networkidle" });
  await page.locator("[data-pro-started], main p[role=alert]").first().waitFor({ timeout: 60000 });
  const forged = (await page.locator("[data-pro-started]").count()) === 0;
  await page.screenshot({ path: `${OUT}/A4-forged-return-en-1440.png` });
  record("4", "return page confirms with Moyasar: a declined payment with status=paid in the address does not start Pro", forged, { payment: declined.id });
  await page.goto(`${BASE_URL}/settings#billing`, { waitUntil: "networkidle" });
  await page.locator("[data-plan=pro]").waitFor({ timeout: 15000 });
  await page.screenshot({ path: `${OUT}/A5-settings-pro-en-1440.png` });

  // Renewal: the paid month is made to end now, then the hourly job runs once.
  sql(`UPDATE subscriptions SET current_period_end = now() - interval '1 minute' WHERE user_id = ${A.account.id}`);
  const run = renewNow();
  b = await billing(page);
  const payments = sql(`SELECT kind || ':' || status FROM billing_payments WHERE user_id = ${A.account.id} ORDER BY created_at`).split("\n");
  A.renewal = sql(`SELECT id FROM billing_payments WHERE user_id = ${A.account.id} AND kind = 'renewal' ORDER BY created_at DESC LIMIT 1`);
  const nextMonth = b.paid_through && new Date(b.paid_through) > new Date(Date.now() + 25 * 86400e3);
  record("5", "renewal: the saved card is charged and Pro moves a month on", b.plan === "pro" && nextMonth && payments.includes("renewal:paid"), {
    note: `job: ${run}; Pro through ${b.paid_through}; payments ${payments.join(", ")}`,
    payment: A.renewal,
  });

  // Cancel: Pro stays to the end of the paid month, no further charge.
  await page.goto(`${BASE_URL}/settings#billing`, { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Cancel renewal" }).click();
  await page.waitForTimeout(1500);
  b = await billing(page);
  await page.screenshot({ path: `${OUT}/A6-cancelled-en-1440.png` });
  record("6", "cancel: Pro until the paid month ends, no renewal", b.plan === "pro" && !b.renews && b.status === "canceled", { note: `status ${b.status}, Pro through ${b.paid_through}, renews=${b.renews}` });

  // Refund (what the owner does in Moyasar's dashboard), then Moyasar's notification: Pro ends.
  const r = refund(A.renewal);
  const w = webhook("payment_refunded", A.renewal);
  b = await billing(page);
  record("7", "refund of the payment for the current month ends Pro", b.plan === "free" && b.status === "expired", {
    note: `Moyasar refund: ${r}; notification: ${w}; plan ${b.plan}, status ${b.status}`,
    payment: A.renewal,
  });
  await ctx.close();
}

// B: Arabic, 390 — the payer closes the browser after paying; the notification starts Pro, once.
{
  const ctx = await context(390);
  const page = await ctx.newPage();
  await newAccount(page, "b", "ar");
  const p = await pay(page, { locale: "ar", card: CARDS.paid, threeDS: "Y", holdReturn: true, shot: "B1-ar-390" });
  let b = await billing(page);
  const before = b.plan;
  const w1 = webhook("payment_paid", p.id);
  b = await billing(page);
  record("8", "browser closed after paying: Moyasar's notification starts Pro", before === "free" && b.plan === "pro", {
    note: `before the notification ${before}; notification: ${w1}; after ${b.plan} through ${b.paid_through}`,
    payment: p.id,
  });
  const end1 = b.paid_through;
  const w2 = webhook("payment_paid", p.id);
  b = await billing(page);
  const rows = sql(`SELECT count(*) FROM billing_payments WHERE id = '${p.id}'`);
  record("9", "the same notification again changes nothing", b.paid_through === end1 && rows === "1", { note: `second: ${w2}; Pro through ${b.paid_through} (was ${end1}); payment rows ${rows}`, payment: p.id });
  await page.goto(`${BASE_URL}/ar/settings#billing`, { waitUntil: "networkidle" });
  await page.locator("[data-plan=pro]").waitFor({ timeout: 15000 });
  await page.screenshot({ path: `${OUT}/B2-settings-pro-ar-390.png` });
  await ctx.close();
}

// C: English 390 and D: Arabic 1440 — the paid path at the other two sizes.
for (const [id, locale, width] of [["10", "en", 390], ["11", "ar", 1440]]) {
  const ctx = await context(width);
  const page = await ctx.newPage();
  await newAccount(page, `${locale}${width}`, locale);
  const p = await pay(page, { locale, card: CARDS.paid, threeDS: "Y", shot: `${id === "10" ? "C" : "D"}-paid-${locale}-${width}` });
  const b = await billing(page);
  const sideways = await page.evaluate(() => document.scrollingElement.scrollWidth - innerWidth);
  record(id, `paid in ${locale === "ar" ? "Arabic" : "English"} at ${width} px`, p.paid && b.plan === "pro" && sideways <= 0, { note: `Pro through ${b.paid_through}; sideways ${sideways}px`, payment: p.id });
  await ctx.close();
}

// A wrong secret is refused.
{
  const out = server(
    "python3 -I -",
    `import json, urllib.request, urllib.error
req = urllib.request.Request("${API}/v1/billing/webhook/moyasar", json.dumps({"type": "payment_paid", "secret_token": "wrong", "data": {"id": "x"}}).encode(), {"content-type": "application/json"})
try:
    print(urllib.request.urlopen(req, timeout=30).status)
except urllib.error.HTTPError as e:
    print(e.code)
`,
  );
  record("12", "a notification with the wrong secret is refused", out === "403", { note: `HTTP ${out}` });
}

await browser.close();
await writeFile(`${OUT}/results.json`, JSON.stringify({ base_url: BASE_URL, at: new Date().toISOString(), results }, null, 2));
const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length} case(s): ${results.length - failed.length} passed, ${failed.length} failed`);
process.exit(failed.length ? 1 : 0);
