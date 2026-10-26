// Advisor images arriving for Step 22: are they usable, and did anything change that should not have?
//
//   node scripts/check-advisor-images.mjs ../docs/advisors-portraits/incoming
//
// Two kinds of file are understood, by name:
//   <id>-cut.png    the approved portrait with its background removed
//   <id>-talk.png   the same portrait with the mouth open, for the speaking frame
//
// The check that matters is the second one. The two frames swap about every 150 ms while an advisor
// writes, so anything that differs apart from the mouth reads as a flicker rather than as speech -- and
// a face that has drifted is worse than that: these portraits are approved and the lawyer reviews them
// (PROJECT.md Step 7). A candidate is composited onto the original's own background colour first, so the
// transparency it gained is not itself counted as a change.
import { readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const here = path.dirname(fileURLToPath(import.meta.url));
// A folder given on the command line is relative to where you are standing, as a path argument should
// be; the default is the repo's own incoming folder, wherever the script is run from.
const arg = process.argv.slice(2).find((a) => !a.startsWith("--"));
const IN = arg ? path.resolve(process.cwd(), arg) : path.resolve(here, "../../docs/advisors-portraits/incoming");
const ORIG = path.resolve(here, "../../docs/advisors-portraits/originals");
const SEATS = ["buffett", "lynch", "dalio", "marks", "alwaleed", "alrajhi", "chair"];
const DIFF = 24; // per-channel difference counted as "this pixel changed"

const failures = [];
const report = [];
const say = (s) => { console.log(s); report.push(s); };
const check = (ok, label) => { say(`${ok ? "PASS" : "FAIL"}  ${label}`); if (!ok) failures.push(label); };
const note = (s) => say(`      ${s}`);

/** Raw RGBA at a known size. */
async function rgba(file, size) {
  const img = sharp(file).ensureAlpha();
  const r = size ? img.resize(size, size, { fit: "fill" }) : img;
  const { data, info } = await r.raw().toBuffer({ resolveWithObject: true });
  return { data, W: info.width, H: info.height };
}

/** The original's background colour, from its top corners. */
function bgOf({ data, W }) {
  let r = 0, g = 0, b = 0, n = 0;
  for (const x0 of [0, W - 24]) for (let y = 0; y < 24; y++) for (let x = x0; x < x0 + 24; x++) {
    const o = (y * W + x) * 4; r += data[o]; g += data[o + 1]; b += data[o + 2]; n++;
  }
  return [r / n, g / n, b / n];
}

async function one(file) {
  const name = path.basename(file);
  const m = name.match(/^([a-z-]+?)-(cut|talk)\.(png|webp)$/i);
  if (!m) { say(`SKIP  ${name}: name should be <id>-cut.png or <id>-talk.png`); return; }
  const [, id, kind] = m;
  if (!SEATS.includes(id)) { check(false, `${name}: "${id}" is not a seat (${SEATS.join(", ")})`); return; }
  say(`\n--- ${name} (${id}, ${kind}) ---`);

  const meta = await sharp(file).metadata();
  check(meta.width === meta.height, `${name}: square (${meta.width}x${meta.height})`);
  check(meta.width >= 512, `${name}: at least 512 px (${meta.width})`);
  check(meta.hasAlpha === true, `${name}: has an alpha channel`);

  const orig = await rgba(`${ORIG}/${id}.webp`);
  const cand = await rgba(file, orig.W);

  // Transparency: a cut-out must actually be cut out, not a flat background baked in.
  let clear = 0;
  for (let i = 0; i < cand.W * cand.H; i++) if (cand.data[i * 4 + 3] < 8) clear++;
  const clearPct = (clear / (cand.W * cand.H)) * 100;
  check(clearPct > 5, `${name}: background actually removed (${clearPct.toFixed(0)}% transparent)`);
  const centre = (((cand.H / 2) | 0) * cand.W + ((cand.W / 2) | 0)) * 4 + 3;
  check(cand.data[centre] > 250, `${name}: the middle of the image is opaque (alpha ${cand.data[centre]})`);

  // What changed, against the original, with both on the original's background colour.
  const [br, bg, bb] = bgOf(orig);
  let changed = 0, x0 = cand.W, y0 = cand.H, x1 = -1, y1 = -1;
  for (let y = 0; y < cand.H; y++) for (let x = 0; x < cand.W; x++) {
    const o = (y * cand.W + x) * 4;
    const a = cand.data[o + 3] / 255;
    const cr = cand.data[o] * a + br * (1 - a);
    const cg = cand.data[o + 1] * a + bg * (1 - a);
    const cb = cand.data[o + 2] * a + bb * (1 - a);
    const d = Math.max(Math.abs(cr - orig.data[o]), Math.abs(cg - orig.data[o + 1]), Math.abs(cb - orig.data[o + 2]));
    if (d > DIFF) {
      changed++;
      if (x < x0) x0 = x; if (x > x1) x1 = x;
      if (y < y0) y0 = y; if (y > y1) y1 = y;
    }
  }
  const pct = (changed / (cand.W * cand.H)) * 100;
  const box = x1 < 0 ? null : { x0: x0 / cand.W, x1: x1 / cand.W, y0: y0 / cand.H, y1: y1 / cand.H };
  note(`changed vs the original: ${pct.toFixed(1)}% of pixels` + (box ? `, within x ${(box.x0 * 100).toFixed(0)}–${(box.x1 * 100).toFixed(0)}%, y ${(box.y0 * 100).toFixed(0)}–${(box.y1 * 100).toFixed(0)}%` : ""));

  if (kind === "cut") {
    // A cut-out must not repaint the subject: only the background should differ.
    check(pct < 6, `${name}: the subject is untouched, only the background was removed (${pct.toFixed(1)}% changed)`);
  } else {
    check(changed > 0, `${name}: something actually changed`);
    check(pct < 8, `${name}: the change is local, not a redraw (${pct.toFixed(1)}% changed)`);
    // The mouth sits in the lower half, centrally. Anything above the eyes means hair or glasses moved.
    if (box) {
      check(box.y0 > 0.35, `${name}: nothing changed above the eyes (change starts at y ${(box.y0 * 100).toFixed(0)}%)`);
      check(box.x0 > 0.15 && box.x1 < 0.85, `${name}: the change is central, not at the edges (x ${(box.x0 * 100).toFixed(0)}–${(box.x1 * 100).toFixed(0)}%)`);
    }
  }
}

/**
 * `--set`: a freshly drawn set of portraits, where there is nothing to diff against — the old files are
 * being replaced, not cut out. What matters instead is that the seven look like they are at the same
 * table: a head shot closer or further than the rest reads as one advisor standing apart. Measured from
 * the alpha, which is where the subject is.
 */
async function asSet(files) {
  const rows = [];
  for (const f of files) {
    const id = path.basename(f).replace(/\.(png|webp)$/i, "").replace(/-cut$/, "");
    if (!SEATS.includes(id)) { check(false, `${path.basename(f)}: "${id}" is not a seat`); continue; }
    const meta = await sharp(f).metadata();
    check(meta.width === meta.height, `${id}: square (${meta.width}x${meta.height})`);
    check(meta.width >= 512, `${id}: at least 512 px (${meta.width})`);
    check(meta.hasAlpha === true, `${id}: has an alpha channel`);
    const { data, W, H } = await rgba(f);
    let x0 = W, x1 = -1, y0 = H, y1 = -1, opaque = 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      if (data[(y * W + x) * 4 + 3] > 128) {
        opaque++;
        if (x < x0) x0 = x; if (x > x1) x1 = x;
        if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
    }
    check(opaque > 0 && x1 >= 0, `${id}: has a visible subject`);
    if (x1 < 0) continue;
    const centre = (((H / 2) | 0) * W + ((W / 2) | 0)) * 4 + 3;
    check(data[centre] > 250, `${id}: opaque in the middle (alpha ${data[centre]})`);
    rows.push({ id, top: y0 / H, height: (y1 - y0 + 1) / H, cx: (x0 + x1) / 2 / W, fill: (opaque / (W * H)) * 100 });
  }
  if (rows.length < 2) return;
  say("\n--- do they look like one set? ---");
  say("  seat       top of subject   subject height   centred at   fills");
  for (const r of rows) {
    say(`  ${r.id.padEnd(10)} ${(r.top * 100).toFixed(0).padStart(9)}%  ${(r.height * 100).toFixed(0).padStart(13)}%  ${(r.cx * 100).toFixed(0).padStart(10)}%  ${r.fill.toFixed(0).padStart(4)}%`);
  }
  const span = (k) => Math.max(...rows.map((r) => r[k])) - Math.min(...rows.map((r) => r[k]));
  const odd = (k, lim) => rows.filter((r) => Math.abs(r[k] - rows.reduce((s, x) => s + x[k], 0) / rows.length) > lim).map((r) => r.id);
  check(span("height") < 0.18, `subjects are a similar size (spread ${(span("height") * 100).toFixed(0)} points)` + (odd("height", 0.09).length ? ` — out: ${odd("height", 0.09).join(", ")}` : ""));
  check(span("top") < 0.15, `subjects start at a similar height (spread ${(span("top") * 100).toFixed(0)} points)` + (odd("top", 0.075).length ? ` — out: ${odd("top", 0.075).join(", ")}` : ""));
  check(span("cx") < 0.12, `subjects are similarly centred (spread ${(span("cx") * 100).toFixed(0)} points)`);
  if (rows.length < SEATS.length) note(`${rows.length} of ${SEATS.length} seats so far: missing ${SEATS.filter((s) => !rows.some((r) => r.id === s)).join(", ")}`);
}

const setMode = process.argv.includes("--set");
const files = (await readdir(IN).catch(() => [])).filter((f) => /\.(png|webp)$/i.test(f)).sort();
if (!files.length) {
  console.log(`Nothing to check in ${IN}\nDrop the images there as they arrive, named <id>-cut.png or <id>-talk.png.`);
  process.exit(0);
}
say(`Checking ${files.length} image(s) in ${IN}${setMode ? " as one set" : ""}`);
if (setMode) await asSet(files.map((f) => path.join(IN, f)));
else for (const f of files) await one(path.join(IN, f));
say(failures.length ? `\n${failures.length} FAILED` : "\nall passed");
process.exit(failures.length ? 1 : 0);
