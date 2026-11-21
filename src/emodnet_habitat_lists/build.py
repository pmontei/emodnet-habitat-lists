"""Build the reference tables into ``data/processed``.

Usage::

    ehl-build                 # or: python -m emodnet_habitat_lists.build
    ehl-build --raw data/raw --out data/processed
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from .schema import SYSTEMS_COLUMNS
from .sources import eunis_habitats

EUNIS_SYSTEMS = [
    ("EUNIS_2012", "EUNIS habitat classification 2007, revised descriptions 2012 (amended 2019)", "2012", "terrestrial + marine"),
    ("EUNIS_M_2019", "EUNIS marine habitat classification", "2019", "marine"),
    ("EUNIS_M_2022", "EUNIS marine habitat classification", "2022", "marine"),
    ("EUNIS_T_2021", "EUNIS terrestrial habitat classification", "2021", "terrestrial"),
]


def build(raw: Path, out: Path) -> dict[str, pd.DataFrame]:
    out.mkdir(parents=True, exist_ok=True)
    rda = eunis_habitats.fetch_rda(raw / "eunis_habitats.rda")
    habitats = eunis_habitats.load(rda)

    today = date.today().isoformat()
    systems = pd.DataFrame(
        [
            {
                "system": s,
                "name": n,
                "version": v,
                "authority": "EEA",
                "scope": sc,
                "source": eunis_habitats.SOURCE_LABEL,
                "accessed": today,
                "notes": "",
            }
            for s, n, v, sc in EUNIS_SYSTEMS
        ],
        columns=SYSTEMS_COLUMNS,
    )

    habitats.to_csv(out / "habitats.csv", index=False)
    systems.to_csv(out / "systems.csv", index=False)
    return {"habitats": habitats, "systems": systems}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--out", type=Path, default=Path("data/processed"))
    a = p.parse_args(argv)
    tables = build(a.raw, a.out)
    for name, df in tables.items():
        print(f"{name}: {len(df)} rows -> {a.out / (name + '.csv')}")


if __name__ == "__main__":
    main()
