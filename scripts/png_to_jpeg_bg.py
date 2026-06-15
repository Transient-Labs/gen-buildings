# /// script
# requires-python = ">=3.14"
# dependencies = ["pillow"]
# ///
"""Flatten one transparent PNG onto a solid background and export as JPEG.

Keeps the exact pixel resolution and embedded color profile (ICC) of the
source file — only the alpha channel is removed by compositing over BG_COLOR.

Run with:  uv run png_to_jpeg_bg.py
"""

from pathlib import Path

from PIL import Image

SRC_FILE = Path("/Users/benstrauss/Downloads/window-0752.png")
DST_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows")

BG_COLOR = (0, 0, 0)  # solid background painted into transparent areas
QUALITY = 95          # JPEG quality
SUBSAMPLING = 0       # 4:4:4 — no chroma subsampling, preserves color detail


def main() -> None:
    if not SRC_FILE.is_file():
        raise SystemExit(f"Source file not found: {SRC_FILE}")
    DST_DIR.mkdir(parents=True, exist_ok=True)

    dst = DST_DIR / f"{SRC_FILE.stem}.jpg"
    with Image.open(SRC_FILE) as im:
        icc = im.info.get("icc_profile")   # preserve the color space
        dpi = im.info.get("dpi")
        rgba = im.convert("RGBA")          # normalize, keep resolution
        bg = Image.new("RGBA", rgba.size, BG_COLOR + (255,))
        flat = Image.alpha_composite(bg, rgba).convert("RGB")

        params = {"quality": QUALITY, "subsampling": SUBSAMPLING}
        if icc:
            params["icc_profile"] = icc
        if dpi:
            params["dpi"] = dpi
        flat.save(dst, "JPEG", **params)

    print(f"Done. {SRC_FILE.name} -> {dst}")


if __name__ == "__main__":
    main()
