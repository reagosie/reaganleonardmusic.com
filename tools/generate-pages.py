"""
generate-pages.py — one-time migration tool that builds site/*.html

Sources (all archived during the pre-migration crawl):
  pre-migration scan/reference/pages-rendered/*.html   fully rendered DOM of each live page
  pre-migration scan/reference/site-data/seo.json      every SEO tag, verbatim
  pre-migration scan/reference/site-data/*.Page.json   the builder's own page data
  pre-migration scan/reference/embeds/*.html           the custom-code blocks
  tools/partials/header.html                           shared header (hand-written)
  tools/partials/footer.html                           shared footer (extracted on first run)
  tools/image-manifest.json                            what make-images.py produced

What it does, per page:
  • rebuilds <head> from the captured SEO data (titles, descriptions, canonical,
    Open Graph, Twitter, JSON-LD, noindex) with images pointed at self-hosted copies
  • takes each content section from the rendered DOM, strips the builder's
    framework noise (Vue scoping attrs, hashed variable names, duplicate
    desktop/mobile image wrappers, sandboxed iframes) and emits clean markup
  • swaps CDN images for <picture> elements over the local AVIF/WebP/JPEG set
  • inlines the custom-code blocks (carousel, FAQ, cards) with scoped classes
  • stamps in the shared header (marking the current page) and footer
  • writes the analytics tags (GTM, GA4, Google Ads) as plain <script>s

Run from the repo root:   py tools/generate-pages.py
Deploy: upload the contents of site/ — no build step is needed afterwards.
Keep this script for provenance; day-to-day edits go straight into site/*.html.
"""
import html, json, os, re, sys
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "pre-migration scan", "reference")
SITE = os.path.join(ROOT, "site")
PARTIALS = os.path.join(ROOT, "tools", "partials")
SITE_ID = "Yg2xxNENX5FGqrpg"
DOMAIN = "https://reaganleonardmusic.com"

NAMES = json.load(open(os.path.join(ROOT, "tools", "image-names.json"), encoding="utf-8"))
NAMES.pop("_comment", None)
MANIFEST = json.load(open(os.path.join(ROOT, "tools", "image-manifest.json"), encoding="utf-8"))
SEO = json.load(open(os.path.join(REF, "site-data", "seo.json"), encoding="utf-8"))

# page file name -> URL path (must not change: these are the live URLs)
PAGES = [
    ("index", "/"), ("contact", "/contact"), ("photos-videos", "/photos-videos"),
    ("weddings", "/weddings"), ("corporate", "/corporate"), ("pricing", "/pricing"),
    ("faq", "/faq"), ("more-videos", "/more-videos"), ("song-list", "/song-list"),
    ("preferred-vendors", "/preferred-vendors"), ("welcome", "/welcome"),
    ("thank-you", "/thank-you"), ("wedding-show-form", "/wedding-show-form"),
]

# Analytics — same three properties the live site loads
GTM_ID, GA4_ID, ADS_ID = "GTM-WNPC2JM", "G-Q4JZ91TEGB", "AW-17134305700"

# Two og:image files were already 404 on the live site; per the owner's
# decision those pages use the site default preview image instead.
OG_DEFAULT = "link-preview"
OG_FALLBACK_FOR = {"img-m5KKLB5nGQiJNLBl.jpg", "rlm-logo-black-mePaxMrewqf64kag.png"}

# Section ids that are link targets on the live site — must survive
KEEP_IDS = {"request-quote", "check-availability"}

