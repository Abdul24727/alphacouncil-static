# Steps 22 and 23 on beta — 2026-10-27

The owner's go-ahead for the beta release came in chat on 2026-10-27 ("Yes, release to beta so I can approve
the look."). Steps 22 and 23 went up together, as the owner asked. This is the record of the first real-model
runs on beta: what the room did right, and the faults they turned up. **Production still waits on the owner
approving the look here**, and on the two open faults below.

## Releases

| Release | What it carried |
| --- | --- |
| `b915b36996` | Step 22's portraits and the room round the table; Step 23's three-round format. The advisors' room takes the full work area. |
| `c5d68f6466` | `data-tally` on each option, and the check able to ask for either mode (`QUESTION_EN` / `QUESTION_AR`, `MODE`). |
| `4b3d04a3e5` | `data-absent` on a turn card, the round checks rewritten round it, and the brief's mode read off the right card. What beta served for the morning's six sessions. |
| `ec620968ac` | The F-1 change (`ddf29d1`) and the owner's F-5 choice (`ec62096`). **This is what beta serves** (2026-10-27: `current` → `releases/ec620968ac`, api 200, web 200). |

Beta's room runs a real model, not the stand-in: `stand_in: false`, advisors on `deepseek/deepseek-v4-pro`,
Chair on `anthropic/claude-sonnet-5.5`. All seven seats are seated, Al-Rumayyan with an empty `recuse` list
(the owner's decision of 2026-10-26) and Alwaleed still sitting out Kingdom Holding (`4280_TADAWUL`).

A note for anyone repeating this: beta's web service binds `[::1]:3200`, not `127.0.0.1:3200`
(`next start -H localhost`), so the tunnel the check needs is
`ssh -N -L 3201:localhost:3200 root@alphacouncil.tech`. Pointed at `127.0.0.1` it fails with
"connect failed: Connection refused", which reads like a dead service and is not one.

## What ran

Three runs, six sessions, all on ticker 2222. Screenshots in `docs/screenshots/advisors-beta-open/` and
`docs/screenshots/advisors-beta-choice/`: every stage live at 1440, every stage replayed at 1440 and 390, in
both languages.

```
# open mode (the check's own questions)
BASE_URL=http://localhost:3201 OUT=../docs/screenshots/advisors-beta-open MODE=open \
  node scripts/check-advisors.mjs

# choice mode
BASE_URL=http://localhost:3201 OUT=../docs/screenshots/advisors-beta-choice MODE=choice \
  QUESTION_EN="Is the dividend covered by earnings, or is it only covered while margins hold?" \
  QUESTION_AR="هل التوزيعات مغطاة بالأرباح، أم أنها مغطاة فقط ما دامت الهوامش قائمة؟" \
  node scripts/check-advisors.mjs
```

| Session | Mode | Seconds | Cost | Round-one absences | Lean tally |
| --- | --- | --- | --- | --- | --- |
| `226688765` en | open | 64.8 | $0.2645 | alwaleed | — |
| `1881239950` ar | open | 77.0 | $0.3346 | none | — |
| `1376395001` en | open | 75.0 | $0.2315 | dalio, buffett | — |
| `1358057443` ar | open | 75.4 | $0.3060 | dalio | — |
| `647689038` en | choice | 62.7 | $0.2753 | none | A 1, B 4, C 1 |
| `1468662968` ar | choice | 56.5 | $0.3260 | none | A 3, B 0, C 3 |

`python -m app.debate stats 1` over the six: **6 done, 0 failed, median 69.9 s, max 77.0 s, median cost
$0.2907, mean $0.2897, total $1.7379.**

These are the time and cost figures Step 23 asked for and had never measured. **No session came close to the
~3 minutes at which Step 23 says to shorten round one on grounds of speed** — but see F-1, which argues for
shortening it anyway, for a different reason.

## What the room did right

- **Every session finished; none failed.** 55 PASS in the choice run, 53 in the open re-run.
- **Both modes work end to end with a real model**, which Step 23 had never seen. A choice session frames
  three options and **where it lands is the engine's arithmetic**: the tallies read off the screen sum to the
  six advisors who leaned (1+4+1 and 3+0+3). The Arabic choice session came out a 3–3 tie and the Chair said
  so — "المجلس منقسم مناصفة" — rather than inventing a winner.
- **The Chair's answer is inside its 200–350 band in all six sessions**: 296, 213, 269, 228, 268, 217 words.
- **Rounds two and three never lost a single advisor** across all six sessions. Every final word says what
  changed; 5–6 of 6 advisors conceded a point in every session; no scores appear anywhere.
- Lines played one at a time across all seven seats; every stage seen live; no sideways scroll at 1440 or 390;
  the disclaimer on screen; citation chips naming a dataset; Arabic sessions in Arabic.
- Arabic round-one answers sit inside the 250–400 band almost always (one run 6 of 6 inside, another 4 of 6).

## Faults

### F-1 — round one loses advisors to `bad_output`. **CLOSED on `ec620968ac`** (see the re-run below).

**Four absences across six sessions, every one of them in round one.** `engine.turn` marks the seat absent
(`{"absent": true, "error": "bad_output"}`), the screen says "no answer this round", and the room carries on.

| Session | Seats lost |
| --- | --- |
| `226688765` en open | alwaleed |
| `1376395001` en open | dalio, buffett |
| `1358057443` ar open | dalio |

It is **not one seat's prompt**: three different seats, both languages. `llm.ask` already asks a second time
saying what was wrong (`attempts < 2`); both attempts failed each time. The error is `bad_output`, not
`cut_off`, so this is **malformed JSON rather than the token ceiling** — which is what long prose inside a
JSON string field tends to produce.

What points at the cause:

- It only ever hits **round one**. Rounds two and three, across six sessions, never lost anybody.
- Round one is the only round asking for **250–400 words**; the others ask for far less.
- It hits **English hardest** (3 of 4 absences), and English round-one answers are the ones running long (F-2).
- Neither **choice** session lost anyone, and those had the shorter round-one answers.

So the recommendation is the lever Step 23 already wrote down for a different trigger: **shorten round one to
200–300 words** (`engine.ANSWER_WORDS` and the wording in the seat files). It should cut the dropouts and the
overshoot together. Worth considering beside it: a third attempt in `llm.ask`, since two is evidently not
enough for the longest stage.

Degradation is graceful — a lost seat still gives its challenge and final word, and `count_answers` /
`count_leans` only count who was actually there — but a member sees a seat with no answer, and Step 23's
"Done when" asks for round-one answers from everyone. **This is not ready for production.**

**Changed in `ddf29d1`, not yet proven.** Round one now asks for **200–300 words** (`engine.ANSWER_WORDS`, the
Answers section of `chair.md`, and `ANSWER_WORDS` in this checker, which reads the same band off the screen);
the shared Output rule in `engine.py` now says each text value is one JSON string with its quotes escaped and
no line breaks; a seat gets **three tries** instead of two (`llm.ATTEMPTS`); and the retry after a malformed
reply says what to escape rather than only asking again. `uv run pytest -q` 169 passed, `npm test` 28 passed.
**None of that is evidence yet** — F-1 only shows up against a real model, so it stays OPEN until both modes
are re-run on beta with the two commands above and the absences are gone.

### F-2 — English round one runs long; Arabic does not. **Much smaller on `ec620968ac`**; left as it is.

English round-one answers against the 250–400 band the seat files ask for: 403–453 (five of five over), then
372–491, then 133–514. Arabic: 257–307 (all inside), 269–346, 198–340. Step 23's rule is to keep an over-long
answer whole and flag it, never to cut it, and that is what happens — the check now names the seats and their
counts. Probably the same root cause as F-1, and probably fixed by the same change.

### F-3 — the mode check was scoped to the wrong card. FIXED in `4b3d04a3e5`.

`[data-stage-view=brief]` is the transcript panel (`Transcript.tsx`), which carries neither the options nor
the focus list; the brief's options live on the "On the table" card (`Stage.tsx`, `data-on-table`). The
options count was therefore always 0, every session read as `open`, and `MODE=open` passed by accident. The
`open` branch failed loudly rather than passing silently, which is what exposed it. It reads `[data-on-table]`
now, and an open session must list the two to four things to weigh, as `chair.md` asks.

### F-4 — an absence was counted as an answer. FIXED in `4b3d04a3e5`.

The first run passed "round 1 is a full answer from each advisor (6)" while one of the six had no answer: the
check counted the turn card and read its "no answer this round" line as a **15-word answer**, which is what
actually failed the length check. The absence itself went unreported. Each round now separates the advisors
who answered from the ones who are away, reports the away list with the engine's own reason, and measures
lengths over the answers alone. `data-absent` marks it on the turn card, beside `data-concedes` and
`data-changed`.

### F-5 — the advice check fires on innocent words, and misses real advice. **CLOSED: the owner chose option B.**

Both choice sessions failed `the Chair's answer is an assessment, not advice`. **Both are false positives, and
the Chair gave no advice in any of the six sessions.**

- English: the only match is "whether cover **holds** only while margins **hold**" — the ordinary verb,
  echoing the question. `\b(buy|sell|hold)\b` cannot tell that from "hold the stock".
- Arabic: the match is `اشتر` inside **اشتراط** ("the stipulation of"), root ش-ر-ط, unrelated to اشترى, "to
  buy". The pattern is a bare prefix, so اشتراك (subscription) and مشترك would trip it too.

It is also too tight in the other direction: Arabic only catches `بيع السهم` and `شراء السهم` as exact
phrases, so advice worded any other way passes. Deliberately **not** changed here — the no-advice rule carries
legal weight and goes to the lawyer at Step 7, so narrowing it is the owner's call, not a quiet edit. It
matters before Step 10: `check-advisors.mjs` runs against production, and a question containing the word
"hold" would fail the launch check for no reason.

**The choice is written out in `docs/advice-check-f5-2026-10-27.md`** (2026-10-27) — three options with the
exact patterns, measured against 19 sentences: the pattern in use today gets 8 of them wrong (4 innocent
sentences failed, 4 pieces of real advice passed), and the recommended one gets all 19 right. Still the
owner's decision; nothing applied.

### F-6 — figures the checker could not match: 15 in English against 3 in Arabic. **Much smaller on `ec620968ac`.**

Marked on screen as not found in the data, which is the honest behaviour and not a BRAND violation: nothing is
presented as a database value when it is not one. They are the advisors' own arithmetic — a payout ratio of
"73", dividends summed to "1.35", "1.92" — derived from figures that are in the pack. It tracks F-2: the
longer the English answers, the more derived numbers they carry, so F-1's fix should reduce it too.

### F-8 — the fix for F-1 flattened every long answer into one paragraph. **FIXED, not yet released.**

Found 2026-10-27 by comparing the two runs' screenshots. Part of the F-1 change was a line in the shared
Output rule (`engine.RULES`): *"Each text value is one JSON string: escape every double quote inside it, and
**use no line breaks**."* The second half was wrong. `DebateText` (`web/src/components/debate/parts.tsx`)
splits a text on blank lines into separate `<p>` elements, so the long texts are **meant** to carry line
breaks; what breaks JSON is a **raw** newline inside a string, not an escaped one.

The effect is plain in the screenshots, same question, same model, same length:

| | Chair's answer |
| --- | --- |
| `4b3d04a3e5`, before the change (`advisors-beta-open/stage-verdict-en-1440.png`) | 4 paragraphs |
| `ec620968ac`, after it (`advisors-beta-f1-open/stage-verdict-en-1440.png`) | **1 block of 288 words** |

Nothing failed: the check counts words, not paragraphs, so all four sessions passed and the wall of text went
to production in `15f5bf8770`, where it is live now.

**Fixed** (not released): the rule now reads *"write every line break as `\n` (a blank line between paragraphs is
`\n\n`), never a real one. Paragraphs are welcome in the long texts."* Two guards went in with it, because this
bug has two halves and the first one hid the second:

