"""
build.py — assemble the version 2.0 site into site-v2/

Every page is a body fragment in tools/v2/pages/<slug>.html with a JSON
comment at the top (title, description, ...). This script wraps each one in
the shared head, header, footer, adds the structured data, expands the
{{placeholders}} (images, reviews, songs, gallery, videos, forms...), and
writes sitemap.xml, robots.txt and .htaccess. Images, fonts, the reviews
data file and refresh-reviews.php are copied from site/ (the v1 tree) so the
two versions share one set of photos and one reviews file.

Run from the repo root:   py tools/v2/build.py
Preview:                  py tools/serve.py --root site-v2 8081
"""
import hashlib, html, io, json, os, re, shutil, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V1 = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "site-v2")
PAGES_DIR = os.path.join(ROOT, "tools", "v2", "pages")
IMG = os.path.join(V1, "assets", "img")

SITE_URL = "https://reaganleonardmusic.com"
NAME = "Reagan Leonard Music"
PHONE = "864-706-5104"
PHONE_TEL = "+18647065104"
EMAIL = "reagan@reaganleonardmusic.com"
GOOGLE = "https://maps.google.com/?cid=10076934354409939073"
ZOLA = "https://www.zola.com/wedding-vendors/wedding-bands-djs/reagan-leonard-music"
BASH = "https://www.thebash.com/singer-guitarist/reagan-leonard-music"
GIGSALAD = "https://www.gigsalad.com/reagan_leonard_music_greenville"
SOCIAL = {"instagram": "https://www.instagram.com/reaganleonardmusic/",
          "facebook": "https://www.facebook.com/reaganleonardmusic/",
          "youtube": "https://www.youtube.com/channel/UCQ51LuzmFciAL771QM8yeQw"}
JOTFORM_MAIN = "230255417493153"
TODAY = date.today().isoformat()

NAV = [("/weddings", "Weddings"), ("/corporate-events", "Corporate"), ("/private-parties", "Private Parties"),
       ("/pricing", "Pricing"), ("/song-list", "Song List"), ("/reviews", "Reviews"),
       ("/photos-videos", "Photos & Videos"), ("/faq", "FAQ")]
MOBILE_EXTRA = [("/about", "About Reagan"), ("/service-area", "Where I Play"), ("/contact", "Contact")]

REVIEWS = json.load(io.open(os.path.join(V1, "assets", "data", "reviews.json"), encoding="utf-8"))
SONGS = json.load(io.open(os.path.join(ROOT, "tools", "song-list.json"), encoding="utf-8"))
SONG_TOTAL = sum(len(g["songs"]) for g in SONGS)

# Frequently asked questions: one list feeds the FAQ page, the FAQPage
# structured data, and the short question blocks on other pages.
FAQ = [
 ("cost", "How much does it cost to book Reagan Leonard Music?",
  "Performances start at $500. Wedding packages run $500 to $1,000, and most events land between $500 and $3,000 depending on the length of the performance and travel. The full rates are on the <a href=\"/pricing\">pricing page</a>, and every quote is itemized before you commit."),
 ("events", "What kinds of events do you play?",
  "Weddings (ceremony, cocktail hour and reception), corporate events, and private parties such as rehearsal dinners, birthdays, anniversaries, engagement parties and holiday parties. If your event needs live acoustic music and the date is free, the answer is almost certainly yes."),
 ("songs", "Can you play our song?",
  f"Almost certainly. The current <a href=\"/song-list\">song list</a> has {SONG_TOTAL} songs across ten genres, and with enough notice before your date I will learn songs on request, including first-dance and ceremony songs. This list is always growing and if you have a special request, just ask me. I can probably learn it but if I don't think I can do it justice, I will be honest and straightforward with you about that."),
 ("equipment", "Do you bring your own sound equipment?",
  "Yes. All I need is a power outlet or an extension cord nearby. My setup is a Bose L1 Compact sound system, a microphone and stand, a Boss RC-30 looper on request, and all the cables, and it fills indoor and outdoor venues of up to 500 guests. I play a Takamine acoustic guitar."),
 ("travel", "How far will you travel?",
  "I'm based in Greer, SC and play anywhere within about 250 miles: Upstate South Carolina, Western North Carolina, Charlotte, North Georgia and East Tennessee. The first hour of round-trip travel is free; after that travel is $100 per hour."),
 ("length", "How long can you perform?",
  "Up to 5 hours, with a 10 to 15 minute break for each hour played. Most performances run 2 to 3 hours, and shorter sets such as a 30-minute ceremony are common."),
 ("outdoor", "Do you play outdoor ceremonies?",
  "Yes, and most of my wedding ceremonies are outdoors. The sound system carries across a lawn or garden without being loud up front. I only need power within reach of an extension cord."),
 ("toasts", "Can guests use your microphone for toasts and announcements?",
  "Yes. A microphone and speakers for toasts and announcements are included in every package at no extra charge."),
 ("ceremony", "What does ceremony music include?",
  "Up to 30 minutes of soft instrumental guitar while guests are seated, then your processional, any songs during the ceremony itself, and the recessional. You choose the songs; I will suggest options if you would like help."),
 ("booking", "How do I book you?",
  "Send the availability form with your date, venue and event type. I reply personally, usually within a day, with a quote. We then have a free 15-minute call to plan your music, and a signed booking holds the date. I play one event per day, so once your date is booked it is yours."),
 ("solo", "Is it just you, or a band?",
  "Just me: one singer-guitarist with a full sound system. That means one vendor to coordinate, a small footprint at the venue, and a price well below a band's, with a volume that guests can still talk over during dinner and cocktails."),
 ("holiday", "Do you play holiday and Christmas parties?",
  "Yes. The song list includes a Christmas set alongside the regular catalogue, and December company parties and private holiday parties are a regular part of my calendar. Book early; December dates go first."),
]

