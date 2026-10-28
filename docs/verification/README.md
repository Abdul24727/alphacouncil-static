# AlphaCouncil — LLM Council verification package

**Prepared 2026-10-28 for independent review. Read-only: nothing in here was changed for this
package, no model was called to produce it, and nothing was deployed.**

AlphaCouncil is a research terminal for listed Gulf equities. One of its features is an **advisors'
room**: six named personas answer a member's question about one company over three rounds, and a
neutral Chair writes the room's answer. This package contains that engine, the benchmark harness
built to test whether the room is worth its cost, and every result measured so far.

## What you are being asked to check

The claim under review is narrow and falsifiable: **does the Council catch material financial errors
that the Chair's model alone misses?**

The answer so far is **no, not demonstrably** — and the reason matters more than the answer. The
pre-registered test returned FAIL, but reading the answers showed the metric was measuring the wrong
thing. Both are in this package, along with the script to re-derive both from the saved text.

**Start here:**

1. `docs/council-test-run-2026-10-27.md` — what was run and what it found, including the defects in
   my own method.
2. `results/rescore.py` — run it (`cd results && python3 rescore.py`, standard library only, no key,
   no network) to recompute the published numbers *and* the correction from the saved answers.
3. `docs/council-test-design-2026-10-28.md` — the replacement test, built but **never run**.

## The honest summary, so nothing here is a surprise

