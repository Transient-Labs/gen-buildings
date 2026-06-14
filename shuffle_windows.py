# /// script
# requires-python = ">=3.14"
# ///
"""Randomly renumber the window tiles in a directory, or undo a prior shuffle.

Shuffle: renames the existing window-<n> files among themselves (a bijection —
every number is reused exactly once, so no tile is lost or duplicated) and
writes an old-name -> new-name map to JSON. KEEP that JSON: it records which
original tile each new number points to, and --undo needs it.

Run with:
    uv run shuffle_windows.py                       # shuffle ./final_windows
    uv run shuffle_windows.py final_windows_webp    # shuffle another dir
    uv run shuffle_windows.py --undo                # restore original names
    uv run shuffle_windows.py --seed 42             # reproducible shuffle
"""

import argparse
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^window-(\d+)\.(\w+)$")


def map_path_for(target_dir: Path) -> Path:
    return ROOT / f"{target_dir.name}_map.json"


def shuffle(target_dir: Path, seed: int | None) -> None:
    map_path = map_path_for(target_dir)

    # Collect window-<n>.<ext> files, keyed by their number.
    files = {}  # number -> (ext, path)
    for p in target_dir.iterdir():
        m = NAME_RE.match(p.name)
        if m:
            files[int(m.group(1))] = (m.group(2), p)
    if not files:
        raise SystemExit(f"No window-<n> files found in {target_dir}")

    # Refuse to clobber an existing map — files + map are a matched pair.
    if map_path.exists():
        raise SystemExit(
            f"{map_path.name} already exists. Run with --undo first, or remove "
            "it, before reshuffling."
        )

    numbers = sorted(files)
    shuffled = numbers[:]
    random.Random(seed).shuffle(shuffled)
    mapping = dict(zip(numbers, shuffled))  # old number -> new number

    # Two-phase rename so we never collide with a name about to be reused.
    for old in numbers:
        ext, path = files[old]
        path.rename(target_dir / f".shuffle_tmp_{old}.{ext}")
    for old in numbers:
        ext = files[old][0]
        (target_dir / f".shuffle_tmp_{old}.{ext}").rename(
            target_dir / f"window-{mapping[old]}.{ext}"
        )

    # Record as a list of {new_shuffled_name, old_name}, ordered by the new
    # (deployed) number so you can look up any shuffled file's original.
    entries = [
        {
            "new_shuffled_name": f"window-{mapping[old]}.{files[old][0]}",
            "old_name": f"window-{old}.{files[old][0]}",
        }
        for old in numbers
    ]
    entries.sort(key=lambda e: int(NAME_RE.match(e["new_shuffled_name"]).group(1)))
    map_path.write_text(json.dumps(entries, indent=2))
    print(f"Renamed {len(mapping)} files in {target_dir.name}/")
    print(f"Mapping written to {map_path.name}")


def undo(target_dir: Path) -> None:
    map_path = map_path_for(target_dir)
    if not map_path.exists():
        raise SystemExit(f"No map at {map_path.name} — nothing to undo.")

    entries = json.loads(map_path.read_text())  # [{new_shuffled_name, old_name}]
    inverse = {e["new_shuffled_name"]: e["old_name"] for e in entries}  # current -> original

    missing = [new for new in inverse if not (target_dir / new).exists()]
    if missing:
        raise SystemExit(
            "Cannot undo; mapped files are missing in "
            f"{target_dir.name}/ (e.g. {', '.join(missing[:5])})"
        )

    # Two-phase rename back: current names -> temp -> original names.
    items = list(inverse.items())  # (current_name, original_name)
    for i, (new, _old) in enumerate(items):
        (target_dir / new).rename(target_dir / f".undo_tmp_{i}")
    for i, (_new, old) in enumerate(items):
        (target_dir / f".undo_tmp_{i}").rename(target_dir / old)

    map_path.unlink()  # files are back to originals; the map no longer applies
    print(f"Restored {len(items)} files to original names in {target_dir.name}/")
    print(f"Removed {map_path.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Shuffle or restore window tile names.")
    ap.add_argument("dir", nargs="?", default="final_windows",
                    help="directory of window-<n>.<ext> files (default: final_windows)")
    ap.add_argument("--undo", action="store_true",
                    help="restore original names from the map JSON")
    ap.add_argument("--seed", type=int, default=None,
                    help="seed for a reproducible shuffle")
    args = ap.parse_args()

    target_dir = ROOT / args.dir
    if not target_dir.is_dir():
        raise SystemExit(f"Directory not found: {target_dir}")

    if args.undo:
        undo(target_dir)
    else:
        shuffle(target_dir, args.seed)


if __name__ == "__main__":
    main()
