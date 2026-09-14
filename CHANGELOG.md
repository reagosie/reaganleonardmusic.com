# Changes

## v1.1 (2026-09-11) — first round of improvements, not yet deployed

Test locally with `py tools/serve.py`, then upload the contents of `site/`
(or `deploy/reaganleonardmusic-v1.1.zip`) to `public_html` and purge the
cache in hPanel. Ideas and reasoning are in [REDESIGN-IDEAS.md](REDESIGN-IDEAS.md).

### Every page
- **"Check availability" button** in the header on desktop, and a fixed bar
  at the bottom of the screen on phones (with a tap-to-call button). The
  buttons jump to the booking form on the same page when there is one, and
  go to /contact otherwise.
- **Menu**: Home · Weddings · Corporate · Pricing · Song List · Photos + Videos
  · FAQ. "Contact" moved off the desktop menu (the button replaces it); it is
  still in the phone menu and the page still exists.
- **Footer**: phone and email are tap-to-call / tap-to-email links; a line
  says "Based in Greer, SC. Serving Greenville, the Upstate and Charlotte."
- **Brand carousel** loops seamlessly instead of scrolling empty for most of
  each cycle.
- **Image descriptions** (alt text) filled in for the gallery photos and the
  brand logos.

### Home page
- New first screen: headline "Live acoustic music for weddings & events",
  your existing tagline, a proof line (300+ events · 15+ years · 32 five-star
  Google reviews · Serving the Upstate & Charlotte), and
  two buttons: "Check my availability" and "Watch me play" (scrolls to the
  promo reel). Same photo.
- **Reviews**: the Elfsight widget is replaced by three hand-picked quotes
  from your 32 five-star Google reviews (Kelsey Herring, GCM, Rhonda
  Marchant), each linking to the Google listing, plus a line linking to all
  reviews on Google, Zola and The Bash. You can cancel Elfsight once you are
  happy with this. Weddings shows three wedding reviews (Courtney Bramlett,
  Katherine Holtzman, Morgan Mundell), Corporate three event reviews (GCM,
  Leighanne Howard, Jalyn Whitlock), and /charlotte two travel/out-of-state
  reviews plus one from The Bash (Davidson, NC). Long quotes are shortened
  with "…"; no words were changed.
- **Live review count** (2026-09-14): the number of Google reviews and the
  quotes are no longer typed into the pages. They come from
  `assets/data/reviews.json`, which `refresh-reviews.php` updates from
  Google once a month (Hostinger cron job; setup in
  `deploy/google-reviews-setup.md`). The pages say "N five-star Google
  reviews" while every review is 5 stars, and switch to "N Google reviews,
  4.9 average" by themselves if that ever changes. New reviews are stored
  but only shown once their id is added to `"featured"` in that file.
  `tools/scrape-google-reviews.py` pulls the full list from the public Maps
  listing when needed.
- Structured data added so Google can show the business details (name,
  phone, area served, price range).

### Weddings
- Below the four package cards: "How your wedding day goes with Reagan"
  (ceremony / cocktail hour / reception, what each package covers), the
  travel note, a "Check my availability" button, two reviews, and four
  common questions with a link to the FAQ page.

### Corporate
- Two reviews (Meals on Wheels gala, a Greenville company party) and a
  "Check my availability" button under the intro.

### Song list (now public)
- Listed in the menu and the sitemap (it was hidden and marked "do not
  index"). A search box that filters as you type, jump links to each genre,
  and a "can't find it? ask me" note.
- 2026-09-14: replaced with the updated list from "Full Song List.pdf":
  248 songs in ten genres (Folk is back, Worship Songs added).
- The songs live in `tools/song-list.json`; `py tools/render-song-list.py`
  writes them into the page.

### Service area wording (2026-09-14)
- Footer, home page proof line and structured data, weddings FAQ excerpt and
  the FAQ answer now say: based in Greer, SC, playing within about 250 miles:
  Upstate South Carolina, Western North Carolina, Charlotte, North Georgia
  and East Tennessee. (The old FAQ said 500 miles.)

### New: /charlotte
- A page for Charlotte-area work: what you bring, how travel is priced,
  links to packages and the song list, two reviews from North Carolina
  clients, and the booking form. Linked from the footer and in the sitemap.

### /welcome (ad landing page)
- Rebuilt with the new components: headline, proof line, "Check
  availability" button, the three reviews, the promo reel, and the booking
  form (JotForm's banner trimmed here too). Still "do not index".

### FAQ
- Structured data for the six questions, so Google can show them under the
  search result.

### Tools
- `tools/verify.py` now checks SEO tags and links only; add `--full` for the
  old 1:1 text comparison with the archived site (no longer expected to pass).
- `tools/sync-shell.py` knows about /charlotte.
- `tools/generate-pages.py` is the one-time migration and will NOT reproduce
  these changes; do not run it again.

### Not changed, on purpose
- The booking form keeps all its fields and stays on JotForm (your call).
- The preferred-vendors page stays hidden.
- No Atlanta page.

## v1.0 (2026-09-10) — live
1:1 rebuild of the builder site as plain files. See [BUILD-REPORT.md](BUILD-REPORT.md).
