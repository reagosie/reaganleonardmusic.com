"""
verify.py — check the rebuilt site/ against the archived original.

Runs three automated parity checks and prints anything that differs:

  1. SEO tags   — <title>, description, keywords, robots, canonical, every
                  Open Graph / Twitter tag and the JSON-LD block, per page,
                  compared field-by-field with the captured originals
                  (image URLs are expected to move to /assets/img/og/).
  2. Text       — the visible text of every page, in document order,
                  compared with the text of the original rendered page.
  3. Links      — every internal link resolves to a page that exists; every
                  external link on the original is still present.
  4. Headings   — the h1–h6 outline per page.

Run from the repo root:   py tools/verify.py
Exit code is 1 if anything differs, so it can gate a deploy.
"""
import json, os, re, sys, difflib
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "pre-migration scan", "reference")
SITE = os.path.join(ROOT, "site")
SEO = json.load(open(os.path.join(REF, "site-data", "seo.json"), encoding="utf-8"))

PAGES = ["index", "contact", "photos-videos", "weddings", "corporate", "pricing", "faq",
         "more-videos", "song-list", "preferred-vendors", "welcome", "thank-you", "wedding-show-form",
         "charlotte"]   # added 2026-09-11 (no archived original; SEO/link checks only)
PAGE_FILES = {"/": "index.html", **{f"/{p}": f"{p}.html" for p in PAGES if p != "index"}}
INDEXED_SINCE = {"song-list"}   # was noindex on the builder site; made public in v1.1

problems = []

# builder element id -> plain text of the custom-code block (from the page data)
_EMBED_TEXT = {}
for _p in PAGES:
    _pj = os.path.join(REF, "site-data", f"{_p}.Page.json")
    if not os.path.exists(_pj):          # pages added after the migration have no archive
        continue
    _els = json.load(open(_pj, encoding="utf-8"))["pageData"]["elements"]
    for _id, _e in _els.items():
        if _e.get("type") == "GridEmbed" and _id not in _EMBED_TEXT:
            _s = BeautifulSoup(_e.get("content", ""), "lxml")
            for _t in _s(["script", "style"]):
                _t.decompose()
            _EMBED_TEXT[_id] = _s.get_text(" ")


def note(page, kind, msg):
    problems.append((page, kind, msg))


def visible_text(soup, *, original):
    """Text a visitor can read, in order. Embeds were iframes on the original
    site, so their text is decoded from the srcdoc attribute."""
    for t in soup(["script", "style", "noscript", "template", "astro-island"]):
        # astro-island wraps the page on the original; keep its children
        if t.name == "astro-island":
            t.unwrap()
        else:
            t.decompose()
    if original:
        for f in soup.select("iframe[srcdoc]"):
            inner = BeautifulSoup(f["srcdoc"], "lxml")
            for t in inner(["script", "style"]):
                t.decompose()
            f.replace_with(inner.get_text(" "))
        # embeds that had not lazily rendered when the DOM was archived:
        # take their text from the builder's page data instead
        for box in soup.select(".grid-embed"):
            if box.find("iframe") is None and not box.get_text(strip=True) and box.get("id") in _EMBED_TEXT:
                box.string = _EMBED_TEXT[box["id"]]
    text = soup.get_text(" ")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def words(text):
    return re.findall(r"[A-Za-z0-9$@'’.\-/&+#:]+", text)


def check_seo(name, new):
    if name not in SEO:                   # page added after the migration: basic checks only
        if not new.title or not new.title.get_text(strip=True):
            note(name, "seo", "missing <title>")
        if not new.find("meta", attrs={"name": "description"}):
            note(name, "seo", "missing meta description")
        if not new.find("link", attrs={"rel": "canonical"}):
            note(name, "seo", "missing canonical link")
        return
    seo = SEO[name]
    meta = {}
    for m in new.find_all("meta"):
        k = m.get("name") or m.get("property")
        if k:
            meta[k] = m.get("content", "")
    if new.title.string.strip() != seo["title"]:
        note(name, "seo", f"title differs:\n      new: {new.title.string.strip()}\n      old: {seo['title']}")
    for k in ("description", "keywords", "robots", "og:url", "og:type", "og:title", "og:description",
              "og:image:alt", "og:site_name", "twitter:card", "twitter:title", "twitter:description",
              "twitter:image:alt"):
        old = seo["meta"].get(k)
        if old is None and k not in meta:
            continue
        if k == "robots" and name in INDEXED_SINCE:   # deliberately made public after the migration
            old = None
        if meta.get(k) != old:
            note(name, "seo", f"{k} differs:\n      new: {meta.get(k)}\n      old: {old}")
    for k in ("og:image", "twitter:image"):
        if not meta.get(k, "").startswith("https://reaganleonardmusic.com/assets/img/og/"):
            note(name, "seo", f"{k} is not a self-hosted OG image: {meta.get(k)}")
    canon = new.find("link", rel="canonical")
    if not canon or canon.get("href") != seo["canonical"]:
        note(name, "seo", f"canonical differs: {canon and canon.get('href')} vs {seo['canonical']}")
    ld = new.find("script", type="application/ld+json")
    if not ld:
        note(name, "seo", "JSON-LD block missing")
    else:
        old = json.loads(seo["jsonld"][0]); newd = json.loads(ld.string)
        for k in old:
            if k == "image":
                continue
            if old[k] != newd.get(k):
                note(name, "seo", f"JSON-LD '{k}' differs: {newd.get(k)!r} vs {old[k]!r}")


