# Response to the third review round — 2026-10-28

Two concerns, both correct, both now settled rather than argued. **No paid call, no deployment, no
change to production data.** Suite: **249 tests**, up from 242.

The archive is re-sent; the earlier upload did not arrive.

---

## 1. The cap was a forecast. It is now a bound, and that changes the number

The review drew exactly the right distinction and I had not implemented it:

> A hard upper bound derived from model pricing, input size, maximum output tokens, and retry limits.
> A forecast that is monitored and settled after execution. **Those are different guarantees.**

What I had was the second one wearing the first one's name. The reservation was a flat **$0.03**
per call from measured history. The review's worry — three admitted calls each costing four times
their reservation — was not hypothetical: **my own concurrency test asserted
`spent <= cap + over_estimate`**, which is not a hard cap, and I had let that slack stand without
saying so.

### The bound, built from the four inputs named

`eval.budget.bound_for(model, prompt_chars, max_output_tokens, attempts)`:

- **Model pricing** from a table read off OpenRouter's own `/api/v1/models` on 2026-10-28:
  sonnet-5.5 $2.00/$10.00 per million, deepseek-v4-pro $0.955/$1.911, gpt-5.2 $1.75/$14.00. A table,
  not a live lookup, so a bound can be computed with no network — and **an unpriced model raises
  `PriceUnknown` and makes no call**, because guessing there would turn the bound back into a
  forecast without saying so.
- **Input size** from *this call's own prompt*, measured before the request, at a floor of
  **2 characters per token** — pessimistic for English (~4) and adequate for the Arabic these
  prompts also carry.
- **Maximum output tokens** from the request's own ceiling (`MAX_TOKENS` per stage).
- **Retry limit**: × `attempts`, because `llm.ask` can bill that many times.

### What it costs to make it a guarantee

Measured against a real arm-B call — **21,971 characters of prompt**, a 2,200-token output ceiling,
three attempts:

| | |
| --- | --- |
| hard bound | **$0.1319** |
| what the run actually cost on 2026-10-27 | **$0.0292** |
| ratio | **4.5×** |

Priced over the room's real stage structure (brief + *n* openings + faultlines + *n* debate +
*n* final + verdict, chair calls on sonnet and advisor calls on deepseek):

| arm | calls | hard bound | forecast | ratio |
| --- | --- | --- | --- | --- |
| A six seats | 21 | **$1.3620** | $0.2257 | 6.0× |
| D four seats | 15 | $1.0434 | $0.1759 | 5.9× |
| B chair alone | 1 | $0.1320 | $0.0292 | 4.5× |
| E two passes | 2 | $0.2640 | $0.0640 | 4.1× |

**And so the planned run's worst case is about $41, against a $7.27 forecast.** That is the
consequence of the review's question, and it is worth stating plainly rather than burying:

```
balance $50.00; 54 runs
  forecast   $5.74   from the measured history of 2026-10-27
  hard bound $31.64   pricing x prompt size x output ceilings x 3 retries
  cap        $8.00   enforced against the BOUND, per call
refusing to start: the cap is $8.00 but this plan's worst case is $31.64, so the cap could not be
honoured as a hard cap - it would refuse a call part way through.
  Either raise --cap-usd to at least $32 (the run is still only expected to cost $5.74; the cap is
  there to make a catastrophe impossible, not to predict the bill),
  or shorten the plan with --repeats or --only.
```

**A cap of $8 enforced against the bound refuses the run on its first call.** So the previous "hard
cap $8.00" was never a hard cap; it was a forecast ceiling, and the review was right to doubt it.

### Two ceilings, with different jobs

Rather than pick one, the harness now carries both, and says which is which:

| | enforced against | its job |
| --- | --- | --- |
| **`cap_usd`** | each call's computed **bound**, before the call | make a catastrophe impossible. Set to the plan's worst case, so in a normal run it never binds |
| **`expect_usd`** | what has really been **billed** | stop early when spending runs above what the measured history predicts. Set to forecast × 1.5 |

And an audit that catches the bound being wrong: **if a real charge ever exceeds the bound reserved
for it**, that is recorded as an overrun and `should_stop()` halts the run — because from that moment
the price table is wrong and the cap has stopped being a guarantee. A silent overrun inside a
"guarantee" is worse than no guarantee.

