# /// script
# requires-python = ">=3.14"
# ///
"""Re-key windows_data.json by shuffled id, via final_windows_map.json.

windows_data.json is a list of entries, each with a `name` like "window-0893".
final_windows_map.json maps each shuffled id (`new_shuffled_name`, e.g.
"window-1.webp") to the original `daves_file_name` (e.g. "window-893.webp").
They reference the same window by NUMBER (893), despite the padding/extension
differences.

Output: an object keyed by the shuffled id (minus ".webp"), whose value is the
matching windows_data entry, e.g.
    { "window-1": { "name": "window-0893", "circadian": "...", ... }, ... }

Run with:  uv run scripts/rekey_windows_data.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
DATA_PATH = ROOT / "windows_data.json"
MAP_PATH = ROOT / "final_windows_map.json"
OUT_PATH = ROOT / "windows_keyed.json"

NUM_RE = re.compile(r"window-(\d+)")


def num(name: str) -> int:
    m = NUM_RE.search(name)
    if not m:
        raise ValueError(f"no window number in {name!r}")
    return int(m.group(1))


def main() -> None:
    data = json.loads(DATA_PATH.read_text())
    entries = data["windows"] if isinstance(data, dict) else data
    mapping = json.loads(MAP_PATH.read_text())

    # Index windows_data entries by their numeric id (parsed from "name").
    by_num = {}
    for e in entries:
        by_num[num(e["daves name"])] = e

    # Order output by the shuffled number (window-1, window-2, ...).
    mapping = sorted(mapping, key=lambda m: num(m["new_shuffled_name"]))

    out = {}
    errors = []
    for m in mapping:
        shuffled_id = m["new_shuffled_name"].rsplit(".", 1)[0]  # drop ".webp"
        daves_num = num(m["daves_file_name"])
        entry = by_num.get(daves_num)
        if entry is None:
            errors.append(f"no windows_data entry for {m['daves_file_name']} -> {shuffled_id}")
            continue
        out[shuffled_id] = entry

    if errors:
        for msg in errors[:20]:
            print("ERROR:", msg)
        raise SystemExit(f"Aborting — {len(errors)} unmatched entries; nothing written.")

    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {len(out)} entries to {OUT_PATH.name}")


if __name__ == "__main__":
    main()
