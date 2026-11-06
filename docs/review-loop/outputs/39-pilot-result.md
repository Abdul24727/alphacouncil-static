# Output 39: the $66 pilot's result (review 38 step)

*(Corrected after review 39: two scorer defects were read as results, "citing none" counted openings missing one or more and the scripted plant openings, the reservations quoted were medians, and "every outcome class" was not seen. See output 40 and the corrected `docs/council-pilot-2026-11-06.md`.)*

The report is `docs/council-pilot-2026-11-06.md`. The record is `docs/eval/probe-results.jsonl` (36 rows, the
harness's RESULTS path), and `docs/eval/pilot-2026-11-06/` holds `pilot.log` and the full `eval probe-report` output.
`PROJECT.md` §9 and the changelog carry the outcome.

- **Accounted:**
  - 36 of 36 runs finished, with 0 failed and 0 stopped;
  - 432 calls;
  - **$5.64 spent** against a $5.17 forecast;
  - the $66 cap was never approached;
  - the balance went from $13.47 to **$7.83**, read from OpenRouter's credits endpoint;
  - the gate kept 6 of 6 probes.
- **What it proves (its job):**
  - the harness runs end to end on live models;
  - every outcome class is scored on live answers;
  - the cost model holds within 9 %;
  - the room's instruments read live numbers, and the single model shows UNAVAILABLE.
- **What it measured,** descriptive only:
  - A, B and D each handled 4 of 6;
  - inference is at a ceiling in every arm, planted and clean;
  - derivation is 1 of 3 per arm;
  - D2 and D5's clean controls are SILENT by design. Their inputs are confirmed present in today's packs on the
    server, for every banded probe.
- **The six-against-four line:** it prints "NON-INFERIOR". The report says plainly that this carries no weight at
  n = 6 with three probes at a ceiling.
- **Priority Two:** 42 of 72 (A) and 26 of 48 (D) openings cite none of the seat's own datasets.
- **Priority Three:** 0 rulings without grounds.
- **For the next run:**
  - **`RUN_BOUND` is stale.** Live per-run reservations are A $3.80, D $2.65 and B $0.32, so the $393 quotation must
    be re-measured.
  - **The inference probes** should be read on `incorrect`, or replaced.
  - **The probe split is 6 / 9.**
  - **The account cannot fund the run.**
- **No change to code or the site.** The pilot directory on the server (`/root/pilot-20261106`) is left in place
  as the run's working copy.

**The question for the review:** is this sound, and what is the single next pre-approved step?
