# /// script
# requires-python = ">=3.14"
# ///
"""Count windows matching each special-building trait.

Reads special_building_traits.csv (col 0 = building name, col 1 = trait to
search, col 2 = trait type) and windows_keyed.json (keyed by the shuffled id
"window-N"). The type selects which window field to search; a window matches if
any comma-separated alternative in the trait matches that field.

Output (special_building_counts.json):
    {
      "Botanist": {
        "trait name": "plants",
        "trait type": "object",
        "count": 12,
        "windows": [3, 57, ...]
      },
      ...
    }

Run with:  uv run scripts/special_building_counts.py
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
TRAITS_CSV = ROOT / "special_building_traits.csv"
WINDOWS_JSON = ROOT / "windows_keyed.json"
OUT_PATH = ROOT / "special_building_counts.json"

# trait "type" (CSV col 2) -> field in windows_keyed.json
TYPE_FIELD = {
    "object": "objects",      # array
    "color": "color",         # string (exact)
    "occupant": "occupant",   # string (exact)
    "circadian": "circadian", # string (exact)
    "treatment": "treatment", # array
    "notable": "notable",     # string (substring)
    "signage": "signage",     # string (exact)
}

NUM_RE = re.compile(r"window-(\d+)")


def num(name: str) -> int:
    m = NUM_RE.search(name)
    return int(m.group(1)) if m else 0


def matches(field_value, alternatives, field) -> bool:
    """True if any alternative matches the window's field value."""
    if isinstance(field_value, list):  # objects / treatment -> exact membership
        items = {str(x).strip().lower() for x in field_value}
        return any(a in items for a in alternatives)
    text = str(field_value).strip().lower()
    if field == "notable":  # prose -> substring
        return any(a in text for a in alternatives)
    return text in alternatives  # categorical string -> exact


def main() -> None:
    windows = json.loads(WINDOWS_JSON.read_text())

    with TRAITS_CSV.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    out = {}
    unknown_types = set()
    for row in rows[1:]:  # skip header
        if not row or not row[0].strip():
            continue
        name = row[0].strip()
        trait = row[1].strip()
        ttype = row[2].strip().lower()

        field = TYPE_FIELD.get(ttype)
        if field is None:
            unknown_types.add(ttype)
            continue

        alternatives = [a.strip().lower() for a in trait.split(",") if a.strip()]
        # Window ids as integers (index.html identifies windows by int), sorted.
        matched = sorted(
            num(wid) for wid, data in windows.items()
            if field in data and matches(data[field], alternatives, field)
        )

        out[name] = {
            "trait name": trait,
            "trait type": ttype,
            "count": len(matched),
            "windows": matched,
        }

    # Pretty-print, but keep each "windows" array on one line. Stash an inline
    # string sentinel, dump normally, then unwrap it back to a bare array.
    for info in out.values():
        info["windows"] = "@@[" + ", ".join(str(n) for n in info["windows"]) + "]@@"
    text = json.dumps(out, indent=2, ensure_ascii=False)
    text = re.sub(r'"@@(.*?)@@"', lambda m: m.group(1), text)
    OUT_PATH.write_text(text)

    if unknown_types:
        print("WARNING: unknown trait types skipped:", ", ".join(sorted(unknown_types)))
    print(f"Wrote {len(out)} special buildings to {OUT_PATH.name}")
    for name, info in out.items():
        print(f"  {name}: {info['count']}")


if __name__ == "__main__":
    main()
