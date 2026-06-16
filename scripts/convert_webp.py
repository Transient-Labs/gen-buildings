# /// script
# requires-python = ">=3.14"
# dependencies = ["pillow"]
# ///
"""Convert every PNG in the input dir to WebP, written to the output dir.

Run with:  uv run convert_webp.py
(uv reads the inline dependency block above and installs Pillow automatically.)
"""

import json
from pathlib import Path

from PIL import Image

INPUT_DIR = Path("/Users/benstrauss/Downloads/final_windows_png")
OUTPUT_DIR = Path("../final_windows_neighborhood")

# --- WebP encode settings (tweak as needed) ---
QUALITY = 100        # 0-100, lossy quality; higher = better and larger
LOSSLESS = False    # True for lossless WebP (ignores QUALITY)
METHOD = 6          # 0-6 effort; higher = slower encode, smaller file
OVERWRITE = False   # re-encode files already present in the output dir

# Optional downscale: shrink each image so its SHORTER edge equals this many px,
# preserving aspect ratio. Only downsizes (never upscales). Set to 0 to disable.
RESIZE_MIN_EDGE = 400

# Optional rename via final_windows_map.json: save each output under its
# new_shuffled_name, matched by the input filename (= daves_file_name). Set to
# None to keep the original input filenames.
MAP_PATH = Path(__file__).resolve().parent.parent / "final_windows_map.json"


def main() -> None:
    if not INPUT_DIR.is_dir():
        raise SystemExit(f"Input directory not found: {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pngs = sorted(INPUT_DIR.glob("*.png"))
    if not pngs:
        raise SystemExit(f"No .png files in {INPUT_DIR}")

    # Optional rename map: input stem (daves_file_name) -> new_shuffled_name stem.
    rename = {}
    if MAP_PATH:
        if not MAP_PATH.exists():
            raise SystemExit(f"Map not found: {MAP_PATH}")
        for e in json.loads(MAP_PATH.read_text()):
            rename[Path(e["daves_file_name"]).stem] = Path(e["new_shuffled_name"]).stem

    total = len(pngs)
    converted = skipped = failed = 0

    for i, src in enumerate(pngs, 1):
        out_stem = rename.get(src.stem, src.stem)
        if MAP_PATH and src.stem not in rename:
            print(f"[{i}/{total}] WARN no map entry for {src.name}; keeping name")
        dst = OUTPUT_DIR / f"{out_stem}.webp"
        if dst.exists() and not OVERWRITE:
            skipped += 1
            continue
        try:
            with Image.open(src) as im:
                # WebP wants RGB/RGBA; convert palette/grayscale modes first.
                if im.mode not in ("RGB", "RGBA"):
                    im = im.convert("RGBA")
                # Optional downscale to a target shorter edge (never upscale).
                if RESIZE_MIN_EDGE and min(im.size) > RESIZE_MIN_EDGE:
                    scale = RESIZE_MIN_EDGE / min(im.size)
                    im = im.resize(
                        (round(im.width * scale), round(im.height * scale)),
                        Image.Resampling.LANCZOS,
                    )
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
