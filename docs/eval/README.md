# The advisors' bench

Answers the question the audit of 2026-10-27 could not: **do six seats produce a better answer than
one good model given the same evidence, and does the room catch a wrong figure that one model would
carry through?**

Three rooms, one pack:

| Arm | What it is |
| --- | --- |
| A | the room as it ships — six seats on `deepseek/deepseek-v4-pro`, Chair on `anthropic/claude-sonnet-5.5` |
| B | **the Chair's own model, alone**, same pack, same question, same output shape |
| C | six seats spread over three models, the same Chair |

Arm B is deliberately the Chair's model rather than some other one: the sharp question is not
"is Claude good" but **"does the Chair plus six DeepSeek seats beat the Chair on its own?"**

## Why it is reproducible

`packs/*.json` are real `Pack` objects, built once from the market database and committed. Every arm
replays the same bytes, so the data is not a variable between arms — and a re-run months from now
sees what this run saw, not whatever the pipeline holds then.

Everything runs in-process: no HTTP, no accounts, no database writes, no contact with beta or
production. A failed session is recorded as a failed row, not a crash.

## The cells

One ticker per category, chosen from what the data actually holds (probed 2026-10-27), not from a
category list written on paper. `questions.py` records the probe figures. 4280 Kingdom Holding is
deliberately excluded: Alwaleed's seat recuses itself there, so the room would be five seats and the
arms would not be comparable.

## The planted-error probe

One seat's round one is replaced by a scripted answer asserting a payout ratio of **97.4%**, which
the pack's own figures do not support. The engine flags the figure as unverified by itself — that is
not what is being tested. What is being tested is whether the **room** notices: whether a challenge
contests it, and whether the wrong figure survives into the Chair's answer. Arm B is given the same
claim as an analyst's note, so both arms face one probe.

## Running it

```
cd api
uv run python -m eval snapshot                        # rebuild the packs (only when you mean to)
uv run python -m eval run --arm A --dry --plant       # free: the stand-in, proves the plumbing
uv run python -m eval run --repeats 2                 # the real thing; needs OPENROUTER_API_KEY
uv run python -m eval report
```

The key lives on the server, never on a developer's machine, so the paid run happens where the key
is. The packs are committed, so running it there still replays the same bytes.
