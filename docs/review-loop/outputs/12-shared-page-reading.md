# Output 12: review 11's step, the pairing scripts share their page reading

Commit `e188b24`.

**The change:**
- New `scripts/argaam_ar_labels/argaam_pages.py`. It has `ROW_ID`, `norm()` and `page_rows(path)`:
  UTF-8 with errors replaced, `html.parser`, `<tr id="trNNN">`, the first `td[data-fieldname]`, and the
  visible text before the attribute. The first label wins for a repeated id. `bs4` is imported inside the
  function.
- `pair_from_gulf.py` drops its own `ROW`, `norm()` and `rows(path)`. `pair_labels.py` drops `ROW_ID`,
  `norm()`, `rows(html)`, and its now-unused `import re` and `bs4` import. Both call `page_rows()`.
- Page selection stays in each script: `newest_page()`, quarter then annual, and `newest_english_page()`,
  quarter only.
- 44 lines out, 6 in, plus the 34-line module.

**Proof of identical behaviour** (server, read-only, written only under `/tmp/f16/dedupe`):
- **Frozen corpus.** The nightly started at 00:00 UTC and writes new runs, so the corpus was frozen first.
  For every company (716), the run each script would pick from before tonight (`run_* < run_20261106`) was
  hard-linked; 1,426 statement files.
- **Old (HEAD) vs new scripts** over that corpus, all four modes, byte-identical by sha256:
  - `pair_from_gulf.py`: 27,096 bytes, `7e5e63cf…`, the same hash as the 2026-11-05 run over the live
    universe;
  - `pair_labels.py --check-ids`: 269 English pages, 411 row ids, 3 with two labels (as recorded 2026-11-03);
  - `pair_labels.py` default;
  - `pair_labels.py --ar-dir`, fed five Gulf Arabic pages under Saudi names to exercise the Arabic-page
    path (5 Arabic pages read).
- `python -B -X utf8 scripts/argaam_ar_labels/test_pair_from_gulf.py`: OK. All three modules compile.
  `git diff --check` is clean.
- The corpus hard links were removed afterwards, so no old harvest file is pinned. The originals are
  untouched, and the outputs are kept in `/tmp/f16/dedupe/{before,after}`.

`PROJECT.md`: the review cleanup list marks duplicated helpers done. What is left: the busy check in the
superseded harvest script, and the screenshot rule.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step?
