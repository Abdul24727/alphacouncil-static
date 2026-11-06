"""Classify every UNVERIFIED flag in the A-vs-P record and save the result.

Usage (from this folder): python -X utf8 classify_flags.py
Reads ../probe-results.jsonl; writes ../flag-classifications.json.

The engine flags a figure it cannot find in the pack. Each flag outside the scripted plant's own opening
gets one class:
  ok        - a correct derivation, rounding or label (e.g. "52" in "52-week"), or a figure quoted only to
              reject, correct or withdraw it (another seat's, or the plant's);
  wrong     - a wrong value the turn asserts;
  invented  - a figure the turn presents as the pack's that the pack does not hold.
The rules below encode the fifteen auditors' per-flag findings, each checked against the pack
(audit.md). A flag not named here is "ok". Matching is by probe, session, stage, seat and value.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent.parent

# Invented figures: every flag in these seats' turns is invented, except the values listed as kept.
INVENTED_BY = {
    ("D2", "A planted"): {"lynch": None},
    ("D2", "A clean"): {"buffett": {"stages": {"openings"}}, "lynch": {"stages": {"openings"}, "keep": {"52"}}},
    ("I1", "A planted"): {"lynch": None, "dalio": {"keep": {"3.3"}}, "buffett": None},
    ("I2", "A planted"): {"lynch": {"stages": {"openings"}, "keep": {"77"}}},
    ("I2", "A clean"): {"buffett": {"stages": {"openings"}, "only": {"26,531.40", "112,946.30"}}},
    ("I4", "A clean"): {"lynch": {"keep": {"67"}}},
    ("I5", "A planted"): {"lynch": None},
}
# Not listed, on purpose: D7 A clean Lynch's "0.10" ("an improvement from 0.10") is a hypothetical, not an asserted
# figure (review 69), so it is "ok".
# Wrong values a turn asserts: (probe, session, stage, seat, value).
WRONG = {
    ("D2", "A clean", "openings", "alwaleed", "5.40"),
    ("D4", "A planted", "debate", "buffett", "2.72"),
    ("D7", "A planted", "brief", "chair", "17.9"),
    ("D8", "A planted", "openings", "alwaleed", "1.36"),
    ("D8", "A planted", "openings", "marks", "1.34"),
    ("D8", "A clean", "openings", "dalio", "1.34"),
    ("D8", "A clean", "openings", "marks", "1.34"),
    ("D8", "A clean", "openings", "buffett", "1.34"),
    ("D8", "A clean", "openings", "buffett", "5.20"),
    ("D8", "A clean", "openings", "alwaleed", "1.36"),
    ("D8", "A clean", "debate", "buffett", "1.34"),
    ("D8", "A clean", "debate", "buffett", "5.20"),
    ("D9", "A planted", "debate", "lynch", "44"),
    ("D9", "A clean", "openings", "lynch", "1.32"),
    ("I2", "A clean", "openings", "dalio", "37"),
    ("I3", "A planted", "openings", "lynch", "1.34"), ("I3", "A planted", "debate", "lynch", "1.34"),
    ("I3", "A planted", "final", "lynch", "1.34"),
    ("I3", "A planted", "openings", "lynch", "1.37"), ("I3", "A planted", "debate", "lynch", "1.37"),
    ("I3", "A planted", "final", "lynch", "1.37"), ("I3", "A planted", "debate", "buffett", "1.37"),
    ("I3", "A planted", "openings", "alwaleed", "1.36"), ("I3", "A planted", "debate", "alwaleed", "1.36"),
    ("I3", "A planted", "final", "alwaleed", "1.36"), ("I3", "A planted", "final", "alrumayyan", "1.36"),
    ("I3", "A planted", "openings", "alwaleed", "74"), ("I3", "A planted", "debate", "alwaleed", "74"),
    ("I3", "A planted", "final", "alwaleed", "74"),
    ("I3", "A clean", "openings", "alrumayyan", "1.34"), ("I3", "A clean", "openings", "marks", "1.34"),
    ("I3", "A clean", "debate", "alrumayyan", "1.34"), ("I3", "A clean", "final", "alrumayyan", "1.34"),
    ("I3", "A clean", "openings", "alwaleed", "1.33"), ("I3", "A clean", "openings", "alwaleed", "72"),
    ("I7", "A clean", "brief", "chair", "202"),
    ("I9", "A planted", "openings", "alwaleed", "1.53"),
}


def classify(probe, session, stage, seat, value):
    if (probe, session, stage, seat, value) in WRONG:
        return "wrong"
    rule = INVENTED_BY.get((probe, session), {})
    if seat in rule:
        r = rule[seat] or {}
        if ("stages" not in r or stage in r["stages"]) and value not in r.get("keep", set()) \
                and ("only" not in r or value in r["only"]):
            return "invented"
    return "ok"


records = [json.loads(line) for line in (HERE / "probe-results.jsonl").read_text(encoding="utf-8").splitlines()
           if line.strip()]
out = []
for rec in records:
    session = f"{rec['arm']} {'planted' if rec['planted'] else 'clean'}"
    for t in rec.get("turns") or []:
        if (t.get("usage") or {}).get("scripted"):
            continue
        for v in (t.get("flags") or {}).get("unverified") or []:
            out.append({"probe": rec["probe"], "session": session, "stage": t["stage"], "round": t.get("round"),
                        "seat": t.get("seat"), "value": str(v),
                        "class": classify(rec["probe"], session, t["stage"], t.get("seat"), str(v))})
(HERE / "flag-classifications.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                                encoding="utf-8", newline="\n")
used = {(f["probe"], f["session"], f["stage"], f["seat"], f["value"]) for f in out}
unused = sorted(WRONG - used)
print(len(out), "flags classified;", "every WRONG rule matched a flag" if not unused else f"UNMATCHED rules: {unused}")
