# Power BI build guide

## Import

Import these CSVs from `data/processed/`:

- `frontier_worker_trend.csv`
- `frontier_workers_by_residence.csv`
- `hourly_earnings.csv`
- `greater_region_employment.csv`

Create a calendar table from 2016 to the latest available year and relate it to
each table's `year` column.

## Page 1 - Workforce overview

- Cards: Total Frontier Workers, Frontier Worker YoY %
- Line chart: `year` vs `frontier_workers`
- 100% stacked column: `year` and `residence_country` with worker count
- Slicer: year

## Page 2 - Sector earnings

- Clustered bar: sector on Y, Average Hourly Earnings on X, legend by resident status
- Matrix: sector, resident status, year and average hourly earnings
- Slicer: year

## Page 3 - Greater Region context

- Line chart: `year` vs employment count, legend country
- Table: latest annual employment values by country

Use the DAX in `Measures.dax` and the M-query starter in `Power_Query_M.txt`.
