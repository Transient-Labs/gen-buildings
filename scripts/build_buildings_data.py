# /// script
# requires-python = ">=3.14"
# dependencies = ["playwright>=1.48"]
# ///
"""Render every building locally and capture its $art traits.

Reads buildings_urls.json (name + animation_url per token), takes the query
params off each animation_url, loads the local index.html with them under the
snapshot capture User-Agent (so $art runs in captureMode and calls finish()
immediately), then reads the traits that finish() passed to $art.setTraits().
Writes { name, tokenId, traits } for each token into buildings_data.json.

The page fetches sibling JSON + window images, so it is served over a local
HTTP server rooted at the repo (file:// would break those fetches).

Setup (once):  uv run --with playwright playwright install chromium
Run with:      uv run scripts/build_buildings_data.py
"""

import asyncio
import functools
import http.server
import json
import socketserver
import threading
import urllib.parse
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
URLS_PATH = ROOT / "buildings_urls.json"
OUT_PATH = ROOT / "buildings_data.json"

# $art flips into captureMode when this sentinel appears in the User-Agent,
# which renders the hero frame synchronously and runs finish() right away.
CAPTURE_UA = "Mozilla/5.0 (build_buildings_data.py) tl-gen-art"
CONCURRENCY = 12         # parallel pages
NAV_TIMEOUT = 20_000     # ms to wait for #art-snapshot-ready
RETRIES = 1              # extra attempts per token on failure

# We only want traits, which finish() computes before any pixels are drawn.
# This init script (runs before the page's own scripts) strips out the expensive
# work the trait values don't depend on, while leaving image *loading* native so
# its onload still fires and loadImage() resolves (and finish() runs):
#   - no-op the 2D draw calls + cap the canvas backing store, skipping the
#     software rasterization of full-native-res canvases
#   - skip image decode + bitmap creation (loadImage() calls img.decode() then
#     createImageBitmap()); the dummy result is only ever drawn by the no-op'd
#     drawImage, so the captured traits are unaffected.
# Real (small) .webp files still load over loopback, so onload is reliable.
STUB_RENDER = """
const proto = CanvasRenderingContext2D.prototype;
const noop = function () {};
proto.drawImage = noop;
proto.fillRect = noop;
const dim = (prop) => {
  const d = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, prop);
  Object.defineProperty(HTMLCanvasElement.prototype, prop, {
    get() { return d.get.call(this); },
    set(v) { d.set.call(this, Math.min(v, 16)); },  // cap backing store to 16px
  });
};
dim("width");
dim("height");

HTMLImageElement.prototype.decode = () => Promise.resolve();
window.createImageBitmap = () => Promise.resolve({});
"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence per-request access logging
        pass


def start_server() -> socketserver.TCPServer:
    """Serve the repo root on an ephemeral localhost port."""
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def query_of(animation_url: str) -> str:
    """The query string (after '?') of an animation_url, or ''."""
    return urllib.parse.urlsplit(animation_url).query


def traits_to_dict(attributes) -> dict:
    """OpenSea [{trait_type, value}] -> { trait_type: value }."""
    return {a["trait_type"]: a["value"] for a in (attributes or [])}


async def capture(page, base: str, building: dict) -> dict:
    query = query_of(building.get("animation_url") or "")
    url = f"{base}/index.html?{query}"
    for _ in range(RETRIES + 1):
        try:
            await page.goto(url, wait_until="commit")
            # Wait for finish() -> setTraits() to populate the traits. (Don't wait
            # on #art-snapshot-ready: it's display:none, so a visibility-based
            # wait never resolves; the traits are what we want anyway.)
            attributes = await page.wait_for_function(
                "() => window.$art && window.$art.getTraits()", timeout=NAV_TIMEOUT
            )
            attributes = await attributes.json_value()
            return {
                "tokenId": building.get("tokenId"),
                "name": building.get("name"),
                "traits": traits_to_dict(attributes),
            }
        except Exception as err:  # noqa: BLE001 - record and retry/skip
            print(f"  ! token {building.get('tokenId')} attempt failed: "
                  f"{type(err).__name__}: {str(err).splitlines()[0]}")
    return {
        "tokenId": building.get("tokenId"),
        "name": building.get("name"),
        "traits": None,
        "error": True,
    }


async def worker(name, context, base, queue, results, total):
    page = await context.new_page()
    try:
        while True:
            try:
                building = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            results.append(await capture(page, base, building))
            done = len(results)
            if done % 50 == 0 or done == total:
                print(f"  captured {done}/{total}")
    finally:
        await page.close()


async def main() -> None:
    data = json.loads(URLS_PATH.read_text())
    buildings = data["buildings"] if isinstance(data, dict) else data

    httpd = start_server()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    queue: asyncio.Queue = asyncio.Queue()
    for b in buildings:
        queue.put_nowait(b)
    results: list[dict] = []

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            context = await browser.new_context(user_agent=CAPTURE_UA)
            await context.add_init_script(STUB_RENDER)

            await asyncio.gather(*(
                worker(i, context, base, queue, results, len(buildings))
                for i in range(CONCURRENCY)
            ))
            await browser.close()
    finally:
        httpd.shutdown()

    results.sort(key=lambda r: (r["tokenId"] is None, r["tokenId"]))
    failed = sum(1 for r in results if r.get("error"))
    OUT_PATH.write_text(json.dumps({"buildings": results}, indent=2, ensure_ascii=False))
    print(f"Wrote {len(results)} buildings to {OUT_PATH.name} ({failed} failed)")


if __name__ == "__main__":
    asyncio.run(main())