# --------------------------------------------------------------------------
# Builder → readable custom-property names
# --------------------------------------------------------------------------
VAR_MAP = {
    # block background
    "--v4cfc8878": "--bg", "--v000e51f2": "--bg-position", "--v3f9ca25a": "--bg-overlay-opacity",
    # block layout grid
    "--v3f3138e2": "--content-width", "--c27f45b8": "--m-content-width",
    "--v66d5c4a6": "--m-padding", "--v1984096a": "--t-padding",
    # layout element (element box height, used by buttons)
    "--v72f86ff9": "--desktop-height", "--v4c707db6": "--mobile-height",
    # text box
    "--v2b806092": "--white-space", "--d294b058": "--m-white-space", "--v12d9d480": "--text-background",
    # image wrapper / image
    "--d8599d80": "--desktop-max-height", "--v636e1b04": "--mobile-max-height",
    "--v3f28ffbc": "--sd-width", "--v21b35439": "--sd-height", "--e3629ab6": "--object-position",
    "--v7007e7a5": "--radius", "--d66f8f86": "--m-radius", "--v76f5f733": "--mask",
    "--v52de0f10": "--image-overlay", "--v6dfc834f": "--xs-width", "--v655f79f4": "--xs-height",
    # gallery
    "--v1a96709a": "--columns", "--v3a2dbdc7": "--gap", "--b30d0c50": "--m-columns", "--v4bdf4085": "--m-gap",
    # video
    "--v1e20e231": "--video-bg",
}
DROP_VARS = {
    # parallax/background plumbing the site doesn't use
    "--v5abb0200", "--v5c6fda9f", "--v47c095f9", "--v79d8fbfe",
    # legacy (non-grid) layout vars
    "--align", "--justify", "--m-element-margin", "--left", "--height", "--m-align-self", "--heightMobile",
    "--cols", "--rows", "--width", "--m-rows", "--col-gap", "--row-gap", "--row-size",
    "--column-gap", "--oldContentWidth", "--block-padding", "--block-padding-top",
    "--block-padding-right", "--block-padding-bottom", "--block-padding-left", "--m-block-padding",
    # embed iframe height (content is inline now)
    "--v52c726c9",
}
# values that mean "unset"
DROP_IF_VALUE = {("--bg-overlay-opacity", "false"), ("--object-position", "initial"),
                 ("--radius", "initial"), ("--m-radius", "initial"), ("--mask", "initial"),
                 ("--image-overlay", "initial"), ("--text-background", "initial")}

DROP_ATTR_PREFIXES = ("data-v-", "data-qa", "data-pagefind", "data-selector", "data-animation-role",
                      "data-page-id", "is-in-preview-mode", "is-preview-mobile-view", "backgroundcolorcontrast")
DROP_CLASSES = {
    "transition", "transition--", "transition--root-hidden", "transition-with-bg", "loaded",
    "block--desktop-first-visible", "block--mobile-first-visible",
    "block-layout--layout", "layout-element--layout", "image-wrapper--layout",
    "image-wrapper--desktop", "image-wrapper--mobile", "social-icons--row",
    "layout-element__component--GridTextBox", "layout-element__component--GridImage",
    "layout-element__component--GridEmbed", "layout-element__component--GridVideo",
    "layout-element__component--GridGallery", "layout-element__component--GridSocialIcons",
}

warnings = []


# --------------------------------------------------------------------------
# Helpers: images
# --------------------------------------------------------------------------
def original_of(url):
    """CDN url -> original filename, or None."""
    m = re.search(r'/' + SITE_ID + r'/([^\s"\'?#]+)', url or "")
    return m.group(1) if m else None


CDN_RE = re.compile(r'cdn-cgi/image/format=auto,w=(\d+)(?:,h=(\d+))?,fit=crop(?:,f=\w+)?/' + SITE_ID + r'/([^\s",]+)')


def local_file(name, w, h, ext):
    """The self-hosted file that stands in for one CDN request.

    w x h crop requests map to the identical crop (make-images.py produced
    every crop the old pages asked for). Width-only requests map to the same
    rung, or to the original's own width when the CDN was asked for more than
    the original had (it never enlarged, and neither do we)."""
    m = MANIFEST[name]
    if h:
        key = f"{w}x{h}"
        if key not in m["crops"]:
            warnings.append(f"{name}: no {key} crop was generated")
        return f"/assets/img/{name}-{key}.{ext}"
    rung = next((r for r in m["widths"] if r >= w), m["widths"][-1] if m["widths"] else None)
    if rung is None:
        warnings.append(f"{name}: no width rungs were generated")
    return f"/assets/img/{name}-{rung}.{ext}"


def mirror_srcset(ref_srcset, ext):
    """Rebuild an old srcset entry-for-entry against local files, keeping the
    original width descriptors so browsers pick exactly what they picked before."""
    parts = []
    # entries are separated by commas, but the CDN urls contain commas too:
    # split only on a comma that starts the next url
    for entry in re.split(r",(?=\s*https?://)", ref_srcset):
        bits = entry.split()
        if not bits:
            continue
        m = CDN_RE.search(bits[0])
        if not m:
            continue
        w, h, orig = int(m.group(1)), m.group(2), m.group(3)
        desc = bits[1] if len(bits) > 1 else ""
        parts.append((local_file(NAMES[orig], w, int(h) if h else None, ext) + " " + desc).strip())
    return ", ".join(parts)


