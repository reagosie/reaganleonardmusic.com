"""
make-images.py — one-time image derivative generator.

Reads the full-resolution originals archived in
    pre-migration scan/reference/assets-original/
and writes AVIF / WebP / JPEG-or-PNG derivatives to
    site/assets/img/

It reproduces exactly what the old Zyro/Hostinger CDN served, at equal or
better quality:

  * Width rungs  (name-{w}.ext)      375 / 768 / 1024 / 1440 / 1920 / 2800 for
    full-bleed backgrounds and the header logo — resampled from the original
    even when that enlarges it, because that is what the CDN did (verified on
    the live site). Gallery-only photos get just the lightbox sizes
    (1440 / 1920 / 2800, never enlarged, at most ~2200px tall).
  * Crops        (name-{w}x{h}.ext)  the per-breakpoint centre crops the old
    pages requested for placed images and gallery tiles (e.g. 768x768 tiles,
    375x549 portrait crops). Like the CDN's fit=crop, a crop is never enlarged:
    if the original is smaller than the requested box it is cropped to the
    box's aspect ratio and kept at its native size. The list of crops comes
    from the archived rendered pages, so the rebuilt srcsets mirror the old
    ones entry for entry.
  * Fixed sizes  (name-{w}x{h}[@2x])  the brand-carousel logos.
  * Favicons and the 1440x756 Open Graph preview images.

Encoder settings are calibrated against files the CDN actually served:
the CDN used quality 85 (its default). Measured PSNR against a clean
downscale of the original — CDN AVIF 40.2 dB, CDN WebP 40.7 dB, CDN JPEG
40.3 dB at 1440px — versus AVIF 82 ≈ 42.5 dB, WebP 90 ≈ 41.9 dB, JPEG 90 ≈
41.8 dB here. Every format is therefore encoded at a higher fidelity than
the old site delivered.

Run from the repo root:   py tools/make-images.py
Requires Pillow >= 11 (AVIF support is built in) and beautifulsoup4.

This is a migration tool, not a build step: run it once, commit the output,
and deploy site/ as plain files. Re-run only if you add or replace a photo.
To add a new photo later: drop the original in assets-original/, give it a
readable name in tools/image-names.json, run this script, and reference the
width rungs from your HTML (crops are only needed to mirror old layouts).
"""
import json, os, re, sys, time
from PIL import Image
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pre-migration scan", "reference", "assets-original")
PAGES = os.path.join(ROOT, "pre-migration scan", "reference", "pages-rendered")
EMBEDS = os.path.join(ROOT, "pre-migration scan", "reference", "embeds")
OUT = os.path.join(ROOT, "site", "assets", "img")
NAMES = json.load(open(os.path.join(ROOT, "tools", "image-names.json"), encoding="utf-8"))
NAMES.pop("_comment", None)
SITE_ID = "Yg2xxNENX5FGqrpg"

WIDTHS = [375, 768, 1024, 1440, 1920, 2800]     # the rungs the old CDN served
OG_ONLY = {"link_preview-mP4XOM8OGgibEMo2.jpg", "img_8141-Yle0WobXXQi4PkKK.jpg"}  # only used as 1440x756 previews
MAX_WIDTH = {"rlm-logo-full-white": 768}        # header logo displays at 125px; 768 is plenty
ALWAYS_RUNGS = {"rlm-logo-full-white"}          # hand-written header partial uses the width rungs
AVIF_Q, WEBP_Q, JPEG_Q = 82, 90, 90             # see calibration note above

os.makedirs(OUT, exist_ok=True)
manifest = {}


def save(img, path, fmt):
    """Encode one derivative. Returns bytes written."""
    kw = {}
    if fmt == "AVIF":
        kw = dict(quality=AVIF_Q, speed=6)
    elif fmt == "WEBP":
        kw = dict(quality=WEBP_Q, method=6)
    elif fmt == "JPEG":
        kw = dict(quality=JPEG_Q, progressive=True, optimize=True)
        if img.mode != "RGB":
            img = img.convert("RGB")
    elif fmt == "PNG":
        kw = dict(optimize=True)
    img.save(path, fmt, **kw)
    return os.path.getsize(path)


def save_all(im, base, fallback):
    """Write base.avif, base.webp and base.<fallback ext>; print sizes."""
    ext = {"PNG": "png", "JPEG": "jpg"}[fallback]
    sizes = {
        "avif": save(im, base + ".avif", "AVIF"),
        "webp": save(im, base + ".webp", "WEBP"),
        ext:    save(im, f"{base}.{ext}", fallback),
    }
    print(f"  {os.path.basename(base)} {im.size[0]}x{im.size[1]}  "
          + "  ".join(f"{k}={v//1024}K" for k, v in sizes.items()))


