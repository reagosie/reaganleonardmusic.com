# Migration Verification Checklist
Use this once Claude Code says the rebuild is done, before pointing your real
domain at the new site.

## 1. Content parity
- [ ] All 12 pages present, at the same URL paths as the original
- [ ] Text content matches the live site on every page (spot-check, don't
      assume)
- [ ] All images present at original quality/resolution, correct alt text
- [ ] Fonts render the same (check for fallback-font flashes)
- [ ] Favicon present and correct

## 2. Functionality
- [ ] Contact/booking form submits successfully and you receive the message
- [ ] Any music player / embedded audio works
- [ ] All internal links go to the correct (preserved) URLs
- [ ] All external/social links work
- [ ] Site renders correctly on mobile, not just desktop
- [ ] No console errors in browser dev tools on any page

## 3. SEO parity — the critical part
- [ ] `sitemap.xml` exists, lists all pages, matches the old one's URL structure
- [ ] `robots.txt` matches (same allow/disallow rules)
- [ ] Every page's `<title>` and meta description match the original exactly
- [ ] Open Graph / social preview tags match (test with a link-preview tool)
- [ ] Structured data (JSON-LD, if the old site had any) is present and valid
      — check with Google's Rich Results Test
- [ ] Heading hierarchy (h1/h2/h3) unchanged per page
- [ ] **No URL has changed** — if any path had to change, a 301 redirect is
      in place from old to new
- [ ] Analytics/tracking script (Google Analytics, etc.) is installed and
      firing on the new site

## 4. Performance
- [ ] Run the new site through PageSpeed Insights / Lighthouse
- [ ] Compare against a saved Lighthouse score from the old site (grab this
      *before* switching, if you haven't already) — new site should be equal
      or better, not worse
- [ ] Compare Google Search Console indexing status weekly for the first
      month after switch (page count indexed shouldn't drop)

## 5. Cutover safety
- [ ] New site is tested live at a temporary URL/subdomain before DNS points
      to it
- [ ] You have a backup/export of the old Zyro site content in case you need
      to reference something you missed
- [ ] DNS change is made during low-traffic hours, in case rollback is needed
- [ ] After go-live, submit the (unchanged) sitemap.xml to Google Search
      Console again to prompt re-crawling
