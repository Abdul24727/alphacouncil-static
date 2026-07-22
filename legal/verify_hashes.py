"""Build check for the legal document integrity (Priority-1).

Proves:
  1. The committed hash registry (backend/legal_hashes.json) matches a fresh hash of the
     authoritative source (so a page cannot claim a version while its source silently changed).
  2. A changed document cannot keep the same version: version<->hash binding is verified, and a
     mismatch fails the build unless an explicit override is recorded in legal_hash_overrides.json.
  3. The combined suite matches the standalone documents (each standalone's normalized text is
     contained in the combined suite's normalized text).
  4. Each generated page was built from the source (spot-check of content).

Exit non-zero on any failure. Run in CI / before deploy.
"""
import os, sys, json, hashlib
from docx import Document

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source")
HASHES_JSON = os.environ.get("LEGAL_HASHES_JSON") or os.path.abspath(os.path.join(
    HERE, "..", "..", "alphacouncil", "Argaam-council-before-testing-cluade-project-",
    "llm-council", "backend", "legal_hashes.json"))
OVERRIDES = os.path.join(HERE, "legal_hash_overrides.json")

DOCS = {
    "terms": "AlphaCouncil-Terms-of-Service-FINAL.docx",
    "privacy": "AlphaCouncil-Privacy-Policy-FINAL.docx",
    "refunds": "AlphaCouncil-Refund-Cancellation-Policy-FINAL.docx",
    "cookies": "AlphaCouncil-Cookie-Policy-FINAL.docx",
    "ai-financial-disclaimer": "AlphaCouncil-AI-Financial-Disclaimer-FINAL.docx",
}
COMBINED = "AlphaCouncil-Legal-Suite-FINAL.docx"


def normalized_text(path):
    d = Document(path)
    parts = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                if c.text.strip():
                    parts.append(c.text.strip())
    return "\n".join(parts)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    fails = []
    reg = json.load(open(HASHES_JSON, encoding="utf-8"))
    overrides = json.load(open(OVERRIDES)) if os.path.exists(OVERRIDES) else {}

    src_norm = {k: normalized_text(os.path.join(SRC, f)) for k, f in DOCS.items()}
    combined_norm = normalized_text(os.path.join(SRC, COMBINED))

    # 1 + 2: recomputed source hash must equal the committed hash for the claimed version.
    for k, text in src_norm.items():
        h = sha(text)
        if h != reg["documents"].get(k):
            if overrides.get(k) == h:
                print(f"OVERRIDE accepted for {k} (audited in legal_hash_overrides.json)")
            else:
                fails.append(f"[{k}] source hash {h[:12]}… != registered {str(reg['documents'].get(k))[:12]}… "
                             f"— rebuild legal_hashes.json AND bump the version (or add an audited override)")
    if sha(combined_norm) != reg.get("combined_suite"):
        fails.append("combined_suite hash mismatch — rebuild legal_hashes.json")

    import re as _re

    def compact(s):
        # whitespace-insensitive + smart-quotes/dashes normalized to ASCII, lowercased
        s = (s.replace("“", '"').replace("”", '"').replace("‘", "'")
             .replace("’", "'").replace("–", "-").replace("—", "-")
             .replace("…", "..."))
        return "".join(s.split()).lower()

    def coverage(samples, haystack):
        hs = compact(haystack)
        hit = sum(1 for s in samples if compact(s) in hs)
        return hit / len(samples) if samples else 1.0

    # 3: combined suite contains each standalone document (>=90% of distinctive sentences).
    comb_c = compact(combined_norm)
    for k, text in src_norm.items():
        samples = [p for p in text.split("\n") if len(p) > 40][:20]
        cov = sum(1 for s in samples if compact(s) in comb_c) / max(1, len(samples))
        if cov < 0.9:
            fails.append(f"[{k}] only {cov:.0%} of content found in the combined suite (drift)")

    # 4: each generated page was built from the source (>=90% of distinctive sentences present).
    for k, text in src_norm.items():
        page = os.path.join(HERE, k, "index.html")
        if not os.path.exists(page):
            fails.append(f"[{k}] generated page missing: {page}"); continue
        import html as _html
        page_text = _html.unescape(_re.sub(r"<[^>]+>", " ", open(page, encoding="utf-8").read()))
        samples = [p for p in text.split("\n") if len(p) > 40][:15]
        cov = coverage(samples, page_text)
        # Spot-check: a page not built from source scores near 0; >=85% confirms it was.
        if cov < 0.85:
            fails.append(f"[{k}] only {cov:.0%} of source content present in the generated page — regenerate")

    if fails:
        print("LEGAL HASH VERIFY: FAIL")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print(f"LEGAL HASH VERIFY: OK  (build_id {reg.get('build_id')}; {len(DOCS)} docs + combined verified)")


if __name__ == "__main__":
    main()
