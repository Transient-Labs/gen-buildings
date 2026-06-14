# /// script
# requires-python = ">=3.14"
# dependencies = ["pillow"]
# ///
"""Flatten transparent PNGs onto a solid background and export as JPEG.

Keeps the exact pixel resolution and embedded color profile (ICC) of each
source file — only the alpha channel is removed by compositing over BG_COLOR.

Run with:  uv run png_to_jpeg_bg.py
"""

from pathlib import Path

from PIL import Image

SRC_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows/FINAL-WINDOWS")
DST_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows/final_windows_black_bg")

BG_COLOR = (0, 0, 0)  # solid background painted into transparent areas
QUALITY = 95          # JPEG quality
SUBSAMPLING = 0       # 4:4:4 — no chroma subsampling, preserves color detail
OVERWRITE = False     # re-export files already present in DST_DIR


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"Source directory not found: {SRC_DIR}")
    DST_DIR.mkdir(parents=True, exist_ok=True)

    pngs = sorted(SRC_DIR.glob("*.png"))
    if not pngs:
        raise SystemExit(f"No .png files in {SRC_DIR}")

    total = len(pngs)
    exported = skipped = failed = 0

    for i, src in enumerate(pngs, 1):
        dst = DST_DIR / f"{src.stem}.jpg"
        if dst.exists() and not OVERWRITE:
            skipped += 1
            continue
        try:
            with Image.open(src) as im:
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
            exported += 1
        except Exception as e:  # keep going; report which file broke
            failed += 1
            print(f"[{i}/{total}] FAILED {src.name}: {e}")
            continue

        if i % 50 == 0 or i == total:
            print(f"[{i}/{total}] {src.name} -> {dst.name}")

    print(f"\nDone. exported={exported} skipped={skipped} failed={failed}")
    print(f"Output: {DST_DIR}")


if __name__ == "__main__":
    main()
