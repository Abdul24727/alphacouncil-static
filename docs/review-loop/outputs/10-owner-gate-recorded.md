# Output 10: review 09's issue answered. The gate is the owner's own words, now recorded

Commit `4b057d3`.

Review 09 was right that the repository held only Claude's deferral ("nobody asked for it"). It could not
see the chat, where **the owner said about this exact fix: "Ask me before applying it; it is a behaviour
change to a check script."** That is a standing owner instruction. Per the master plan, the owner's
go-ahead is not something a review can stand in for, and the owner's word outranks §4's general
pre-approval.

What changed, so no later review has to take it on trust:
- `PROJECT.md` §9's note on the fix now quotes the owner's words and says why they were recorded only now.
- `docs/review-loop/MASTER-PLAN.md` gains "Owner instructions given in chat stand, even where the
  repository's general rules would allow more". It lists the standing ones: this fix, never signing in to
  Argaam, and never recording the Argaam account name.
- The patch (`docs/check-advisors-owns-case-2026-11-06.patch`) stays prepared and unapplied, and the owner
  is being asked.

Nothing else changed. The nightly is running (started 00:00 UTC); F-16's after-publish check is due after
05:00 UTC.

**The question for the review:** with that gate respected, what is the single next step Claude may take now
under pre-approved rules toward the final goal? It must not be the owns fix, a release, a push, a pipeline
change or a paid call.
