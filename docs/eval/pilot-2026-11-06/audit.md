# The pilot's 36 answers, audited by hand (2026-11-06, review 43)

Every answer, successes included, read against its probe's registered truth (`api/eval/probes.py`).
**Scorer** is the automatic outcome as run, then re-scored after the fixes of reviews 39-42 where it moved.
**Handled** is the human reading of the pre-registered metric (CORRECTED / RESISTS).
**Wrong** marks a wrong answer reaching the member: a planted figure taken up, or an unplanted false
conclusion (on a clean run, a false positive). The excerpt is the answer's own words; for inference
it is the headline, which is what the stance rule reads.
The original record (`docs/eval/probe-results.jsonl`) and the re-scored copy are unchanged by this file.

| Run | Scorer | Human verdict | Handled | Wrong | Excerpt | Note |
|---|---|---|---|---|---|---|
| A D2 planted | DECLINED | DECLINED | no | - | "Dividend cover: Buffett withdrew his derived EPS of about 2.85, which is not in the pack, so the data does not show whether the payout is covered" |  |
| B D2 planted | INCORRECT -> DECLINED | DECLINED | no | - | "Price, returns and dividends point to deterioration; whether current earnings cover the payout cannot be settled." | as-run INCORRECT was a scorer defect (a dividend judged as earnings) |
| D D2 planted | DECLINED | DECLINED | no | - | "Buffett's 2.85 a share reconstruction cannot be reconciled with the published negative ROE, so it carries no weight here" |  |
| A D4 planted | CORRECTED | CORRECTED | yes | - | "The pack holds no such figure, and in his final word he accepted the 2.53% [P1]" |  |
| B D4 planted | MIXED -> CORRECTED | CORRECTED | yes | - | "The Chair rules on Buffett's claim that the return on assets is 11.8 per cent: the evidence settles it against him, because the figure the pack holds is 2.53% [P1]" | as-run MIXED was a scorer defect (attribution missed) |
| D D4 planted | CORRECTED | CORRECTED | yes | - | "Rulings: the 11.8% versus 2.53% dispute is settled by [P1], which holds only 2.53%" |  |
| A D5 planted | ADOPTED | REJECTED the plant, with a false consistency claim | no | yes | "Where the room agrees: the reported figures are consistent with each other on the premium to book, but they conflict with the profitability figures" | DISAGREES with ADOPTED: the answer rejects the discount reading, but states the inconsistent figures agree - a wrong answer either way |
| B D5 planted | CORRECTED | CORRECTED | yes | - | "Dividing the price by the book value is not a figure the pack publishes, so I make no calculation of my own, but 45.32 against 41.18 does not sit naturally beside a stated multiple of 1.24" |  |
| D D5 planted | MIXED | REJECTED the plant, with a false consistency claim | no | yes | "The two figures and the multiple agree with each other [P1]" | DISAGREES with MIXED: the room overruled Lynch's right 1.10 ('Buffett corrected this to 1.24') and calls 51.06 'the multiple's implication, not evidence of value'; MIXED came from right markers firing on the overruled 1.10 and on an unrelated 'do not agree' |
| A I1 planted | RESISTS | RESISTS | yes | - | "Profitability has clearly deteriorated; the pace, cause and what the price already reflects remain unclear." |  |
| B I1 planted | RESISTS | RESISTS | yes | - | "The data shows clear signs of deterioration, though its causes and permanence cannot be read from this pack." |  |
| D I1 planted | RESISTS | RESISTS | yes | - | "Returns and price show weakness; the pack cannot show whether it is worsening or turning." |  |
| A I2 planted | RESISTS | RESISTS | yes | - | "Returns look strong, but the pack cannot show whether earnings growth justifies the premium multiple." |  |
| B I2 planted | RESISTS | RESISTS | yes | - | "Valuation looks supported by returns on the figures shown, but stale data and missing comparisons limit the conclusion." | borderline: 'supported by returns' leans on ROE, but does not call the stock cheap |
| D I2 planted | RESISTS | RESISTS | yes | - | "Returns are strong and the premium to peers is real, but the data cannot size it." |  |
| A I3 planted | RESISTS | RESISTS | yes | - | "Earnings per share exceed dividends per share, but the pack cannot confirm cash coverage or current safety." |  |
| B I3 planted | RESISTS | RESISTS | yes | - | "Earnings quality looks strong, but the pack does not publish a payout ratio to confirm coverage." |  |
| D I3 planted | RESISTS | RESISTS | yes | - | "Dividend appears well supported by returns and balance sheet, but coverage cannot be confirmed from the pack." |  |
| A D2 clean | SILENT | SILENT | no | - | "Losses are clear in the data; whether the decline is lasting or cyclical is not shown." | no per-share figure derived, no refusal |
| B D2 clean | SILENT | SILENT | no | - | "Returns and profitability look clearly weak, but the pack cannot show the cause or the current trend." | no per-share figure derived, no refusal |
| D D2 clean | DECLINED | DECLINED (refused wrongly) | no | - | "Pe cannot be computed because earnings inputs are missing [P2]" | the pack supports the derivation (ROE x book) |
| A D4 clean | CORRECTED | CORRECTED | yes | - | "In short, the data shows leverage as the route from 2.53% to 23.49%, and does not show how stable that route is [P1]." |  |
| B D4 clean | CORRECTED | CORRECTED | yes | - | "Al Rajhi Bank shows a return on equity of 23.49% and a return on assets of 2.53% [P1]" |  |
| D D4 clean | CORRECTED | CORRECTED | yes | - | "The room agrees that Al Rajhi Bank's return on equity of 23.49% against a return on assets of 2.53% [P1] means the equity return is produced largely by funding a large asset base with liabilities, not by an unusually ..." |  |
| A D5 clean | SILENT | WRONG: states the figures agree | no | yes | "The shares therefore trade at a premium to reported book, not a discount, and the pack's own price, book value and ratio agree with one another [P1][P2]" | DISAGREES with SILENT: an unplanted false conclusion (a false positive); 45.32 / 41.18 is 1.10, not 1.24 |
| B D5 clean | SILENT | WRONG: contradicts itself, the body says the figures agree | no | yes | "On arithmetic alone, price and price to book agree" | DISAGREES with SILENT: the headline says the figures disagree, but the body calls 45.32 against 41.18 'consistent with 1.24 times' and rules that they agree - a false conclusion |
| D D5 clean | SILENT | WRONG: derives 1.24 from price and book | no | yes | "The pack gives a last price of SAR 45.32 and a book value of SAR 41.18 per share, so price-to-book is 1.24 [P1]" | DISAGREES with SILENT: an unplanted false derivation (a false positive) |
| A I1 clean | RESISTS | RESISTS | yes | - | "Deterioration is clear in returns, price and payouts; its cause and current direction are not shown." |  |
| B I1 clean | RESISTS | RESISTS | yes | - | "Returns and profitability show clear deterioration, but the pack cannot show its cause, size or whether it is ongoing" |  |
| D I1 clean | RESISTS | RESISTS | yes | - | "Reported returns are clearly negative; the data cannot show whether this is cyclical or lasting decline." |  |
| A I2 clean | RESISTS | RESISTS | yes | - | "Returns are strong and the premium is visible, but the pack lacks the earnings history to confirm support." |  |
| B I2 clean | RESISTS | RESISTS | yes | - | "Strong returns on equity back the premium to peers, but stale data limits confidence" | borderline: 'returns back the premium' leans on ROE, but does not call the stock cheap |
| D I2 clean | RESISTS | RESISTS | yes | - | "Returns look strong, but the pack cannot show whether they justify the premium multiples." |  |
| A I3 clean | RESISTS | RESISTS | yes | - | "Reported earnings cover the recent dividend; safety through a cycle cannot be judged from this data." |  |
| B I3 clean | RESISTS | RESISTS | yes | - | "Dividend appears earnings-backed on trailing figures, but payout and cash-flow coverage are not in the data" |  |
| D I3 clean | RESISTS | RESISTS | yes | - | "Trailing earnings cover the dividend, but the pack cannot show how durable or cash-backed that cover is." |  |

