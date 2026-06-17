# /// script
# requires-python = ">=3.14"
# ///
"""Convert windows_keyed.json into windows_keyed.csv.

Emits one row per window. The first column is "Window" (the window-N key);
the remaining columns are exactly the keys present in each window object.
List-valued keys (treatment, objects) are pipe-delimited, matching the
format used in windows-data.csv.

Run with:  uv run scripts/keyed_to_csv.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
JSON_PATH = ROOT / "windows_keyed.json"
CSV_PATH = ROOT / "windows_keyed.csv"


def main() -> None:
    if not JSON_PATH.exists():
        raise SystemExit(f"JSON not found: {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    # Column order = keys of the first window object, preserved as-is.
    first = next(iter(data.values()))
    keys = list(first.keys())
    header = ["Window", *keys]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for window_name, obj in data.items():
            row = [window_name]
            for key in keys:
                val = obj.get(key, "")
                if isinstance(val, list):
                    val = "|".join(str(v) for v in val)
                row.append(val)
            writer.writerow(row)

    print(f"Wrote {len(data)} windows to {CSV_PATH.name}")


if __name__ == "__main__":
    main()
