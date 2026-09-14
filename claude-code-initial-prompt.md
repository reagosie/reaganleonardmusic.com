# Rebuild reaganleonardmusic.com as self-hosted static site

## Background
My music business site (reaganleonardmusic.com) was built ~5 years ago in Zyro, a
website builder Hostinger has since deprecated. I can't access the underlying
code — only HTML/CSS injection blocks. A recent Hostinger/Zyro domain
deprecation took the site offline for over a week with no warning. I'm staying
on Hostinger for hosting (cheap, otherwise reliable) but want to own my code
going forward instead of depending on a builder.

## Objective
Recreate the site **exactly as it looks and functions today** — same pages,
same layout, same content, same SEO performance — as plain, portable code I
fully control. This is a 1:1 migration, **not** a redesign. Improvements come
in a later phase.

## Step 1 — Inspect before building
Before writing any code, crawl and inventory the live site at
reaganleonardmusic.com:
- Full list of pages/URLs (check sitemap.xml and robots.txt first)
- Rendered HTML, CSS, and JS for each page (view-source / computed styles,
  since Zyro outputs standard rendered markup even though the editor is
  proprietary)
- All images, fonts, icons, favicons — save at original resolution
- Every `<meta>` tag, Open Graph tag, and any structured data (JSON-LD) per page
- Page titles, meta descriptions, and heading hierarchy (h1/h2/etc.) per page
- Any embedded widgets: music players, contact/booking forms (and where they
  submit to), social embeds, analytics/tracking scripts (e.g. Google
  Analytics, Meta Pixel)
- Exact URL paths/slugs — these must be preserved exactly for SEO; don't
  change routing structure

Summarize findings and flag anything ambiguous (e.g. a form with no visible
submit endpoint, missing alt text, broken links) before proceeding — don't
silently fix or skip these, just note them for Phase 2.

## Step 2 — Confirm scope
After the inventory, give me a short plan: page list, file structure, and how
you'll handle anything that depended on Zyro's backend (forms, etc.) before
building.

## Step 3 — Build
- Output: plain HTML/CSS/JS, no build step, no framework — deployable by
  dropping files directly into Hostinger via FTP/File Manager (this matches
  my "host my own code, keep Hostinger" goal most directly; tell me if you
  think a lightweight static-site generator is worth it instead, but default
  to plain files).
- Preserve all SEO elements found in Step 1 verbatim: meta tags, OG tags,
  structured data, sitemap.xml, robots.txt, URL paths, heading structure, alt
  text, analytics scripts.
- Replace any Zyro-backend-dependent features (contact forms, etc.) with a
  static-site-compatible equivalent (e.g. Formspree, mailto, or similar) —
  flag the option you pick and why.
- Clean, readable, commented code — no obfuscated or generated-looking markup.

## Explicitly out of scope for this pass
No visual redesign, no new features, no content changes. Once this is live
and verified against the current site, we'll do a second pass for
improvements.
