# Data Klub Lab 01: an S3 data lake for housing listings

**Data Klub** is a peer group of data engineers who learn by building production-style
pipelines together. Lab 01 is the first hands-on AWS exercise. Python generates synthetic Warsaw
flat listings, pandas analyses them, and the files land in Amazon S3 as date-partitioned Parquet,
the layout real data lakes use.

It is a warm-up for the club's main project,
[House_Prices](https://github.com/kubilayf/House_Prices): a medallion lakehouse on Databricks
fed by a mock listings API.

All data is synthetic. No real listings and no credentials are stored in this repo.

## Architecture

```
generate.py ──► data/listings.parquet ──► analyze.py   (pandas: medians by district, filters)
                         │
                         └──► upload.py ──► s3://<bucket>/raw/listings/ingest_date=YYYY-MM-DD/listings.parquet
                                               │
                                               └──► read back into pandas (round-trip check)
```

- **Deterministic generator:** a fixed seed means the same 1,000 rows every run.
- **Parquet:** columnar and typed. 1,000 rows take about 21 KB.
- **Hive-style partitions** (`ingest_date=…`): one folder per daily load, never overwritten. Spark,
  Databricks and Athena can skip partitions they don't need.
- **No keys in code:** boto3 and the AWS CLI read credentials from the local AWS config.

## AWS setup

- Root user protected with MFA (a passkey) and a zero-spend budget alert. Root is used only for setup.
- A private S3 bucket (`eu-central-1`) with Block Public Access on and SSE-S3 encryption.
- An IAM user for the CLI and SDK with **least privilege**: one inline policy that allows only
  this bucket. It can't list other buckets, create buckets or touch IAM.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ListThisBucket", "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::<bucket>" },
    { "Sid": "ReadWriteObjectsInThisBucket", "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::<bucket>/*" }
  ]
}
```

`ListBucket` acts on the bucket ARN; object actions need the `/*` object ARN. Mixing them up is
the most common S3 policy bug.

**Sign-up tip:** use the classic "(advanced)" AWS sign-up. Accounts from the newer project-style
sign-up can be pinned to one region by a service control policy (`explicit deny in a service
control policy`), and they have no root login.

## Run it

Requires [uv](https://docs.astral.sh/uv/) and the [AWS CLI](https://aws.amazon.com/cli/), with `aws configure` done.

```bash
uv sync
uv run python generate.py     # write data/listings.parquet
uv run python analyze.py      # pandas exploration
uv run python upload.py       # upload to S3, list partitions, read back
```

Set `BUCKET` in `upload.py` to your own bucket name.

## Skills covered

S3 (buckets, keys, prefixes, partitioned layout), IAM users and access keys, the AWS CLI,
boto3 (clients, paginators, streaming bodies, `ClientError`), least-privilege IAM, root MFA,
explicit deny (SCP) vs implicit deny (no allowing policy),
and pandas (groupby, boolean filters, medians).

## Roadmap

- [x] Least-privilege IAM policy scoped to one bucket (see below)
- [ ] Query the Parquet files with SQL in Athena (Glue Data Catalog, partitions)
- [ ] Run the generator daily with Lambda and EventBridge Scheduler
