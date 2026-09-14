# Google reviews: automatic monthly refresh

The site shows your Google star rating, your total review count and a few
hand-picked quotes. They come from one file on the server,
`assets/data/reviews.json`. A small job (`refresh-reviews.php`) asks Google
once a month for the current numbers and the latest reviews and updates that
file. The pages read it when they load, so the number on the site is never
typed in by hand.

This guide sets that job up. It takes about 20 minutes, once. Cost: $0 at
this volume (details in the last section).

## What you need

- A Google account (the one that owns the Business Profile is fine, but any
  Google account works; this does not use the Business Profile login).
- A card to put on the Google Cloud billing account. Google requires it even
  when usage stays inside the free allowance.
- Access to hPanel (Hostinger).

## Part 1: get a Google API key (about 10 minutes)

An API key is a long password that lets a program ask Google for data.

1. Go to https://console.cloud.google.com/ and sign in.
2. At the top, open the project menu and click **New project**. Name it
   `Reagan Leonard Music website` and create it. Make sure it is selected.
3. Billing: menu (three lines, top left) → **Billing** → link a billing
   account (create one with your card if you have none). Nothing is charged
   at our usage, see the cost section below.
4. Menu → **APIs & Services** → **Library**. Search for **Places API (New)**
   and click **Enable**. (Not the one called just "Places API"; that is the
   old version.)
5. Menu → **APIs & Services** → **Credentials** → **Create credentials** →
   **API key**. Copy the key somewhere safe for the next part.
6. Click the new key to edit it, then lock it down:
   - **Application restrictions**: None is fine (the key only lives on the
     Hostinger server, never in a browser).
   - **API restrictions**: choose **Restrict key** and tick only
     **Places API (New)**. Save.

## Part 2: put the key on the server (about 5 minutes)

The key goes in a small file called `reviews-config.json`, one folder ABOVE
`public_html`, so it is not reachable from the web. (If you cannot write
there, next to `refresh-reviews.php` inside `public_html` also works; the
site's `.htaccess` refuses to serve that file name.)

1. hPanel → your website → **Files** → **File Manager**.
2. You land in `public_html`. Go one level up (the folder that contains
   `public_html`).
3. **New file** → name it `reviews-config.json` → open it and paste:

   ```json
   {
     "key": "PASTE-YOUR-API-KEY-HERE",
     "token": "make-up-a-long-random-secret-here"
   }
   ```

   The token is a password of your own choosing (30+ random characters).
   It is only needed if you ever run the job from a browser. Save.

## Part 3: the monthly cron job (about 5 minutes)

A cron job is a command the server runs on a schedule.

1. hPanel → your website → **Advanced** → **Cron Jobs**.
2. Type: **Custom**. Command to run:

   ```
   php /home/USERNAME/domains/reaganleonardmusic.com/public_html/refresh-reviews.php
   ```

   Replace `USERNAME` with your hosting username. You can see the full path
   in File Manager (it is shown at the top when you are inside `public_html`),
   or in hPanel → **Advanced** → **SSH Access** (the "Username" there, which
   looks like `u123456789`).
3. Schedule: **Monthly**. Pick the 1st of the month, 3:00 AM (any quiet time
   works). Save.
4. Optional: turn on email output for the job so you get the short report each
   month. The report says the current count and lists any new reviews.

## Part 4: run it once by hand and check

Either click **Run now** on the cron job (if hPanel offers it), or open this
address in your browser, using your token from Part 2:

```
https://reaganleonardmusic.com/refresh-reviews.php?token=YOUR-TOKEN
```

A good run prints something like:

```
OK 2026-10-01 03:00
Google rating: 5  reviews on Google: 32
Reviews returned by Google: 5  already known: 5  new: 0
Stored reviews: 33
```

If it prints `ERROR: ...`, the message says what is wrong (no config file,
wrong key, Google refused). Nothing on the site changes when it fails; the
pages keep the previous numbers and quotes.

After a successful run, purge the cache (hPanel → **Performance** → **CDN** →
Purge, or **Advanced** → **Cache Manager**) so visitors get the new file
right away. Without a purge it can take up to a day to show.

## When a new review arrives

The job stores every new review it sees, but does not show it. The quotes on
each page are chosen in `assets/data/reviews.json` under `"featured"`. To
feature a new one, add its id there (the monthly report and the file list the
ids). Ask Claude Code to do it, or edit the file in File Manager. The count
and star rating, on the other hand, update on their own.

## Limits, in plain words

- **Google gives at most 5 reviews per request**, chosen by Google as "most
  relevant". They are not always the newest ones. The rating and the total
  count are always current. To pull every review (for example after a busy
  wedding season), run `py tools/scrape-google-reviews.py` on the PC; it
  reads the whole public listing and merges into the same file, which you
  then upload.
- **The month-old copy.** Between runs the site shows last month's number.
  If you get a review you want counted today, run the job by hand (Part 4).
- **Rating below 5.0.** While every Google review is 5 stars the site says
  "N five-star Google reviews". If a lower rating ever arrives it switches
  automatically to "N Google reviews, 4.9 average", which stays truthful.

## Cost

Google prices the request we make in the "Place Details Enterprise +
Atmosphere" tier because it includes reviews. That tier has a free allowance
of 1,000 requests per month; we make one. Above the allowance it would be
$25 per 1,000 requests. So the expected bill is $0. Google still needs a
billing account with a card on file. Keep the key restricted (Part 1, step 6)
so nobody else can run up usage on it.
