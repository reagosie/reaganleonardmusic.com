# Redesign ideas for reaganleonardmusic.com

Written 2026-09-11, after the v1.0 launch. Based on: your four friends' sites
(Jordan Okrend, Adam Harris Thompson, Logan Thomas, CJ Brewer), who ranks for
wedding-musician searches in Greenville / Charlotte / Atlanta, and general
guidance on wedding-vendor websites that turn visitors into inquiries.

Screenshots of all five sites (desktop and phone) are in
`verification/peer-sites/` for reference.

## What I could and could not measure

- I cannot see anyone's traffic numbers. Small sites do not publish them and
  the free estimate tools are guesses. The best public proxy for "traction"
  is where people show up in Google results and in the wedding directories
  (The Bash, WeddingWire, The Knot, Zola, GigSalad), because that is where
  most couples start.
- On The Bash's "Top 20 wedding singers in Greenville" list, Jordan (9
  reviews, $500), CJ (6 reviews, $500) and Adam (27 reviews, $300) all appear.
  You have a Bash profile but are not in that list. WeddingWire's Greenville
  ceremony-music list has none of you (it is harps and string quartets). You
  are on Zola, GigSalad, PartySlate and Eventective, and you rank #1 for your
  own name.
- Those directory listings are not web design, but they send more first
  visits than the design does. Worth a separate look.

## Honest comparison

| | Reagan (now) | Jordan | Logan | CJ | Adam |
|---|---|---|---|---|---|
| Who it is for | couples + corporate | couples + corporate | couples + corporate | couples + venues | fans (original music) |
| Headline says what + where | no (headline is your name) | yes | yes | partly | no |
| Button to book in the header | no | no | yes | yes | yes |
| Trust numbers near the top | no (they are on /welcome only) | no | no | yes (500+ shows, 10+ yrs) | no |
| Reviews on home page | yes, 1 at a time | yes, 1 at a time | yes, 1 at a time | yes, 1 at a time | no |
| Client / venue logos | yes | yes | yes | yes | no |
| Videos on home page | 1 | 4 | 8 (carousel) | 0 | many |
| Published prices | yes (rare, good) | no | no | no | no |
| Song list on the site | hidden page | button | no | yes, by genre | n/a |
| Inquiry form fields | 10 | 4 | ~8 | 7 | n/a |
| Page speed | fast (plain HTML) | ok | slow (Wix) | ok | slow |

My honest read: your site is already better than Adam's for booking (his is
a fan site) and at least as good as CJ's. Jordan's and Logan's are the two to
learn from, and each beats you in exactly one or two places: Jordan's
headline and video section, Logan's repeated "reserve your date" buttons.
Your two clear advantages are published pricing and speed. Keep both.

## Ideas, ranked by expected effect on inquiries

Effort: S = an hour or two, M = a day, L = several days.

### 1. Rewrite the top of the home page (effort S, effect high)
Right now the first screen shows a paragraph, then your name, then a button.
Visitors decide in about five seconds whether they are in the right place.
Change the first screen to:
- Headline that says what and where: "Live acoustic music for weddings and
  events in Greenville, SC" (your name moves to the logo and the line below).
  This is also what Google reads first.
- One line of proof under it: "300+ events · 15+ years · 5.0 on Google". You
  already wrote this for the /welcome ad page; it belongs on the home page.
- Two buttons: "Check my availability" (main) and "Watch me play" (scrolls to
  the video).

### 2. A "Check availability" button that is always visible (effort S, effect high)
Add it to the header on desktop and as a thin bar at the bottom of the
screen on phones. Every page, every scroll position. Logan and CJ both do
this; your site makes people scroll to the footer to find the form.

### 3. Shorter inquiry form (effort S, effect medium-high)
Ten required-looking fields is a lot on a phone. Ask for the five things you
need to reply: name, email, phone, event date, event type, plus one free-text
box. Ask budget, guest count and length on the follow-up call. This is
changed inside JotForm, not in the site code, and I can walk you through it.

