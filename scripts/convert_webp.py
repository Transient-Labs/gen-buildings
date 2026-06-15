# /// script
# requires-python = ">=3.14"
# dependencies = ["pillow"]
# ///
"""Convert every PNG in the input dir to WebP, written to the output dir.

Run with:  uv run convert_webp.py
(uv reads the inline dependency block above and installs Pillow automatically.)
"""

from pathlib import Path

from PIL import Image

INPUT_DIR = Path("/Users/benstrauss/Downloads/new-window")
OUTPUT_DIR = Path("/Users/benstrauss/Downloads/new-window")

# --- WebP encode settings (tweak as needed) ---
QUALITY = 100        # 0-100, lossy quality; higher = better and larger
LOSSLESS = False    # True for lossless WebP (ignores QUALITY)
METHOD = 6          # 0-6 effort; higher = slower encode, smaller file
OVERWRITE = False   # re-encode files already present in the output dir


def main() -> None:
    if not INPUT_DIR.is_dir():
        raise SystemExit(f"Input directory not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pngs = sorted(INPUT_DIR.glob("*.png"))
    if not pngs:
        raise SystemExit(f"No .png files in {INPUT_DIR}")

    total = len(pngs)
    converted = skipped = failed = 0

    for i, src in enumerate(pngs, 1):
        dst = OUTPUT_DIR / f"{src.stem}.webp"
        if dst.exists() and not OVERWRITE:
            skipped += 1
            continue
        try:
            with Image.open(src) as im:
                # WebP wants RGB/RGBA; convert palette/grayscale modes first.
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                im.save(
                    dst,
                    format="WEBP",
                    quality=QUALITY,
                    lossless=LOSSLESS,
                    method=METHOD,
                )
            converted += 1
        except Exception as e:  # keep going; report which file broke
            failed += 1
            print(f"[{i}/{total}] FAILED {src.name}: {e}")
            continue

        if i % 50 == 0 or i == total:
            print(f"[{i}/{total}] {src.name} -> {dst.name}")

    print(f"\nDone. converted={converted} skipped={skipped} failed={failed}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
