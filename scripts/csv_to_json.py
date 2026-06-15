# /// script
# requires-python = ">=3.14"
# ///
"""Convert windows-data.csv into windows_data.json.

Keeps only columns A, C, D, E, F, G, H, J. The treatment (G) and objects (H)
columns are pipe-delimited in the CSV and are emitted as arrays of strings.

Run with:  uv run scripts/csv_to_json.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
CSV_PATH = ROOT / "windows-data.csv"
JSON_PATH = ROOT / "windows_data.json"

# CSV column index -> output key  (A=0, B=1, ... L=11)
COLUMNS = {
    0: "daves name",       # A: window  (e.g. window-0001)
    2: "circadian",  # C
    3: "color",      # D
    4: "frame",      # E
    5: "occupant",   # F
    6: "treatment",  # G  (pipe-delimited -> array)
    7: "objects",    # H  (pipe-delimited -> array)
    8: "signage",    # I
    9: "notable",    # J
    10: "special",   # K
}
LIST_COLS = {6, 7}  # columns emitted as arrays of strings
NONE_COLS = {5, 6, 7, 8}  # occupant/treatment/objects/signage -> "none" when empty
SPECIAL_COL = 10  # -> "no" when empty


def main() -> None:
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV not found: {CSV_PATH}")

    with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    windows = []
    for row in rows[1:]:  # skip header
        if not any(cell.strip() for cell in row):
            continue  # skip blank lines
        obj = {}
        for idx, key in COLUMNS.items():
            val = row[idx].strip().lower() if idx < len(row) else ""
            if idx in LIST_COLS:
                val = [p.strip() for p in val.split("|") if p.strip()]
            if not val:  # empty string or empty list -> fill defaults
                if idx in NONE_COLS:
                    val = ["none"] if idx in LIST_COLS else "none"
                elif idx == SPECIAL_COL:
                    val = "no"
            obj[key] = val
        windows.append(obj)

    JSON_PATH.write_text(
        json.dumps({"windows": windows}, indent=2, ensure_ascii=False)
    )
    print(f"Wrote {len(windows)} windows to {JSON_PATH.name}")


if __name__ == "__main__":
    main()
