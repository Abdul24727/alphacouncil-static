#!/usr/bin/env bash
# The P9 fix-only release candidate, checked in its own worktree (review 84's step), 2026-11-07.
# Local only: nothing is uploaded, pushed, deployed or paid for. The API's Python environment is the main checkout's
# (api/.venv); every test imports `app` from the candidate's own tree, which step 3 prints.
set -u
P=026699b906ea3a513b4f2dbfc37672fa68ee9d42
W=/c/AlphaCouncil-Staging/deploy-p9
REPO=/c/projects/alphacouncil-platform
PY=$REPO/api/.venv/Scripts/python.exe
EV=$REPO/docs/screenshots/p9-no-statements-2026-11-07
step() { echo; echo "### $1"; echo "\$ $2"; }
ex() { echo "[exit $1]"; }
C=$(git -C $W rev-parse HEAD)
echo "P9 release candidate checks, run $(TZ=UTC date '+%Y-%m-%d %H:%M:%S UTC')"

step "1. the candidate: branch, commit, parent, clean tree" "git status -sb; git log -2; git rev-parse HEAD^"
git -C $W status -sb; git -C $W log --oneline -2; echo "commit: $C"; echo "parent: $(git -C $W rev-parse HEAD^) (production $P)"
[ "$(git -C $W rev-parse HEAD^)" = "$P" ]; ex $?

step "2. exactly the four P9 files changed from production, whitespace clean" "git diff --name-status $P HEAD; git diff --check $P HEAD; git show --check HEAD"
git -C $W diff --name-status $P HEAD; git -C $W diff --check $P HEAD; ex $?; git -C $W show --check --format=%h HEAD; ex $?

step "3. the four files' blobs: candidate, rebuild at 2ee892a (the reviewed fix), production before" "git rev-parse <commit>:<file>"
for f in api/app/evidence.py api/app/debate/pack.py api/tests/test_evidence.py api/tests/test_debate.py; do
  c=$(git -C $W rev-parse HEAD:$f); r=$(git -C $REPO rev-parse 2ee892a:$f); p=$(git -C $W rev-parse $P:$f)
  echo "  $f  candidate=$c  rebuild=$r  $([ $c = $r ] && echo SAME || echo DIFFERENT)  production-before=$p"
done

step "4. none of the rejected prototype" "test -e api/app/debate/presenter.py; grep -c debate_engine api/app/settings.py; git diff $P HEAD -- api/app/routers api/app/settings.py web"
cd $W && { test -e api/app/debate/presenter.py && echo "presenter.py PRESENT" || echo "presenter.py absent"; echo "debate_engine in settings.py: $(grep -c debate_engine api/app/settings.py)"; git diff --quiet $P HEAD -- api/app/routers api/app/settings.py web && echo "routers, settings and web: identical to production"; }; ex $?

step "5. the tests import the candidate's own code" "cd $W/api && python -c 'import app.evidence, app.debate.pack'"
cd $W/api && $PY -c "import app.evidence as e, app.debate.pack as p; print(e.__file__); print(p.__file__)"; ex $?

step "6. the P9 tests on the candidate" "pytest -v -k <P9 tests> tests/test_evidence.py tests/test_debate.py"
cd $W/api && $PY -m pytest -v -p no:cacheprovider tests/test_evidence.py -k "p9_says_exactly or never_say_the_source or never_empties or no_cash_flow or no_statements or quarters_alone or without_a_number or balance_sheet_alone" 2>&1 | grep -E "passed|failed|FAILED|ERROR" | sed 's/ *\[ *[0-9]*%\]//'; ex ${PIPESTATUS[0]}
cd $W/api && $PY -m pytest -v -p no:cacheprovider tests/test_debate.py -k "statements or quarters or comparison_packs or invented_statement" 2>&1 | grep -E "passed|failed|FAILED|ERROR" | sed 's/ *\[ *[0-9]*%\]//'; ex ${PIPESTATUS[0]}

step "7. the related files and the whole API suite on the candidate" "pytest -q tests/test_evidence.py tests/test_debate.py tests/test_copilot.py; pytest -q"
cd $W/api && $PY -m pytest -q -p no:cacheprovider tests/test_evidence.py tests/test_debate.py tests/test_copilot.py 2>&1 | tail -1; ex ${PIPESTATUS[0]}
cd $W/api && $PY -m pytest -q -p no:cacheprovider 2>&1 | tail -1; ex ${PIPESTATUS[0]}

step "8. ruff: each changed file on the candidate against production" "ruff check --output-format concise"
cd $W/api && for f in app/evidence.py app/debate/pack.py tests/test_evidence.py tests/test_debate.py; do
  now=$(ruff check --quiet --output-format concise $f 2>/dev/null | grep -c ":")
  before=$(git -C $W show $P:api/$f | ruff check --quiet --output-format concise --stdin-filename $f - 2>/dev/null | grep -c ":")
  echo "  $f  production=$before candidate=$now"
done

step "9. review 83's reproductions and the P9 demonstration, run on the candidate's code" "cd $W/api && python p9-review83-repro.py; python p9-after.py"
cd $W/api && $PY -X utf8 $EV/p9-review83-repro.py > /tmp/rc-repro.txt 2>&1; ex $?
diff <(tr -d '\r' < /tmp/rc-repro.txt) <(tr -d '\r' < $EV/p9-review83-after.txt) && echo "identical to p9-review83-after.txt (rebuild)"
cd $W/api && $PY -X utf8 $EV/p9-after.py > /tmp/rc-after.txt 2>&1; ex $?
diff <(tr -d '\r' < /tmp/rc-after.txt) <(tr -d '\r' < $EV/p9-after.txt) && echo "identical to p9-after.txt (rebuild)"
rm -f /tmp/rc-repro.txt /tmp/rc-after.txt

step "10. the web" "git diff --quiet $P HEAD -- web"
git -C $W diff --quiet $P HEAD -- web; ex $?
echo "the web tree is production's, byte for byte: no web build, typecheck, lint or test can differ from production's"

step "11. nothing pushed or deployed" "git ls-remote origin release/p9-no-statements; readlink beta/production current (read-only ssh)"
echo "remote branch: $(git -C $W ls-remote --heads origin release/p9-no-statements | wc -l) (0 = not pushed)"
ssh -o ConnectTimeout=15 root@alphacouncil.tech "echo beta: \$(readlink -f /opt/alphacouncil-platform/current); echo production: \$(readlink -f /opt/alphacouncil-platform/prod/current)"; ex $?
