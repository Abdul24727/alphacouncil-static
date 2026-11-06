# Output 53: the owner's direction on the advisors' room, the costs measured, and the question of a test

**The owner said in chat, 2026-11-06, quoted in full in `docs/review-loop/MASTER-PLAN.md`:**
- **The aim of the room:** it is "not only for performance". Its presentation of advisors with portraits
  discussing is "a major selling factor" and stays.
- **The build:** if performance is similar and the cost is too high, run it on one model, "two maximum, one for
  keeping the presentation and one is doing the heavy lifting".
- **Paid tests:** extra tests run if Claude and the reviewer judge them necessary; the account is topped up.
- **The site:** "continue on the progress and publish the site"; the lawyer evaluates the published, running site.

**Done in this output (documentation only):**
- **`MASTER-PLAN.md` brought current:**
  - the site is live on `b5655a5064`;
  - today's done items;
  - the open items: the lawyer, F-12 (optional), Step 18 item 4, paid runs per go-ahead;
  - the `owns` fix confirmed;
  - the owner's direction, quoted, with how it sits with the plan.
- **`PROJECT.md`:**
  - **the top-up:** $37.83 read from OpenRouter, and the monitor's credit check ok again;
  - **a changelog entry** for the direction.
- **`docs/council-cost-options-2026-11-06.md`:** the measured costs and three options.

**The costs, from the pilot's live per-run totals:**
- **Per session:** A $0.2511 over 20.5 calls; D $0.1870 over 14.5; B $0.0318 over 1.
- **The split, derived:** one advisor call ≈ (A − D) ÷ 6 = $0.0107, so in A the 18 advisor calls are ≈ $0.19 (77 %)
  and the Chair ≈ $0.06.
- **Labelled as derived:** per-turn costs were not stored by the harness, and the stored real sessions were
  deleted with the test accounts.

**The options:**
- **0, as today:** ~$0.25.
- **1, one call per round:** ~$0.08–0.10, estimated.
- **2, analyst and presenter:** the Chair model decides, and a cheaper model writes the seats' rounds. ~$0.05–0.07,
  estimated.
- **The presentation:** unchanged in all three.
- **Before release, options 1 and 2 need four things:**
  - a setting, off by default;
  - a measured paired comparison with every answer hand-audited;
  - an owner viewing on beta;
  - copy kept true. "Each advisor writes their own full answer at the same time…" (`debate.how.steps.openings`)
    would no longer hold, so it goes to the lawyer before release.

**The site is already published.** alphacouncil.tech is live with billing open, so the lawyer can evaluate it now.

**My recommendation:**
- **The design:** option 2 matches the owner's words most closely.
- **The order:**
  1. Build it behind the setting on `rebuild`, free and offline. Tests and dry runs check the presentation's shape
     against the UI.
  2. Run one paid comparison on beta: A against option 2, on the 15 active probes plus clean controls, one repeat,
     every answer audited.
- **Its cost:** about $5–6 expected, from the pilot's per-run costs. Its cap is to be set by the dry run.
- **No decision-grade A-against-D run is needed for this decision.**

**The questions for the review:** is this sound, is the paid comparison necessary, and what is the single next
pre-approved step?
