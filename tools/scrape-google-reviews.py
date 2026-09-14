"""
scrape-google-reviews.py — fetch EVERY Google review from the public Maps listing.

Google's API only hands out 5 reviews at a time, so the monthly job on the
server (site/refresh-reviews.php) can miss one. This script opens the public
Google Maps listing in a hidden Chrome window on this PC, scrolls through the
whole review list, and merges anything new into site/assets/data/reviews.json
(it also updates the rating and the total count). Then upload that JSON file
(or run a full deploy) and purge the cache.

Needs Google Chrome and the Python package "websocket-client".
Run from the repo root:   py tools/scrape-google-reviews.py
"""
import base64, io, json, os, re, subprocess, sys, time, urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "assets", "data", "reviews.json")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9351


def normalise(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def key_of(name, text):
    return normalise(name) + "|" + normalise(text)[:40]


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "review"


def fetch(place_id):
    import websocket  # pip install websocket-client
    profile = os.path.join(os.environ["TEMP"], "rlm-gmaps-scrape")
    p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--lang=en-US",
                          f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}", "--window-size=1440,1000", "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://localhost:{PORT}/json/version", timeout=1); break
            except Exception:
                time.sleep(0.2)
        info = json.loads(urllib.request.urlopen(urllib.request.Request(f"http://localhost:{PORT}/json/new?about:blank", method="PUT")).read())
        ws = websocket.create_connection(info["webSocketDebuggerUrl"], suppress_origin=True); ws.settimeout(120); mid = [0]

        def send(m, **pr):
            mid[0] += 1; ws.send(json.dumps({"id": mid[0], "method": m, "params": pr}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == mid[0]:
                    return r.get("result")

        def ev(e):
            return send("Runtime.evaluate", expression=e, returnByValue=True, awaitPromise=True)["result"].get("value")

        send("Page.enable")
        send("Emulation.setUserAgentOverride", userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36", acceptLanguage="en-US,en")
        send("Page.navigate", url=f"https://www.google.com/maps/place/?q=place_id:{place_id}&hl=en"); time.sleep(8)
        if ev("!!document.querySelector('form[action*=consent], button[aria-label*=Accept]')"):
            ev("(document.querySelector('button[aria-label*=Accept]')||document.querySelector('form[action*=consent] button')).click()"); time.sleep(6)
        title = ev("document.title") or ""
        if "Google Maps" not in title:
            raise SystemExit(f"unexpected page: {title!r}")
        header = ev("(()=>{const m=document.querySelector('div[role=main]'); const s=m&&m.querySelector('[role=img][aria-label*=star]'); const c=[...(m||document).querySelectorAll('span,button')].map(e=>e.textContent.trim()).find(t=>/^\\d+ reviews?$/.test(t)); return {rating: s?s.getAttribute('aria-label'):'', count: c||''}})()") or {}
        tab = ev("(()=>{const b=[...document.querySelectorAll('button[role=tab]')].find(b=>/reviews/i.test(b.textContent)); if(b){b.click();return true} return false})()")
        if not tab:
            raise SystemExit("could not find the Reviews tab on the Maps page (Google may have changed its layout)")
        time.sleep(5)
        scroll = """(()=>{let el=document.querySelector('div[data-review-id]'); while(el && el!==document.body){const s=getComputedStyle(el); if(/(auto|scroll)/.test(s.overflowY) && el.scrollHeight>el.clientHeight){el.scrollTop=el.scrollHeight; return true} el=el.parentElement} return false})()"""
        last, same = -1, 0
        for _ in range(80):
            n = ev("document.querySelectorAll('div[data-review-id]').length"); ev(scroll); time.sleep(2.5)
            same = same + 1 if n == last else 0
            last = n
            if same >= 4:
                break
        ev("document.querySelectorAll('button[aria-label*=\"See more\"], button[aria-expanded=false][jsaction*=expand]').forEach(b=>b.click())"); time.sleep(2)
        rows = ev(r"""(()=>{const out=[],seen=new Set();
          for(const c of document.querySelectorAll('div[data-review-id]')){const id=c.getAttribute('data-review-id'); if(seen.has(id)) continue; seen.add(id);
            const t=s=>s?s.textContent.replace(/\s+/g,' ').trim():'';
            const stars=c.querySelector('[role=img][aria-label*=star]'); const name=c.querySelector('[class*=d4r55], button[data-href*="/maps/contrib"] div');
            const when=[...c.querySelectorAll('span')].map(e=>t(e)).find(x=>/ago$/.test(x)); const text=c.querySelector('[class*=wiI7pd], [data-expandable-section]');
            out.push({name:t(name), stars:stars?parseInt(stars.getAttribute('aria-label')):0, when:when||'', text:t(text)});}
          return out;})()""") or []
        return header, rows
    finally:
        p.terminate()


def main():
    data = json.load(io.open(DATA, encoding="utf-8"))
    header, rows = fetch(data["google"]["placeId"])
    print(f"Maps page: {header.get('count') or '?'}, rating {header.get('rating') or '?'}; review cards read: {len(rows)}")
    index = {key_of(r["name"], r["text"]): r for r in data["reviews"]}
    ids = {r["id"] for r in data["reviews"]}
    added = []
    for row in rows:
        if not row["name"] or not row["text"]:
            continue
        k = key_of(row["name"], row["text"])
        if k in index:
            if row["when"]:
                index[k]["when"] = row["when"]
            if row["stars"]:
                index[k]["stars"] = row["stars"]
            continue
        rid = base = slug(row["name"]); n = 2
        while rid in ids:
            rid = f"{base}-{n}"; n += 1
        ids.add(rid)
        new = {"id": rid, "source": "Google", "name": row["name"], "stars": row["stars"] or 5, "when": row["when"], "date": "",
               "text": row["text"], "role": "", "url": data["google"]["url"], "added": date.today().isoformat()}
        data["reviews"].append(new); index[k] = new; added.append(f'{row["name"]} ({new["stars"]} stars)')
    m = re.match(r"(\d+)", header.get("count") or "")
    if m:
        data["google"]["count"] = int(m.group(1))
    m = re.match(r"([\d.]+)", header.get("rating") or "")
    if m:
        data["google"]["rating"] = float(m.group(1))
    data["google"]["fetched"] = date.today().isoformat(); data["google"]["fetchedBy"] = "scrape-google-reviews.py"
    data["updated"] = date.today().isoformat()
    io.open(DATA, "w", encoding="utf-8", newline="\n").write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"Google count now {data['google']['count']}, rating {data['google']['rating']}. New reviews: {len(added)}")
    for a in added:
        print("  +", a)
    if added:
        print('New reviews are stored but not shown until you add their id to "featured" in site/assets/data/reviews.json,')
        print("then run  py tools/render-reviews.py  and upload the changed files.")


if __name__ == "__main__":
    sys.exit(main())
