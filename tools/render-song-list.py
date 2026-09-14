"""
render-song-list.py — write the songs from tools/song-list.json into the song list page.

Edit tools/song-list.json (a list of genres, each with its songs), then run
from the repo root:   py tools/render-song-list.py [site/song-list.html]

It rewrites the genre filter buttons, the genre blocks and the song count on the
page. Everything else on the page is left alone.
"""
import html, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "song-list.json")
PAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "site", "song-list.html")


CLEAR_BTN = '<button class="chip chip--clear" type="button" hidden>Clear filters \u2715</button></div>'


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def main():
    genres = json.load(io.open(DATA, encoding="utf-8"))
    total = sum(len(g["songs"]) for g in genres)
    jump = '<div class="songs__filters" role="group" aria-label="Filter by genre">' + "".join(
        f'<button class="chip" type="button" data-genre="genre-{slug(g["genre"])}" aria-pressed="false">{html.escape(g["genre"])}</button>' for g in genres) + CLEAR_BTN
    groups = []
    for g in genres:
        items = []
        for s in g["songs"]:
            t = html.escape(s["title"])
            items.append(f"<li>{t} <span>– {html.escape(s['artist'])}</span></li>" if s.get("artist") else f"<li>{t}</li>")
        groups.append(f'<div class="songs__group" id="genre-{slug(g["genre"])}"><h2>{html.escape(g["genre"])}</h2>'
                      f'<ul class="songs__list">{"".join(items)}</ul></div>')
    page = io.open(PAGE, encoding="utf-8").read()
    page, n1 = re.subn(r'(?:<ul class="songs__jump">.*?</ul>|<div class="songs__filters".*?</div>)', jump, page, count=1, flags=re.S)
    page, n2 = re.subn(r'(<div class="songs__group" id="[^"]*">.*</ul></div>)', "".join(groups), page, count=1, flags=re.S)
    page, n3 = re.subn(r'<span class="songs__count">\d+ songs</span>', f'<span class="songs__count">{total} songs</span>', page)
    page, n4 = re.subn(r'\b\d+ songs and counting\b', f'{total} songs and counting', page)
    if not (n1 and n2):
        print("could not find the song list markup on the page; nothing written"); return 1
    io.open(PAGE, "w", encoding="utf-8", newline="\n").write(page)
    print(f"{os.path.relpath(PAGE, ROOT)}: {total} songs in {len(genres)} genres written (jump {n1}, groups {n2}, count {n3}, intro {n4})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
