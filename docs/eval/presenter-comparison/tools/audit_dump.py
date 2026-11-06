"""Lay out a probe-results file for the hand audit: one markdown file per probe, every displayed turn in
full, with the probe's registered truth and markers, the scorer's outcome, the engine's unverified-figure
flags per turn, and where the plant's false markers fire. Arm P runs also carry the analyst's plan.

Usage (from the api folder): python -X utf8 audit_dump.py <results.jsonl> <out dir>
Reads only; writes only into <out dir>.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from eval import score as S  # noqa: E402
from eval.probes import BY_ID, PLANT_SEAT  # noqa: E402

rows = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)


def flat(v, depth=0):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(f"{'  ' * depth}- {flat(x, depth + 1)}" for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}: {flat(x, depth + 1)}" for k, x in v.items() if x not in (None, "", [], {}))
    return json.dumps(v, ensure_ascii=False)


def blob(data):
    return " ".join(flat(v) for v in (data or {}).values() if isinstance(v, (str, list, dict)))


ORDER = {"A": 0, "P": 1}
by_probe = {}
for r in rows:
    by_probe.setdefault(r["probe"], []).append(r)

for pid, rs in sorted(by_probe.items()):
    p = BY_ID[pid]
    rs.sort(key=lambda r: (not r["planted"], ORDER.get(r["arm"], 9), r["repeat"]))
    lines = [f"# {pid} ({p.family}, cell {p.cell})", "",
             f"**Truth:** {p.truth}", "",
             f"**The plant** (seat {PLANT_SEAT}, planted runs only): {p.headline} {p.text}", "",
             f"**Wrong markers:** {p.wrong}  **Right markers:** {p.right}  **Metric:** {p.metric}"
             f"  **Declined:** {p.declined}  **Exact:** {p.exact}  **Sign:** {p.sign}  **Band:** {p.band}", ""]
    for r in rs:
        tag = f"{r['arm']} {pid} {'planted' if r['planted'] else 'clean'} r{r['repeat']}"
        lines += [f"## {tag}", "",
                  f"- ok {r['ok']}  error {r.get('error')}  outcome **{r.get('outcome')}**  evidence {r.get('evidence')}"
                  f"  gate {r.get('gate_hits')}  challenged {r.get('challenged')}",
                  f"- cost ${r.get('cost_usd')}  calls {r.get('calls')}  engine {r.get('engine')} {r.get('engine_stats')}"
                  f"  extra {len(r.get('extra_calls') or [])}  failed {len(r.get('failed_calls') or [])}"
                  f"  absent {r.get('absent')}  first turn {r.get('first_turn_seconds')}s  total {r.get('seconds')}s",
                  f"- unverified in the answer: {r.get('unverified')}", ""]
        for t in r.get("turns") or []:
            data = t.get("data") or {}
            text = blob(data)
            fired, _ = S.hits(S.normalize_digits(text) if hasattr(S, "normalize_digits") else text, p.wrong, p.metric, p.exact, p.sign)
            right, _ = S.hits(text, p.right, p.metric, p.exact, p.sign)
            unv = (t.get("flags") or {}).get("unverified") or []
            u = t.get("usage") or {}
            src = "SCRIPTED PLANT" if u.get("scripted") else ("shared" if u.get("shared") else u.get("model"))
            marks = []
            if fired:
                marks.append(f"WRONG-MARKERS {fired}")
            if right:
                marks.append(f"right-markers {right}")
            if unv:
                marks.append(f"UNVERIFIED {unv}")
            lines.append(f"### {t.get('stage')}{'' if t.get('round') is None else ' r' + str(t.get('round'))} / {t.get('seat')}"
                         f"  ({src}){'  ' + ' | '.join(marks) if marks else ''}")
            lines.append("")
            if data.get("absent"):
                lines += [f"(absent: {data.get('error')})", ""]
                continue
            for k, v in data.items():
                if v in (None, "", [], {}) or k in ("absent",):
                    continue
                lines.append(f"**{k}:** {flat(v)}")
            lines.append("")
        if r.get("analyst_plan"):
            lines += ["### THE ANALYST'S PLAN (not displayed; for telling what the presenter added)", "",
                      "```json", json.dumps(r["analyst_plan"], ensure_ascii=False, indent=1), "```", ""]
    (out / f"{pid}.md").write_text("\n".join(lines), encoding="utf-8")
    print(pid, len(rs), "runs", sum(len(r.get("turns") or []) for r in rs), "turns")