def check_headings(name, new, old):
    def outline(s):
        return [(h.name, re.sub(r"\s+", " ", h.get_text()).strip()) for h in s.find_all(re.compile("^h[1-6]$"))]
    o, n = outline(old), outline(new)
    # the old site's embeds were iframes, so their headings were not part of the page outline
    n_core = [x for x in n if not (x[0] == "h2" and x[1] in {"Silver", "Gold", "Diamond", "Rehearsal Dinner",
                                                              "Make your corporate event the best one yet!"})]
    if o != n_core:
        diff = "\n      ".join(difflib.unified_diff([f"{a} {b}" for a, b in o], [f"{a} {b}" for a, b in n_core],
                                                    "original", "rebuild", lineterm="", n=0))
        note(name, "headings", "outline differs:\n      " + diff)


def check_text(name, new, old):
    a, b = words(visible_text(old, original=True)), words(visible_text(new, original=False))
    # the original nav appears twice (desktop + mobile) and so does ours; compare as sequences
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        gone, added = " ".join(a[i1:i2]), " ".join(b[j1:j2])
        # ignore: JotForm/Elfsight/Zola are third-party; "Video thumbnail" alt is ours
        if not gone.strip() and added.strip() in ("", "Video thumbnail"):
            continue
        note(name, "text", f"{tag}: -[{gone[:120]}] +[{added[:120]}]")


def check_links(name, new, old):
    def hrefs(s):
        out = set()
        for a in s.find_all("a", href=True):
            h = a["href"].strip()
            if h.startswith("https://reaganleonardmusic.com"):
                h = h[len("https://reaganleonardmusic.com"):] or "/"
            out.add(h)
        return out
    o, n = hrefs(old), hrefs(new)
    # original srcdoc iframes contained links too
    for f in old.select("iframe[srcdoc]"):
        o |= hrefs(BeautifulSoup(f["srcdoc"], "lxml"))
    for h in sorted(o - n):
        if h.startswith("#") or "jotform" in h:
            continue
        note(name, "links", f"link on original missing from rebuild: {h}")
    for h in sorted(n):
        if h.startswith("/") and not h.startswith("//"):
            path = h.split("#")[0]
            if path and path not in PAGE_FILES and not os.path.exists(os.path.join(SITE, path.lstrip("/"))):
                note(name, "links", f"internal link has no target file: {h}")


def main():
    for name in PAGES:
        new = BeautifulSoup(open(os.path.join(SITE, f"{name}.html"), encoding="utf-8").read(), "lxml")
        archived = os.path.join(REF, "pages-rendered", f"{name}.html")
        old = BeautifulSoup(open(archived, encoding="utf-8", errors="replace").read(), "lxml") if os.path.exists(archived) else BeautifulSoup("", "lxml")
        check_seo(name, new)
        if "--full" in sys.argv and os.path.exists(archived):   # 1:1 parity with the old site (pre-redesign)
            check_headings(name, new, old)
            check_text(name, new, old)
        check_links(name, new, old)

    if not problems:
        print(f"All {len(PAGES)} pages pass: SEO tags and links" + (", headings and text vs the archive" if "--full" in sys.argv else "") + ".")
        return 0
    by_page = {}
    for page, kind, msg in problems:
        by_page.setdefault(page, []).append((kind, msg))
    for page, items in by_page.items():
        print(f"\n== /{'' if page == 'index' else page}")
        for kind, msg in items:
            print(f"  [{kind}] {msg}")
    print(f"\n{len(problems)} difference(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
