# Migration Plan — reaganleonardmusic.com

Proposed before building, per Step 2. See [INVENTORY.md](INVENTORY.md) for the evidence
behind every claim here.

---

## Headline: this migration is lower-risk than expected

Three findings de-risk it substantially:

1. **The forms are already JotForm**, not Zyro. Nothing to replace, nothing to rebuild,
   same inbox, same `/thank-you` redirect. The "replace Zyro-backend-dependent features"
   task in your brief turns out to be a no-op.
2. **The site is already static HTML** served from Hostinger with extensionless URLs.
   Plain `.html` files reproduce today's URL behaviour natively.
3. **I recovered the site's own content model** (the builder embeds it as JSON in every
   page), so the rebuild is driven by authored source content — exact text, positions,
   alt attributes, colours, font sizes — rather than by re-scraping rendered markup.

The one genuine risk is **images** (§3 below).

---

## 1. Recommendation on tooling: plain files — your instinct is right

You asked whether a static-site generator is worth it. **No — go with plain HTML/CSS/JS**,
for this site specifically:

- 13 pages, ~7 of which change essentially never
- No blog, no collections, no pagination, no content that grows
- An SSG would add Node/npm, a toolchain to maintain, and a build step between you and a
  fix — the exact class of dependency you're migrating *away* from

The one thing I'd script is image derivative generation (§3), and that runs **once,
locally, by me** — it produces plain files. Deployment stays drag-and-drop FTP. Nothing
needs to be installed on your machine or on Hostinger.

Trade-off worth naming: with no build step, the shared header/footer markup is duplicated
across 13 files. Changing a nav link means editing 13 files. For a site that changes a
few times a year, I think that's the right trade against a toolchain — but see the
question at the end.

---

## 2. File structure

```
public_html/
├── index.html                  →  /
├── contact.html                →  /contact
├── photos-videos.html          →  /photos-videos
├── weddings.html               →  /weddings
├── corporate.html              →  /corporate
├── pricing.html                →  /pricing
├── faq.html                    →  /faq
├── more-videos.html            →  /more-videos          (noindex)
├── song-list.html              →  /song-list            (noindex)
├── preferred-vendors.html      →  /preferred-vendors    (noindex)
├── welcome.html                →  /welcome              (noindex)
├── thank-you.html              →  /thank-you            (noindex, Ads conversion)
├── wedding-show-form.html      →  /wedding-show-form    (noindex)
│
├── robots.txt                  copied verbatim
├── sitemap.xml                 same 7 URLs, same priorities
├── .htaccess                   extensionless URLs, https+apex canonicalisation
│
└── assets/
    ├── css/site.css            one stylesheet, hand-written & commented
    ├── js/site.js              mobile nav toggle, FAQ accordion, JotForm autoresize
    ├── fonts/                  Montserrat 400/500/800 woff2, self-hosted
    └── img/
        ├── favicon-16.png, favicon-32.png, favicon-192.png, apple-touch-icon.png
        ├── og/                 social preview images
        └── <name>-{375,768,1024,1440,1920,2800}.{avif,webp,jpg}
```