def mirror_src(ref_src, ext):
    m = CDN_RE.search(ref_src or "")
    if not m:
        return None
    w, h, orig = int(m.group(1)), m.group(2), m.group(3)
    return local_file(NAMES[orig], w, int(h) if h else None, ext)


def srcset_for(name, ext):
    """Fixed-size images (carousel logos): 1x / 2x."""
    m = MANIFEST[name]
    w, h = m["width"], m["height"]
    parts = [f"/assets/img/{name}-{w}x{h}.{ext} 1x"]
    if 2 in m["scales"]:
        parts.append(f"/assets/img/{name}-{w}x{h}@2x.{ext} 2x")
    return ", ".join(parts)


def largest_src(name, ext=None):
    """Biggest width rung — the lightbox's no-srcset fallback."""
    m = MANIFEST[name]
    return f"/assets/img/{name}-{m['widths'][-1]}.{ext or m['fallback']}"


def rung_srcset(name, ext):
    """All width rungs with real width descriptors — the lightbox's srcset."""
    return ", ".join(f"/assets/img/{name}-{w}.{ext} {w}w" for w in MANIFEST[name]["widths"])


def make_picture(soup, ref, *, classes=None):
    """Build <picture> (avif, webp, fallback) that mirrors an archived <img>:
    same srcset entries and descriptors, same sizes, pointed at local files."""
    orig = original_of(ref.get("src", "")) or original_of(ref.get("srcset", ""))
    name = NAMES[orig]
    m = MANIFEST[name]
    fixed = m["kind"] == "fixed"
    sizes = ref.get("sizes")
    pic = soup.new_tag("picture")
    for fmt in ("avif", "webp"):
        srcset = srcset_for(name, fmt) if fixed else mirror_srcset(ref.get("srcset", ""), fmt)
        s = soup.new_tag("source", attrs={"type": f"image/{fmt}", "srcset": srcset})
        if sizes and not fixed:
            s["sizes"] = sizes
        pic.append(s)
    img = soup.new_tag("img")
    if fixed:
        img["src"] = f"/assets/img/{name}-{m['width']}x{m['height']}.{m['fallback']}"
        img["srcset"] = srcset_for(name, m["fallback"])
    else:
        img["src"] = mirror_src(ref.get("src"), m["fallback"]) or ""
        img["srcset"] = mirror_srcset(ref.get("srcset", ""), m["fallback"])
        if sizes:
            img["sizes"] = sizes
    for a in ("width", "height", "loading", "title"):
        if ref.get(a):
            img[a] = ref[a]
    img["alt"] = ref.get("alt") or ""
    if classes:
        img["class"] = classes
    pic.append(img)
    return pic


# --------------------------------------------------------------------------
# Helpers: attribute / style clean-up
# --------------------------------------------------------------------------
def clean_style(value):
    out = []
    for decl in value.split(";"):
        if ":" not in decl:
            continue
        k, v = decl.split(":", 1)
        k, v = k.strip(), v.strip()
        k = VAR_MAP.get(k, k)
        # authored text sometimes names the font inline; point it at the self-hosted face
        if k == "font-family" and v.strip("'\"").lower() == "montserrat":
            v = "var(--font-secondary)"
        if k in DROP_VARS or (k, v) in DROP_IF_VALUE:
            continue
        if k.startswith("--v") and re.fullmatch(r"--[vdecb][0-9a-f]{7,8}", k):
            warnings.append(f"unmapped variable {k}: {v}")
        out.append(f"{k}: {v}")
    return "; ".join(out)


