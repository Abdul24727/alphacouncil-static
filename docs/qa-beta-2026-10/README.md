# Independent QA audit of beta.alphacouncil.tech (2026-10-15 to 2026-10-21)

Three runs by an outside QA pass (Claude, browser-only, public HTTPS to the beta site, read-only except
one owner-approved cross-account write test). Accounts' emails are redacted throughout.

- `report.md` — the verdict table (run 2 with run-1 results in brackets; run 3 re-tests at the top),
  exact repro steps for every FAIL, and the "Not tested" list. Goal 3 in `PROJECT.md` works from it.
- `moyasar-checkout-interview-prompt.md` — a prompt that has an AI agent interview the owner to write the
  Moyasar TEST-mode checkout test plan (Step 16).
- `copilot-adversarial-plan.md` — the Copilot trust tests C1–C8 (all passed in run 3).

The evidence paths in `report.md` (screenshots, JSON captures) point at the audit's own working folder,
which was not copied here and may no longer exist. Re-run a check to get fresh evidence.
