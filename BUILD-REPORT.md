# Build report — reaganleonardmusic.com rebuild

Built 2026-09-09 from the archive in `pre-migration scan/`. This documents what
was produced, how it was verified, and the few places where the rebuild
deliberately differs from the old site. Read alongside
[README.md](README.md) (how to edit/deploy) and
[verification/migration-verification-checklist.md](verification/migration-verification-checklist.md)
(your pre-cutover checklist).

## What was built

`site/` — 13 pages + 404, at the exact same URLs as the live site, as plain
HTML/CSS/JS. Deployable by uploading the folder's contents to `public_html`.

| Path | File | Notes |
|---|---|---|
| `/` | index.html | |
| `/contact` `/photos-videos` `/weddings` `/corporate` `/pricing` `/faq` | same names + .html | indexed, in sitemap |
| `/more-videos` `/song-list` `/preferred-vendors` `/welcome` `/thank-you` `/wedding-show-form` | same names + .html | `noindex`, as before |
| anything else | 404.html | branded 404 (the old one was Hostinger's generic page) |

Plus `robots.txt` (verbatim), `sitemap.xml` (same 7 URLs and priorities),
`.htaccess` (https + bare-domain 301s, extensionless URLs, caching), one
stylesheet, one script, self-hosted fonts, and 429 image derivatives.

## How the layout was reproduced

The builder rendered every section as a CSS grid whose row/column templates it
computed per breakpoint. Rather than re-derive positions, the rebuild carries
those exact grid definitions over (as readable custom properties in each
section's `style` attribute) and re-implements the ~40 CSS rules that consume
them, by hand, in `site/assets/css/site.css`. Text, images, alt attributes,
colours and per-element font sizes come from the builder's own page data, not
from scraping. Result: every page renders at the same pixel height as the
original at both 1440px and 390px.

## Images

The old CDN resized every photo on the fly; the rebuild pre-generates the
same files (`tools/make-images.py`) and the rebuilt `<picture>` elements
mirror the old `srcset`s entry for entry — same crops (e.g. 768x768 gallery
tiles, 1024x1501 portrait crops), same width descriptors — so every screen
picks a file of exactly the same pixel size it picked before. This was
verified in headless Chrome at 1440px/2x and 390px/3x by reading each
image's `currentSrc` on the live site and the rebuild and decoding both.

Two CDN behaviours were reproduced deliberately:
- It **enlarged** full-bleed backgrounds to the requested width (the 1193px
  homepage hero was served at 2800x1382 to 2x screens). The rebuild does the
  same so nothing renders differently; a higher-resolution original is the
  real improvement for those photos (see *Things worth knowing*).
- It **never enlarged** placed images and gallery tiles; a small original was
  cropped to the box's aspect and kept at native size. Same here.

Encoder quality is higher than the CDN's. Its files were fetched and measured
against a clean downscale of the original (PSNR, 1440px porch photo):

| | Old CDN (quality 85) | Rebuild |
|---|---|---|
| AVIF | 40.2 dB | 42.5 dB (quality 82) |
| WebP | 40.7 dB | 41.9 dB (quality 90) |
| JPEG | 40.3 dB | 41.8 dB (quality 90) |

The first build used AVIF 60 / WebP 80 / JPEG 82, which was visibly softer
than the CDN; that is what the owner noticed and it has been corrected.

The gallery lightbox loads the full photo (1440–2800px wide, never enlarged,
capped at ~2200px tall) with AVIF/WebP negotiation and a responsive `srcset`,
so phones do not download desktop-sized files.

## Verification results

**Automated parity (`tools/verify.py`)** — all 13 pages pass:
- `<title>`, meta description/keywords, `robots`, canonical, all Open Graph and
  Twitter tags, JSON-LD: identical to the captured originals (image URLs now
  point at self-hosted copies)
- heading outline (h1–h6): identical
- visible text, in document order: identical
- every internal and external link present and resolving

**Visual comparison (headless Chrome, live site vs rebuild, full-page)**
- Desktop 1440px: every page renders at the same height as the original
  (±6px, all of it in the footer: the old site's JotForm sat inside a sandbox
  iframe that reported its height with a few px of wrapper slack). 0.2–3.9% of
  pixels differ per page — third-party widget timing (which review the
  Elfsight carousel is showing, the brand-carousel animation phase, JotForm's
  render state), not layout.
- Mobile 390px (iPhone emulation): every page within ±2px of the original's
  height; `/preferred-vendors` and `/weddings` match to the pixel. Remaining
  pixel differences are the same third-party timing effects.
- Computed-style probes (font size, family, weight, letter-spacing, element
  heights) were compared live-vs-rebuild for the hero heading, FAQ, and all
  four package cards at 390px: identical.
- Side-by-side sheets for all 13 pages, desktop and mobile, are in
  `verification/screenshots-live-vs-rebuild/` (live on the left, rebuild on
  the right).

**Functional checks (`site.js`, headless Chrome)** — 7/7 pass: mobile menu
open/close, FAQ accordion, gallery lightbox (open / next / Esc / swipe),
YouTube players loading on scroll and autoplaying on click, JotForm injecting
and auto-sizing (1238px), current page highlighted in the nav.

**Page weight (`tools/measure-weight.py`, real bytes over the wire, desktop)**

| | Old site | Rebuild | |
|---|---|---|---|
| First-party bytes, all 13 pages | 11,094 KB | 5,922 KB | **−47%** |
| Homepage first-party | 1,153 KB | 1,031 KB | −11% |
| Third-party (YouTube, JotForm, Google, Elfsight, Zola) | 9,987 KB | 10,241 KB | same services, same IDs |

First-party is everything the site itself serves. Image-heavy pages now weigh
about what they did before (the same pixel sizes, encoded at higher quality);
the saving comes from the builder's framework JS/CSS being gone.

## Where the rebuild deliberately differs

Everything below was agreed during planning or is a builder artefact with no
visible effect. Nothing else was changed.

1. **Custom-code blocks are inline, not sandboxed iframes** (your decision).
   Wedding package cards, FAQ, corporate card and brand carousel now sit in
   the page with scoped CSS. Visually identical; their text is now indexable.
   Side effect: the four package names and the corporate headline are real
   `<h2>`s in the outline now (they were invisible to search engines before).
   The cards' own `@media (max-width: …)` rules used to measure their iframe,
   not the screen, so they are now CSS container queries on the card box —
   verified against the live site at 360/412/430/768 px (card heights
   identical) after a real Android phone showed the desktop sizes at 412 px.
   One deliberate improvement: a wedding card's 375 px height is now a
   minimum, so at 920–1224 px desktop widths, where the text needs more
   room, the card grows instead of the text being cut off as it was inside
   the old iframe.
2. **Two dead `og:image` files** (`/photos-videos`, `/more-videos`, `/faq`)
   use the site's default preview image, per your instruction.
3. **Analytics load as plain `<script>` tags in `<head>`** instead of being
   injected by the builder's runtime. Same GTM, GA4 and Ads IDs, same
   `/thank-you` conversion event. The builder's `ns.html?id=undefined` noscript
   bug is fixed.
4. **Fonts are self-hosted** — the same Google-Fonts Montserrat files the old
   site pulled through Zyro's proxy (verified: identical line wrapping). They
   are registered under three family names that mirror exactly which weights
   each context had before (`"Montserrat RLM"` 400/500/800 for site text;
   `"Montserrat RLM Cards"` adds 600/700 for the package and corporate cards;
   `"Montserrat RLM FAQ"` is 400-only so the FAQ's bold is synthesised as it
   was). They are not named plain `"Montserrat"` because the Elfsight widget
   injects its own faces under that name, which otherwise collide.
5. **Dead `carousel.css` link dropped** — it returned 403 on the live site and
   the brand carousel's styles live inside its own block.
6. **Branded 404 page** instead of Hostinger's generic one.
7. **JotForm / Elfsight / Zola are injected when within 500px of the
   viewport**, replicating the old site's lazy behaviour, so initial loads stay
   light. Without JavaScript the forms don't appear — same as before.
8. **The footer is a hand-written layout** (requested before v1.0, after the
   1:1 pass): same content, but the "Check my availability for your event:"
   heading now sits directly above the booking form, and the whole form is
   shown beside the contact / social / badges / photo column, ending a little
   below the photo (nothing scrolls). JotForm's blank top margin and its
   "create your own form" footer are trimmed off the iframe (`JOTFORM_TOP`
   and `JOTFORM_BANNER` in site.js). The footer's rows in the live-vs-rebuild
   screenshot sheets predate this change.
9. **Nav links are weight 400**, matching the live header (which overrode the
   theme's 500 inline); link widths now match the live site to 0.01px.
9b. **The mobile menu opens tall enough to show all seven links** (requested
   before v1.0). The builder capped the open menu at half the screen height,
   which on most phones hid "FAQ" (and on small phones everything after
   "Weddings") behind an invisible scrollbar. The panel may now use the whole
   screen below the bar; it only scrolls on screens shorter than the list.
10. `/song-list`'s inverted heading structure, the 18 empty alt attributes, the
   malformed vendor mailto link and the lack of a cookie banner are **left
   exactly as they were**, per the Phase 2 list in
   [pre-migration scan/INVENTORY.md](pre-migration%20scan/INVENTORY.md#8-️-pre-existing-problems--flagged-not-fixed).

## Things worth knowing

- The brand carousel scrolls its logos off-screen after ~65 seconds and shows
  an empty band until it loops at 150s. That is how your original code behaves;
  it was reproduced faithfully. Easy to fix in Phase 2 if you want a seamless loop.
- Some originals are smaller than the screens they fill, and the old CDN was
  upscaling them: the homepage hero (`backgroundtest…`, 1193px wide), the
  /weddings hero (`z82_5728-Aq2N…`, 1067px), the homepage's third background
  (`z82_5452…`, 1600px), /welcome's background (`img_7996_2…`, 1607px) and the
  1067–1215px portraits. The rebuild reproduces that exactly, but replacing
  those originals with your full-resolution versions (drop them in
  `assets-original/` under the same file name and re-run `make-images.py`)
  is the one change that would make them genuinely sharper on 2x/3x screens.
- Elfsight plans can be domain-locked. If the reviews widget doesn't appear on
  a test subdomain, that's why — it will on the real domain.
- JotForm's post-submit redirect to `/thank-you` is configured inside JotForm,
  not on the site. It keeps working because the URL is unchanged.
- The JotForm banner is hidden by clipping, not removed. The iframe is kept
  at most 760px wide so JotForm always renders its compact layout (wider
  iframes get a padded layout with a 72px top margin and a 145px gap under
  the form); in the compact layout the blank top margin is 8px and the
  banner is the bottom 56px, at every screen size measured (390–1440px).
  Those two numbers are `JOTFORM_TOP` and `JOTFORM_BANNER` in
  `site/assets/js/site.js`. If JotForm ever changes its layout, adjust them
  (too small shows the banner; too large clips the Submit button). The same
  banner still shows under the forms on /welcome and /wedding-show-form — a
  v1.1 item, or remove it in JotForm's paid plan.

## Suggested cutover order

1. Upload `site/` contents to a temporary subdomain on Hostinger.
2. Walk `verification/migration-verification-checklist.md`; submit the
   booking form once and confirm it lands in your JotForm inbox and redirects
   to `/thank-you`.
3. Run PageSpeed Insights on the subdomain and compare with the links you saved
   in `pre-migration scan/scans.txt`.
4. Point the domain at the new files (low-traffic hours); keep the builder site
   available for a day in case of rollback.
5. Re-submit `sitemap.xml` in Google Search Console.