problems = []


# --------------------------------------------------------------------------- images
_img_cache = {}


def image_files(base):
    """All rendered files for a base name, grouped: {'full': [(w, None)], 'crops': [(w, h)]}."""
    if base in _img_cache:
        return _img_cache[base]
    full, crops = set(), set()
    for f in os.listdir(IMG):
        m = re.match(re.escape(base) + r"-(\d+)(?:x(\d+))?\.(?:jpg|png)$", f)
        if m:
            (crops if m.group(2) else full).add((int(m.group(1)), int(m.group(2)) if m.group(2) else None))
    _img_cache[base] = {"full": sorted(full), "crops": sorted(crops)}
    return _img_cache[base]


def pick_variant(base, variant):
    files = image_files(base)
    if variant == "full":
        return [(w, None) for w, _ in files["full"]]
    crops = files["crops"]
    if variant == "square":
        sel = [c for c in crops if c[0] == c[1]]
    elif variant == "tall":
        sel = [c for c in crops if c[1] > c[0]]
    elif variant == "wide":
        sel = [c for c in crops if c[1] < c[0]]
    else:
        sel = [tuple(int(x) for x in v.split("x")) for v in variant.split(",")]
    # one file per width (some crops exist at 1024x1500 and 1024x1501)
    seen, out = set(), []
    for w, h in sorted(sel):
        if w not in seen:
            seen.add(w); out.append((w, h))
    return out


