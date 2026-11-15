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

- An IAM user (not root) with S3 access for the CLI and SDK.
- A private S3 bucket with Block Public Access left on.
- Region: the account's home region. New accounts can be restricted to a single region by a
  service control policy, so check that first if you get `explicit deny in a service control policy`.

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
boto3 (clients, paginators, streaming bodies, `ClientError`), debugging an SCP explicit deny,
and pandas (groupby, boolean filters, medians).

## Roadmap

- [ ] Least-privilege IAM policy scoped to one bucket
- [ ] Query the Parquet files with SQL in Athena (Glue Data Catalog, partitions)
- [ ] Run the generator daily with Lambda and EventBridge Scheduler
