"""
stamp-assets.py — add a version code to the style and script links on every page.

Browsers (and the Hostinger CDN) keep a saved copy of site.css and site.js for
up to a month. Without a version code, a visitor can get a new page with an old
style sheet, and the page looks broken. This tool rewrites every page so the
links look like

    /assets/css/site.css?v=1a2b3c4d
    /assets/js/site.js?v=5e6f7a8b

where the code is a hash (a short code calculated from the file's contents).
It changes whenever the file changes, so browsers fetch the new file.

Run it from the repo root after any edit to site/assets/css/site.css or
site/assets/js/site.js:

    py tools/stamp-assets.py            # version 1.1 pages in site/
    py tools/stamp-assets.py --check    # only report pages with a stale code

(Version 2.0 does this on its own inside tools/v2/build.py.)
"""
import hashlib, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
ASSETS = ["/assets/css/site.css", "/assets/js/site.js"]


def version_of(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()[:8]


def main():
    check = "--check" in sys.argv
    codes = {a: version_of(os.path.join(SITE, a.strip("/").replace("/", os.sep))) for a in ASSETS}
    stale = 0
    for fname in sorted(os.listdir(SITE)):
        if not fname.endswith(".html"):
            continue
        path = os.path.join(SITE, fname)
        original = io.open(path, encoding="utf-8").read()
        updated = original
        for asset, code in codes.items():
            updated = re.sub(re.escape(asset) + r'(?:\?v=[0-9a-f]+)?(?=")', f"{asset}?v={code}", updated)
        if updated != original:
            stale += 1
            if check:
                print(f"  stale: {fname}")
            else:
                io.open(path, "w", encoding="utf-8", newline="\n").write(updated)
    if check:
        print(f"{stale} page(s) have a stale version code" if stale else "all pages carry the current version codes")
        return 1 if stale else 0
    print("stamped " + ", ".join(f"{a}?v={c}" for a, c in codes.items()) + f" on {stale} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