def has_alpha(img):
    return img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)


def load(orig_name):
    img = Image.open(os.path.join(SRC, orig_name))
    return img.convert("RGBA") if has_alpha(img) else img.convert("RGB")


def rungs(cap=None):
    """Width rungs for full-bleed images: the CDN's ladder, resampled from the
    original even when that means enlarging — measured on the live site, a
    1193px-wide hero was served at 2800x1382 for the 2800 request. Mirroring
    that keeps every screen rendering exactly as before (a higher-resolution
    original is the real fix; see BUILD-REPORT.md)."""
    return [w for w in WIDTHS if w <= (cap or WIDTHS[-1])]


LIGHTBOX_MAX_H = 2200   # the lightbox shows at most 90vh; 2200px covers a 2x 1440x900 screen or 4K


def lightbox_rungs(ow, oh):
    """Sizes for the gallery lightbox: 1440 / 1920 / 2800 (never enlarged), but
    only those no taller than LIGHTBOX_MAX_H — a 4000x6000 portrait stops at
    1440x2160. Always at least one size."""
    cands = sorted({min(w, ow) for w in (1440, 1920, 2800)})
    keep = [w for w in cands if round(oh * w / ow) <= LIGHTBOX_MAX_H]
    return keep or cands[:1]


def cf_crop(img, w, h):
    """What the CDN's fit=crop did: centre-crop to the w:h aspect, then shrink
    to w x h — but never enlarge (a smaller original keeps its native size)."""
    ow, oh = img.size
    if ow / oh > w / h:            # too wide: trim the sides
        cw, ch = round(oh * w / h), oh
    else:                          # too tall: trim top and bottom
        cw, ch = ow, round(ow * h / w)
    left, top = (ow - cw) // 2, (oh - ch) // 2
    im = img.crop((left, top, left + cw, top + ch))
    if cw > w:
        im = im.resize((w, h), Image.LANCZOS)
    return im


def cover_crop(img, w, h):
    """Crop to w:h then resize to exactly w x h (fixed-size logos, OG image)."""
    ow, oh = img.size
    scale = max(w / ow, h / oh)
    nw, nh = round(ow * scale), round(oh * scale)
    im = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - w) // 2, (nh - h) // 2
    return im.crop((left, top, left + w, top + h))


# --------------------------------------------------------------------------
# What did the old pages ask the CDN for?  Scan every rendered page's <img>
# tags (skipping the hidden mobile duplicates, which the rebuild merges away)
# and collect, per image, the width-only requests and the w x h crop requests.
# --------------------------------------------------------------------------
def scan_usage():
    wants = {}   # new name -> {"widths": set(), "crops": set(), "gallery": bool}
    pat = re.compile(r'cdn-cgi/image/format=auto,w=(\d+)(?:,h=(\d+))?,fit=crop(?:,f=\w+)?/' + SITE_ID + r'/([^\s",]+)')
    for f in sorted(os.listdir(PAGES)):
        soup = BeautifulSoup(open(os.path.join(PAGES, f), encoding="utf-8").read(), "lxml")
        for img in soup.find_all("img"):
            if img.find_parent(class_="image-wrapper--mobile"):
                continue
            in_gallery = img.find_parent(class_="grid-gallery-grid__image") is not None
            # srcset entries are comma-separated, but so are the CDN's url parameters:
            # split only on a comma that starts the next url
            entries = re.split(r",(?=\s*https?://)", img.get("srcset", ""))
            for url in [img.get("src", "")] + [e.split()[0] for e in entries if e.strip()]:
                m = pat.search(url)
                if not m:
                    continue
                w, h, orig = int(m.group(1)), m.group(2), m.group(3)
                if orig not in NAMES or ",f=" in url:      # favicons / og handled separately
                    continue
                d = wants.setdefault(NAMES[orig], {"widths": set(), "crops": set(), "gallery": False})
                if h:
                    d["crops"].add((w, int(h)))
                else:
                    d["widths"].add(w)
                d["gallery"] |= in_gallery
    return wants


