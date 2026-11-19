# Generator spec

The design of the fake data source. Moved here from House_Prices `docs/spec.md` §4–5 on
2026-11-19 ([ADR 0008](https://github.com/data-klub/House_Prices/blob/main/docs/adr/0008-generator-separate-sources-by-config.md)),
with the sections renumbered. House_Prices keeps the bronze contract, adapters, silver and gold.

## 1. Rules

- **Determinism:** same `seed` + same date ⇒ byte-identical output. Never use unseeded randomness
  or wall-clock time inside the generator.
- English text and labels; Polish geography keeps its diacritics (Łódź, Białołęka); prices in PLN.
- Only synthetic data. No real listings, names, phones or emails.
- Runs natively on macOS, Windows and Linux; `pathlib` for paths; UTF-8 files with LF line endings.
- The API and payload formats are a contract with House_Prices: change them only together with
  the House_Prices parsers, and pin them with golden-file tests.


## 2. Generator

### 2.1 World model
- **Property**: true attributes (location TERYT, type flat/house, area, rooms, floor, year built, true condition, plot area for houses, building type) and true sale price if sold. Never visible to the pipeline.
- **Listing**: one ad of a property on one source. A property can have several listings over time (reposts) and on both sources (cross-posts).
- **Development**: developer investment with sibling units (Otodom-like).
- **Truth export** to `truth/`: `properties`, `listing_property_map`, `events`, `renovation_labels`.

### 2.2 Determinism
World starts at `world_start`; day D is produced by replaying from day 0 with `seed`. No stored state needed. 20,000 properties must replay in well under a minute (vectorize / cache if needed).

### 2.3 Geography (all of Poland)
- Hierarchy: voivodeship → powiat → gmina → city/town/village → district/sub-district (large cities).
- Keys: TERYT codes (GUS). Warsaw powiat = `1465`. Ship `reference/locations_pl.csv` (small curated subset is fine to start: all 16 voivodeships, ~50 cities incl. all Warsaw districts, a sample of towns and villages).
- Distribution by population weight; Warsaw ≈ 10–15% of listings.
- Each location: base price per m² + monthly trend.
- Payload location is **text** at one of three precision levels (street + number, district, city only) + approximate coordinates (+ OLX map zoom 17 or 13). Text→TERYT is a silver task.

### 2.4 Daily events (configurable probabilities, not market facts)

| Event | Probability | Payload effect |
|---|---|---|
| New listing | 2–4% of active stock | New id |
| Price change | 3% (80% cuts of 1–10%) | Price, price/m² |
| Description edit | 2% | Text changed |
| Refresh / bump | 5% (OLX) | Only date line — **not** a real change |
| Field correction | 0.5% | e.g. area 84 → 84.5 |
| Sold | 1% | Disappears; true sale price 90–100% of last ask → truth |
| Withdrawn | 0.3% | Disappears |
| Repost | 0.3% | Old id gone; same property returns days later, new id, rewritten text |
| Cross-post | 20% of new properties | Also on the other source, different wording/fields |
| Temporary gap | 0.5% | Missing 1–2 days, returns unchanged |
| Promo (developer) | small | Price drop + `price_lowest_30d` |
| Price on request toggle | small | Number ↔ "Ask for price" |

### 2.5 Source renderers (English labels, Polish geography)

**OLX-like** (small fixed param set; detail lives in description)
- Flats: `price_per_m2` (string, decimal point), `floor` ("Ground floor", "1".."10", "Above 10"), `furnished` (Yes/No), `market` (Primary/Secondary), `building_type` (Block, Tenement, Apartment building), `area` ("117,56 m²" comma decimal), `rooms` ("2 rooms", "4 or more").
- Houses: `price_per_m2`, `market`, `area`, `plot_area` ("1 078 m²"), `building_type` (Detached, Terraced, Farmstead, Summer house), `floors` ("Single-storey", "One floor", "Single-storey with usable attic"). No rooms field.
- Price as formatted text ("999 000 zł") + `negotiable` flag; machine-readable integer price also present in a widget field.
- Date line in 3 formats: "Added 01 November 2026", "Refreshed today at 12:23", "Refreshed on 01 November 2026".
- Seller: type private/business, display name, profile id, member since; business adds company block (name, tax id, phone, email, address).
- Map: lat/lon + zoom (17 = street, 13 = city).
- No condition field.

**Otodom-like** (rich, sectioned)
- `characteristics` list with sections differing by type: flats (main, building & materials, equipment), houses (main, building details, plot & surroundings).
- Numeric price; price states: number | promo with `lowest_price_30d` | `price_on_request`.
- `floor` as "3/5"; multi-valued fields as arrays (heating, media, security, fencing, extras).
- `finishing_state`: ready to move in | to renovate | to finish | no information.
- "no information" sentinels distinct from real 0 (e.g. rent 0 vs no information).
- Advertiser type private | agency | developer; agency reference number on agency ads.
- `last_updated` date; JSON-LD block that occasionally disagrees with visible fields.
- Development pages: name, completion quarter, status, units available "3 of 6", area range, "from X zł/m²", unit table linking child ads.

### 2.6 Descriptions (English)
Template + phrase banks from true attributes, with noise: condition only in text ~40% of the time; contradictions (title vs field area/rooms, text location outside the location field); boilerplate ("Direct sale, no agents please"), capitals, emoji; bundled prices ("flat 555 000 + garage 85 000"); parking/storage priced separately; phone numbers in text (plain, "5-0-4-5…", "60*******69"); occasional typos in text prices/dates; cadastral parcel number ("plot 260/15") sometimes.

### 2.7 Renovation labels (truth + classifier target)
`needs_renovation`, `renovation_possible`, `renovated`, `to_finish` (+ `build_stage`: developer_standard | closed_shell), `unknown`.

### 2.8 Injected edge cases (each must have a test)
1. Whole-source outage one day — no listing marked sold.
2. Partial crawl (manifest `partial`, 30% missing) — same rule.
3. Duplicate envelope within one crawl.
4. Same listing fetched by two crawls in one day.
5. Price typo fixed next day (999 000 → 99 900 → back).
6. Refresh-only days create no history row.
7. Relist under new id 10 days after removal.
8. Listing reappears after being marked sold.
9. Late data: yesterday's file after today's.
10. Schema drift: new Otodom field from a set date.
11. Development with 5–10 near-identical sibling units on one street — must not merge.
12. Rent 0 vs "no information".
13. Parking/storage priced separately in text only.
14. Price ↔ "price on request" toggling.
15. Developer promo with 30-day lowest price, then reverts.
16. Development "units available" decreasing over time.
17. Same unit cross-posted by developer and agent, slightly different area and sub-district.
18. Area including garage on some listings of one development.
19. Field "ready to move in" vs text "needs refreshing".
20. "Available from" in the past on an active listing.
21. OLX date line switching formats for the same ad.
22. Area field holds built-up area; usable area only in text.
23. Rooms field disagrees with title.
24. Package price in text differs from field price.
25. Non-property listing (cabin for relocation) in houses.
26. Phone numbers in description (plain and obfuscated).
27. Location precision varies with map zoom.
28. Same seller profile reposts one property under a new id.

## 3. Mock listings API

| Endpoint | Returns |
|---|---|
| `GET /olx/api/v1/offers?category=flats|houses&region=&page=` | 50 cards: id, title, price text, date line, url |
| `GET /olx/api/v1/offers/{id}` | OLX-like detail; 404/410 after removal |
| `GET /otodom/api/v1/search?type=flat|house&region=&page=` | 50 cards |
| `GET /otodom/api/v1/ads/{id}` | Otodom-like detail |
| `GET /otodom/api/v1/investments/{id}` | Development page |