| | |
| --- | --- |
| Pre-registered primary result | **FAIL.** Arm A (six seats) 13/15 vs arm B (Chair's model alone) 15/15 propagated the planted error, Fisher exact p = 0.4828 |
| What reading the answers showed | **0 of 45 planted runs adopted the planted claim.** All three arms rejected it every time. The metric was a substring test, so an answer that *named* the wrong figure in order to reject it scored as repeating it |
| So the honest reading | **a ceiling effect.** The single model caught the error 15/15, so there was no shortfall for six seats to cover. The Council's error-catching advantage is **neither demonstrated nor disproven** by this test |
| Why the task was too easy | the data pack is in the prompt, and every plant contradicted a figure published in it. Catching it took one lookup |
| The one measured difference in 60 runs | on the only cell whose answer the pack does **not** publish, the rooms derived the payout ratio **4/4** and answered; the single model derived it **0/4** and said coverage could not be confirmed. n = 4, post hoc, decides nothing |
| Cost | six seats **$0.2257**/run, four seats $0.1759, single model **$0.0292**. The room costs **7.7×** the single model and takes 7.3× as long |
| Four seats vs six | no difference on the error metric; 22% cheaper; **more** unverified figures (median 2 vs 1). Seat count is not shown to be the variable in either direction |

Known defects in my own work, all recorded in the docs rather than smoothed over: the validity gate
was missing from the code and had to be written before the result could be read; the first plant
design was mismatched to four of five questions and was caught by that gate; a planted figure was
briefly chosen that a *correct* answer would have matched (−15.37 rounds to "15.4"); the
payout-derivation check first counted the "75" inside a return on equity of 26.75; and one paid run
was started against a stale release and cost $1.23 before being killed.

## What is in here

### 1. The engine — `code/api/app/debate/`

| file | what it is |
| --- | --- |
| `engine.py` | the room: stages (brief → openings → faultlines → debate → final → verdict), the shared system rules, token and word budgets, temperatures. `ANSWER_WORDS`, `MAX_TOKENS`, `TEMPERATURE`, `RULES` are here |
| `llm.py` | every model call. JSON parsing, the retry loop (`ATTEMPTS = 3`), and the error taxonomy — `credentials` (401), `busy` (429), `no_credit` (402), `unreachable`, `bad_output` |
| `checks.py` | server-side validation of what a model returns: digit normalisation, citation matching, `unverified_figures` (a figure not present in the pack is marked on screen), `drop_advice` (sentences giving investment advice are removed) |
| `pack.py` | the data pack: eight datasets P1–P8 built once per session from the project's own read-only SQLite files, and rendered into the prompt |
| `roster.py` | which seats sit, recusals, `MIN_ADVISORS = 2` |
| `standin.py` | the labelled no-model stand-in used for `--dry` runs |
| `store.py` | session persistence |

**Two things worth knowing before reading it.** The advisors have **no web search and no
tool-calling**: every figure they can cite comes from the pack in their prompt. And where the room
has to choose between readings, `count_leans` / `count_answers` in `engine.py` are **engine
arithmetic, not a model** — a tie is reported as a tie.

Note that `api/app/council.py` (not in this package) is a *different* thing with a confusing name:
six deterministic rule-based seats scoring database values against thresholds, with no model
involved. The LLM Council is `api/app/debate/` only.

### 2. The harness — `code/api/eval/`

| file | what it is |
| --- | --- |
| `questions.py` | the five cells (company, question) and, at the commit that ran, one planted error per cell |
| `run.py` | `snapshot` / `run` / `report`: builds a pack once, replays arms off identical bytes, enforces the spending cap |
| `gate.py` | the validity gate — a case counts only if every compared arm's clean answer engages with the metric the plant corrupts |
| `report.py` | the tables, `fisher_exact` (written out; scipy is not a dependency), and the pre-registered verdict |
| `probes.py`, `score.py`, `probe_run.py`, `probe_report.py` | **the 2026-10-28 replacement test. Implemented, dry-verified, calibrated — and never run against a model.** See the caveat below |

**The spending cap is real and worth checking.** `run.py` and `probe_run.py` read the account balance
before the first run and refuse a plan the balance cannot finish, then re-read it before every run.
They also refuse if the balance cannot be read at all, because a cap that silently does not apply is
worse than none.

### 3. The investor philosophies — `code/api/app/advisors/`

One file per seat plus `chair.md`. The roster the benchmark ran was
`buffett,lynch,dalio,marks,alwaleed,alrumayyan` (`settings.py:71`). `alrajhi.md` is present but **not
in that roster** — it is an unused seat file, and the commented example in `deploy/api.env.example`
still lists it, which is stale. The four-seat arm used `buffett,lynch,marks,alwaleed`.

Each file is written in AlphaCouncil's own words from the person's publicly documented principles.
The rules built into every seat, in code: never claim to be the person, never quote them, never
describe their private views or holdings, and **never tell anyone to buy, sell or hold anything**.
Whether real names and likenesses may be used at all is an open legal question for this product, not
a settled one.

### 4. Settings, manifests and tests — `code/api/`

`app/settings.py` (every tunable, with defaults), `app/copilot/openai_compat.py` (the HTTP client all
model calls share — one client per event loop; the fault that made it one per call is F-11),
`pyproject.toml` and `uv.lock` (dependencies; `[tool.pytest.ini_options] testpaths = ["tests"]`), and
`tests/test_debate.py`, `tests/test_copilot.py`, `tests/test_eval_score.py`,
`tests/test_eval_budget.py`, `tests/test_eval_probe_run.py`.

**What this archive can verify on its own**, and the figure worth quoting: the scoring, budget and
runner tests, run from `code/api/`. The fourth review round was right that the *application* suite
cannot be checked here — this package carries the evaluation code and its dependencies, not the
market database, fixtures or frontend assets, so the broader integration tests cannot run and their
failures say nothing about the deployed application. The repository-wide figure (279 tests) is a
repository claim and should be treated as one.

**99 pass and 6 skip**, and the skips state their real cause rather than a guess. Five
behavioural runner tests and the constant-drift guard need `app.routers`, which
`app/copilot/openai_compat.py` imports at module scope; shipping it would drag in the market
database and the billing plans for six tests, so it is not here and the skip says exactly that. The
structural tests — no reservation without a bound, no path opting out of it, both ceilings wired,
the stop condition read — run anywhere, and they are the ones that catch the class of fault the
fourth review round found.

`deploy/api.env.example` documents every environment variable. **No key is in this package and none
is in the codebase**: `OPENROUTER_API_KEY` is read from the process environment at call time
(`openai_compat.py:108`) and is never a settings field.

### 5. The data snapshots — `data/packs/`

The five packs the benchmark replayed, byte-identical across every arm so the data is not a variable:

| file | company | notable |
| --- | --- | --- |
| `1120_TADAWUL.en.json` | Al Rajhi Bank | full pack; P/E 14.51, ROE 23.49% |
| `2010_TADAWUL.en.json` | SABIC | **no P/E and no EPS at all**; ROE −15.37% |
| `2222_TADAWUL.en.json` | Saudi Aramco | the dividend cell; payout ratio not published |
| `4190_TADAWUL.en.json` | Jarir | valuation against momentum; P/B 12.28 |
| `4061_TADAWUL.en.json` | Anaam | genuinely thin; no EPS, no dividends, current ratio 0.18 |

Public market and fundamental data only — company figures, price history, dividend rows, news
headlines. No customer data, no account data, no personal data of any kind. 4280 Kingdom Holding was
deliberately excluded because one seat recuses itself there, which would have made the arms
non-comparable.

### 6. The results — `results/`

| file | what it holds |
| --- | --- |
| `results.jsonl` | **the paired test: 60 runs.** 45 planted (arms A, B, D × 5 cells × 3 repeats) and 15 clean controls. Each row carries the full answer text, headline, gaps, disagreements, timings, cost, the unverified-figure list and the probe flags |
| `paired-clean.log`, `paired-planted.log` | the raw stdout of both phases, one line per run |
| `aggregate-report.txt` | the harness's own report and pre-registered verdict, regenerated from `results.jsonl` |
| `rescore.py`, `rescore-output.txt` | independent re-derivation of the published metric, the adopt-or-reject correction, and the dividend-cell finding |
| `exploratory-2026-10-27.jsonl` | the earlier 15-run exploratory bench: arms A, B and **C** (six seats spread over three models), clean runs only. Cost and length only; it measures nothing about error-catching |
| `planted-partial.jsonl` | 12 rows from a run that should not have been started (stale release, no spending guard, killed after $1.23). 3 are $0.00 dry leftovers, 9 are real. Kept because they were measured, not because they support anything |

**Arm C appears only in the exploratory file.** It was dropped from the paired test on cost: $0.4327
a run against arm A's $0.2257.

### 7. Provenance

In `PROVENANCE.md`: the exact commits, which code ran on which phase, what changed mid-benchmark and
what changed after, with the one-line proof that the engine is byte-identical to the benchmark's.

## The caveat that matters most

**The 2026-10-28 probe harness has never been run against a model.** `probes.py`, `score.py`,
`probe_run.py` and `probe_report.py` are implemented, dry-verified and calibrated against the 60
answers already measured — but they have produced no result, and `docs/council-test-design-2026-10-28.md`
says so on its first line. Its base-rate calibration killed half of its own first design before any
money was spent: the omission family was dropped because every arm already supplies the figure the
probe hides, and the inference family was re-instrumented because its markers fired in 12 of 12
answers that saw no plant.

If you review that design, the two questions worth pressing are whether **arm E** (the same single
model given a second pass, rather than six seats) is the right way to separate "more seats" from
"more rounds", and whether the derivation family measures error-catching at all or simply measures
which arms will do arithmetic the pack does not do for them. The design concedes the second point.

## Reproducing

**Offline, no key, no cost** — recomputes every published number from the saved answers:

```bash
cd results && python3 rescore.py            # add --answers to read the figure sentences
```

**The aggregate report** needs the project's dependencies but no key:

```bash
cd code/api && uv sync && uv run python -m eval report
```

**A dry run of the full plan** — real prompts assembled, no model, no cost:

```bash
cd code/api && uv run python -u -m eval probe --dry --repeats 1 --pause 0
```

**Paid runs need `OPENROUTER_API_KEY` in the environment and are capped.** They are not needed to
check anything in this package.

## Known defects in the engine, as of this package

The fault record is `docs/beta-advisors-2026-10-27.md` (F-1 to F-11). Those closed are closed in the
code here. Two are worth naming because they shaped the results:

- **F-10** — OpenRouter answers HTTP 402 when the account cannot cover a request, and every
  `APIStatusError` was mapped to `SeatError("unreachable")`, so a billing refusal reached the member
  as "the AI service could not be reached". Fixed: 402 is now `no_credit`, and is not retried.
- **F-11** — `make_client()` returned a new HTTP client per model call and never closed it, about 21
  connection pools a session; three sessions in one process ran and the fourth hung. Fixed: one
  client cached per event loop.

## Excluded, deliberately

API keys, tokens and `.env` files; the live `api.env` from any host; database credentials and
connection strings; subscriber, account and customer data of any kind; payment-processor
configuration; email and SMTP credentials; backups; and the one SSH login target that appeared in the
fault record, which is marked `[login target redacted for this package]`.

`MANIFEST.txt` lists every file with its SHA-256 so the package can be checked for completeness.
Please keep it private rather than publishing it to a public repository.

---

## Second package, 2026-10-28 — what changed after the first review

The first package was reviewed independently and the review found four reproducible scoring defects
in the replacement benchmark, a spending-guard hole and a packaging defect. **All of them reproduced,
and all of them are fixed in this package.** `docs/council-review-response-2026-10-28.md` answers the
review point by point; the short version:

- **`api/eval/score.py` rewritten.** A signed quantity now counts only with its sign; a marker inside
  a negation does not fire; a new `REJECTED` outcome separates "named the wrong figure and rejected
  it" from both adopting it and correcting it. The negation scope is asymmetric and the file says why.
- **`api/tests/test_eval_score.py` — 35 new tests**, one named for each of the review's four cases,
  plus both false-positive cases it asked for and two calibration guards. The suite is **209 tests**.
- **The spending guard fails closed** on every balance check, in this harness and in the original,
  and a second cap sums the per-call costs the provider returns, so it does not depend on the account
  endpoint being reachable or current.
- **`MANIFEST.txt` no longer lists itself** — the defect the review found. The archive's SHA-256
  travels outside the archive. The package is now built by `scripts/verification-package.sh`, which
  refuses to produce an archive if its own secret scan finds anything.
- **`app/copilot/` is included in full**, so `tests/test_copilot.py` runs: the first package shipped
  that test without `app.copilot.context`.

**On the data finding**, which the review called most consequential: its numbers are right about the
snapshots, and the pattern goes further — P/E and P/B are off by the *same* factor within each
company, which rules out EPS and book value and points at the price. The cause is that each pack
carries a fourteen-day-old quote flagged `stale: true` beside ratios computed against a fresher
price. **On production today the ratios reconcile** (read-only checks in the response doc, §4). What
does not reconcile live is `market_cap_mn`, which runs 1.8–3.3% below `last_price × shares_out` — a
smaller but real defect, and one nothing checks, because `checks.py` asks only whether a figure is
present in the pack and never whether the pack agrees with itself. Two fixes are proposed there and
neither is built, because both change the application.

The `unit_unconfirmed` criticism is accepted as a stated limitation: D2 and D3 test the **direction**
of per-share earnings, which published ROE confirms independently, not an exact figure.

---

## Round four — 2026-10-28

Six findings, all reproduced, all real. Full write-up in
`docs/council-review-response-2026-10-28-round4.md`.

The spending cap I had described in round three was bypassed by two of the four arms, its stop
condition stopped nothing, and the bound itself omitted three things it was meant to bound. Fixing
all of it raised the plan's true maximum from **$33.62 to $93.71** — the number got much worse
because it got honest.

| What the review found | What it was |
| --- | --- |
| Arms B and E reserve a forecast, not the bound | `budget.take(f"a {arm} pass")` with no bound: a flat $0.09 where the real bound is $0.41–0.81 |
| 2-characters-per-token not established | It was an average, not a bound. Arabic beats it before the tokenizer is reached |
| Reasoning allowance not priced | `llm.ask` sends `max_tokens + 2048` on every call to the chair's model |
| `expect_usd` never activated | Computed, used for the balance check, then dropped: `Budget(cap_usd)` |
| Overrun detection does not stop anything | The loop read `budget.refused` and never `should_stop()` |
| Retry prompt growth unaccounted | A retry appends the unusable reply, up to 6,000 characters |

**The bound is now measured, not asserted.** `eval probe --dry` routes every stand-in call through
the same `metered` wrapper a paid call uses and prints the total of the reservations it took, so the
published maximum and the enforced reservations are the same arithmetic.
`results/dry-probe-results.jsonl` is that run: every row marked `dry`, every one at zero cost,
each carrying its `bound_usd`. It was 48 rows while the bench had six probes; since the twelve
added on 2026-10-28 the same command writes 144.

**`UNRESOLVED`** joins the inference outcomes. "Insufficient evidence." used to score `RESISTS` and
count as successfully handling a planted error; an arm now earns `RESISTS` only by showing the
grounds on a metric it engages with.

**`tests/test_eval_probe_run.py`** tests the wiring rather than the helpers, which is where every
fault in this round lived: no helper was broken.

**One finding of ours**, found while measuring the bound: `--dry` and a paid run appended to the same
results file with no field distinguishing them. Dry runs now write elsewhere and every row is marked.
Nothing was lost — the paid probe run has never happened.

**The limit of all of it**: every control here runs inside the process doing the spending. The only
true external cap is a dedicated provider key with its own credit limit, funded with the plan's
maximum and no more. That needs the owner's hands and is recommended, not done.
