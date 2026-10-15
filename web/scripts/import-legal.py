"""Copy the current legal documents from the old static site into this app, verbatim.

The old site's pages are generated from the signed-off .docx files (legal/build_pages.py)
and carry a canonical content hash. This script lifts each page's document text out of
that HTML without rewriting a word, keeps the hash, and writes one JSON file per document
and language under src/content/legal/. Re-run it when the old site's documents change:

    python scripts/import-legal.py C:/projects/alphacouncil-static/legal

It reads the old repository and never writes to it.
"""

import html
import json
import re
import sys
from pathlib import Path

DOCS = ["terms", "privacy", "refunds", "cookies", "ai-financial-disclaimer"]
OUT = Path(__file__).resolve().parent.parent / "src" / "content" / "legal"
BLOCK = re.compile(r"<(h2|h3|p|li|th|td)\b[^>]*>(.*?)</\1>", re.S)


def text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def blocks(fragment: str) -> list[str]:
    return [t for _tag, inner in BLOCK.findall(fragment) if (t := text(inner))]


def relink(fragment: str, locale: str) -> str:
    """Old static routes -> this app's routes (/legal/x/ar -> /ar/legal/x). Text is untouched."""

    def sub(m: re.Match) -> str:
        href = m.group(1)
        if href == "/index.html":
            href = "/ar" if locale == "ar" else "/"
        elif href.startswith("/legal"):
            parts = href.strip("/").split("/")
            # The old site marks the Arabic version with a trailing /ar; anything else is English.
            href = ("/ar/" if parts[-1] == "ar" else "/") + "/".join(p for p in parts if p != "ar")
        return f'href="{href}"'

    return re.sub(r'href="([^"]+)"', sub, fragment)


def parse(page: str, locale: str) -> dict:
    main = page[page.index('<main id="content">') : page.index("</main>")]
    meta = dict(re.findall(r"<span><b>([^<]+)</b>\s*([^<]+)</span>", main))
    operator = re.search(r'<p class="operator">(.*?)</p>', main, re.S).group(1)
    note = re.search(r'<p class="translation-note">(.*?)</p>', main, re.S)
    body_m = re.search(r'<div id="legal-body" data-canonical-hash="([0-9a-f]+)">(.*?)</div>\s*$', main, re.S)
    if body_m:
        canonical, body = body_m.group(1), body_m.group(2)
    else:  # Arabic pages: the document follows the operator line directly.
        canonical, body = None, main[main.index(operator) + len(operator) + len("</p>") :]
    toc = re.findall(r'<li><a href="(#sec-\d+)">(.*?)</a></li>', main)
    return {
        "title": text(re.search(r"<h1>(.*?)</h1>", main, re.S).group(1)),
        "version": (meta.get("Version") or meta.get("الإصدار") or "").strip(),
        "effective": (meta.get("Effective date") or meta.get("تاريخ السريان") or "").strip(),
        "updated": (meta.get("Last updated") or "").strip() or None,
        "operator": text(operator),
        "translationNote": relink(note.group(1).strip(), locale) if note else None,
        "toc": [{"href": h, "label": text(label)} for h, label in toc],
        "canonicalHash": canonical,
        "html": relink(body.strip(), locale),
        "blocks": len(blocks(body)),
    }


def merchant(page: str, locale: str) -> dict:
    footer = page[page.index('<footer class="site">') : page.index("</footer>")]
    paras = re.findall(r"<p>(.*?)</p>", footer, re.S)
    return {"html": [relink(p.strip(), locale) for p in paras if "&copy;" not in p]}


def main(root: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for doc in DOCS:
        for locale, rel in (("en", f"{doc}/index.html"), ("ar", f"{doc}/ar/index.html")):
            page = (root / rel).read_text(encoding="utf-8")
            data = parse(page, locale)
            # Faithfulness: the copied body has exactly the old page's text blocks, in order.
            old = blocks(page[page.index('<main id="content">') : page.index("</main>")])
            new = blocks(data["html"])
            assert new == old[len(old) - len(new) :], f"{rel}: copied text differs from the source"
            (OUT / f"{doc}.{locale}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
            )
            print(f"{doc}.{locale}: {data['title']} v{data['version']} ({data['blocks']} blocks)")
    for locale, rel in (("en", "terms/index.html"), ("ar", "terms/ar/index.html")):
        page = (root / rel).read_text(encoding="utf-8")
        (OUT / f"merchant.{locale}.json").write_text(
            json.dumps(merchant(page, locale), ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "C:/projects/alphacouncil-static/legal"))