### 4. Show the song list (effort M, effect medium-high)
You have a 100+ song list but it is a hidden page, marked "do not index" and
not in the menu. Couples search for "can he play X". Put it in the menu,
group by mood (ceremony, cocktail hour, upbeat) as well as by genre, add a
search box, keep the "I can learn songs on request" note. Also good for
Google: pages that list artists and songs pick up long searches.

### 5. Reviews section that shows more than one review (effort S-M, effect medium)
Show three reviews side by side with the Google rating and count at the top
("5.0 · 24 Google reviews"), and put one wedding review on the weddings page
and one corporate review on the corporate page. The Elfsight widget can do
the three-up layout; or we drop Elfsight and hand-pick quotes, which loads
faster and never breaks. Trade-off: hand-picked quotes do not update
themselves.

### 6. More video on the home page (effort S, effect medium)
One promo reel is good. Add three short clips under it (a ceremony song, a
cocktail-hour song, an upbeat one), like Jordan's page. Video is the thing
couples most want before they email. If you have 30–60 second clips on
YouTube already, this is an afternoon.

### 7. Weddings page: keep the cards, add the story (effort M, effect medium)
The four package cards with prices are your best asset. Around them add: a
short "how the day goes" strip (ceremony → cocktail hour → reception, what
you provide at each), one couple's review, an FAQ excerpt ("Do you bring your
own sound?"), and a "Check availability" button right under the cards. Also
fix the brand carousel that goes blank for 85 seconds of every loop.

### 8. Photo gallery with captions (effort M, effect low-medium)
The 12 identical squares look like a builder default. A mixed-size gallery
with venue names as captions looks more professional, and venue names help
Google match you to "[venue] wedding musician" searches.

### 9. Service-area pages (effort M-L, effect medium for Charlotte/Atlanta)
Google shows local results. Jordan's headline names Asheville on purpose. If
you want Charlotte and Atlanta work, add a short page for each ("Wedding and
event musician traveling to Charlotte, NC") with the travel policy from your
pricing page, a review from an event there if you have one, and the form.
Downside: thin pages can look like spam; each needs real content.

### 10. Make "Preferred vendors" public (effort S, effect low-medium)
It is currently hidden. A public "Venues and vendors I recommend" page is
good for Google and good for relationships: venues you list tend to link
back and refer you.

### 11. Visual refresh (effort L, effect low on its own)
The green and cream palette and the photos are good; keep them. What looks
"built in a builder" is the inconsistency: some sections have parallax photo
backgrounds with dark overlays, some are flat grey, text sizes jump around.
A refresh would set one type scale, one spacing rhythm, one way of doing
section backgrounds, and use the photos larger and less often. I would do
this last, after the content changes above, and I can show you two or three
mock-ups to pick from before touching code.

### 12. Small technical items (effort S each)
- Structured data for Google (a small block of code describing you as a
  local business and your FAQ page as questions and answers), so search
  results can show stars and FAQ lines.
- A real "Contact" page instead of a page that says "Contact Reagan below"
  above the footer form.
- Tap-to-call and tap-to-email on the phone number and address.
- Fill in the 18 empty image descriptions (helps Google Images and screen
  readers).

## Suggested order

1. Ideas 1, 2, 3, 6, 12 together: one afternoon of changes, all on the home
   page and shell, largest effect.
2. Ideas 4, 5, 7: content and page work, a few days.
3. Ideas 8, 9, 10 as you have material for them.
4. Idea 11 with mock-ups once the content is settled.

## Questions to decide together

- Do you want Charlotte and Atlanta work enough to have pages for them?
- Are you happy for the song list and the preferred-vendors list to be
  public and searchable?
- Reviews: keep the live Google widget, or hand-picked quotes?
- Do you have short performance clips already (YouTube or phone videos)?
- Is the form change in JotForm something you want to do, or would you
  rather I build a form on the site (works without JotForm; needs a form
  service or email handler)?