def tidy(root):
    """Strip framework noise from a subtree, in place."""
    for c in root.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for el in [root] + root.find_all(True):
        for a in list(el.attrs):
            if a.startswith(DROP_ATTR_PREFIXES):
                del el.attrs[a]
        for a in ("dir", "aria-hidden", "disabled"):
            if el.attrs.get(a) in ("auto", "false"):
                del el.attrs[a]
        for a in ("title", "rel", "target", "class"):
            if a in el.attrs and (el.attrs[a] == "" or el.attrs[a] == []):
                del el.attrs[a]
        if el.attrs.get("target") == "_self":
            del el.attrs["target"]
        if el.name in ("div", "section", "header") and "rel" in el.attrs:
            del el.attrs["rel"]
        if el.name not in ("img", "iframe", "svg", "source") and "height" in el.attrs and "width" not in el.attrs:
            del el.attrs["height"]          # e.g. height="539" on an embed wrapper
        if "class" in el.attrs:
            cls = list(dict.fromkeys(c for c in el.attrs["class"] if c not in DROP_CLASSES))
            if cls:
                el.attrs["class"] = cls
            else:
                del el.attrs["class"]
        if "style" in el.attrs:
            st = clean_style(el.attrs["style"])
            if st:
                el.attrs["style"] = st
            else:
                del el.attrs["style"]
    return root


# --------------------------------------------------------------------------
# Helpers: the custom-code blocks (were sandboxed iframes; now inline)
# --------------------------------------------------------------------------
def embed_source(fname):
    return open(os.path.join(REF, "embeds", fname), encoding="utf-8").read()


def strip_style_and_head(fragment):
    frag = re.sub(r"<style.*?</style>", "", fragment, flags=re.S)
    frag = re.sub(r"<link[^>]*>|<meta[^>]*>", "", frag)
    return frag.strip()


def build_carousel(soup):
    """Brand logo marquee: same logos, same order, same crop sizes, local files."""
    src = BeautifulSoup(embed_source("01_z98ieM.html"), "lxml")
    wrap = soup.new_tag("div", attrs={"class": "brand-carousel"})
    track = soup.new_tag("div", attrs={"class": "brand-carousel__track"})
    for img in src.select(".track .logo img"):
        orig = original_of(img["src"])
        m = re.search(r"w=(\d+),h=(\d+)", img["src"])
        cell = soup.new_tag("div", attrs={"class": "brand-carousel__logo"})
        ref = soup.new_tag("img", attrs={"src": img["src"], "width": m.group(1), "height": m.group(2), "loading": "lazy", "alt": ""})
        cell.append(make_picture(soup, ref))
        track.append(cell)
    wrap.append(track)
    return wrap


def build_faq(soup):
    frag = strip_style_and_head(embed_source("05_zivX2c.html"))
    frag = re.sub(r"<script.*?</script>", "", frag, flags=re.S)
    frag = frag.replace('class="accordion"', 'class="faq-question" type="button" aria-expanded="false"')
    frag = frag.replace('class="panel"', 'class="faq-answer"')
    frag = frag.replace('href="https://reaganleonardmusic.com/', 'href="/')
    return BeautifulSoup(f"<div class='faq'>{frag}</div>", "lxml").div


def build_card(soup, fname, modifier=None):
    frag = strip_style_and_head(embed_source(fname))
    node = BeautifulSoup(f"<div>{frag}</div>", "lxml").div
    if modifier:  # each wedding package card had its own colours
        card = node.select_one(".pricing-card")
        card["class"] = card.get("class", []) + [f"pricing-card--{modifier}"]
    return node


def build_raw(soup, fname):
    """Snippets kept verbatim (the Ads conversion event on /thank-you)."""
    return BeautifulSoup(f"<div>{embed_source(fname).strip()}</div>", "lxml").div


# Third-party widgets are injected by site.js when they come within 500px of
# the viewport (as the old site did). The container carries the script URL.
def build_jotform(soup, form_id):
    d = soup.new_tag("div", attrs={"data-lazy-script": f"https://form.jotform.com/jsform/{form_id}"})
    d.append(Comment(f" JotForm {form_id} — the form iframe is injected here by site.js "))
    return d


def build_elfsight(soup):
    d = soup.new_tag("div", attrs={"data-lazy-script": "https://apps.elfsight.com/p/platform.js"})
    d.append(soup.new_tag("div", attrs={"class": "elfsight-app-f8cd8f7b-53a5-47bf-a5de-e1610afad937"}))
    return d


def build_zola(soup):
    d = soup.new_tag("div", attrs={"data-lazy-script": "https://d1tntvpcrzvon2.cloudfront.net/static-assets/js/marketplace/zolaVendorBadge.js"})
    badge = BeautifulSoup(embed_source("03_zRaMck.html"), "lxml").select_one(".zola-vendor-badge")
    d.append(badge)
    return d


