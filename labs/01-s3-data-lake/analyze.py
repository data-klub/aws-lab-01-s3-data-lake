"""Explore the fake listings."""

import pandas as pd

df = pd.read_parquet("data/listings.parquet")

# Q1. What columns and types do we have? Any missing values?
df.info()

# Q2. Add a column price_per_m2 (whole number).
df["price_per_m2"] = (df["price_pln"] / df["area_m2"]).round()
print(df.head())

# Q3. Median price per m² by district, most expensive first.
by_district = df.groupby("district")["price_per_m2"].median().sort_values(ascending=False)
print(by_district)

# Q4. How many listings per number of rooms?
rooms_count = df["rooms"].value_counts().sort_index()
print(rooms_count)

# Q5. Cheapest 3-room flat in Mokotów: show the whole row.
Mokotów_3 = df[(df["rooms"] == 3) & (df["district"] == "Mokotów")]
print(Mokotów_3.nsmallest(1, "price_pln"))

# Q6 (bonus). Listings per week.
#     hint: pd.to_datetime(df["listed_on"]).dt.to_period("W").value_counts().sort_index()
