"""
measure-weight.py — real page-weight comparison, old site vs rebuild.

Drives headless Chrome over the DevTools Protocol, loads each page, and sums
the bytes actually transferred (Network.loadingFinished encodedDataLength),
split into first-party vs third-party (YouTube, JotForm, Google, Elfsight…).

    py tools/measure-weight.py                # live site vs http://localhost:8080
    py tools/measure-weight.py --mobile       # emulate a phone (390px, touch UA)

Needs: Chrome, and `pip install websocket-client`. Start tools/serve.py first.
"""
import json, os, subprocess, sys, time, urllib.request, urllib.parse
import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9222
PAGES = ["/", "/contact", "/photos-videos", "/weddings", "/corporate", "/pricing", "/faq",
         "/more-videos", "/song-list", "/preferred-vendors", "/welcome", "/thank-you", "/wedding-show-form"]
LIVE = "https://reaganleonardmusic.com"
LOCAL = "http://localhost:8080"
MOBILE = "--mobile" in sys.argv
FIRST_PARTY = ("reaganleonardmusic.com", "localhost", "assets.zyrosite.com", "cdn.zyrosite.com", "srv1015-files.hstgr.io")


def start_chrome():
    profile = os.path.join(os.environ.get("TEMP", "."), "rlm-weight-profile")
    args = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", f"--remote-debugging-port={PORT}",
            f"--user-data-dir={profile}", "--disable-extensions", "--window-size=1440,900", "about:blank"]
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/json/version", timeout=1)
            return p
        except Exception:
            time.sleep(0.2)
    raise SystemExit("Chrome did not start")


class Tab:
    def __init__(self):
        info = json.load(urllib.request.urlopen(f"http://localhost:{PORT}/json/new?about:blank", timeout=5)) \
            if False else json.loads(urllib.request.urlopen(
                urllib.request.Request(f"http://localhost:{PORT}/json/new?about:blank", method="PUT"), timeout=5).read())
        self.ws = websocket.create_connection(info["webSocketDebuggerUrl"], suppress_origin=True)
        self.id = 0
        self.send("Network.enable")
        self.send("Page.enable")
        self.send("Network.setCacheDisabled", cacheDisabled=True)
        if MOBILE:
            self.send("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=3, mobile=True)
            self.send("Emulation.setUserAgentOverride", userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")

    def send(self, method, **params):
        self.id += 1
        self.ws.send(json.dumps({"id": self.id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.id:
                return msg.get("result")

    def load(self, url, settle=6.0):
        """Navigate, wait for load + settle time, return {url: bytes}."""
        self.ws.settimeout(0.5)
        sizes, urls = {}, {}
        self.id += 1
        self.ws.send(json.dumps({"id": self.id, "method": "Page.navigate", "params": {"url": url}}))
        deadline = time.time() + 40
        loaded_at = None
        while time.time() < deadline:
            try:
                msg = json.loads(self.ws.recv())
            except websocket.WebSocketTimeoutException:
                if loaded_at and time.time() - loaded_at > settle:
                    break
                continue
            m = msg.get("method")
            if m == "Network.requestWillBeSent":
                urls[msg["params"]["requestId"]] = msg["params"]["request"]["url"]
            elif m == "Network.loadingFinished":
                rid = msg["params"]["requestId"]
                sizes[urls.get(rid, rid)] = sizes.get(urls.get(rid, rid), 0) + msg["params"]["encodedDataLength"]
            elif m == "Page.loadEventFired":
                loaded_at = time.time()
            if loaded_at and time.time() - loaded_at > settle:
                break
        return sizes


def split(sizes):
    fp = tp = 0
    for u, b in sizes.items():
        host = urllib.parse.urlparse(u).hostname or ""
        if any(host.endswith(d) for d in FIRST_PARTY):
            fp += b
        else:
            tp += b
    return fp, tp


def main():
    chrome = start_chrome()
    try:
        tab = Tab()
        print(f"{'page':22} {'OLD first-party':>16} {'NEW first-party':>16} {'change':>8}   {'OLD 3rd-party':>14} {'NEW 3rd-party':>14}")
        tot = [0, 0, 0, 0]
        for path in PAGES:
            old = split(tab.load(LIVE + path))
            new = split(tab.load(LOCAL + path))
            change = (new[0] - old[0]) / old[0] * 100 if old[0] else 0
            print(f"{path:22} {old[0]/1024:13.0f} KB {new[0]/1024:13.0f} KB {change:+7.0f}%   {old[1]/1024:11.0f} KB {new[1]/1024:11.0f} KB")
            for i, v in enumerate((old[0], new[0], old[1], new[1])):
                tot[i] += v
        print("-" * 100)
        print(f"{'TOTAL':22} {tot[0]/1024:13.0f} KB {tot[1]/1024:13.0f} KB {(tot[1]-tot[0])/tot[0]*100:+7.0f}%   {tot[2]/1024:11.0f} KB {tot[3]/1024:11.0f} KB")
        print("\nfirst-party = HTML, CSS, JS, fonts and images served by the site itself (old: via Zyro CDN)")
        print("3rd-party  = YouTube, JotForm, Google tags, Elfsight, Zola — identical services on both")
    finally:
        chrome.terminate()


if __name__ == "__main__":
    main()
