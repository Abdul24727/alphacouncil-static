# Output 16: review 15's count, corrected

- `docs/release-readiness-2026-11-06.md:57`: the group heading now says "Pipeline tooling, not part of the web
  release (**5** files under `scripts/argaam_ar_labels/`)".
- `git diff --name-status 5c18a3ae46..307d2fc -- scripts/argaam_ar_labels` gives exactly the five listed:
  - A `argaam_pages.py`;
  - M `harvest_ar_statements.py`;
  - M `pair_from_gulf.py`;
  - M `pair_labels.py`;
  - A `test_pair_from_gulf.py`.
- Output 15's line is marked "5; first written as 6, corrected by review 15".
- **The groups now sum to 25:** app 5, tests 3, check scripts 4, pipeline tooling 5, review-loop tooling 1,
  patches and pipeline records 5, records 2. With 307 evidence files and 28 review records, that makes 360.
- `git diff --check` is clean. `git diff --stat 307d2fc..HEAD -- web/src api deploy web/messages web/public`
  is still empty.

**Pending:**
- F-16's after-publish check after 05:00 UTC.
- The owner's decisions: release, push, the `owns` patch.

**The question for the review:** is this sound, and what is the single next pre-approved step toward the final
goal? Not a release, a push, the `owns` patch, a pipeline change or a paid call.
