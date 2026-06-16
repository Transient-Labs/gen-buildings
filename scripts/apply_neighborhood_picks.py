# /// script
# requires-python = ">=3.14"
# ///
"""Write each array from neighborhood_picks.json into a neighborhoods/neighborhood-N.html.

Set index 0 -> neighborhood-1.html, index 1 -> neighborhood-2.html, ... Replaces the
single `const picks = [...];` line in each file; everything else is left untouched.

Run with:  uv run scripts/apply_neighborhood_picks.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
PICKS_PATH = ROOT / "neighborhood_picks.json"
HTML_DIR = ROOT / "neighborhoods"

# Matches the whole `const picks = ...;` line — both the empty placeholder
# (`const picks = ;`) and an already-filled array (`const picks = [..];`).
PICKS_RE = re.compile(r"const picks = [^;]*;")


def main() -> None:
    sets = json.loads(PICKS_PATH.read_text())

    # Validate everything up front; abort before writing if anything is off.
    errors = []
    for i in range(len(sets)):
        f = HTML_DIR / f"neighborhood-{i + 1}.html"
        if not f.is_file():
            errors.append(f"missing {f.name}")
        elif len(PICKS_RE.findall(f.read_text())) != 1:
            errors.append(f"{f.name}: expected exactly one `const picks = [...];`")
    if errors:
        for m in errors:
            print("ERROR:", m)
        raise SystemExit("Aborting — nothing written.")

    for i, arr in enumerate(sets):
        f = HTML_DIR / f"neighborhood-{i + 1}.html"
        new_line = "const picks = " + json.dumps(arr) + ";"
        content = PICKS_RE.sub(lambda _: new_line, f.read_text(), count=1)
        f.write_text(content)
        print(f"neighborhood-{i + 1}.html <- set {i} ({len(arr)} ids)")

    print(f"\nDone. Updated {len(sets)} files in {HTML_DIR.name}/")


if __name__ == "__main__":
    main()
