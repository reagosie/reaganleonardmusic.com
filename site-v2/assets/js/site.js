/* reaganleonardmusic.com — version 2.0 behaviour (no dependencies)
   1. Header: solid once the page scrolls; phone menu
   2. "Check availability" links point at the form on the same page when there is one
   3. YouTube: poster first, player on click or when scrolled into view
   4. Song list search and genre chips
   5. Gallery lightbox
   6. Lazy third-party embeds (JotForm) and JotForm iframe height
   7. Google reviews: count and quotes from /assets/data/reviews.json; home page carousel
   8. Reveal-on-scroll animation */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* 1. header */
  var header = $(".site-header");
  var toggle = $(".nav-toggle");
  function onScroll() { header.classList.toggle("is-solid", window.scrollY > 40); }
  if (header) { onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); }
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = header.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.classList.toggle("nav-open", open);
    });
    $(".site-nav").addEventListener("click", function (e) {
      if (e.target.closest("a")) { header.classList.remove("is-open"); toggle.setAttribute("aria-expanded", "false"); document.body.classList.remove("nav-open"); }
    });
  }

  /* 2. CTA links */
  if (document.getElementById("request-quote")) {
    $$("a[data-cta]").forEach(function (a) { a.setAttribute("href", "#request-quote"); });
  }

  /* 3. videos */
  var videos = $$(".video[data-video-src]");
  function loadPlayer(video, autoplay) {
    if (video.querySelector("iframe")) return;
    var src = video.getAttribute("data-video-src");
    if (autoplay) src = src.replace("autoplay=0", "autoplay=1");
    var frame = document.createElement("iframe");
    frame.src = src;
    frame.allow = "accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture";
    frame.setAttribute("allowfullscreen", "");
    frame.title = video.getAttribute("data-title") || "YouTube video";
    video.appendChild(frame);
  }
  videos.forEach(function (v) { v.addEventListener("click", function () { loadPlayer(v, true); }); });
  if ("IntersectionObserver" in window) {
    var vw = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { loadPlayer(en.target, false); vw.unobserve(en.target); } });
    }, { rootMargin: "200px 0px" });
    videos.forEach(function (v) { vw.observe(v); });
  }

  /* ------------------------------------------------------------------ */
  /* 4. Song list (/song-list): search box + genre filter buttons.     */
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

  /* 5. lightbox */
  var items = $$(".gallery__item[data-lightbox-src]");
  if (items.length) {
    var box = document.createElement("div");
    box.className = "lightbox"; box.hidden = true;
    box.innerHTML = '<picture class="lightbox__picture"><source type="image/avif" srcset="" sizes="92vw"><source type="image/webp" srcset="" sizes="92vw"><img class="lightbox__image" alt="" sizes="92vw"></picture>' +
      '<button class="lightbox__btn lightbox__btn--prev" type="button" aria-label="Previous">‹</button>' +
      '<button class="lightbox__btn lightbox__btn--next" type="button" aria-label="Next">›</button>' +
      '<button class="lightbox__btn lightbox__btn--close" type="button" aria-label="Close">×</button>';
    document.body.appendChild(box);
    var img = $(".lightbox__image", box), sources = $$("source", box), current = 0;
    var show = function (i) {
      current = (i + items.length) % items.length;
      var el = items[current];
      sources[0].srcset = el.getAttribute("data-lightbox-avif") || "";
      sources[1].srcset = el.getAttribute("data-lightbox-webp") || "";
      img.srcset = el.getAttribute("data-lightbox-srcset") || "";
      img.src = el.getAttribute("data-lightbox-src");
      img.alt = (el.querySelector("img") || {}).alt || "";
      box.hidden = false; document.body.style.overflow = "hidden";
    };
    var hide = function () { box.hidden = true; document.body.style.overflow = ""; };
    items.forEach(function (el, i) { el.addEventListener("click", function () { show(i); }); });
    $(".lightbox__btn--prev", box).addEventListener("click", function () { show(current - 1); });
    $(".lightbox__btn--next", box).addEventListener("click", function () { show(current + 1); });
    $(".lightbox__btn--close", box).addEventListener("click", hide);
    box.addEventListener("click", function (e) { if (e.target === box) hide(); });
    document.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      if (e.key === "Escape") hide(); if (e.key === "ArrowLeft") show(current - 1); if (e.key === "ArrowRight") show(current + 1);
    });
    var tx = null;
    img.addEventListener("touchstart", function (e) { tx = e.touches[0].clientX; }, { passive: true });
    img.addEventListener("touchend", function (e) { if (tx === null) return; var dx = e.changedTouches[0].clientX - tx; if (dx > 40) show(current - 1); if (dx < -40) show(current + 1); tx = null; });
  }

  /* 6. lazy embeds + JotForm height */
  var embeds = $$("[data-lazy-script]");
  function loadEmbed(el) {
    if (el.getAttribute("data-lazy-loaded")) return;
    el.setAttribute("data-lazy-loaded", "true");
    var s = document.createElement("script"); s.src = el.getAttribute("data-lazy-script"); el.appendChild(s);
  }
  if ("IntersectionObserver" in window) {
    var ew = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { loadEmbed(en.target); ew.unobserve(en.target); } });
    }, { rootMargin: "600px 0px" });
    embeds.forEach(function (el) { ew.observe(el); });
  } else { embeds.forEach(loadEmbed); }
  var JOTFORM_TOP = 8, JOTFORM_BANNER = 56;   // JotForm's blank top margin and promo footer, trimmed off (measured in the compact layout, iframe <= 760px)
  window.addEventListener("message", function (e) {
    if (typeof e.data !== "string" || e.data.indexOf("setHeight") === -1) return;
    var parts = e.data.split(":"), height = parseInt(parts[1], 10), formId = parts[2];
    $$('iframe[src*="jotform"]').forEach(function (frame) {
      if (formId && frame.src.indexOf(formId) === -1) return;
      frame.style.height = height + "px";
      var boxEl = frame.closest(".form-frame");
      if (boxEl) { frame.style.marginTop = -JOTFORM_TOP + "px"; boxEl.style.height = Math.max(0, height - JOTFORM_TOP - JOTFORM_BANNER + 8) + "px"; }
    });
  });

  /* 7. reviews */
  if ($("[data-reviews], [data-review-claim], [data-review-count]") && window.fetch) {
    fetch("/assets/data/reviews.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        var all = data.reviews || [], google = data.google || {};
        var fromGoogle = all.filter(function (r) { return r.source === "Google"; });
        var count = google.count || fromGoogle.length;
        var rating = typeof google.rating === "number" ? google.rating : null;
        var allFive = fromGoogle.every(function (r) { return r.stars === 5; }) && (rating === null || rating >= 4.95);
        var claim = allFive ? count + " five-star Google reviews" : count + " Google reviews, " + rating.toFixed(1) + " average";
        $$("[data-review-claim]").forEach(function (el) { el.textContent = claim; });
        $$("[data-review-count]").forEach(function (el) { el.textContent = String(count); });
        var byId = {}; all.forEach(function (r) { byId[r.id] = r; });
        var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
        var card = function (r) {
          var stars = r.stars || 5, who = esc(r.name) + (r.role ? ", " + esc(r.role) : "");
          return '<article class="review"><div class="review__stars" aria-label="' + stars + ' out of 5 stars">' + new Array(stars + 1).join("★") + "</div>" +
            '<p class="review__text">' + esc(r.excerpt || r.text) + '</p><p class="review__who">' + who + "</p>" +
            '<p class="review__source">Review on <a href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.source) + "</a></p></article>";
        };
        $$("[data-reviews]").forEach(function (boxEl) {
          var key = boxEl.getAttribute("data-reviews"), list;
          if (key === "all") {          // every Google review with text; the page's featured ones first
            var first = (data.featured || {})[boxEl.getAttribute("data-reviews-first")] || [];
            list = first.map(function (id) { return byId[id]; }).filter(Boolean)
              .concat(fromGoogle.filter(function (r) { return r.text && first.indexOf(r.id) === -1; }));
          } else list = ((data.featured || {})[key] || []).map(function (id) { return byId[id]; }).filter(Boolean);
          if (list.length) { boxEl.innerHTML = list.map(card).join(""); boxEl.dispatchEvent(new Event("scroll")); }
        });
      })
      .catch(function () { /* the static copy in the HTML stays */ });
  }

  /* 7b. review carousel (home page): arrows move one card at a time; swiping and trackpads work anyway */
  $$(".carousel").forEach(function (carousel) {
    var track = $(".reviews--carousel", carousel), prev = $(".carousel__arrow--prev", carousel), next = $(".carousel__arrow--next", carousel);
    if (!track || !prev || !next) return;
    function update() {
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 2;
    }
    function move(dir) {
      var cardEl = track.querySelector(".review");
      var gap = parseFloat(getComputedStyle(track).columnGap) || 24;
      track.scrollBy({ left: dir * (cardEl ? cardEl.getBoundingClientRect().width + gap : track.clientWidth), behavior: "smooth" });
    }
    prev.addEventListener("click", function () { move(-1); });
    next.addEventListener("click", function () { move(1); });
    track.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  });

  /* 8. reveal */
  var targets = $$(".card, .review, .step, .timeline__item, .package, .region, .section-head, .split__text, .split__media, .videos figure")
    .filter(function (el) { return !el.closest(".reviews--carousel"); });   // carousel cards scroll sideways; no fade-in
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    targets.forEach(function (el) { el.classList.add("reveal"); });
    var rw = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in-view"); rw.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    targets.forEach(function (el) { rw.observe(el); });
  }

  var y = $("[data-year]"); if (y) y.textContent = String(new Date().getFullYear());
})();
