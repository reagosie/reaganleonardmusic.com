# reaganleonardmusic.com — self-hosted rebuild

The site, rebuilt as plain HTML/CSS/JS that you own outright. No builder,
no framework, no build step. Upload the contents of `site/` to Hostinger and
it runs.

```
site/                       ← THE WEBSITE. Upload this folder's contents to public_html.
├── index.html …            13 pages, one file per URL (pricing.html → /pricing)
├── 404.html
├── robots.txt, sitemap.xml
├── .htaccess               https + bare-domain redirects, extensionless URLs, caching
└── assets/
    ├── css/site.css        the whole stylesheet, commented section by section
    ├── js/site.js          mobile menu, videos, lightbox, FAQ, lazy embeds
    ├── fonts/              Montserrat (the same files the old site served)
    └── img/                every image in AVIF, WebP and JPEG/PNG, at the same sizes and crops
                            the old CDN served (encoded at higher quality than it did)

tools/                      ← helpers. Optional; nothing here is needed to deploy or edit.
├── serve.py                local preview:  py tools/serve.py  →  http://localhost:8080
├── sync-shell.py           push a header/footer change to all 13 pages
├── verify.py               compare site/ with the archived original (SEO tags, text, links)
├── measure-weight.py       real page-weight comparison, old site vs new
├── make-images.py          regenerate image derivatives from originals (only if you add photos)
├── generate-pages.py       the one-time migration that produced v1.0 (do not re-run; see CHANGELOG.md)
├── song-list.json          the songs on /song-list
└── partials/               header.html / footer.html — the single source for the shared shell

pre-migration scan/         ← the archive of the old site: inventory, plan, every page,
                              image, embed and screenshot, captured 2026-09-09
verification/               ← your pre-cutover checklist
```

## Editing the site

Every page in `site/` is a normal HTML file — open it and edit. Text lives in
`<div class="text-box">` blocks; the layout system is explained at the top of
`site/assets/css/site.css` (each section is a CSS grid whose row/column
definitions sit in the section's `style` attribute).

**Header or footer** (nav links, phone, email, socials): edit
`tools/partials/header.html` or `footer.html`, then run

    py tools/sync-shell.py

which rewrites the marked `<!-- #shell:… -->` region in every page. (You can
also just edit all 13 files by hand — the script only saves you the repetition.)
The footer's layout rules are the "Footer" section of `site.css`; the pixels
trimmed off the top and bottom of the booking form (JotForm's blank margin
and its promotional banner) are `JOTFORM_TOP` / `JOTFORM_BANNER` at the
bottom of `site.js`.

**Adding or replacing a photo**: drop the full-resolution original in
`pre-migration scan/reference/assets-original/`, give it a name in
`tools/image-names.json`, run `py tools/make-images.py`, then reference it from
the page with a `<picture>` like the existing ones. Photos are served at the
sizes and crops the old site used, encoded at a higher quality than the old
CDN (AVIF 82 / WebP 90 / JPEG 90 — the settings are at the top of
`tools/make-images.py`, with the measurements behind them). Files named
`name-375.avif` are width rungs; `name-768x768.avif` are the per-breakpoint
crops that placed images and gallery tiles use.

## Previewing locally

    py tools/serve.py          # then open http://localhost:8080

The preview server mimics `.htaccess` (extensionless URLs, 404 page) so what
you see locally is what Hostinger will serve. It also prints a
`http://192.168.x.x:8080` address: open that on a phone on the same Wi-Fi
to test the real mobile experience (allow it through Windows Firewall the
first time). For a shareable test, upload `site/` to a temporary subdomain
on Hostinger.

## Checking before deploy

    py tools/verify.py         # SEO tags and links on every page (add --full for the old 1:1 text comparison)

## Things that are repeated on several pages

- **Reviews** (home, weddings, corporate, /welcome, /charlotte) come from
  `site/assets/data/reviews.json`: the Google rating and review count, every
  review, and under `"featured"` which review ids each page shows. `site.js`
  loads that file and fills in the count ("N five-star Google reviews") and
  the quote cards. The pages also hold a static copy of the cards (for
  no-JavaScript visitors and search engines); refresh it with
  `py tools/render-reviews.py` after editing the JSON.
  - `site/refresh-reviews.php` runs monthly on Hostinger (cron) and pulls the
    rating, the count and the latest reviews from Google. Setup:
    `deploy/google-reviews-setup.md`. It needs `reviews-config.json` (API
    key) on the server; that file is not in this repo.
  - `py tools/scrape-google-reviews.py` reads every review from the public
    Maps listing (Google's API only returns 5) and merges them in.
  - Long quotes use `"excerpt"` (cuts marked with …, words never changed);
    `"role"` is the event, shown after the name.
- **Song list** (`/song-list`): the songs are in `tools/song-list.json`.
  Edit the JSON, then run `py tools/render-song-list.py` to write them into
  the page.
- **Header and footer**: `tools/partials/`, then `py tools/sync-shell.py`.

`tools/generate-pages.py` was the one-time migration from the builder. It
does not know about the v1.1 changes; running it again would undo them.

## Deploying to Hostinger

Upload everything inside `site/` (including the hidden `.htaccess`) to
`public_html/` via File Manager or FTP. Test on a temporary subdomain first —
see `verification/migration-verification-checklist.md`.

## Third-party services the site depends on

| Service | What | Where |
|---|---|---|
| JotForm | booking request form `230255417493153`, wedding-show form `260106174629152` | footer, /welcome, /wedding-show-form |
| Elfsight | Google Reviews carousel widget | /, /welcome |
| Zola | "Best of Zola 2024" badge | footer |
| YouTube | 6 embedded videos | /, /photos-videos, /more-videos, /welcome |
| Google | Tag Manager `GTM-WNPC2JM`, Analytics `G-Q4JZ91TEGB`, Ads `AW-17134305700` (+ conversion on /thank-you) | every page |

These are exactly the services the old site used, with the same IDs.
