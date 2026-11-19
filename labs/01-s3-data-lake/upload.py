"""Upload listings.parquet to S3, list what's there, and read it back with pandas."""

import io
import sys
from datetime import date
from pathlib import Path

import boto3
import pandas as pd
from botocore.exceptions import ClientError

BUCKET = "data-klub-lab-k7q2"
LOCAL_FILE = Path("data") / "listings.parquet"

s3 = boto3.client("s3")  # uses your `aws configure` keys and region automatically


def upload(ingest_date: date) -> str:
    """Upload the local file under raw/listings/ingest_date=YYYY-MM-DD/ and return its key."""
    key = f"raw/listings/ingest_date={ingest_date.isoformat()}/listings.parquet"
    s3.upload_file(str(LOCAL_FILE), BUCKET, key)
    return key


def list_keys(prefix: str) -> list[str]:
    """Return every object key under prefix."""
    paginator = s3.get_paginator("list_objects_v2")
    return list(paginator.paginate(Bucket=BUCKET, Prefix=prefix).search("Contents[].Key"))


def read_back(key: str) -> pd.DataFrame:
    """Download an object into memory and load it as a DataFrame."""
    with s3.get_object(Bucket=BUCKET, Key=key)["Body"] as body:
        return pd.read_parquet(io.BytesIO(body.read()))


def main() -> int:
    """Upload, list, read back."""
    try:
        key = upload(date.today())
        print("Uploaded:", key)
        print("In bucket:", list_keys("raw/"))
        df = read_back(key)
        print(f"Downloaded {len(df)} rows")
        print("First 3 rows:")
        print(df.head(3))
        return 0
    except ClientError as e:
        print(f"AWS error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
