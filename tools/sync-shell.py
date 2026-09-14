"""
sync-shell.py — keep the shared header/footer identical across all pages.

The deployed pages in site/ are plain, self-contained HTML files. The header
and footer appear in every file between marker comments:

    <!-- #shell:header start --> … <!-- #shell:header end -->
    <!-- #shell:footer start --> … <!-- #shell:footer end -->

Edit the shared markup ONCE in tools/partials/header.html or footer.html,
then run:

    py tools/sync-shell.py            # rewrite the shell in every page
    py tools/sync-shell.py --check    # just report pages that are out of sync

The current page's nav link is re-marked with "item-content-wrapper--active"
automatically. Optional convenience only — the site deploys without it.
"""
import os, re, sys
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
PARTIALS = os.path.join(ROOT, "tools", "partials")

PAGE_URLS = {
    "index.html": "/", "contact.html": "/contact", "photos-videos.html": "/photos-videos",
    "weddings.html": "/weddings", "corporate.html": "/corporate", "pricing.html": "/pricing",
    "faq.html": "/faq", "more-videos.html": "/more-videos", "song-list.html": "/song-list",
    "preferred-vendors.html": "/preferred-vendors", "welcome.html": "/welcome",
    "thank-you.html": "/thank-you", "wedding-show-form.html": "/wedding-show-form",
    "charlotte.html": "/charlotte",
    "404.html": "/404",
}


def region(kind):
    return re.compile(rf"<!-- #shell:{kind} start -->.*?<!-- #shell:{kind} end -->", re.S)


def header_for(url):
    raw = open(os.path.join(PARTIALS, "header.html"), encoding="utf-8").read()
    soup = BeautifulSoup(raw, "html.parser")
    for a in soup.select("a.item-content"):
        if a.get("href") == url:
            a.parent["class"] = a.parent.get("class", []) + ["item-content-wrapper--active"]
    return str(soup).strip()


def main():
    check = "--check" in sys.argv
    footer = open(os.path.join(PARTIALS, "footer.html"), encoding="utf-8").read().strip()
    changed = 0
    for fname, url in PAGE_URLS.items():
        path = os.path.join(SITE, fname)
        if not os.path.exists(path):
            continue
        original = open(path, encoding="utf-8").read()
        updated = region("header").sub(lambda m: header_for(url), original)
        updated = region("footer").sub(lambda m: footer, updated)
        if updated != original:
            changed += 1
            if check:
                print(f"  out of sync: {fname}")
            else:
                open(path, "w", encoding="utf-8", newline="\n").write(updated)
                print(f"  updated: {fname}")
    if changed == 0:
        print("All pages already in sync.")
    elif check:
        sys.exit(1)


if __name__ == "__main__":
    main()