EMBEDS = {
    "z98ieM": lambda s: build_carousel(s),                       # brand carousel (/)
    "zPR9hD": lambda s: build_carousel(s),                       # brand carousel (/corporate)
    "zO4dpY": lambda s: build_elfsight(s),                       # Google reviews (/)
    "z951ZE": lambda s: build_elfsight(s),                       # Google reviews (/welcome)
    "zRaMck": lambda s: build_zola(s),                           # Zola badge (footer)
    "zlCvGR": lambda s: build_jotform(s, "230255417493153"),     # booking form (footer)
    "z3i3sO": lambda s: build_jotform(s, "230255417493153"),     # booking form (/welcome)
    "znefQJ": lambda s: build_jotform(s, "260106174629152"),     # wedding-show form
    "z3Ij_M": lambda s: build_raw(s, "11_z3Ij_M.html"),          # Ads conversion (/thank-you)
    "zivX2c": lambda s: build_faq(s),                            # FAQ accordion
    "zg0x4z": lambda s: build_card(s, "06_zg0x4z.html"),         # corporate card
    "zAZI1X": lambda s: build_card(s, "07_zAZI1X.html"),         # Silver package
    "zSw7Ct": lambda s: build_card(s, "08_zSw7Ct.html", "diamond"),    # Diamond package
    "zVeUyj": lambda s: build_card(s, "09_zVeUyj.html", "rehearsal"),  # Rehearsal Dinner package
    "zWkiln": lambda s: build_card(s, "10_zWkiln.html", "gold"),       # Gold package
}


# --------------------------------------------------------------------------
# Section conversion
# --------------------------------------------------------------------------
def convert_images(soup, section):
    # a) block background photo
    for img in section.select(".block-background img"):
        orig = original_of(img.get("src", "")) or original_of(img.get("srcset", ""))
        if not orig:
            warnings.append("background image without archived original")
            continue
        # keep the --fixed modifier: those blocks use a parallax (fixed) background
        classes = [c for c in img.get("class", []) if c.startswith("block-background__image")]
        if not img.get("sizes"):
            img["sizes"] = "100vw"
        pic = make_picture(soup, img, classes=classes or ["block-background__image"])
        img.replace_with(pic)

    # b) placed images: merge the desktop + mobile wrappers into one <picture>
    for wrapper in section.select(".image-wrapper"):
        desktop = wrapper.select_one(".image.image-wrapper--desktop")
        mobile = wrapper.select_one(".image.image-wrapper--mobile")
        if not desktop:
            continue
        if mobile:
            # the ≤360px sizing lives on the mobile wrapper; carry it over
            xs_vars = ("--v6dfc834f", "--v655f79f4")
            mvars = dict(d.split(":", 1) for d in mobile.get("style", "").split(";") if ":" in d)
            extra = {k.strip(): v.strip() for k, v in mvars.items() if k.strip() in xs_vars}
            keep = [d for d in desktop.get("style", "").split(";")
                    if ":" in d and d.split(":")[0].strip() not in xs_vars]
            desktop["style"] = ";".join(keep + [f"{k}:{v}" for k, v in extra.items()])
            mobile.decompose()
        img = desktop.find("img")
        classes = [c for c in img.get("class", []) if c in ("image__image", "image__image--cropped")]
        pic = make_picture(soup, img, classes=classes)
        img.replace_with(pic)

    # c) gallery tiles
    for tile in section.select(".grid-gallery-grid__image"):
        img = tile.find("img")
        if not img:
            continue
        # the lightbox shows the full photo at its largest size, in the best format the browser supports
        name = NAMES[original_of(img.get("src", ""))]
        tile["data-lightbox-src"] = largest_src(name)
        tile["data-lightbox-srcset"] = rung_srcset(name, MANIFEST[name]["fallback"])
        tile["data-lightbox-avif"] = rung_srcset(name, "avif")
        tile["data-lightbox-webp"] = rung_srcset(name, "webp")
        pic = make_picture(soup, img, classes=["image__image"])
        img.replace_with(pic)