def picture(base, variant="full", alt="", sizes="100vw", cls="", loading="lazy", fetchpriority=""):
    rungs = pick_variant(base, variant)
    if not rungs:
        problems.append(f"no image files for {base} ({variant})"); return ""
    def name(w, h, ext):
        return f"/assets/img/{base}-{w}{'x' + str(h) if h else ''}.{ext}"
    def srcset(ext):
        return ", ".join(f"{name(w, h, ext)} {w}w" for w, h in rungs)
    # natural dimensions of the fallback for width/height attributes
    from PIL import Image
    w0, h0 = rungs[-1]
    with Image.open(os.path.join(IMG, name(w0, h0, "jpg").split("/")[-1])) as im:
        W, H = im.size
    mid = rungs[min(len(rungs) - 1, max(0, len(rungs) // 2))]
    attrs = f'width="{W}" height="{H}" alt="{html.escape(alt)}" loading="{loading}" decoding="async"'
    if fetchpriority:
        attrs += f' fetchpriority="{fetchpriority}"'
    return (f'<picture class="{cls}">'
            f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
            f'<img src="{name(mid[0], mid[1], "jpg")}" srcset="{srcset("jpg")}" sizes="{sizes}" {attrs}>'
            f'</picture>')


# --------------------------------------------------------------------------- pieces
def review_card(r):
    stars = int(r.get("stars") or 5)
    who = html.escape(r["name"]) + (", " + html.escape(r["role"]) if r.get("role") else "")
    text = html.escape(r.get("excerpt") or r["text"])
    return (f'<article class="review"><div class="review__stars" aria-label="{stars} out of 5 stars">{"★" * stars}</div>'
            f'<p class="review__text">{text}</p><p class="review__who">{who}</p>'
            f'<p class="review__source">Review on <a href="{html.escape(r["url"])}" target="_blank" rel="noopener">{html.escape(r["source"])}</a></p></article>')


def reviews_block(key):
    by_id = {r["id"]: r for r in REVIEWS["reviews"]}
    ids = REVIEWS["featured"].get(key)
    if not ids:
        problems.append(f"reviews.json has no featured list for '{key}'"); ids = REVIEWS["featured"]["index"]
    return f'<div class="reviews" data-reviews="{key}">' + "".join(review_card(by_id[i]) for i in ids if i in by_id) + "</div>"


ARROW = ('<button class="carousel__arrow carousel__arrow--{0}" type="button" aria-label="{1} reviews">'
         '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path d="{2}" fill="none" stroke="currentColor" '
         'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button>')


def reviews_carousel(first_key):
    """Every Google review with text in a sideways-scrolling track with arrows;
    the page's featured reviews come first. site.js reads the same order from
    reviews.json at page load (data-reviews="all")."""
    first = REVIEWS["featured"].get(first_key, [])
    by_id = {r["id"]: r for r in REVIEWS["reviews"]}
    ids = first + [r["id"] for r in REVIEWS["reviews"] if r.get("source") == "Google" and r.get("text") and r["id"] not in first]
    return ('<div class="carousel">' + ARROW.format("prev", "Previous", "M15 5l-7 7 7 7") +
            f'<div class="reviews reviews--carousel" data-reviews="all" data-reviews-first="{first_key}">' +
            "".join(review_card(by_id[i]) for i in ids if i in by_id) + "</div>" +
            ARROW.format("next", "Next", "M9 5l7 7-7 7") + "</div>")


def reviews_wall():
    rs = [r for r in REVIEWS["reviews"] if r.get("source") == "Google" and r.get("text")]
    return '<div class="review-wall" data-reviews="all">' + "".join(review_card(r) for r in rs) + "</div>"


def review_claim():
    g = REVIEWS["google"]; gr = [r for r in REVIEWS["reviews"] if r.get("source") == "Google"]
    count = g.get("count") or len(gr)
    if all(r.get("stars") == 5 for r in gr) and (g.get("rating") is None or g["rating"] >= 4.95):
        return count, f"{count} five-star Google reviews"
    return count, f"{count} Google reviews, {g['rating']:.1f} average"


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


CLEAR_BTN = '<button class="chip chip--clear" type="button" hidden>Clear filters \u2715</button></div>'


def songs_block():
    chips = '<div class="chips" role="group" aria-label="Filter by genre">' + "".join(
        f'<button class="chip" type="button" data-genre="genre-{slug(g["genre"])}" aria-pressed="false">{html.escape(g["genre"])} <span>{len(g["songs"])}</span></button>' for g in SONGS) + CLEAR_BTN
    groups = []
    for g in SONGS:
        items = "".join(f'<li>{html.escape(s["title"])}' + (f' <span>– {html.escape(s["artist"])}</span>' if s.get("artist") else "") + "</li>" for s in g["songs"])
        groups.append(f'<section class="songs__group" id="genre-{slug(g["genre"])}"><h2>{html.escape(g["genre"])} <small>{len(g["songs"])} songs</small></h2><ul class="songs__list">{items}</ul></section>')
    return chips, "".join(groups)


def genre_chips():
    return "".join(f'<li>{html.escape(g["genre"])}</li>' for g in SONGS)


GALLERY = [  # (base, variant, alt, tall?)
 ("ceremony-woods", "tall", "Reagan performing for an outdoor wedding ceremony in the woods", True),
 ("bench-boxwood-wide", "wide", "Reagan seated with his guitar beside a boxwood hedge", False),
 ("garden-ceremony-harp", "square", "Reagan performing at a garden wedding ceremony", False),
 ("stage-dark-venue", "tall", "Reagan performing on stage at a rustic indoor venue", True),
 ("guitar-garden-path", "square", "Reagan playing acoustic guitar on a garden path", False),
 ("stone-wall-autumn", "square", "Reagan playing guitar beside a stone wall in autumn", False),
 ("porch-seated", "wide", "Reagan seated on a porch with his guitar", False),
 ("columns-guitar", "square", "Reagan playing guitar between white columns", False),
 ("forest-rock", "square", "Reagan with his guitar in the forest", False),
 ("stairs-portrait", "tall", "Reagan Leonard with his guitar on a staircase", True),
 ("stool-indoor", "square", "Reagan playing guitar on a stool indoors", False),
 ("portrait-brick-alcove", "square", "Reagan with his guitar in a brick alcove", False),
 ("bench-garden", "square", "Reagan playing guitar on a garden bench", False),
 ("garden-suit-portrait", "square", "Reagan in a suit with his guitar in a garden", False),
]


def gallery_block():
    out = []
    for base, variant, alt, tall in GALLERY:
        fams = [pick_variant(base, v) for v in ("full", "tall", "wide", "square")]
        full = max((f for f in fams if f), key=lambda f: f[-1][0])   # the family with the largest file
        big = full[-1]
        def name(w, h, ext): return f"/assets/img/{base}-{w}{'x' + str(h) if h else ''}.{ext}"
        light = " ".join(f'data-lightbox-{ext}="{", ".join(f"{name(w, h, ext)} {w}w" for w, h in full)}"' for ext in ("avif", "webp"))
        out.append(f'<figure class="gallery__item{" gallery__item--tall" if tall else ""}" data-lightbox-src="{name(big[0], big[1], "jpg")}" '
                   f'data-lightbox-srcset="{", ".join(f"{name(w, h, "jpg")} {w}w" for w, h in full)}" {light}>'
                   + picture(base, variant, alt, "(min-width: 900px) 33vw, 50vw") + "</figure>")
    return '<div class="gallery">' + "".join(out) + "</div>"


LOGOS = [("logo-boot-barn", "Boot Barn"), ("logo-reids", "Reid's"), ("logo-toyota", "Toyota"), ("logo-maa", "MAA"),
         ("logo-greystar", "Greystar"), ("logo-td-synnex", "TD SYNNEX"), ("logo-palmetto-moon", "Palmetto Moon"),
         ("logo-grubb-properties", "Grubb Properties"), ("logo-ushja", "USHJA"), ("logo-southwood-realty", "Southwood Realty"),
         ("logo-willow-bridge", "Willow Bridge"), ("logo-sesblc", "SESBLC"), ("logo-steeples-city-club", "Steeples City Club"),
         ("logo-carolina-golf-club", "Carolina Golf Club")]


def logos_block():
    items = []
    for base, alt in LOGOS:
        crops = image_files(base)["crops"]
        if not crops:
            problems.append(f"missing logo {base}"); continue
        w, h = crops[0]
        items.append(f'<img src="/assets/img/{base}-{w}x{h}.png" width="{w}" height="{h}" alt="{html.escape(alt)}" loading="lazy" decoding="async">'
                     if os.path.exists(os.path.join(IMG, f"{base}-{w}x{h}.png")) else
                     f'<img src="/assets/img/{base}-{w}x{h}.jpg" width="{w}" height="{h}" alt="{html.escape(alt)}" loading="lazy" decoding="async">')
    return '<div class="logos">' + "".join(items) + "</div>"


def video_block(vid, title):
    src = f"https://www.youtube.com/embed/{vid}?autoplay=0&amp;controls=1&amp;playsinline=1&amp;rel=0"
    return (f'<div class="video" data-video-src="{src}" data-title="{html.escape(title)}">'
            f'<img class="video__poster" src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="{html.escape(title)}" loading="lazy" decoding="async">'
            f'<button class="video__play" type="button" aria-label="Play {html.escape(title)}"></button></div>')


def form_section(form_id=JOTFORM_MAIN, heading="Check my availability", intro=None):
    intro = intro or ("Tell me about your event and I'll reply personally, usually within a day, with a quote and my availability. "
                      "The form asks for the details I need to give you a real number, not a range.")
    return f'''<section id="request-quote" class="section section--white booking-section">
  <div class="container booking">
    <div class="booking__side">
      <p class="eyebrow">Booking</p>
      <h2 class="h2">{html.escape(heading)}</h2>
      <p class="lede">{intro}</p>
      <ol class="next-steps">
        <li><strong>You send the form.</strong> Date, venue, event type and what you have in mind.</li>
        <li><strong>I reply with a quote.</strong> Itemized, including any travel, usually within a day.</li>
        <li><strong>We plan the music.</strong> A free 15-minute call, then your song list takes shape.</li>
      </ol>
      <div class="contact-lines">
        <a href="tel:{PHONE_TEL}">{PHONE}</a>
        <a href="mailto:{EMAIL}">{EMAIL}</a>
        <p>Prefer to text? Same number. Based in Greer, SC.</p>
      </div>
    </div>
    <div class="booking__form">
      <div class="form-frame" data-lazy-script="https://form.jotform.com/jsform/{form_id}">
        <noscript><p>The booking form needs JavaScript. You can also email <a href="mailto:{EMAIL}">{EMAIL}</a> or call <a href="tel:{PHONE_TEL}">{PHONE}</a>.</p></noscript>
      </div>
    </div>
  </div>
</section>'''


def cta_band(title="Let's make your event the one people talk about.", sub="Check my availability for your date. No obligation, and I reply personally."):
    return f'''<section class="cta-band">
  <div class="container">
    <h2 class="cta-band__title">{title}</h2>
    <p class="cta-band__sub">{sub}</p>
    <div class="cta-band__actions">
      <a class="btn btn--gold btn--lg" href="/contact#request-quote" data-cta>Check my availability</a>
      <a class="btn btn--ghost btn--lg" href="tel:{PHONE_TEL}">Call {PHONE}</a>
    </div>
  </div>
</section>'''


def faq_items(keys=None, open_first=False):
    items = [f for f in FAQ if keys is None or f[0] in keys]
    out = []
    for i, (k, q, a) in enumerate(items):
        out.append(f'<details class="faq__item" id="faq-{k}"{" open" if open_first and i == 0 else ""}><summary>{html.escape(q)}</summary><div class="faq__answer"><p>{a}</p></div></details>')
    return '<div class="faq">' + "".join(out) + "</div>"


def faq_jsonld():
    def plain(s): return re.sub(r"<[^>]+>", "", s)
    return {"@type": "FAQPage", "@id": f"{SITE_URL}/faq#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for k, q, a in FAQ]}


# --------------------------------------------------------------------------- shell
def header_html(path):
    def item(href, label):
        cur = ' aria-current="page"' if href == path else ""
        return f'<li><a href="{href}"{cur}>{label}</a></li>'
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" id="top">
  <div class="container site-header__inner">
    <a class="site-header__logo" href="/" aria-label="{NAME}, home">
      <img src="/assets/img/rlm-logo-full-white-375.png" srcset="/assets/img/rlm-logo-full-white-375.png 375w, /assets/img/rlm-logo-full-white-768.png 768w" sizes="150px" width="375" height="248" alt="{NAME}" decoding="async">
    </a>
    <nav class="site-nav" id="site-nav" aria-label="Main">
      <ul class="site-nav__list">{"".join(item(h, l) for h, l in NAV)}</ul>
      <ul class="site-nav__list site-nav__list--extra">{"".join(item(h, l) for h, l in MOBILE_EXTRA)}</ul>
      <div class="site-nav__contact"><a href="tel:{PHONE_TEL}">{PHONE}</a><a href="mailto:{EMAIL}">{EMAIL}</a></div>
    </nav>
    <a class="btn btn--gold btn--small site-header__cta" href="/contact#request-quote" data-cta>Check availability</a>
    <button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav"><span></span><span></span><span></span></button>
  </div>
</header>
<div class="cta-bar">
  <a class="btn btn--gold" href="/contact#request-quote" data-cta>Check availability</a>
  <a class="btn btn--outline" href="tel:{PHONE_TEL}">Call</a>
</div>'''


ICONS = {
 "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 4 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zM12 0C8.7 0 8.3 0 7.1.1 2.7.3.3 2.7.1 7.1 0 8.3 0 8.7 0 12s0 3.7.1 4.9c.2 4.4 2.6 6.8 7 7 1.2.1 1.6.1 4.9.1s3.7 0 4.9-.1c4.4-.2 6.8-2.6 7-7 .1-1.2.1-1.6.1-4.9s0-3.7-.1-4.9c-.2-4.4-2.6-6.8-7-7C15.7 0 15.3 0 12 0zm0 5.8a6.2 6.2 0 1 0 0 12.4 6.2 6.2 0 0 0 0-12.4zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.4-11.8a1.4 1.4 0 1 0 0 2.9 1.4 1.4 0 0 0 0-2.9z"/></svg>',
 "facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M24 12.1C24 5.4 18.6 0 12 0S0 5.4 0 12.1C0 18.1 4.4 23 10.1 23.9v-8.4H7.1v-3.5h3v-2.6c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9v2.2h3.3l-.5 3.5h-2.8v8.4C19.6 23 24 18.1 24 12.1z"/></svg>',
 "youtube": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1c.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg>',
}


def footer_html():
    social = "".join(f'<a href="{u}" target="_blank" rel="noopener" aria-label="{k.capitalize()}">{ICONS[k]}</a>' for k, u in SOCIAL.items())
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer__grid">
      <div class="footer__brand">
        <img src="/assets/img/rlm-logo-full-white-375.png" width="375" height="248" alt="{NAME}" loading="lazy" decoding="async">
        <p>Solo acoustic singer-guitarist for weddings, corporate events and private parties. Based in Greer, SC. Serving all of Upstate SC, Western NC, Charlotte, North GA, and East TN.</p>
        <div class="footer__social">{social}</div>
      </div>
      <div>
        <h4>Services</h4>
        <ul><li><a href="/weddings">Wedding music</a></li><li><a href="/corporate-events">Corporate events</a></li><li><a href="/private-parties">Private parties</a></li><li><a href="/pricing">Pricing</a></li><li><a href="/song-list">Song list</a></li></ul>
      </div>
      <div>
        <h4>Explore</h4>
        <ul><li><a href="/about">About Reagan</a></li><li><a href="/reviews">Reviews</a></li><li><a href="/photos-videos">Photos &amp; videos</a></li><li><a href="/faq">FAQ</a></li><li><a href="/contact">Contact</a></li></ul>
      </div>
      <div>
        <h4>Where I play</h4>
        <ul><li><a href="/service-area">Greenville &amp; Upstate SC</a></li><li><a href="/charlotte">Charlotte, NC</a></li><li><a href="/asheville">Asheville &amp; Western NC</a></li><li><a href="/service-area#georgia">North Georgia</a></li><li><a href="/service-area#tennessee">East Tennessee</a></li></ul>
      </div>
    </div>
    <div class="footer__bottom">
      <p class="footer__nap"><strong>{NAME}</strong> · Greer, SC · <a href="tel:{PHONE_TEL}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
      <div class="footer__badges">
        <a href="{ZOLA}?utm_source=vendor&amp;utm_medium=various&amp;utm_content=award" target="_blank" rel="noopener"><img src="https://d1tntvpcrzvon2.cloudfront.net/static-assets/images/badges/best_of_zola_2024.png" width="130" height="130" alt="Best of Zola 2024" loading="lazy"></a>
        <img src="/assets/img/badge-upstate-bridal-association-375x373.png" width="375" height="373" alt="Upstate Bridal Association member" loading="lazy" decoding="async">
      </div>
      <p class="footer__copy">© <span data-year>{date.today().year}</span> {NAME}. Reviews link to their source on Google, Zola and The Bash.</p>
    </div>
  </div>
</footer>'''


def business_graph():
    cities = ["Greenville, SC", "Greer, SC", "Spartanburg, SC", "Anderson, SC", "Clemson, SC", "Asheville, NC", "Hendersonville, NC",
              "Charlotte, NC", "Athens, GA", "Gainesville, GA", "Knoxville, TN", "Chattanooga, TN"]
    return [
     {"@type": ["LocalBusiness", "ProfessionalService"], "@id": f"{SITE_URL}/#business", "name": NAME, "url": SITE_URL,
      "telephone": "+1-864-706-5104", "email": EMAIL, "image": f"{SITE_URL}/assets/img/og/link-preview-1440x756.jpg",
      "logo": f"{SITE_URL}/assets/img/rlm-logo-full-white-768.png",
      "description": "Solo acoustic singer-guitarist for weddings, corporate events and private parties. Based in Greer, SC; playing within about 250 miles: Upstate South Carolina, Western North Carolina, Charlotte, North Georgia and East Tennessee.",
      "priceRange": "$500 - $3000", "address": {"@type": "PostalAddress", "addressLocality": "Greer", "addressRegion": "SC", "postalCode": "29651", "addressCountry": "US"},
      "geo": {"@type": "GeoCoordinates", "latitude": 34.9387, "longitude": -82.2271},
      "areaServed": [{"@type": "GeoCircle", "geoMidpoint": {"@type": "GeoCoordinates", "latitude": 34.9387, "longitude": -82.2271}, "geoRadius": "400000"}] + [{"@type": "City", "name": c} for c in cities],
      "founder": {"@id": f"{SITE_URL}/#reagan"}, "employee": {"@id": f"{SITE_URL}/#reagan"},
      "sameAs": [SOCIAL["facebook"], SOCIAL["instagram"], SOCIAL["youtube"], ZOLA, BASH, GIGSALAD, GOOGLE],
      "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Live music services", "itemListElement": [
        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Wedding ceremony, cocktail hour and reception music", "url": f"{SITE_URL}/weddings"}, "priceSpecification": {"@type": "PriceSpecification", "minPrice": 500, "maxPrice": 1000, "priceCurrency": "USD"}},
        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Corporate event live music", "url": f"{SITE_URL}/corporate-events"}},
        {"@type": "Offer", "itemOffered": {"@type": "Service", "name": "Private party and rehearsal dinner live music", "url": f"{SITE_URL}/private-parties"}}]}},
     {"@type": "Person", "@id": f"{SITE_URL}/#reagan", "name": "Reagan Leonard", "jobTitle": "Singer-guitarist", "url": f"{SITE_URL}/about",
      "worksFor": {"@id": f"{SITE_URL}/#business"}, "homeLocation": {"@type": "Place", "name": "Greer, SC"},
      "sameAs": [SOCIAL["instagram"], SOCIAL["youtube"], SOCIAL["facebook"]]},
     {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": SITE_URL, "name": NAME, "publisher": {"@id": f"{SITE_URL}/#business"}, "inLanguage": "en-US"},
    ]


def head_html(meta, path):
    url = SITE_URL + ("" if path == "/" else path)
    og_img = f"{SITE_URL}/assets/img/og/link-preview-1440x756.jpg"
    title = html.escape(meta["title"]); desc = html.escape(meta["description"])
    robots = "noindex, nofollow" if meta.get("noindex") else "index, follow"
    graph = business_graph() + [{"@type": "WebPage", "@id": f"{url}#webpage", "url": url, "name": meta["title"], "description": meta["description"],
                                 "isPartOf": {"@id": f"{SITE_URL}/#website"}, "about": {"@id": f"{SITE_URL}/#business"}, "inLanguage": "en-US", "dateModified": TODAY}]
    if path != "/":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL},
            {"@type": "ListItem", "position": 2, "name": meta.get("crumb") or meta["title"].split("|")[0].strip(), "item": url}]})
    if meta.get("service"):
        s = meta["service"]
        graph.append({"@type": "Service", "@id": f"{url}#service", "name": s["name"], "serviceType": s["name"], "description": s.get("description", meta["description"]),
                      "provider": {"@id": f"{SITE_URL}/#business"}, "areaServed": {"@type": "GeoCircle", "geoMidpoint": {"@type": "GeoCoordinates", "latitude": 34.9387, "longitude": -82.2271}, "geoRadius": "400000"}, "url": url})
    if meta.get("faq"):
        graph.append(faq_jsonld())
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1440">
<meta property="og:image:height" content="756">
<meta property="og:image:alt" content="Reagan Leonard playing acoustic guitar">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#1E332A">
<link rel="icon" href="/assets/img/favicon-32.png" sizes="32x32">
<link rel="icon" href="/assets/img/favicon-192.png" sizes="192x192">
<link rel="apple-touch-icon" href="/assets/img/favicon-180.png">
<link rel="preload" href="/assets/fonts/fraunces-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/inter-normal-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/site.css?v={asset_version("assets/css/site.css")}">
<script type="application/ld+json">{ld}</script>'''


def asset_version(rel):
    """Short hash of a file in site-v2/, put on its link so browsers and the CDN
    fetch the new file after every change instead of a month-old saved copy."""
    return hashlib.sha1(open(os.path.join(OUT, rel.replace("/", os.sep)), "rb").read()).hexdigest()[:8]


# --------------------------------------------------------------------------- placeholders
def expand(body, path):
    count, claim = review_claim()
    chips, groups = songs_block()
    simple = {
        "review_claim": f'<span data-review-claim>{claim}</span>',
        "review_count": f'<span data-review-count>{count}</span>',
        "song_count": str(SONG_TOTAL),
        "songs": groups, "song_chips": chips, "genre_chips": genre_chips(),
        "gallery": gallery_block(), "logos": logos_block(), "reviews_all": reviews_wall(),
        "form": form_section(), "cta": cta_band(), "phone": PHONE, "phone_tel": PHONE_TEL, "email": EMAIL,
        "faq_all": faq_items(open_first=True),
    }
    def repl(m):
        name, _, args = m.group(1).partition(":")
        parts = [a.strip() for a in args.split("|")] if args else []
        if name in simple:
            return simple[name]
        if name == "img":       # {{img:base|variant|alt|sizes|class|loading}}
            base, variant, alt = parts[0], parts[1] if len(parts) > 1 else "full", parts[2] if len(parts) > 2 else ""
            sizes = parts[3] if len(parts) > 3 and parts[3] else "100vw"
            cls = parts[4] if len(parts) > 4 else ""
            loading = parts[5] if len(parts) > 5 and parts[5] else "lazy"
            return picture(base, variant, alt, sizes, cls, loading, "high" if loading == "eager" else "")
        if name == "hero_bg":   # {{hero_bg:base|variant|position}}
            base, variant = parts[0], parts[1] if len(parts) > 1 else "full"
            pos = parts[2] if len(parts) > 2 else "center"
            return f'<div class="hero__bg" style="--pos:{pos}">' + picture(base, variant, "", "100vw", "", "eager", "high") + "</div>"
        if name == "reviews":
            return reviews_block(parts[0])
        if name == "reviews_carousel":   # {{reviews_carousel:featured-key}}
            return reviews_carousel(parts[0] if parts else "index")
        if name == "video":
            return video_block(parts[0], parts[1] if len(parts) > 1 else "Video")
        if name == "faq":       # {{faq:key,key,key}}
            return faq_items(parts[0].split(","))
        if name == "form_id":
            return form_section(parts[0], parts[1] if len(parts) > 1 else "Check my availability", parts[2] if len(parts) > 2 else None)
        if name == "cta_text":
            return cta_band(parts[0], parts[1] if len(parts) > 1 else "")
        problems.append(f"{path}: unknown placeholder {{{{{m.group(1)}}}}}")
        return ""
    return re.sub(r"\{\{([^}]+)\}\}", repl, body)


def page_html(meta, body, path):
    cls = meta.get("bodyclass", "")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{head_html(meta, path)}
</head>
<body class="{cls}">
{header_html(path)}
<main id="main">
{body}
</main>
{footer_html()}
<script src="/assets/js/site.js?v={asset_version("assets/js/site.js")}" defer></script>
</body>
</html>
'''