- `test_the_output_rule_asks_for_escaped_line_breaks_not_none` — the escape is easy to get wrong in a non-raw
  Python string: written with one backslash it becomes a real newline and **cuts the sentence in half**, which
  is exactly what the first attempt at this fix did. The test fails on that form and on the shipped
  "no line breaks" form, and was checked against both.
- `check-advisors.mjs` now reports the Chair's answer's **paragraph count** as an INFO line. It is reported,
  never failed: a short answer may honestly be one paragraph.

**Still to prove:** a beta release and a re-run, to see the paragraphs come back on a real model. Then
production, which is serving the flattened text until then.

### F-7 — a failed turn's tokens are not recorded. **FIXED 2026-10-27.**

When a seat ends up absent the turn is saved with no usage (`engine.turn` passes `None`), so the attempts that
failed cost money that never reaches `cost_usd`. **The $0.29 median above is therefore a floor, not an exact
figure** — understated most in the sessions that lost a seat.

**Fixed 2026-10-27.** `SeatError` now carries the `Usage` the failed attempts accumulated, and `engine.turn`
saves the absent turn with it instead of `None`, so the tokens and cost reach the turn row and `store.finish`
sums them into the session. The screen is unchanged: there is still no answer to show. One case is left and is
not worth code — when the **Chair** fails, `turn` re-raises without saving a row at all, so that session (which
fails entirely) still loses its tokens. A test covers the advisor case:
`test_a_seat_that_never_answers_is_absent_and_its_failed_attempts_are_still_paid_for`, which also pins the
third attempt from F-1. **The six figures above were measured before this fix and are not restated.**