def convert_videos(soup, section, elements):
    for video in section.select(".video"):
        eid = video.get("id")
        settings = (elements.get(eid) or {}).get("settings", {})
        src = settings.get("src", "")
        video["data-video-src"] = src
        # the reference DOM may already contain a loaded player; always start from the thumbnail
        for frame in video.select("iframe"):
            frame.decompose()
        play = video.select_one(".video__play")
        if play:
            play["aria-label"] = "Play video"
        # Rebuild the thumbnail <picture> cleanly (lxml nests the <img> inside
        # the void <source> when parsing the rendered page).
        old_pic = video.find("picture")
        ph = video.find("img", class_="video__placeholder")
        if old_pic is not None and ph is not None:
            webp = old_pic.find("source")
            pic = soup.new_tag("picture")
            if webp is not None and webp.get("srcset"):
                pic.append(soup.new_tag("source", attrs={"type": webp.get("type", "image/webp"),
                                                         "srcset": webp["srcset"]}))
            ph.extract()
            ph["alt"] = "Video thumbnail"
            for a in ("height", "width"):
                if a in ph.attrs:
                    del ph.attrs[a]
            pic.append(ph)
            old_pic.replace_with(pic)


def convert_embeds(soup, section):
    for box in section.select(".grid-embed"):
        eid = box.get("id")
        builder = EMBEDS.get(eid)
        if not builder:
            warnings.append(f"no inline builder for embed {eid}")
            continue
        box.clear()
        node = builder(soup)
        if node.get("data-lazy-script"):
            box["data-lazy-script"] = node["data-lazy-script"]
        # unwrap the temporary <div> used by the builders
        children = list(node.children) if node.name == "div" and not node.get("class") else [node]
        for child in children:
            box.append(child)


def section_label(section):
    h = section.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if h:
        return re.sub(r"\s+", " ", h.get_text()).strip()[:60]
    t = section.select_one(".text-box")
    if t:
        return re.sub(r"\s+", " ", t.get_text()).strip()[:60]
    kinds = {c.split("--")[-1] for el in section.select(".layout-element__component") for c in el.get("class", []) if "--Grid" in c}
    return ", ".join(sorted(kinds)) or "section"


def convert_section(soup, section, elements):
    label = section_label(section)
    convert_embeds(soup, section)
    convert_images(soup, section)
    convert_videos(soup, section, elements)
    tidy(section)
    # drop builder ids except anchor targets
    for el in [section] + section.find_all(True):
        if "id" in el.attrs and el.attrs["id"] not in KEEP_IDS:
            del el.attrs["id"]
    # the section's own style only held legacy vars
    if "style" in section.attrs:
        del section.attrs["style"]
    return label


# --------------------------------------------------------------------------
# Serialiser — readable indentation, but never touches whitespace inside
# text boxes (they render with white-space: break-spaces).
# --------------------------------------------------------------------------
VOID = {"img", "source", "br", "meta", "link", "input", "hr"}
INLINE = {"a", "span", "u", "b", "i", "strong", "em", "small", "sup", "sub", "br", "label"}
COMPACT_ROOTS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "button", "title", "svg"}
ATTR_CASE = {"viewbox": "viewBox"}


def attr_str(tag):
    parts = []
    for k, v in tag.attrs.items():
        k = ATTR_CASE.get(k, k)
        if isinstance(v, list):
            v = " ".join(v)
        if v == "" and k in ("defer", "async", "allowfullscreen", "hidden"):
            parts.append(k)
        else:
            parts.append(f'{k}="{html.escape(str(v), quote=False).replace(chr(34), "&quot;")}"')
    return (" " + " ".join(parts)) if parts else ""


def serialize(node, depth=0, compact=False):
    ind = "  " * depth
    if isinstance(node, Comment):
        return f"\n{ind}<!--{node}-->"
    if isinstance(node, NavigableString):
        text = str(node)
        if node.parent and node.parent.name in ("script", "style"):
            return text
        if not compact and text.strip() == "":
            return ""
        return html.escape(text, quote=False)
    tag = node
    is_compact = compact or tag.name in INLINE or tag.name in COMPACT_ROOTS or \
        "text-box" in tag.get("class", [])
    open_tag = f"<{tag.name}{attr_str(tag)}>"
    if tag.name in VOID:
        # void elements can't have children; if the parser nested any, emit them as siblings
        hoisted = "".join(serialize(c, depth, is_compact) for c in tag.children)
        return (open_tag if is_compact else f"\n{ind}{open_tag}") + hoisted
    inner = "".join(serialize(c, depth + 1, is_compact) for c in tag.children)
    if is_compact:
        return f"{open_tag}{inner}</{tag.name}>" if compact else f"\n{ind}{open_tag}{inner}</{tag.name}>"
    if inner and "\n" in inner:
        return f"\n{ind}{open_tag}{inner}\n{ind}</{tag.name}>"
    return f"\n{ind}{open_tag}{inner}</{tag.name}>"


