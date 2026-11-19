"""Generate fake Warsaw flat listings and save them as Parquet."""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_LISTINGS = 1000

# Rough asking price per m² (PLN) by district. Made up, but realistic-ish.
DISTRICTS = {
    "Śródmieście": 24000,
    "Mokotów": 19000,
    "Wola": 18500,
    "Praga-Południe": 15500,
    "Bemowo": 14000,
    "Białołęka": 11500,
}


def make_listing(rng: random.Random, i: int) -> dict:
    """Return one fake listing as a dict."""
    district = rng.choice(list(DISTRICTS))
    rooms = rng.randint(1, 5)
    area_m2 = round(rooms * 18 + rng.uniform(5, 20), 1)
    price_per_m2 = DISTRICTS[district] * rng.uniform(0.85, 1.15)
    return {
        "listing_id": f"FAKE-{i:05d}",
        "district": district,
        "rooms": rooms,
        "area_m2": area_m2,
        "price_pln": round(area_m2 * price_per_m2),
        "listed_on": date(2026, 10, 1) + timedelta(days=rng.randint(0, 44)),
    }


def main() -> None:
    """Build the table and write it to data/listings.parquet."""
    rng = random.Random(SEED)
    rows = [make_listing(rng, i) for i in range(N_LISTINGS)]
    df = pd.DataFrame(rows)
    out = Path("data") / "listings.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(df.head())
    print(f"Wrote {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