def responsive(orig_name, new_name, want):
    """Photo / icon / badge: width rungs and/or the crops the old pages used."""
    img = load(orig_name)
    ow, oh = img.size
    fallback = "PNG" if img.mode == "RGBA" else "JPEG"
    ext = {"PNG": "png", "JPEG": "jpg"}[fallback]
    # width rungs: the full ladder for full-bleed uses and the header logo; a
    # gallery-only photo just needs what the lightbox shows (1440 + full size)
    if want["widths"] or new_name in ALWAYS_RUNGS:
        widths = rungs(MAX_WIDTH.get(new_name))
    elif want["gallery"]:
        widths = lightbox_rungs(ow, oh)
    else:
        widths = []
    entry = manifest[new_name] = {
        "original": orig_name, "width": ow, "height": oh,
        "widths": widths, "crops": {}, "fallback": ext, "kind": "responsive"}
    for w in widths:
        h = round(oh * w / ow)
        im = img if w == ow else img.resize((w, h), Image.LANCZOS)
        save_all(im, os.path.join(OUT, f"{new_name}-{w}"), fallback)
    for (w, h) in sorted(want["crops"]):
        im = cf_crop(img, w, h)
        entry["crops"][f"{w}x{h}"] = list(im.size)
        save_all(im, os.path.join(OUT, f"{new_name}-{w}x{h}"), fallback)


def fixed(orig_name, new_name, w, h, scales=(1, 2)):
    """Fixed-size crop (partner logos) at 1x and 2x."""
    img = load(orig_name)
    fallback = "PNG" if img.mode == "RGBA" else "JPEG"
    ext = {"PNG": "png", "JPEG": "jpg"}[fallback]
    manifest[new_name] = {
        "original": orig_name, "width": w, "height": h,
        "scales": list(scales), "fallback": ext, "kind": "fixed"}
    for s in scales:
        im = cover_crop(img, w * s, h * s)
        save_all(im, os.path.join(OUT, f"{new_name}-{w}x{h}" + (f"@{s}x" if s != 1 else "")), fallback)


t0 = time.time()

# ---- 0. Start clean so no stale derivative is left behind
for f in os.listdir(OUT):
    p = os.path.join(OUT, f)
    if os.path.isfile(p):
        os.remove(p)

# ---- 1. Partner logos in the brand carousel: exact crop sizes from the embed
carousel = open(os.path.join(EMBEDS, "01_z98ieM.html"), encoding="utf-8").read()
logo_sizes = {}
for m in re.finditer(r'w=(\d+),h=(\d+),fit=crop/' + SITE_ID + r'/([^"\s]+)', carousel):
    logo_sizes[m.group(3)] = (int(m.group(1)), int(m.group(2)))
print(f"Carousel logos ({len(logo_sizes)}):")
for orig, (w, h) in logo_sizes.items():
    fixed(orig, NAMES[orig], w, h)

# ---- 2. Favicons (the old site linked 16/32/192 PNG + 180 apple-touch)
print("Favicons:")
icon = Image.open(os.path.join(SRC, "rlm_logo_icon-01-AVLD7aoM3Qckg2eY.jpg")).convert("RGB")
for s in (16, 32, 180, 192):
    p = os.path.join(OUT, f"favicon-{s}.png")
    icon.resize((s, s), Image.LANCZOS).save(p, "PNG", optimize=True)
    print(f"  favicon-{s}.png {os.path.getsize(p)//1024}K")
manifest["favicon"] = {"original": "rlm_logo_icon-01-AVLD7aoM3Qckg2eY.jpg", "sizes": [16, 32, 180, 192], "kind": "favicon"}

# ---- 3. Open Graph / link-preview images at the exact 1440x756 the site used
print("OG images:")
for orig in ("link_preview-mP4XOM8OGgibEMo2.jpg", "img_8141-Yle0WobXXQi4PkKK.jpg"):
    img = Image.open(os.path.join(SRC, orig)).convert("RGB")
    p = os.path.join(OUT, "og", f"{NAMES[orig]}-1440x756.jpg")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    save(cover_crop(img, 1440, 756), p, "JPEG")
    print(f"  og/{os.path.basename(p)} {os.path.getsize(p)//1024}K")
    manifest.setdefault("og", {})[NAMES[orig]] = f"og/{os.path.basename(p)}"

# ---- 4. Everything else: the rungs and crops the old pages used
print("Responsive images:")
wants = scan_usage()
done = set(logo_sizes) | OG_ONLY | {"rlm_logo_icon-01-AVLD7aoM3Qckg2eY.jpg"}
for orig, new in NAMES.items():
    if orig in done:
        continue
    want = wants.get(new)
    if not want:
        print(f"  {new}: not used by any page — skipped")
        continue
    responsive(orig, new, want)

json.dump(manifest, open(os.path.join(ROOT, "tools", "image-manifest.json"), "w", encoding="utf-8"), indent=1)
n = sum(len(fs) for _, _, fs in os.walk(OUT))
total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
print(f"\nDone in {time.time()-t0:.0f}s — {n} files, {total/1024/1024:.1f} MB across all derivatives (originals were 48.4 MB)")
