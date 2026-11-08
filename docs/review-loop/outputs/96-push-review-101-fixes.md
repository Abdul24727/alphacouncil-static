# Output 96: review 101's fix: the value must be well-formed UTF-8

**Review 101 said FIX.** It reproduced two value files read as different bytes. Neither ever matched, and both
returned three zeros and exit 0:
1. "中文测试" saved as UTF-16BE without a byte-order mark.
2. "café" saved as Latin-1.

**What was done** (commits `3284f46` and `ec45135` on `rebuild`, local only; diff in `review-101-fixes.diff`):

1. **The value is validated in bash builtins before any pattern is built:**
   - **No NUL byte anywhere in the file:** checked with `IFS= read -r -d ''`. If that read finds a NUL delimiter, the
     check fails.
   - **The existing checks, unchanged:**
     - a UTF-16 byte-order mark is refused;
     - exactly one line is required;
     - a UTF-8 byte-order mark, CR and surrounding spaces are stripped;
     - control characters are refused.
   - **Strict UTF-8, checked byte by byte** (`utf8_ok`, using `printf -v b '%d' "'X"` under `LC_ALL=C`):
     - lead bytes C2–DF, E0–EF and F0–F4 only;
     - the second byte limited for E0 (A0–BF), ED (80–9F, so no surrogates), F0 (90–BF) and F4 (80–8F);
     - continuations 80–BF, with nothing cut short;
     - C1 controls refused (C2 80 to C2 9F).

     Anything else is exit 2, with "the value is not valid UTF-8; save the file as UTF-8".
2. **Stated limits** (in the script and Step 2):
   - **Mis-encoded but valid:** a file in another encoding whose bytes happen to be valid UTF-8 cannot be told apart,
     for example a value encoded twice.
   - **Found where:** a non-ASCII value is found only where the repository stores it as UTF-8. An ASCII value is
     found in UTF-8, Latin-1, Windows-1252 and UTF-16 text alike.
   - **Commit messages:** the same applies to messages with a non-UTF-8 encoding header.
3. **The tests:** 55 pass (`count-script-test.txt`). The 9 new cases:
   - a valid UTF-8 Chinese value, found (exit 3);
   - a valid UTF-8 accented value, found (exit 3);
   - review 101's UTF-16BE case (exit 2);
   - review 101's Latin-1 case (exit 2);
   - UTF-16LE without a mark (exit 2);
   - a trailing NUL (exit 2);
   - an overlong form (exit 2);
   - a C1 control (exit 2);
   - a cut-short sequence (exit 2).
4. **Against the previous version (`6a68598`):** both of review 101's cases give exit 0 there and exit 2 here.
5. **Reply 101:** its table rows came through as tab-only lines. Their trailing whitespace was stripped (8 lines) so
   that `git diff --check` passes. The text is otherwise as copied, SHA-checked before the strip.
6. **Command output** (`git-state-96.txt`):
   - `git diff --check 6a68598..ec45135` exits 0.
   - `bash -n` passes for both scripts.
   - The tests were rerun after the comment-only commit `ec45135`, with 0 failures.
   - The branch is `[ahead 14]`.
   - The remote's `rebuild` is still `dcc4189`.

**The question for the review:**
- Is this right and complete?
- Does any path remain to exit 0 while a correctly supplied UTF-8 value is in what the range shows or publishes,
  without git or grep lying?
- What is next on the plan? Every open item is the owner's:
  - Step 7;
  - the Argaam count for `eeb9a9d..dcc4189`;
  - a push after the checkpoint;
  - Step 18 item 4.