**`.htaccess`** — I'll add one rather than relying on Hostinger's Apache defaults, so
URL behaviour is explicit and portable:
- serve `/pricing` from `pricing.html` (matches today)
- force HTTPS + apex (matches today's 301s)
- custom 404

---

## 3. Images — the one real risk, and the fix

Covered in detail in INVENTORY.md §7. Summary:

The originals total **48.4 MB**; the live site delivers **6.1 MB** because Cloudflare
resizes and re-encodes to AVIF/WebP on demand. That pipeline does **not** come with you.
Naively self-hosting the originals would make the site ~8× heavier and tank the
Lighthouse comparison in your verification checklist.

**Fix:** pre-generate derivatives at the same breakpoints the live site already uses
(375 / 768 / 1024 / 1440 / 1920 / 2800), in AVIF + WebP + JPEG fallback, and serve them
with `<picture>` + `srcset` + `sizes`. Browsers pick the smallest format they support —
the same outcome as today, without the CDN.

Expected result: **equal or better** than current, since the derivatives are static files
on the same origin with no CDN round-trip. I'll measure before/after and report actual
numbers rather than assert this.

Everything stays on your Hostinger account. No CDN, no third-party image host, no
ongoing cost.

---

## 4. Forms — keep JotForm exactly as-is

No change, no replacement. Same two embeds:

- `230255417493153` — Booking Request, in the footer of all 13 pages + `/welcome`
- `260106174629152` — Wedding festival form, on `/wedding-show-form`

Submissions keep going to your existing JotForm inbox. The post-submit redirect to
`/thank-you` is configured **inside JotForm**, so it keeps working as long as
`/thank-you` stays at the same path — which it does.

I'll carry over your iframe-autoresize snippet, but move it out of the inline embed into
`site.js` so it isn't duplicated 13 times.

---

## 5. Analytics — preserved exactly, but loaded earlier

All three tracking systems carry over verbatim:

| System | ID |
|---|---|
| Google Tag Manager | `GTM-WNPC2JM` |
| Google Analytics 4 | `G-Q4JZ91TEGB` |
| Google Ads | `AW-17134305700` |

Plus the `/thank-you` conversion event `AW-17134305700/xsCtCIL52eYaEKSDo-o_` — this is
your Ads booking conversion and I'll verify it fires after the rebuild.

**One implementation difference, in your favour:** the builder currently injects these
via JavaScript *after* page hydration. I'll place them as ordinary `<script>` tags in
`<head>`, which is the standard Google install. Same IDs, same events, same data — they
just start collecting a few hundred ms earlier and don't depend on framework JS running.
This makes tracking more reliable, not less.

I'll also fix the `id=undefined` GTM `<noscript>` bug (INVENTORY §8.3) unless you'd
rather I reproduce it faithfully — it's a builder defect with no upside.

---

## 6. SEO parity — the non-negotiable part

Reproduced verbatim, per page: `<title>`, meta description, meta keywords, canonical,
all Open Graph tags, all Twitter Card tags, the JSON-LD block, `lang="en"`, favicon
links, and the `noindex` on all six hidden pages.

`sitemap.xml` and `robots.txt` copied as-is. **No URL changes anywhere**, so no redirects
are needed and nothing to lose.

Heading hierarchy preserved exactly as-is per page — including the odd structure on
`/song-list` (INVENTORY §8.6), which I'll leave alone in this pass.

Two `og:image` URLs are already 404 on the live site (INVENTORY §8.1). I'll reproduce the
tags as they are and leave the broken references — flagged for you rather than silently
substituted, since choosing replacement images is a content decision.

---

## 7. Verification before cutover

Against your existing [migration-verification-checklist.md](../verification/migration-verification-checklist.md),
I'll additionally run automated checks:

- **Diff every SEO tag** — new page vs the captured original, field by field, all 13 pages
- **Visual diff** — new build vs the 26 reference screenshots (desktop + mobile) already captured
- **Link check** — every internal and external link, including the 28 vendor links
- **Weight/performance comparison** — measured page weight vs the live site, per page
- Confirm all three tracking IDs fire, and the `/thank-you` conversion event

I'll report actual results, including anything that doesn't match.

---

## 8. Explicitly out of scope for this pass

No redesign, no new features, no content changes, and **none of the 11 pre-existing
issues** in INVENTORY §8 get silently fixed — except the two trivial mechanical ones I
flagged above (GTM `noscript` id, and deduplicating the autoresize script), and only if
you agree.

---

## Decisions (settled 2026-09-09)

### A. Custom HTML blocks → inline and scope

Your custom-code blocks (wedding package cards, FAQ accordion, corporate card, logo
carousel) currently render inside **sandboxed `<iframe srcdoc>`** containers, which means
that text is *not* indexable page content today — Google doesn't credit `/weddings` with
the package names/prices, or `/faq` with the answers.

**Decision: inline them into the page and scope their CSS.** Since this is your own
custom code, rewriting the selectors is safe. Visually identical; the pricing and FAQ
text becomes real indexable content. Net SEO gain.

Care required — these blocks currently rely on iframe isolation:
- FAQ block sets a global `ul { column-count: 2 }` → will be scoped to `.faq-panel ul`
- Cards use `@import url(…Montserrat…)` → dropped, since Montserrat is self-hosted site-wide
- Generic class names (`.wrapper`, `.track`, `.logo`, `.panel`, `.accordion`) → prefixed

All 13 blocks were recovered verbatim from the site data during the crawl and are saved
in [reference/embeds/](reference/embeds/) — no need to re-export them from the builder.

### B. Header/footer → duplicated markup, in marked regions, with an optional sync script

Since Claude Code will be making future edits, the priority is a single reliable place to
change and no drift.

**Decision: keep the deployed artifact as 13 plain, self-contained HTML files** (no build
step, exactly what gets FTP'd), but make the shared shell mechanically maintainable:

- header/footer wrapped in explicit `<!-- #shell:header start --> … end -->` markers,
  byte-identical across all 13 files
- an optional `tools/sync-shell.py` that propagates the shell from `index.html` to the
  other 12 and verifies they match

So a nav change is one edit plus one command — or one instruction to Claude Code — while
the thing you upload stays plain HTML that never *requires* a build step to edit or
deploy.

---

## One thing I couldn't recover — can you send it?

`carousel.css` — your injected stylesheet at
`srv1015-files.hstgr.io/b48071fee3e95af8/files/carousel.css` returns **403 Forbidden**
(verified in a real browser, so it's dead for visitors too, not just for my crawler).

It's the only piece of your custom code I can't read. If you can grab the file from
Hostinger's File Manager, I'll fold it into `site.css` properly. If you can't find it or
don't remember what it did, that's fine — it's been doing nothing on the live site, and
the site currently renders correctly without it, so I'll simply drop the dead reference.

---

*Nothing has been built yet. Next: the shared shell (header/footer/CSS), then the 7
indexed pages, then the 6 hidden ones.*
