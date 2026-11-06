# Output 14: review 13's three issues, fixed

Commits: `307d2fc` (code), `283af04` and the following commit (evidence and records).

**1. Phone tables hid their labels when scrolled, and showed a period cut in half** ("1,7" for 1,701, ".75"
beside a label). Fixed in `web/src/components/stock/research-panels.tsx` and `web/src/lib/statement-period.ts`:
- **Sticky labels.** The label header and label cells are `sticky start-0` with an opaque `bg-panel`;
  `start-0` is the inline start, so it holds in RTL. The header row was already sticky.
- **Phone layout.** `phoneColumnWidth(boxWidth, columns)` returns null where the table fits, so the layout is
  unchanged there, as on desktop. Otherwise it returns `boxWidth − 192`: the labels plus exactly one whole
  period fill the box. The panel measures its box with a `ResizeObserver`.
- **Phone scrolling.** In the phone layout the table is `table-fixed`, the label column 192px and each period
  that width. The box is `snap-x snap-mandatory` with `scroll-padding-inline-start: 192px`, and the period
  headers are `snap-start`. Scrolling therefore moves one whole period at a time, and no figure is ever shown
  cut, beside the labels or at the edge.
- **Tests.** 2 new tests for the width rule; `npm test` 66/66, `tsc` 0, lint 0, `npm run build` 93/93.

**The phone check now requires more** (`7-phone-gap.txt`):
- the labels stay in view scrolled to the end;
- the oldest period sits beside them, not under them;
- **no period is shown cut** on load, at every column step (`scrollBy` one column at a time) and at the end.

On `307d2fc` it passes **11/11**. To show the rule is not trivially true, the same check was run on the
previous commit (source stashed, then restored): it **fails 9/11**, with labels out of view and cut periods.
The two single-period panels have nothing to scroll and pass.

**2. Visual inspection of all eleven.** All 11 phone panels on load and the 9 that scroll, in their scrolled
state, were put side by side on three contact sheets and inspected. The sheets are now in the repository:
`docs/screenshots/release-candidate-307d2fc/contact-sheets/sheet{1,2,3}.png`.
- On load, one whole period sits beside the labels in both languages; for example, 8010 opens on "يونيو 2026".
- Scrolled, the labels stay and the oldest period is whole; 8010's 2025 shows 1,701.
- Blank cells are the panel's "·" for empty values, matching the API.

A 1440 sample (108's balance sheet) is unchanged: five years side by side, nothing sticky in effect.

**3. Counts.** The readiness report now names candidate **`307d2fc`**.
- Its evidence is `docs/screenshots/release-candidate-307d2fc/`: 150 screenshots and 7 logs, plus the contact
  sheets.
- The superseded `509d7bf` folder is recorded as 150, not 130.
- The phone-table change is added to the visitor table and the file list.

**The whole candidate check was re-run on `307d2fc`; all PASS:**
- the 11-04 label set;
- the Gulf English pages;
- newest-first;
- the bank sub-lines;
- the real-estate label;
- `check-arabic` with `WIDTHS=1440,390` (48 views, 0 stray English);
- the phone check.

`git diff --stat 307d2fc..HEAD -- web/src api deploy web/messages web/public` is empty.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