# --------------------------------------------------------------------------
# <head>
# --------------------------------------------------------------------------
def og_image_url(seo_url):
    orig = original_of(seo_url) or ""
    name = OG_DEFAULT if orig in OG_FALLBACK_FOR or orig not in NAMES else NAMES[orig]
    path = MANIFEST["og"].get(name) or MANIFEST["og"][OG_DEFAULT]
    return f"{DOMAIN}/assets/img/{path}"


def esc(v):
    return html.escape(str(v), quote=True)


def build_head(name, url):
    seo = SEO[name]
    meta = seo["meta"]
    og_img = og_image_url(meta.get("og:image", ""))
    jsonld = json.loads(seo["jsonld"][0])
    jsonld["image"] = og_img
    lines = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '',
        '<!-- Search / social metadata — carried over verbatim from the previous site -->',
        f'<title>{esc(seo["title"])}</title>',
        f'<meta name="description" content="{esc(meta["description"])}">',
        f'<meta name="keywords" content="{esc(meta["keywords"])}">',
    ]
    if meta.get("robots"):
        lines.append(f'<meta name="robots" content="{esc(meta["robots"])}">')
    lines.append(f'<link rel="canonical" href="{esc(seo["canonical"])}">')
    if name == "index":
        lines.append(f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/">')
    lines += [
        f'<meta property="og:url" content="{esc(meta["og:url"])}">',
        f'<meta property="og:type" content="{esc(meta["og:type"])}">',
        f'<meta property="og:title" content="{esc(meta["og:title"])}">',
        f'<meta property="og:description" content="{esc(meta["og:description"])}">',
        f'<meta property="og:image" content="{og_img}">',
        f'<meta property="og:image:alt" content="{esc(meta.get("og:image:alt", ""))}">',
        f'<meta property="og:site_name" content="{esc(meta["og:site_name"])}">',
        f'<meta name="twitter:card" content="{esc(meta["twitter:card"])}">',
        f'<meta name="twitter:title" content="{esc(meta["twitter:title"])}">',
        f'<meta name="twitter:description" content="{esc(meta["twitter:description"])}">',
        f'<meta name="twitter:image" content="{og_img}">',
        f'<meta name="twitter:image:alt" content="{esc(meta.get("twitter:image:alt", ""))}">',
        '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")) + '</script>',
        '',
        '<link rel="icon" type="image/png" sizes="16x16" href="/assets/img/favicon-16.png">',
        '<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">',
        '<link rel="icon" type="image/png" sizes="192x192" href="/assets/img/favicon-192.png">',
        '<link rel="apple-touch-icon" href="/assets/img/favicon-180.png">',
        '',
        '<link rel="stylesheet" href="/assets/css/site.css">',
        '<script src="/assets/js/site.js" defer></script>',
        '',
        '<!-- Google Tag Manager -->',
        "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':",
        "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],",
        "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=",
        "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);",
        f"}})(window,document,'script','dataLayer','{GTM_ID}');</script>",
        '<!-- End Google Tag Manager -->',
        '',
        '<!-- Google Analytics 4 -->',
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>',
        '<script>',
        '  window.dataLayer = window.dataLayer || [];',
        '  function gtag(){dataLayer.push(arguments);}',
        "  gtag('js', new Date());",
        f"  gtag('config', '{GA4_ID}');",
        '</script>',
        '</head>',
    ]
    return "\n".join(lines)


ADS_SNIPPET = f"""
<!-- Google Ads tag (was the site's custom body code) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={ADS_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{ADS_ID}');
</script>
"""

GTM_NOSCRIPT = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


# --------------------------------------------------------------------------
# Shell partials
# --------------------------------------------------------------------------
def header_for(url):
    raw = open(os.path.join(PARTIALS, "header.html"), encoding="utf-8").read()
    soup = BeautifulSoup(raw, "html.parser")
    for a in soup.select("a.item-content"):
        if a.get("href") == url:
            a.parent["class"] = a.parent.get("class", []) + ["item-content-wrapper--active"]
    return str(soup).strip()


def ensure_footer_partial(soup, section, elements):
    """First run: extract the footer block from the rendered homepage."""
    path = os.path.join(PARTIALS, "footer.html")
    if os.path.exists(path):
        return
    convert_section(soup, section, elements)
    body = serialize(section, 2).strip("\n")
    text = ("<!-- #shell:footer start -->\n"
            "<!--\n  Site footer — contact details, social links, badges and the JotForm\n"
            "  booking request form. Shared by every page that has a footer.\n"
            "  To change it: edit here, then run  py tools/sync-shell.py\n-->\n"
            f"{body}\n<!-- #shell:footer end -->\n")
    open(path, "w", encoding="utf-8").write(text)
    print("  wrote tools/partials/footer.html (extracted from the homepage)")


def footer_html():
    return open(os.path.join(PARTIALS, "footer.html"), encoding="utf-8").read().strip()


# --------------------------------------------------------------------------
# Page assembly
# --------------------------------------------------------------------------
def build_page(name, url):
    rendered = open(os.path.join(REF, "pages-rendered", f"{name}.html"), encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(rendered, "lxml")
    page_data = json.load(open(os.path.join(REF, "site-data", f"{name}.Page.json"), encoding="utf-8"))["pageData"]
    elements = page_data.get("elements", {})

    sections = soup.select("main .page__blocks > section.block")
    out_sections = []
    n = 0
    has_footer = False
    for section in sections:
        if section.get("id") == "request-quote":
            ensure_footer_partial(soup, section, elements)
            has_footer = True
            continue
        n += 1
        label = convert_section(soup, section, elements)
        out_sections.append(f"\n\n    <!-- ============ Section {n}: {label} ============ -->" + serialize(section, 2))

    body = [
        "<body>",
        GTM_NOSCRIPT,
        "",
        '<div class="page">',
        '  <div class="top-blocks">',
        header_for(url),
        "  </div>",
        "",
        '  <main class="page__blocks">',
        "".join(out_sections),
    ]
    if has_footer:
        body += ["", "", "    <!-- ============ Footer ============ -->", footer_html()]
    body += ["  </main>", "</div>", ADS_SNIPPET, "</body>", "</html>", ""]
    html_out = build_head(name, url) + "\n" + "\n".join(body)
    open(os.path.join(SITE, f"{name}.html"), "w", encoding="utf-8", newline="\n").write(html_out)
    print(f"  {name}.html  ({len(out_sections)} sections{', footer' if has_footer else ''}, {len(html_out)//1024} KB)")


def build_404():
    lines = [
        '<!DOCTYPE html>', '<html lang="en">', '<head>',
        '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<title>Page not found | Reagan Leonard - Acoustic Musician - Greenville, SC</title>',
        '<meta name="robots" content="noindex">',
        '<link rel="icon" type="image/png" sizes="32x32" href="/assets/img/favicon-32.png">',
        '<link rel="stylesheet" href="/assets/css/site.css">',
        '<script src="/assets/js/site.js" defer></script>',
        '</head>', '<body>',
        '<div class="page">',
        '  <div class="top-blocks">', header_for("/404"), '  </div>',
        '  <main class="page__blocks">',
        '    <section class="not-found">',
        '      <h1>404</h1>',
        '      <p>Page not found.<br>This could be because the page URL is incorrect or the page you are looking for does not exist.</p>',
        '      <p><a href="/">Go to the homepage</a></p>',
        '    </section>',
        '  </main>',
        '</div>',
        '</body>', '</html>', '',
    ]
    open(os.path.join(SITE, "404.html"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("  404.html")


if __name__ == "__main__":
    os.makedirs(SITE, exist_ok=True)
    print("Generating pages:")
    # homepage first so the footer partial gets extracted from it
    for name, url in PAGES:
        build_page(name, url)
    build_404()
    if warnings:
        print("\nWarnings:")
        for w in sorted(set(warnings)):
            print("  -", w)
    print("\nDone.")