HTACCESS = '''# reaganleonardmusic.com — Apache configuration (version 2.0)
RewriteEngine On

# HTTPS and the bare domain (only for the real domain, so a temporary
# Hostinger domain can be used for testing)
RewriteCond %{HTTP_HOST} ^(www\\.)?reaganleonardmusic\\.com$ [NC]
RewriteCond %{HTTPS} off [OR]
RewriteCond %{HTTP_HOST} ^www\\. [NC]
RewriteRule ^ https://reaganleonardmusic.com%{REQUEST_URI} [L,R=301]

# Old addresses from versions 1.x
RewriteRule ^corporate$ /corporate-events [R=301,L]
RewriteRule ^more-videos$ /photos-videos [R=301,L]
RewriteRule ^preferred-vendors$ / [R=301,L]
RewriteRule ^booking$ /contact [R=301,L]

# /page -> page.html
RewriteCond %{REQUEST_FILENAME} !-d
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{DOCUMENT_ROOT}/$1.html -f
RewriteRule ^([^/.]+)$ $1.html [L]

ErrorDocument 404 /404.html
Options -Indexes

# The reviews refresh job reads its Google API key from reviews-config.json
<Files "reviews-config.json">
  Require all denied
</Files>

<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/avif  "access plus 1 year"
  ExpiresByType image/webp  "access plus 1 year"
  ExpiresByType image/jpeg  "access plus 1 year"
  ExpiresByType image/png   "access plus 1 year"
  ExpiresByType font/woff2  "access plus 1 year"
  ExpiresByType text/css    "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
  ExpiresByType application/json "access plus 1 day"
  ExpiresByType text/html   "access plus 0 seconds"
</IfModule>
<IfModule mod_mime.c>
  AddType image/avif .avif
  AddType image/webp .webp
  AddType font/woff2 .woff2
</IfModule>
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
'''


