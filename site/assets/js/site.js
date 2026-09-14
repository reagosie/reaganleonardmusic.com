/*
 * reaganleonardmusic.com — site behaviour
 *
 * Small, dependency-free replacements for the interactive bits the old
 * builder handled with its Vue runtime:
 *   1. Mobile navigation (hamburger)
 *   2. YouTube videos: thumbnail first, iframe on click
 *   3. Photo gallery lightbox (/photos-videos)
 *   4. FAQ accordion (/faq)
 *   5. JotForm iframe auto-height
 *   6. Google reviews (count and quotes from /assets/data/reviews.json)
 *   7. Review carousel on the home page
 */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* 1. Mobile navigation                                                */
  /* ------------------------------------------------------------------ */
  var burger = document.querySelector(".block-header__hamburger-menu");
  var dropdown = document.querySelector(".block-header-layout-mobile__dropdown");
  if (burger && dropdown) {
    burger.addEventListener("click", function () {
      var open = dropdown.classList.toggle("block-header-layout-mobile__dropdown--open");
      burger.classList.toggle("burger--open", open);
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // close the menu after choosing a link
    dropdown.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        dropdown.classList.remove("block-header-layout-mobile__dropdown--open");
        burger.classList.remove("burger--open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* 2. YouTube videos                                                   */
  /*    Pages start with a lightweight thumbnail; the real player loads   */
  /*    once the video scrolls into view (as the old site did), or        */
  /*    immediately with autoplay if the thumbnail is clicked first.      */
  /* ------------------------------------------------------------------ */
  var videos = document.querySelectorAll(".video[data-video-src]");

  function loadPlayer(video, autoplay) {
    if (video.querySelector("iframe")) return;
    var src = video.getAttribute("data-video-src");
    if (autoplay) src = src.replace("autoplay=0", "autoplay=1");
    var frame = document.createElement("iframe");
    frame.className = "video__frame";
    frame.src = src;
    frame.width = "100%";
    frame.height = "100%";
    frame.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture";
    frame.setAttribute("allowfullscreen", "");
    frame.title = "YouTube video";
    video.appendChild(frame);
  }

  videos.forEach(function (video) {
    video.addEventListener("click", function () { loadPlayer(video, true); });
  });

  if ("IntersectionObserver" in window) {
    var watcher = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          loadPlayer(entry.target, false);
          watcher.unobserve(entry.target);
        }
      });
    }, { threshold: 0 });
    videos.forEach(function (video) { watcher.observe(video); });
  } else {
    videos.forEach(function (video) { loadPlayer(video, false); });
  }

  /* ------------------------------------------------------------------ */
  /* 2b. "Check availability" buttons (header, phone bar, page CTAs)     */
  /*     They link to /contact#request-quote so they work everywhere;   */
  /*     when this page has the booking form, point at it directly.     */
  /* ------------------------------------------------------------------ */
  if (document.getElementById("request-quote")) {
    document.querySelectorAll("a[data-cta]").forEach(function (a) {
      a.setAttribute("href", "#request-quote");
    });
  }

  /* ------------------------------------------------------------------ */
  /* 2c. Song list (/song-list): search box + genre filter buttons.     */
  /*     Genres are multi-select; "Clear" buttons reset each control.   */
  /* ------------------------------------------------------------------ */
  var songSearch = document.querySelector(".songs__search");
  if (songSearch) {
    var songs = songSearch.closest(".songs");
    var groups = Array.prototype.slice.call(songs.querySelectorAll(".songs__group"));
    var countEl = songs.querySelector(".songs__count");
    var chips = Array.prototype.slice.call(songs.querySelectorAll(".chip[data-genre]"));
    var clearChips = songs.querySelector(".chip--clear");
    var clearSearch = songs.querySelector(".songs__clear");
    var total = songs.querySelectorAll(".songs__list li").length;
    var selected = {};
    function filterSongs() {
      var q = songSearch.value.trim().toLowerCase();
      var anyGenre = Object.keys(selected).length > 0;
      var shown = 0;
      groups.forEach(function (g) {
        var on = !anyGenre || selected[g.id];
        var visible = 0;
        Array.prototype.forEach.call(g.querySelectorAll("li"), function (li) {
          var hit = on && (!q || li.textContent.toLowerCase().indexOf(q) !== -1);
          li.hidden = !hit;
          if (hit) visible++;
        });
        g.hidden = visible === 0;
        shown += visible;
      });
      songs.classList.toggle("songs--empty", shown === 0);
      countEl.textContent = (q || anyGenre) ? shown + " of " + total + " songs" : total + " songs";
      if (clearChips) clearChips.hidden = !anyGenre;
      if (clearSearch) clearSearch.hidden = !q;
    }
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        var id = chip.getAttribute("data-genre");
        if (selected[id]) delete selected[id]; else selected[id] = true;
        chip.setAttribute("aria-pressed", selected[id] ? "true" : "false");
        filterSongs();
      });
    });
    if (clearChips) clearChips.addEventListener("click", function () {
      selected = {};
      chips.forEach(function (chip) { chip.setAttribute("aria-pressed", "false"); });
      filterSongs();
    });
    if (clearSearch) clearSearch.addEventListener("click", function () {
      songSearch.value = "";
      filterSongs();
      songSearch.focus();
    });
    songSearch.addEventListener("input", filterSongs);
    filterSongs();
  }

  /* ------------------------------------------------------------------ */
  /* 3. Gallery lightbox                                                 */
  /* ------------------------------------------------------------------ */
  var galleryImages = Array.prototype.slice.call(
    document.querySelectorAll(".grid-gallery-grid__image[data-lightbox-src]")
  );
  if (galleryImages.length) {
    var box = document.createElement("div");
    box.className = "lightbox";
    box.hidden = true;
    box.innerHTML =
      '<div class="lightbox__container">' +
      '  <div class="lightbox__nav"><button class="lightbox__button lightbox__button--nav lightbox__button--prev" type="button" aria-label="Previous"></button></div>' +
      '  <picture class="lightbox__picture">' +
      '    <source type="image/avif" srcset="" sizes="(min-width: 921px) 80vw, 100vw">' +
      '    <source type="image/webp" srcset="" sizes="(min-width: 921px) 80vw, 100vw">' +
      '    <img class="lightbox__image" alt="" sizes="(min-width: 921px) 80vw, 100vw">' +
      '  </picture>' +
      '  <div class="lightbox__nav"><button class="lightbox__button lightbox__button--nav lightbox__button--next" type="button" aria-label="Next"></button></div>' +
      "</div>" +
      '<button class="lightbox__button lightbox__button--close" type="button" aria-label="Close"></button>';
    document.body.appendChild(box);

    var img = box.querySelector(".lightbox__image");
    var sources = box.querySelectorAll(".lightbox__picture source");
    var current = 0;

    function show(i) {
      current = (i + galleryImages.length) % galleryImages.length;
      var el = galleryImages[current];
      // full photo, sized for the screen, in the best format the browser supports (AVIF > WebP > JPEG)
      sources[0].srcset = el.getAttribute("data-lightbox-avif") || "";
      sources[1].srcset = el.getAttribute("data-lightbox-webp") || "";
      img.srcset = el.getAttribute("data-lightbox-srcset") || "";
      img.src = el.getAttribute("data-lightbox-src");
      img.alt = el.querySelector("img") ? el.querySelector("img").alt : "";
      box.hidden = false;
      document.body.style.overflow = "hidden";
    }
    function hide() {
      box.hidden = true;
      document.body.style.overflow = "";
    }

    galleryImages.forEach(function (el, i) {
      el.addEventListener("click", function () { show(i); });
    });
    box.querySelector(".lightbox__button--prev").addEventListener("click", function () { show(current - 1); });
    box.querySelector(".lightbox__button--next").addEventListener("click", function () { show(current + 1); });
    box.querySelector(".lightbox__button--close").addEventListener("click", hide);
    box.addEventListener("click", function (e) { if (e.target === box) hide(); });
    document.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      if (e.key === "Escape") hide();
      if (e.key === "ArrowLeft") show(current - 1);
      if (e.key === "ArrowRight") show(current + 1);
    });

    // swipe on touch screens
    var touchX = null;
    img.addEventListener("touchstart", function (e) { touchX = e.touches[0].clientX; }, { passive: true });
    img.addEventListener("touchend", function (e) {
      if (touchX === null) return;
      var dx = e.changedTouches[0].clientX - touchX;
      if (dx > 40) show(current - 1);
      if (dx < -40) show(current + 1);
      touchX = null;
    });
  }

  /* ------------------------------------------------------------------ */
  /* 4. FAQ accordion                                                    */
  /* ------------------------------------------------------------------ */
  document.querySelectorAll(".faq-question").forEach(function (button) {
    button.addEventListener("click", function () {
      var open = button.classList.toggle("is-open");
      var panel = button.nextElementSibling;
      button.setAttribute("aria-expanded", open ? "true" : "false");
      panel.style.maxHeight = open ? panel.scrollHeight + "px" : null;
    });
  });

  /* ------------------------------------------------------------------ */
  /* 5. Third-party embeds (JotForm, Google reviews, Zola badge)         */
  /*    The old site only injected these once they were within 500px of  */
  /*    the viewport, which keeps the initial page load light. The       */
  /*    <script> to load is stored on the container as data-lazy-script. */
  /* ------------------------------------------------------------------ */
  var lazyEmbeds = document.querySelectorAll("[data-lazy-script]");

  function loadEmbed(box) {
    if (box.getAttribute("data-lazy-loaded")) return;
    box.setAttribute("data-lazy-loaded", "true");
    var script = document.createElement("script");
    script.src = box.getAttribute("data-lazy-script");
    box.appendChild(script);   // JotForm inserts its iframe right after its script tag
  }

  if ("IntersectionObserver" in window) {
    var embedWatcher = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          loadEmbed(entry.target);
          embedWatcher.unobserve(entry.target);
        }
      });
    }, { rootMargin: "500px 0px" });
    lazyEmbeds.forEach(function (box) { embedWatcher.observe(box); });
  } else {
    lazyEmbeds.forEach(loadEmbed);
  }

  /* ------------------------------------------------------------------ */
  /* 6. JotForm iframe auto-height                                       */
  /*    JotForm posts "setHeight:<px>:<formId>" from inside its iframe.   */
  /* ------------------------------------------------------------------ */
  var JOTFORM_TOP = 8;       // px of blank margin JotForm puts above the form
  var JOTFORM_BANNER = 56;   // px height of JotForm's promotional footer
  window.addEventListener("message", function (e) {
    if (typeof e.data !== "string" || e.data.indexOf("setHeight") === -1) return;
    var parts = e.data.split(":");           // ["setHeight", "1234", "230255417493153"]
    var height = parts[1];
    var formId = parts[2];
    var frames = document.querySelectorAll('iframe[src*="jotform"]');
    frames.forEach(function (frame) {
      if (!formId || frame.src.indexOf(formId) !== -1) {
        frame.style.height = height + "px";
        // In the footer the iframe sits in a clipping frame. Shift the iframe
        // up by JOTFORM_TOP (JotForm's blank margin above the form) and make
        // the frame shorter by that plus JOTFORM_BANNER (JotForm's "create
        // your own form" footer), so neither is visible. Both were measured
        // on the rendered form in its compact layout (iframe <= 760px wide,
        // enforced in site.css); adjust if JotForm changes its layout.
        var frameBox = frame.closest(".form-frame");
        if (frameBox) {
          frame.style.marginTop = -JOTFORM_TOP + "px";
          frameBox.style.height = Math.max(0, parseInt(height, 10) - JOTFORM_TOP - JOTFORM_BANNER) + "px";
        }
      }
    });
  });

  /* ------------------------------------------------------------------ */
  /* 6. Google reviews: the count and the quotes come from              */
  /*    /assets/data/reviews.json, which refresh-reviews.php updates    */
  /*    monthly. The HTML carries a static copy in case this fails.     */
  /* ------------------------------------------------------------------ */
  var wantsReviews = document.querySelector("[data-reviews], [data-review-claim], [data-review-count]");
  if (wantsReviews && window.fetch) {
    fetch("/assets/data/reviews.json", { cache: "no-cache" })
      .then(function (res) { return res.ok ? res.json() : Promise.reject(res.status); })
      .then(function (data) {
        var all = data.reviews || [];
        var google = data.google || {};
        var fromGoogle = all.filter(function (r) { return r.source === "Google"; });
        var count = google.count || fromGoogle.length;
        var rating = typeof google.rating === "number" ? google.rating : null;
        var allFive = fromGoogle.every(function (r) { return r.stars === 5; }) && (rating === null || rating >= 4.95);
        var claim = allFive ? count + " five-star Google reviews" : count + " Google reviews, " + rating.toFixed(1) + " average";
        Array.prototype.forEach.call(document.querySelectorAll("[data-review-claim]"), function (el) { el.textContent = claim; });
        Array.prototype.forEach.call(document.querySelectorAll("[data-review-count]"), function (el) { el.textContent = String(count); });

        var byId = {};
        all.forEach(function (r) { byId[r.id] = r; });
        function esc(s) {
          return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
        }
        function card(r) {
          var stars = r.stars || 5;
          var who = esc(r.name) + (r.role ? ", " + esc(r.role) : "");
          return '<article class="review"><div class="review__stars" aria-label="' + stars + ' out of 5 stars">' + new Array(stars + 1).join("★") + "</div>" +
            '<p class="review__text">“' + esc(r.excerpt || r.text) + '”</p><p class="review__who">' + who + "</p>" +
            '<p class="review__source">Review on <a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.source) + "</a></p></article>";
        }
        Array.prototype.forEach.call(document.querySelectorAll("[data-reviews]"), function (box) {
          var key = box.getAttribute("data-reviews");
          var ids = (data.featured || {})[key] || [];
          if (key === "all") {
            // every Google review with text; the page's featured ones come first
            var first = (data.featured || {})[box.getAttribute("data-reviews-first")] || [];
            ids = first.concat(fromGoogle.filter(function (r) { return r.text && first.indexOf(r.id) === -1; }).map(function (r) { return r.id; }));
          }
          var cards = ids.map(function (id) { return byId[id]; }).filter(Boolean).map(card);
          if (cards.length) { box.innerHTML = cards.join(""); box.dispatchEvent(new Event("scroll")); }
        });
      })
      .catch(function () { /* keep the static copy already in the HTML */ });
  }

  /* ------------------------------------------------------------------ */
  /* 7. Review carousel (home page): the arrows scroll the track one    */
  /*    card at a time. Swiping and trackpads work anyway.              */
  /* ------------------------------------------------------------------ */
  Array.prototype.forEach.call(document.querySelectorAll(".carousel"), function (carousel) {
    var track = carousel.querySelector(".reviews--carousel");
    var prev = carousel.querySelector(".carousel__arrow--prev");
    var next = carousel.querySelector(".carousel__arrow--next");
    if (!track || !prev || !next) return;
    function update() {
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    }
    function move(dir) {          // one card at a time
      var card = track.querySelector(".review");
      var gap = parseFloat(getComputedStyle(track).columnGap) || 24;
      var step = card ? card.getBoundingClientRect().width + gap : track.clientWidth;
      track.scrollBy({ left: dir * step, behavior: "smooth" });
    }
    prev.addEventListener("click", function () { move(-1); });
    next.addEventListener("click", function () { move(1); });
    track.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  });
})();