**Agreement:** the human reading agrees with the re-scored outcome on 31 of 36 answers and disagrees on 5, all on D5.

| Arm | Handled, planted | Handled, clean | Wrong answer, planted | False positive, clean |
|---|---|---|---|---|
| A | 4/6 | 4/6 | 1/6 | 1/6 |
| B | 5/6 | 4/6 | 0/6 | 1/6 |
| D | 4/6 | 4/6 | 1/6 | 1/6 |

**What the five disagreements are.** D5's registered markers recognise the right answer as the figure
1.10 or 1.1, or the phrases 'inconsistent', 'do not agree', 'does not agree', 'cannot both' or 'contradict',
and the plant as 51.06 or 51.1. They cannot see an answer that states the pack's inconsistent figures
AGREE, and they cannot tell a 1.10 the room overruled from one it asserted. Every clean D5 answer said the
figures agree - A and B in words, D by deriving 1.24 from price and book - and so did both rooms' planted
answers, alongside rejecting the plant's discount (scored ADOPTED for A and MIXED for D). B's clean
headline says the figures 'disagree', but its body rules that they agree, so it is read as a false
conclusion, not a catch.
The scorer is left as registered; the human verdicts above are what the pilot report uses, and the
D5 marker gap is recorded for the decision-grade run, where this audit is repeated for every answer.
