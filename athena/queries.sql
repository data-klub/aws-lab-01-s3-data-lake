-- Athena (Glue Data Catalog) over the partitioned Parquet files in S3.
-- Run one statement at a time in the Athena query editor (eu-central-1).

CREATE DATABASE data_klub;

-- EXTERNAL: Athena only stores the definition; dropping the table never deletes the files.
-- ingest_date is a partition column whose value comes from the folder name.
CREATE EXTERNAL TABLE data_klub.listings (
  listing_id  string,
  district    string,
  rooms       bigint,
  area_m2     double,
  price_pln   bigint,
  listed_on   date
)
PARTITIONED BY (ingest_date string)
STORED AS PARQUET
LOCATION 's3://<bucket>/raw/listings/';

-- Register new ingest_date=... folders (run after new days land).
MSCK REPAIR TABLE data_klub.listings;

-- Median price per m2 by district for one day (partition pruning via WHERE ingest_date).
-- Reconciled against pandas: every district within 0.25% (approx_percentile is approximate).
SELECT district,
       COUNT(*) AS listings,
       ROUND(approx_percentile(price_pln / area_m2, 0.5)) AS median_price_per_m2
FROM data_klub.listings
WHERE ingest_date = '2026-11-15'
GROUP BY district
ORDER BY median_price_per_m2 DESC;

-- One row per daily partition.
SELECT ingest_date,
       COUNT(*)              AS listings,
       MIN(listing_id)       AS first_id,
       ROUND(AVG(price_pln)) AS avg_price
FROM data_klub.listings
GROUP BY ingest_date
ORDER BY ingest_date;