## Still to do

1. ~~F-1~~ — **CLOSED**: changed in `ddf29d1`, released to beta as `ec620968ac`, and both modes re-run on a
   real model with **zero round-one absences** in 24 answers across four sessions. See the re-run below.
2. ~~F-5~~ — **CLOSED**: the owner chose option B on 2026-10-27 (`ec62096`); the patterns and the reasoning
   are in `docs/advice-check-f5-2026-10-27.md`. Both choice sessions now pass the advice check with the same
   question that failed in the morning.
3. ~~The owner approves the look on beta~~ — **DONE 2026-10-27**: approved in chat on `4b3d04a3e5`, judged at
   1440 in both languages and at 390 on a phone, knowing no seat's mouth moves and the arc is shallow.
4. **The mouth-open talk frames were never made**, so no seat's mouth moves. Step 22's "Done when" asks the
   mid-session screenshots to show the mouth-open frame; they cannot until those images exist. The seats hold
   still with the speaker's lift and ring instead.
5. **The arc is shallow** — heads rise about 40 px toward the middle, flatter than the owner's reference.
   Left deliberately for the owner to judge on beta.
6. **Production**, with the owner's go-ahead — now the only thing left for Steps 22 and 23. Items 1–3 are done.
7. ~~`c5d68f6` and `4b3d04a` are committed on `rebuild` but not pushed~~ — **all pushed**: on the owner's
   go-ahead of 2026-10-27, `origin/rebuild` is at `db8539a`, which contains every commit of the day including
   the F-1 and F-5 work.