def copy_shared():
    os.makedirs(OUT, exist_ok=True)
    for sub in ("assets/img", "assets/data"):
        src, dst = os.path.join(V1, sub), os.path.join(OUT, sub)
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            s, d = os.path.join(src, f), os.path.join(dst, f)
            if os.path.isfile(s) and (not os.path.exists(d) or os.path.getmtime(s) > os.path.getmtime(d)):
                shutil.copy2(s, d)
    shutil.copy2(os.path.join(V1, "refresh-reviews.php"), os.path.join(OUT, "refresh-reviews.php"))
    # fonts for the new design live next to this script
    os.makedirs(os.path.join(OUT, "assets", "fonts"), exist_ok=True)
    fdir = os.path.join(ROOT, "tools", "v2", "fonts")
    for f in os.listdir(fdir):
        shutil.copy2(os.path.join(fdir, f), os.path.join(OUT, "assets", "fonts", f))


def main():
    copy_shared()
    pages = sorted(f[:-5] for f in os.listdir(PAGES_DIR) if f.endswith(".html"))
    sitemap = []
    for slug_ in pages:
        raw = io.open(os.path.join(PAGES_DIR, slug_ + ".html"), encoding="utf-8").read()
        m = re.match(r"\s*<!--meta\s*(\{.*?\})\s*-->", raw, re.S)
        if not m:
            problems.append(f"{slug_}: missing meta comment"); continue
        meta = json.loads(m.group(1)); body = raw[m.end():]
        path = "/" if slug_ == "index" else ("/404.html" if slug_ == "404" else f"/{slug_}")
        out = page_html(meta, expand(body, path), path)
        io.open(os.path.join(OUT, slug_ + ".html"), "w", encoding="utf-8", newline="\n").write(out)
        if not meta.get("noindex") and slug_ != "404":
            sitemap.append((SITE_URL + ("" if path == "/" else path), meta.get("priority", "0.7")))
    io.open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>\n" for u, p in sitemap) + "</urlset>\n")
    io.open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8", newline="\n").write(
        f"User-agent: *\nAllow: /\nDisallow: /thank-you\nDisallow: /refresh-reviews.php\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    io.open(os.path.join(OUT, ".htaccess"), "w", encoding="utf-8", newline="\n").write(HTACCESS)
    print(f"built {len(pages)} pages into site-v2/ ({len(sitemap)} in the sitemap)")
    for p in problems:
        print("  problem:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
