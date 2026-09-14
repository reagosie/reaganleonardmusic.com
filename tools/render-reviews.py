"""
render-reviews.py — write the featured reviews and the review count into the pages.

The pages carry a static copy of the quotes so they show without JavaScript and
so search engines see them. This script rewrites that copy from
site/assets/data/reviews.json (the file the monthly refresh job updates).
site.js loads the same JSON at page load and replaces the static copy, so the
static copy only needs refreshing when you want the HTML itself up to date
(before a deploy is a good time).

Run from the repo root:   py tools/render-reviews.py
"""
import html, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(SITE, "assets", "data", "reviews.json")

ZOLA = "https://www.zola.com/wedding-vendors/wedding-bands-djs/reagan-leonard-music"
BASH = "https://www.thebash.com/singer-guitarist/reagan-leonard-music"


def claim_text(data):
    """'32 five-star Google reviews' while every Google review is 5 stars,
    otherwise '32 Google reviews, 4.9 average'. Same rule as site.js."""
    google = data.get("google", {})
    gr = [r for r in data["reviews"] if r.get("source") == "Google"]
    count = google.get("count") or len(gr)
    rating = google.get("rating")
    all_five = all(r.get("stars") == 5 for r in gr) and (rating is None or rating >= 4.95)
    if all_five:
        return count, f"{count} five-star Google reviews"
    return count, f"{count} Google reviews, {rating:.1f} average"


def card(r):
    stars = int(r.get("stars") or 5)
    who = html.escape(r["name"]) + (", " + html.escape(r["role"]) if r.get("role") else "")
    text = html.escape(r.get("excerpt") or r["text"])
    return (f'<article class="review"><div class="review__stars" aria-label="{stars} out of 5 stars">{"★" * stars}</div>'
            f'<p class="review__text">“{text}”</p><p class="review__who">{who}</p>'
            f'<p class="review__source">Review on <a href="{html.escape(r["url"])}" target="_blank" rel="noopener">{html.escape(r["source"])}</a></p></article>')


def main():
    data = json.load(io.open(DATA, encoding="utf-8"))
    by_id = {r["id"]: r for r in data["reviews"]}
    count, claim = claim_text(data)
    google_url = data["google"]["url"]
    links = (f'<p class="reviews__links">Read all <span data-review-count>{count}</span> reviews on '
             f'<a href="{google_url}" target="_blank" rel="noopener">Google</a>, and more on '
             f'<a href="{ZOLA}" target="_blank" rel="noopener">Zola</a> and <a href="{BASH}" target="_blank" rel="noopener">The Bash</a>.</p>')
    bad = 0
    for page, ids in data["featured"].items():
        path = os.path.join(SITE, f"{page}.html")
        if not os.path.exists(path):
            continue                      # featured list for a page of another site version
        missing = [i for i in ids if i not in by_id]
        if missing:
            print(f"{page}: unknown review id(s) {missing}, skipped"); bad += 1; continue
        s = io.open(path, encoding="utf-8").read()
        block = f'<div class="reviews" data-reviews="{page}">' + "".join(card(by_id[i]) for i in ids) + "</div>"
        s, n1 = re.subn(r'<div class="reviews(?: reviews--two)?"(?: data-reviews="[^"]*")?>.*?</article></div>', block, s, count=1, flags=re.S)
        s, n2 = re.subn(r'<p class="reviews__links">.*?</p>', links, s, count=1, flags=re.S)
        s, n3 = re.subn(r'<li(?: data-review-claim)?>\d+ (?:five-star )?Google reviews(?:, [\d.]+ average)?</li>',
                        f'<li data-review-claim>{claim}</li>', s, flags=re.S)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        print(f"{page}: {len(ids)} quotes written ({n1} block), links line {n2}, count line {n3}")
    print(f"Count shown: {claim}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
