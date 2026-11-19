"""Generate fake Warsaw listings for one day and write them to S3 as Parquet.

Deployed as the Lambda function `generate-listings` (Python 3.12, x86_64) with the
AWS-managed layer AWSSDKPandas-Python312. Triggered daily at 06:00 Europe/Warsaw by
EventBridge Scheduler. Pass {"date": "YYYY-MM-DD"} to backfill a past day.
"""

import io
import os
import random
from datetime import UTC, date, datetime, timedelta

import boto3
import pandas as pd

BUCKET = os.environ["BUCKET"]
N_LISTINGS = 1000
DISTRICTS = {
    "Śródmieście": 24000,
    "Mokotów": 19000,
    "Wola": 18500,
    "Praga-Południe": 15500,
    "Bemowo": 14000,
    "Białołęka": 11500,
}

s3 = boto3.client("s3")  # created once, reused across runs


def make_listing(rng: random.Random, i: int, day: date) -> dict:
    """Return one fake listing for the given day."""
    district = rng.choice(list(DISTRICTS))
    rooms = rng.randint(1, 5)
    area_m2 = round(rooms * 18 + rng.uniform(5, 20), 1)
    price_per_m2 = DISTRICTS[district] * rng.uniform(0.85, 1.15)
    return {
        "listing_id": f"FAKE-{day:%Y%m%d}-{i:05d}",
        "district": district,
        "rooms": rooms,
        "area_m2": area_m2,
        "price_pln": round(area_m2 * price_per_m2),
        "listed_on": day - timedelta(days=rng.randint(0, 44)),
    }


def lambda_handler(event, context):
    """Entry point: Lambda calls this. Optional event {"date": "YYYY-MM-DD"} for backfills."""
    if "date" in event:
        day = date.fromisoformat(event["date"])
    else:
        day = datetime.now(UTC).date()

    rng = random.Random(int(day.strftime("%Y%m%d")))
    df = pd.DataFrame([make_listing(rng, i, day) for i in range(N_LISTINGS)])

    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    key = f"raw/listings/ingest_date={day.isoformat()}/listings.parquet"
    s3.put_object(Bucket=BUCKET, Key=key, Body=buf.getvalue())

    return {"key": key, "rows": len(df)}
