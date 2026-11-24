# Luxembourg Cross-Border Workforce Dashboard

![Dashboard preview](assets/dashboard_preview.png)

## Business question

How has Luxembourg's cross-border workforce changed by country of residence,
how do earnings differ by sector and resident status, and what is the broader
employment context in Belgium, France, Germany and Luxembourg?

## What this project does

1. Retrieves official STATEC/LUSTAT data on frontier workers resident in
   Belgium, France and Germany.
2. Retrieves STATEC average hourly earnings by NACE sector and resident status.
3. Retrieves Eurostat labour-force employment counts for the four countries.
4. Produces cleaned CSV files, a SQLite database, SQL analysis and a dashboard.

## Dashboard pages

1. **Workforce overview** - total frontier workers, year-over-year change and
   residence-country mix.
2. **Sector earnings** - average hourly earnings for residents and cross-border
   workers by NACE sector.
3. **Greater Region context** - employment trends in Belgium, France, Germany
   and Luxembourg.

## Key findings from the included refresh

The dashboard uses STATEC annual figures as at 30 September. The included
refresh shows **228,800** frontier workers in 2025. France is the largest
residence country in the series, followed by Germany and Belgium. Earnings are
shown as descriptive averages, not evidence of a causal wage gap.

## Data sources

- [STATEC frontier workers DF_B3107](https://lustat.statec.lu/vis?df%5Bag%5D=LU1&df%5Bds%5D=ds-release&df%5Bid%5D=DF_B3107&df%5Bvs%5D=1.0&lc=en&pg=0&snb=1&tm=DF_B3107)
- [STATEC average hourly earnings by economic activity](https://lustat.statec.lu/vis?df%5Bag%5D=LU1&df%5Bds%5D=ds-release&df%5Bid%5D=DSD_ESS_EARN_H%40DF_C1214&df%5Bvs%5D=1.1&lc=en&pg=0&snb=1&tm=C1214)
- [Eurostat Statistics API](https://ec.europa.eu/eurostat/data/web-services)

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/build_project.py
```

## Power BI

Use the CSVs in `data/processed/`, then follow
[`powerbi/PowerBI_Build_Guide.md`](powerbi/PowerBI_Build_Guide.md). The project
contains DAX measures and an M-query starter. A `.pbix` file is not included
because it is a proprietary desktop binary; the model-ready assets are included
instead.

## Project structure

```text
data/raw/        API snapshots
data/processed/  dashboard-ready CSVs and SQLite database
sql/             reproducible analysis queries
src/             extraction, transformation and visualisation code
dashboard/       HTML dashboard landing page
powerbi/         Power BI model instructions and measures
assets/          generated dashboard preview
```

## Disclaimer

This is an independent educational portfolio project. Values are sourced from
public statistical APIs and may be revised by the publishers. Always refresh
before using figures in a decision-making context.
