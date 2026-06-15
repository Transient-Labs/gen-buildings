# /// script
# requires-python = ">=3.14"
# dependencies = ["pillow"]
# ///
"""Generate per-window NFT metadata (1..1000) from windows_keyed.json.

For each window N: pull traits from windows_keyed.json["window-N"], read the
matching image final_windows/window-N.jpg for dimensions / byte size / sha256,
and write a metadata file named exactly "N" (no extension) into windows_metadata/.

Run with:  uv run scripts/make_window_metadata.py
"""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
KEYED_PATH = ROOT / "windows_keyed.json"
OUTPUT_DIR = ROOT / "windows_metadata"
IMAGE_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows/final_windows")

CID = "Qmb7ene5pzR28XE3PcbQcGwAsUP9rD8pRg6b5Du7K85KSP"
COUNT = 1000
MIME_TYPE = "image/jpg"  # per the metadata template


def caps(s: str) -> str:
    """Attribute values are ALL CAPS (e.g. 'double-hung' -> 'DOUBLE-HUNG')."""
    return s.upper()


def cap(s: str) -> str:
    """Capitalize the first character only (sentence case)."""
    return s[:1].upper() + s[1:] if s else s


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    keyed = json.loads(KEYED_PATH.read_text())

    # Validate everything up front; abort before writing if anything is missing.
    errors = []
    for n in range(1, COUNT + 1):
        if f"window-{n}" not in keyed:
            errors.append(f"windows_keyed.json missing window-{n}")
        if not (IMAGE_DIR / f"window-{n}.jpg").is_file():
            errors.append(f"image missing: window-{n}.jpg")
    if errors:
        for m in errors[:20]:
            print("ERROR:", m)
        raise SystemExit(f"Aborting — {len(errors)} problem(s); nothing written.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for n in range(1, COUNT + 1):
        w = keyed[f"window-{n}"]
        img = IMAGE_DIR / f"window-{n}.jpg"

        with Image.open(img) as im:
            dims = f"{im.width}x{im.height}"

        attributes = [
            {"trait_type": "CIRCADIAN", "value": caps(w["circadian"])},
            {"trait_type": "COLOR", "value": caps(w["color"])},
            {"trait_type": "FRAME", "value": caps(w["frame"])},
            {"trait_type": "OCCUPANT", "value": caps(w["occupant"])},
        ]
        for t in w["treatment"]:
            attributes.append({"trait_type": "TREATMENT", "value": caps(t)})
        for o in w["objects"]:
            attributes.append({"trait_type": "OBJECT", "value": caps(o)})
        attributes.append({"trait_type": "SPECIAL", "value": "YES" if w["special"] == "yes" else "NO"})

        meta = {
            "name": f"WINDOW {n}",
            "description": cap(w["notable"]),
            "attributes": attributes,
            "image": f"ipfs://{CID}/window-{n}.jpg",
            "image_sha256": sha256_of(img),
            "media": {
                "dimensions": dims,
                "size": str(img.stat().st_size),
                "mimeType": MIME_TYPE,
            },
        }

        (OUTPUT_DIR / str(n)).write_text(json.dumps(meta, indent=4, ensure_ascii=False))
        if n % 100 == 0 or n == COUNT:
            print(f"[{n}/{COUNT}] wrote {n}")

    print(f"\nDone. {COUNT} metadata files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
