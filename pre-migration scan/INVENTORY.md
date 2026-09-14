# reaganleonardmusic.com — Pre-Migration Inventory

Crawled 2026-09-09. Everything below is observed from the live site, not assumed.
Raw evidence is in [reference/](reference/).

---

## 1. What the site actually is

Not Zyro anymore — Hostinger migrated it to their newer stack:

| | |
|---|---|
| Generator | `Hostinger AI Builder` (Zyro's successor) |
| Framework | Astro + Vue, server-rendered to **static HTML** |
| Hosting | Hostinger, serving pre-built `.html` files |
| Assets | `assets.zyrosite.com` behind Cloudflare image-resizing (`/cdn-cgi/image/…`) |
| Fonts | Montserrat via Zyro's Google-Fonts proxy (`cdn.zyrosite.com`) |
| Site ID | `Yg2xxNENX5FGqrpg` |
| Build date | 2026-08-26 |

**This is good news for the migration.** The pages are already static HTML with
extensionless URLs (`/pricing` and `/pricing.html` both return 200 today). Dropping
plain `.html` files into `public_html` reproduces the current URL behaviour natively —
no rewrite gymnastics needed.

The full authored content model is embedded in each page as JSON (Astro island props).
I extracted it, so the rebuild works from the **actual source content**, not from
scraped markup. Decoded per-page data is in [reference/site-data/](reference/site-data/).

---

## 2. Pages — 13, not 12

The sitemap lists only 7. Five more are live but hidden from nav *and* unlinked, so a
link-crawl alone would have missed them. I found them in the site's own page table and
confirmed each returns HTTP 200.

| # | URL | `<title>` (rendered) | Indexed | In sitemap | In nav |
|---|---|---|---|---|---|
| 1 | `/` | Greenville SC Musician for Weddings & Events \| … | yes | yes | yes |
| 2 | `/contact` | Contact - Reagan Leonard Music \| … | yes | yes | yes |
| 3 | `/photos-videos` | Photos and Videos - Reagan Leonard Music \| … | yes | yes | yes |
| 4 | `/weddings` | Wedding Musician - Greenville, SC \| … | yes | yes | yes |
| 5 | `/corporate` | Corporate Event Entertainment - Greenville, SC \| … | yes | yes | yes |
| 6 | `/pricing` | Pricing - Reagan Leonard Music \| … | yes | yes | yes |
| 7 | `/faq` | FAQ - Reagan Leonard \| … | yes | yes | yes |
| 8 | `/more-videos` | More Videos - Reagan Leonard Music \| … | **noindex** | no | hidden, linked from `/photos-videos` |
| 9 | `/song-list` | Song List - Reagan Leonard Music \| … | **noindex** | no | hidden, linked from FAQ answer |
| 10 | `/preferred-vendors` | Preferred Vendors \| … | **noindex** | no | hidden, **unlinked** |
| 11 | `/welcome` | Welcome - Reagan Leonard Music \| … | **noindex** | no | hidden, **unlinked** (ad landing page) |
| 12 | `/thank-you` | Thank You - Reagan Leonard Music \| … | **noindex** | no | hidden, **unlinked** (form redirect target) |
| 13 | `/wedding-show-form` | Wedding Show Contact Form \| … | **noindex** | no | hidden, **unlinked** |

All 13 must ship. `/thank-you` in particular is load-bearing — it is the JotForm
redirect target and fires the Google Ads conversion.

The `noindex` on pages 8–13 is deliberate and **must be preserved**; the sitemap is
correctly limited to the 7 indexable pages.

### URL behaviour to preserve
- `http://` → `https://` — 301
- `www.` → apex — 301
- `/pricing/` (trailing slash) → **404 today**
- `/pricing.html` → 200 (duplicate of `/pricing`, protected by the canonical tag)
- No `/favicon.ico` at root; favicons are `<link>` tags to CDN PNGs

---

## 3. SEO elements (captured verbatim per page)

Every page carries, and the rebuild must reproduce exactly:

- `<title>`, `<meta name="description">`, `<meta name="keywords">`
- `<link rel="canonical">` — absolute, extensionless
- Open Graph: `og:url`, `og:title`, `og:description`, `og:type`, `og:image`,
  `og:image:alt` (empty on every page), `og:site_name`
- Twitter: `card` (`summary_large_image`), `title`, `description`, `image`, `image:alt`
- **JSON-LD** — one block per page. Homepage is `@type: WebSite`; the other 12 are
  `@type: WebPage`. Each carries name/url/description/image/inLanguage/keywords.
- 4 favicon `<link>`s (16, 32, 192, apple-touch 180)
- `<html lang="en">`, `hreflang="x-default"` on the homepage

Exact values per page: [reference/site-data/seo.json](reference/site-data/seo.json).

### Heading structure
Every page has exactly one `<h1>`. The shared footer contributes an `<h6>` "CONTACT ME"
and an `<h4>` "Check my availability for your event:" to all 13.
Full per-page outline is in `seo.json`.

---

## 4. Analytics & tracking — three separate systems, all live

These are injected **client-side into `<head>`** by the builder's JS, which is why they
don't appear in view-source. I confirmed all three fire by rendering the page in a real
browser.

| System | ID | How it gets there |
|---|---|---|
| Google Tag Manager | `GTM-WNPC2JM` | builder setting, injected at runtime |
| Google Analytics 4 | `G-Q4JZ91TEGB` | builder setting, injected at runtime |
| Google Ads | `AW-17134305700` | user's custom body-code injection |

Plus a **conversion event on `/thank-you`**:
```js
gtag('event', 'conversion', {'send_to': 'AW-17134305700/xsCtCIL52eYaEKSDo-o_'});
```
This is the booking-conversion signal for Google Ads. If it doesn't survive the
migration, Ads conversion tracking silently dies.

There is **no cookie-consent banner** shown; tags fire unconditionally on load.

---

## 5. Forms — no Zyro backend dependency at all

This is the single most important finding for migration risk. Both forms are
**JotForm**, already fully third-party:

| Form | JotForm ID | Where |
|---|---|---|
| "Booking Request" — 9 fields | `230255417493153` | global footer on all 13 pages, plus `/welcome` |
| Wedding festival interest form | `260106174629152` | `/wedding-show-form` only |

Fields on the main form: Event Type\*, Length of Performance\*, Location of Event\*,
Budget\*, Estimated # of Guests, Additional Details, Contact Name\*, Contact Email\*,
Contact Phone #\*. It posts to `https://submit.jotform.com/submit/230255417493153`.

**So there is nothing to replace.** No Formspree, no mailto fallback, no server code.
Copy the same embed script and the forms keep working, keep the same submission inbox,
and keep the `/thank-you` redirect (that redirect is configured inside JotForm, not on
the site).

The site data does contain a vestigial Hostinger-native form token
(`forms."Contact form"`), but no page uses a native form element — it's dead config.

---

## 6. Third-party embeds

| Embed | Detail | Migration note |
|---|---|---|
| **Elfsight Google Reviews** | app `google-reviews`, widget `f8cd8f7b-…afad937`, Google Place `ChIJxToXfm6xe2QRgeCIy2d22Is`, 5-star filter, carousel | on `/` and `/welcome`. Paid Elfsight account — check whether the plan is domain-locked before cutover |
| **Zola "Best of Zola 2024" badge** | script + image from `d1tntvpcrzvon2.cloudfront.net` | in footer on all 13 pages |
| **YouTube** | 6 videos, `youtube-nocookie` preconnect | `SgA_gRUz2J4` (home, photos-videos, welcome); `Ar4LiBfcGVQ`, `cb8al5-ahCM`, `6M1ydzS44SI`, `Oh-GQ7zuUM4`, `Dy9GmmOKAp0` (more-videos) |
| **Brand logo carousel** | hand-written CSS marquee, 10 partner logos | `/` and `/corporate` |
| **FAQ accordion** | hand-written JS accordion, 6 Q&As | `/faq` |
| **Wedding package cards** | 4 hand-written HTML cards (Silver $500, Gold $600, Diamond $1000, Rehearsal Dinner $750) | `/weddings` |
| **Corporate card** | hand-written HTML card | `/corporate` |

⚠️ **Custom HTML blocks currently render inside sandboxed iframes.** That isolation is
why the FAQ accordion's `ul { column-count: 2 }` and the cards' `@import` don't leak into
the page. If these are inlined directly during the rebuild, their CSS **will** leak and
break other elements. They need either scoped selectors or the same iframe isolation.

All 13 embed sources saved to [reference/embeds/](reference/embeds/).

---

## 7. Assets

41 unique site-hosted images, downloaded at original resolution to
[reference/assets-original/](reference/assets-original/).

### ⚠️ The performance trap
The originals are camera-resolution files. The live site never serves them — Cloudflare
resizes and re-encodes to AVIF/WebP on the fly.

| | Total |
|---|---|
| Original files | **48.4 MB** |
| What the live site actually delivers | **6.1 MB** |
| Ratio | **7.9× heavier** |

Worst individual cases:

| File | Original | Served | Factor |
|---|---|---|---|
| `cropped-YbNNK7rQ3eCWbGOQ.jpg` | 11.3 MB (4000×4177) | 120 KB @768 AVIF | **94×** |
| `img-m6LL6lEQMwfvxE1N.jpg` | 5.9 MB (4000×6000) | 249 KB @768 AVIF | 24× |
| `img-AzGG6JGQpWie8oMD.jpg` | 8.1 MB (4000×2556) | 1.2 MB @2800 WebP | 6× |
| `pxl_20230716_191002135-…jpg` | 2.5 MB (3840×2160) | 110 KB @768 AVIF | 22× |

**Dropping the originals in as-is would make the site dramatically slower than it is
today** and fail the "equal or better Lighthouse" goal in the verification checklist.
The rebuild must pre-generate resized AVIF/WebP/JPEG derivatives.

Responsive widths the live site requests: **375, 768, 1024, 1440, 1920, 2800**
(logos/badges use fixed small widths). Per-image size list:
[reference/site-data/cdn_variants.json](reference/site-data/cdn_variants.json).

### Fonts
Montserrat, weights **400 / 500 / 800**, `display=swap`, currently proxied through
`cdn.zyrosite.com`. That proxy is a Zyro dependency and should be replaced with
self-hosted woff2 (best) or Google Fonts directly.

### Typography & colour (from site config, exact)
- h1 96/44px w500 · h2 64/36 w400 · h3 48/32 w400 · h4 36/28 w400 · h5 28/24 w400 · h6 20/20 w800
- body 16px w500 lh1.6 ls0.04em · nav-link 14px w500 · body-large 18px · body-small 14px
- Header/footer green `rgb(20,46,20)`, hover `rgb(39,89,39)`, light grey `rgb(221,221,221)`,
  mid grey `rgb(181,181,181)`, button cream `rgb(222,216,192)` on text `rgb(35,35,35)`
- Header: sticky, logo 125px desktop / 100px mobile, content width 1240px, grid 1224px/12col

### Contact details (in footer, all 13 pages)
`864-706-5104` · `reagan@reaganleonardmusic.com` ·
[instagram.com/reaganleonardmusic](https://www.instagram.com/reaganleonardmusic/) ·
[facebook.com/reaganleonardmusic](https://www.facebook.com/reaganleonardmusic/)

---

## 8. ⚠️ Pre-existing problems — flagged, NOT fixed

Per your instruction these are recorded rather than silently corrected. All exist on the
live site **today**.

| # | Issue | Impact | Suggested phase |
|---|---|---|---|
| 1 | **Two `og:image` URLs return 404** — `img-m5KKLB5nGQiJNLBl.jpg` (used by `/photos-videos`, `/more-videos`) and `rlm-logo-black-mePaxMrewqf64kag.png` (used by `/faq`). The source files are gone from the CDN. | Those 3 pages show **no image** in social/link previews | Phase 2 — needs you to pick replacement images |
| 2 | **Your injected `carousel.css` returns 403** (`srv1015-files.hstgr.io/…/carousel.css`). Verified dead in a real browser. | The stylesheet does nothing today. Site currently looks correct without it — but whatever it was meant to style never applies | Phase 2 — decide if it's still needed |
| 3 | **GTM `<noscript>` iframe has `id=undefined`** — builder bug, emits `googletagmanager.com/ns.html?id=undefined` | No-JS visitors aren't tracked by GTM | Easy fix in rebuild if you want it |
| 4 | **Malformed link on `/preferred-vendors`**: `https://Mailto:James@jdlmediaclt.com` — `https://` prefixed onto a `mailto:` | Broken link; goes nowhere | Phase 2 (1-char fix) |
| 5 | **18 of 41 images have empty `alt`** — including all 12 gallery images on `/photos-videos` and the hero/portrait shots | Accessibility + image-SEO loss | Phase 2 — needs you to write alt text |
| 6 | **`/song-list` heading hierarchy is inverted** — 9 category headings are `<h6>`, and the `<h1>` is the disclaimer paragraph ("Please note that these are not the only songs…") styled down to 24px | Confusing structure; limited SEO impact since noindex | Phase 2 |
| 7 | **`/wedding-show-form` has no meta title set**; the rendered title falls back to the internal page name | Cosmetic | Phase 2 |
| 8 | **`/pricing.html` and `/pricing` both return 200** | Duplicate content, currently mitigated by canonical tags | Keep canonicals; optionally 301 in Phase 2 |
| 9 | **Trailing-slash URLs 404** (`/pricing/`) | Minor; matches current behaviour | Consider 301 rather than 404 in Phase 2 |
| 10 | **No cookie-consent banner** though consent CSS loads; GA4/GTM/Ads fire unconditionally | Possible GDPR/CCPA exposure depending on audience | Phase 2 legal call |
| 11 | `og:image:alt` is empty on all 13 pages | Minor a11y/social nicety | Phase 2 |

None of these block the rebuild.

---

## 9. What's captured in `reference/`

| Folder | Contents |
|---|---|
| `pages-raw/` | 13 × server HTML as delivered |
| `pages-rendered/` | 13 × fully JS-executed DOM (shows the injected analytics) |
| `content/` | 13 × human-readable content outline, in visual order, with positions/alt/links |
| `assets-original/` | 41 images at full original resolution (48 MB) |
| `embeds/` | 13 unique custom-HTML/embed blocks, verbatim |
| `site-data/` | decoded page JSON, `seo.json`, asset detail, CDN size map, `sitemap.xml`, `robots.txt`, site CSS + font CSS |
| `screenshots/` | desktop (1440px) + mobile (390px) full-page reference shots of all 13 pages |

`robots.txt` is trivial and unchanged:
```
Sitemap: https://reaganleonardmusic.com/sitemap.xml

User-agent: *
Disallow:
```
