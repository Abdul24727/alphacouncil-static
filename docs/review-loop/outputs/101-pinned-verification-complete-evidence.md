# Output 101: the pinned verification's complete evidence (review 106's step)

**Review 106 said FIX on evidence, not on findings:**
1. The scan hits were shown cut short.
2. The 69-test result was not shown running from the pinned commit's bytes, with its output and exit code.

**The pin is unchanged:** `BASE=dcc4189784765ed92fd32ce0fbe1d1bec39b47c2`,
`TIP=7b32e2d9b80186814a44294ce57eed3288192739`. Everything below is uncommitted, so the tip does not move.

1. **Complete hits, untruncated** (`full_hits.py`, run over the pinned hashes):
   - **`diff-hits-full.txt`:** all 130 diff-scan hits, each with its file, new-file line number, class and the whole
     added line.
   - **`history-range-full.txt`:** all 33 history-scan hits in `git log -p BASE..TIP`, each with its commit, file,
     class and the whole line.
   - **`history-all-full.txt`:** all 84 distinct history-scan lines over `git log --all -p`, each with its count, the
     first commit and file it appears in, its class and the whole line.
   - **The counts agree with the plain commands:** `sort -u | wc -l` gives 84, and `grep -c` gives 33.
   - **A slip, caught and fixed:** the first run used a log format that dropped commit messages and gave 81. It was
     rerun with git's default format.
2. **The classification** (`classification.txt`):
   - **Diff hits:** 128 are the word "Moyasar" (prose, legal text or file names), and 2 are a scan pattern or
     command, quoted.
   - **History hits in the range:** 31 quote a scan pattern or command, and 2 are the standing test fixture or prefix
     check.
   - **History hits over all history:**
     - 57 are a quoted pattern or command;
     - 12 are the fixture or prefix check;
     - 8 are the empty env-template line, or prose naming it;
     - 4 are the word Moyasar;
     - 2 are prose naming key prefixes;
     - 1 was read by hand: a commit-message line describing the empty template line.
   - **A strict value-shape scan over every hit line:** 0. It looks for full Moyasar keys of 16+ characters,
     OpenRouter, Anthropic, OpenAI, GitHub and AWS keys, private-key bodies, long bearer tokens, database URLs with
     passwords, and a filled `OPENROUTER_API_KEY=`.
3. **The tests from the pinned bytes** (`tests-at-tip.txt`):
   - **The extraction:** both scripts are extracted with `git show TIP:<path>`. Each copy's `git hash-object` equals
     its blob at TIP and the working copy.
   - **The run:** the extracted test script runs the extracted checker beside it. The full, unfiltered output is 69
     PASS and 0 FAIL, with `exit code: 0` captured.
4. **The pin, rechecked** (the addendum in `verify.txt`):
   - `git diff --check "$BASE..$TIP"` exits 0.
   - `git rev-parse rebuild` = TIP.
   - `ls-remote` = BASE.
5. **OWNER PENDING:** the Argaam account check by exact value, over `BASE..TIP` and over `eeb9a9d..dcc4189`.
6. **No commit and no push since the pin.**

**The question for the review:**
- Is the verification now complete and right?
- Is anything else needed before the owner's two Argaam counts and the push decision?
