# /// script
# requires-python = ">=3.14"
# ///
"""Fetch building NFTs from the Transient catalog and collect name + animation_url.

Pages through the catalog listing for the BUILDINGS // NYC contract and writes
the "name" and "animation_url" of each token into buildings_urls.json.

Run with:  uv run scripts/fetch_buildings_urls.py
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
JSON_PATH = ROOT / "buildings_urls.json"

CONTRACT = "0x9b3a20417a2fbe9d4980e0295c5f7e0a7b817137"
CHAIN = "1"
LIMIT = 200           # page size (catalog default is 24)
TIMEOUT = 30          # seconds per request
RETRIES = 3           # attempts per page before giving up
# The API 403s the default Python-urllib User-Agent, so send a browser-like one.
USER_AGENT = "Mozilla/5.0 (fetch_buildings_urls.py)"

START_URL = "https://api.transient.xyz/v1/catalog/nfts?" + urllib.parse.urlencode(
    {"address": CONTRACT, "chain": CHAIN, "expand": "metadata_json", "limit": LIMIT}
)


def get_page(url: str) -> dict:
    last_err = None
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for _ in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.load(resp)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as err:
            last_err = err
    raise SystemExit(f"Failed to fetch page after {RETRIES} attempts: {url}\n{last_err}")


def main() -> None:
    buildings = []
    url = START_URL
    expected = None

    while url:
        page = get_page(url)
        if expected is None:
            expected = page.get("count")
        for nft in page.get("results", []):
            meta = nft.get("metadata_json") or {}
            buildings.append({
                "tokenId": nft.get("token_id"),
                "name": nft.get("name"),
                "animation_url": meta.get("animation_url"),
            })
        print(f"  fetched {len(buildings)}/{expected or '?'}")
        url = page.get("next")

    buildings.sort(key=lambda b: (b["tokenId"] is None, b["tokenId"]))
    missing = sum(1 for b in buildings if b["animation_url"] is None)

    JSON_PATH.write_text(json.dumps({"buildings": buildings}, indent=2, ensure_ascii=False))
    print(f"Wrote {len(buildings)} buildings to {JSON_PATH.name} ({missing} missing animation_url)")
    if expected is not None and len(buildings) != expected:
        print(f"  ! expected {expected} buildings but got {len(buildings)}")


if __name__ == "__main__":
    main()