### Tests — 18 in `test_eval_budget.py`

The hard-cap test the review's worry demands, with **no slack term**: reservations are the computed
bound, every admitted call is then **settled at its full bound**, and `assert b.spent <= b.cap`.
Plus: the bound built from each named input and checkable by hand ($2,000 chars + 1,000 output
tokens + 1 attempt = $0.012); an unpriced model refusing; the bound sitting 4.5× above the forecast;
a charge above its bound recorded and stopping the run; the forecast ceiling firing without any
overrun; the two ceilings independent; and twenty concurrent takes admitting exactly the number the
cap affords. The older concurrency test that *does* carry a slack term now says in its own docstring
that it exercises the **fallback forecast path**, not the guarantee.

---

## 2. The market-cap cause is established, not inferred

The review was right that a sign change alone does not prove two sources were each correct at their
own timestamp, and right that `market_cap_raw` carrying no visible timestamp left the cause partly
inferred. **It has one — it was simply not in the response I was reading.**

`briefs` has its own `as_of_date`, and the `/peers` endpoint returns `as_of_date`, `last_price` and
`market_cap_mn` **from the same briefs row**. Read-only:

```
  sym     briefs as_of    price     mcap_mn  implied shares_mn
  1180      2026-10-23    34.62    207720.0          6000.0000
  1010      2026-10-23    19.20     76800.0          4000.0000
  1150      2026-10-23    21.46     64380.0          3000.0000
  1050      2026-10-23    18.40     46000.0          2500.0000
  1080      2026-10-23    19.90     39800.0          2000.0000
  1140      2026-10-23    20.30     30450.0          1500.0000
  1030      2026-10-23    11.16     16740.0          1500.0000
```

**`market_cap_mn ÷ briefs.last_price` gives an exact round share count in 7 of 8 rows** — 6,000mn,
4,000mn, 3,000mn, 2,500mn, 2,000mn, 1,500mn, 1,500mn. The eighth (1060) gives 2,054.8mn, which is
simply a company whose share count is not round.

That is not a sign change and it is not an inference. It establishes two things directly:

1. **`market_cap_raw` is internally consistent**: it is `briefs.last_price × shares_out`, computed
   within briefs at **`briefs.as_of_date = 2026-10-23`**.
2. The ticker endpoint serves `last_price` from a different source — `source: "prices_file"`,
   `as_of_date: 2026-10-27` — and stamps the response with **that** date only.

**The two sources are four days apart, and the response shows one date.** Neither figure is wrong;
the defect is that a market cap from the 23rd and a price from the 27th are returned in one `quote`
object under the 27th's date, with briefs' own date surfaced nowhere in it. Provenance and labelling,
not arithmetic.

The gap sizes follow from exactly that: Al Rajhi −1.81%, Aramco −2.61%, Jarir −3.31% live are the
price movements between 23 and 27 October.

**Nothing in production was changed**, per the instruction, and the order the review supports is the
order I would take:

1. **Surface `market_cap_as_of`** in the `quote` object and on screen. It makes nothing less true and
   stops two dates being presented as one. Smallest change; no number moves.
2. **A pack-build consistency check** — flag a market cap and a quote more than a tolerance apart,
   and a stale quote beside fresh ratios. Catches the class rather than the instance, and would have
   caught the P/E artefact of round one too.
3. **Recalculation only after the provider's definition is confirmed** — the vendor's figure may be
   free-float adjusted or defined on a different share class, and the exact round share counts above
   say it is *consistent*, not that it is defined the way we would define it.

---

## Still not done, and still blocked

- **The six-probe benchmark has not run.** It now has two reasons not to: the balance is about
  **$4.74** against a $7.27 forecast, and a cap that can be honoured as a hard cap must be about
  **$32–41**, which is a decision for the owner rather than a default I should set.
- **Production market data unchanged.** All three fixes above await separate review.
- On the review's closing point — that scoring must distinguish correct reasoning, incorrect
  reasoning, appropriate refusal and genuine error detection before another table of percentages is
  worth anything — that is what round two's five outcomes are for: `CORRECTED`, `INCORRECT`,
  `DECLINED`, `REJECTED`, `SILENT`, with `ADOPTED` for propagation. I agree that getting those four
  distinctions right matters more than the percentages, and that is now where the test suite spends
  most of its 249 assertions.