## The F-1 re-run — release `ec620968ac`, both modes, all passed

Beta was moved to `ec620968ac` (`scripts/deploy-staging.sh`, `current` → `releases/ec620968ac`, api 200, web
200) on the owner's go-ahead of 2026-10-27, and both modes ran again against it with the same two commands,
only the output folders changed:

```
BASE_URL=http://localhost:3201 OUT=../docs/screenshots/advisors-beta-f1-open MODE=open \
  node scripts/check-advisors.mjs

BASE_URL=http://localhost:3201 OUT=../docs/screenshots/advisors-beta-f1-choice MODE=choice \
  QUESTION_EN="Is the dividend covered by earnings, or is it only covered while margins hold?" \
  QUESTION_AR="هل التوزيعات مغطاة بالأرباح، أم أنها مغطاة فقط ما دامت الهوامش قائمة؟" \
  node scripts/check-advisors.mjs
```

That release carries the F-1 change (`ddf29d1`: round one 200–300 words, the Output rule's JSON-string
sentence, three tries per seat, a retry that says what to escape) and the owner's F-5 choice (`ec62096`,
option B).

**Both runs ended `all passed`, exit 0.** Four sessions, 45 files in each output folder.

| Session | Mode | On screen | Round-one absences | Round-one words | Lean tally |
| --- | --- | --- | --- | --- | --- |
| en | open | 1:34 | **none** | 305, 296, 317, 291, 333, 280 | — |
| ar | open | 1:15 | **none** | 249, 239, 262, 269, 265, 270 | — |
| en | choice | 0:59 | **none** | 300, 293, 288, 302, 332, 276 | A 1, B 1, C 4 |
| ar | choice | 1:24 | **none** | 189, 201, 223, 227, 211, 252 | A 0, B 2, C 4 |

Rounds two and three lost nobody either; every final word says what changed; all six conceded a point in
every session; no scores anywhere; the Chair's answer inside 200–350 in all four (288, 206, 296, 211).

`python -m app.debate stats 1` now covers all ten of today's sessions — the morning's six and these four:
**10 done, 0 failed, median 75.17 s, max 94.5 s, total $2.9423.** Taking the morning's $1.7379 off that, the
four re-run sessions cost **$1.2044**, a mean of **$0.3011** — the same price per session as before, so the
third attempt did not cost anything noticeable (nobody needed it in these four).

### What that settles

- **F-1 — CLOSED.** 24 round-one answers across four sessions, both modes, both languages, **zero absences**,
  against four absences in the morning's six. Step 23's second "Done when" is met.
- **F-5 — CLOSED by the owner's decision** (option B, `ec62096`). Both choice sessions passed
  `the Chair's answer is an assessment, not advice` with the *same* question that failed in the morning —
  the one containing "margins hold" and "ما دامت الهوامش قائمة".
- **F-2 — much smaller, not gone.** English round one was 372–514 words against a 250–400 band; it is now
  276–333 against 200–300. Three of twelve English answers are over 300, by 2 to 33 words; Arabic is inside
  except one at 189. Step 23's rule is to keep an over-long answer whole and report it, and that is what the
  INFO lines do. Not worth another prompt change on this evidence.
- **F-6 — much smaller.** Figures the checker could not match: 6 and 0 in English (was 15), 4 and 0 in Arabic
  (was 3). As predicted, shorter answers carry less of the advisors' own arithmetic.
- **F-3, F-4** were already fixed in `4b3d04a3e5`. **F-7** (a failed turn's tokens unrecorded) is untouched and
  now matters less: no turn failed.

### What is left

**The production release, and only that.** The look was approved on beta on 2026-10-27, the check passes clean
in both modes and both languages, and `uv run pytest -q` (169) and `npm test` (28) pass. Steps 22 and 23 need
the owner's go-ahead for the production release — an "Always stop" in the autorun policy — and then Step 10
reruns the launch check against it.
