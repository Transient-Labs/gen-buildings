# /// script
# requires-python = ">=3.14"
# ///
"""Copy the black-bg JPEGs into a NEW folder, renamed per final_windows_map.json.

For each map entry: the file named after `daves_file_name` (matched by number,
which is zero-padded on disk: window-0893.jpg) is copied to the output folder
under its `new_shuffled_name` number, UNPADDED (window-1.jpg), keeping .jpg.

Non-destructive: source files are never modified. Validates the whole plan and
aborts before copying anything if a source is missing or the mapping isn't a
clean bijection.

Run with:  uv run rename_black_bg.py
"""

import json
import re
import shutil
from pathlib import Path

GEN_ROOT = Path(__file__).resolve().parent
MAP_PATH = GEN_ROOT / "final_windows_map.json"

SRC_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows/final_windows_black_bg")
DST_DIR = Path("/Users/benstrauss/TransientLabs/NFT-Projects/windows/final_windows_black_bg_shuffled")

EXT = ".jpg"
SRC_PAD = 4  # source files are window-0001.jpg ... window-1000.jpg
NUM_RE = re.compile(r"window-(\d+)")


def num(name: str) -> int:
    m = NUM_RE.search(name)
    if not m:
        raise ValueError(f"no window number in {name!r}")
    return int(m.group(1))


def main() -> None:
    if not SRC_DIR.is_dir():
        raise SystemExit(f"Source not found: {SRC_DIR}")
    if not MAP_PATH.exists():
        raise SystemExit(f"Map not found: {MAP_PATH}")

    entries = json.loads(MAP_PATH.read_text())
    src_files = {p.name for p in SRC_DIR.glob(f"window-*{EXT}")}

    # Build the full plan and validate BEFORE copying anything.
    plan = []          # (src_path, dst_path)
    errors = []
    old_nums, new_nums = set(), set()
    for e in entries:
        old_n = num(e["daves_file_name"])
        new_n = num(e["new_shuffled_name"])
        if old_n in old_nums:
            errors.append(f"duplicate source number: {old_n}")
        if new_n in new_nums:
            errors.append(f"duplicate destination number: {new_n}")
        old_nums.add(old_n)
        new_nums.add(new_n)
        src = SRC_DIR / f"window-{old_n:0{SRC_PAD}d}{EXT}"
        dst = DST_DIR / f"window-{new_n}{EXT}"
        if not src.exists():
            errors.append(f"missing source {src.name} (would become {dst.name})")
        plan.append((src, dst))

    if len(plan) != len(src_files):
        errors.append(f"map has {len(plan)} entries but {len(src_files)} files in source")

    if errors:
        for msg in errors[:20]:
            print("ERROR:", msg)
        more = len(errors) - 20
        if more > 0:
            print(f"... and {more} more")
        raise SystemExit("Aborting — problems found, nothing copied.")

    DST_DIR.mkdir(parents=True, exist_ok=True)
    copied = skipped = 0
    for i, (src, dst) in enumerate(plan, 1):
        if dst.exists():
            skipped += 1
        else:
            shutil.copy2(src, dst)  # copy2 preserves timestamps/metadata
            copied += 1
        if i % 100 == 0 or i == len(plan):
            print(f"[{i}/{len(plan)}] {src.name} -> {dst.name}")

    print(f"\nDone. copied={copied} skipped={skipped} total={len(plan)}")
    print(f"Output: {DST_DIR}")


if __name__ == "__main__":
    main()
