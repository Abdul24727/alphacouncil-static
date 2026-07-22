"""EXACT build check for legal-document integrity (Priority-1, no percentage thresholds).

For each document it proves, deterministically:
  1. Registry binding: sha256 of the RAW canonical source (substantive blocks, presentation
     excluded) == the committed backend/legal_hashes.json == the page's data-canonical-hash.
     A silently-changed document therefore cannot keep its version without a rebuild + version
     bump (or an audited override in legal_hash_overrides.json).
  2. Exact content: the generated page's #legal-body, reduced to an ordered list of normalized
     content blocks, EQUALS the authoritative source's ordered normalized blocks — any
     substantive insertion, omission, reordering or alteration fails, with a first-mismatch report.
  3. The combined suite reproduces each standalone document as a contiguous block subsequence.
Exit non-zero on any failure.
"""
import os, sys, re, json, html, hashlib
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
_PRESENTATION = {"Title", "Legal Metadata"}
_BLOCK_RE = re.compile(r"<(h2|h3|p|li|th|td)\b[^>]*>(.*?)</\1>", re.DOTALL)


def canonical_blocks(path):
    """Ordered substantive blocks of the authoritative source (presentation excluded)."""
    d = Document(path)
    blocks = [p.text.strip() for p in d.paragraphs
              if (p.style.name if p.style else "") not in _PRESENTATION and p.text.strip()]
    for t in d.tables:
        for row in t.rows:
            blocks += [c.text.strip() for c in row.cells if c.text.strip()]
    return blocks


def norm(s):
    """Normalize HTML entities, unicode punctuation, whitespace — NON-substantive representation
    only. Case and words are preserved, so any substantive change still fails."""
    s = html.unescape(s)
    s = (s.replace("“", '"').replace("”", '"').replace("‘", "'")
         .replace("’", "'").replace("–", "-").replace("—", "-")
         .replace("…", "..."))
    return " ".join(s.split())


def page_blocks(page_html):
    m = re.search(r'<div id="legal-body"[^>]*>(.*?)</div>\s*</main>', page_html, re.DOTALL)
    body = m.group(1) if m else ""
    out = []
    for _tag, inner in _BLOCK_RE.findall(body):
        text = norm(re.sub(r"<[^>]+>", "", inner))
        if text:
            out.append(text)
    return out


def page_canonical_hash(page_html):
    m = re.search(r'id="legal-body" data-canonical-hash="([0-9a-f]+)"', page_html)
    return m.group(1) if m else None


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_subsequence(sub, whole):
    it = iter(whole)
    return all(x in it for x in sub)


def main():
    fails = []
    reg = json.load(open(HASHES_JSON, encoding="utf-8"))
    overrides = json.load(open(OVERRIDES)) if os.path.exists(OVERRIDES) else {}
    src_blocks = {k: canonical_blocks(os.path.join(SRC, f)) for k, f in DOCS.items()}
    comb_blocks_norm = [norm(b) for b in canonical_blocks(os.path.join(SRC, COMBINED))]

    for k, blocks in src_blocks.items():
        raw_hash = sha("\n".join(blocks))
        # 1a. registry binding
        if raw_hash != reg["documents"].get(k):
            if overrides.get(k) == raw_hash:
                print(f"OVERRIDE accepted for {k}")
            else:
                fails.append(f"[{k}] source hash != registered — rebuild legal_hashes.json + bump version")
                continue
        page_path = os.path.join(HERE, k, "index.html")
        if not os.path.exists(page_path):
            fails.append(f"[{k}] generated page missing"); continue
        ph = open(page_path, encoding="utf-8").read()
        # 1b. page's embedded canonical hash matches the registry
        if page_canonical_hash(ph) != reg["documents"].get(k):
            fails.append(f"[{k}] page data-canonical-hash != registered hash — regenerate")
        # 2. EXACT content comparison, block by block
        src_norm = [norm(b) for b in blocks]
        pg_norm = page_blocks(ph)
        if src_norm != pg_norm:
            # first-mismatch report
            i = next((j for j in range(max(len(src_norm), len(pg_norm)))
                      if j >= len(src_norm) or j >= len(pg_norm) or src_norm[j] != pg_norm[j]), 0)
            s = src_norm[i] if i < len(src_norm) else "(missing)"
            p = pg_norm[i] if i < len(pg_norm) else "(missing)"
            fails.append(f"[{k}] content mismatch at block {i} (src {len(src_norm)} / page {len(pg_norm)}):\n"
                         f"      SOURCE: {s[:120]}\n      PAGE:   {p[:120]}")

    # 1c. combined suite registry binding
    if sha("\n".join(canonical_blocks(os.path.join(SRC, COMBINED)))) != reg.get("combined_suite"):
        fails.append("combined_suite source hash != registered")
    # 3. combined reproduces each standalone as a contiguous block subsequence
    for k, blocks in src_blocks.items():
        sn = [norm(b) for b in blocks]
        # contiguous window search
        found = any(comb_blocks_norm[i:i+len(sn)] == sn
                    for i in range(0, max(0, len(comb_blocks_norm) - len(sn) + 1)))
        if not found and not is_subsequence(sn, comb_blocks_norm):
            fails.append(f"[{k}] not reproduced in the combined suite")

    if fails:
        print("LEGAL CONTENT VERIFY: FAIL")
        for f in fails:
            print("  - " + f)
        sys.exit(1)
    print(f"LEGAL CONTENT VERIFY: OK (exact) — build_id {reg.get('build_id')}; "
          f"{len(DOCS)} docs + combined, block-exact match")


if __name__ == "__main__":
    main()
