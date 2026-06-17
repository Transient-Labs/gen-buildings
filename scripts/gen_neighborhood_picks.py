# /// script
# requires-python = ">=3.14"
# ///
"""Generate SETS arrays of COUNT random window ids in [LOW, HIGH] -> JSON.

Default: 20 sets of 240 unique ids in [1, 1000] (240 = a 20x12 neighborhood).
Output is a JSON array of arrays, one set per line.

Run with:  uv run scripts/gen_neighborhood_picks.py
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # project root (script lives in scripts/)
OUT_PATH = ROOT / "neighborhood_picks.json"

LOW, HIGH = 1, 1000  # inclusive on both ends
COUNT = 320          # numbers per set
SETS = 20            # number of sets
UNIQUE = True        # True = no repeats within a set; False = independent draws
SEED = None          # int for a reproducible result; None = OS randomness


def main() -> None:
    rng = random.Random(SEED)
    pool = range(LOW, HIGH + 1)

    sets = []
    for _ in range(SETS):
        if UNIQUE:
            sets.append(rng.sample(pool, COUNT))  # COUNT distinct values in range
        else:
            sets.append([rng.randint(LOW, HIGH) for _ in range(COUNT)])

    # Pretty-print the outer array but keep each set on a single line.
    body = ",\n".join("  " + json.dumps(s) for s in sets)
    OUT_PATH.write_text("[\n" + body + "\n]\n")

    print(f"Wrote {SETS} sets of {COUNT} ids ({LOW}-{HIGH}, unique={UNIQUE}) to {OUT_PATH.name}")


if __name__ == "__main__":
    main()
