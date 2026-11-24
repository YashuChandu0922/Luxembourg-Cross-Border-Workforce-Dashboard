-- Run after src/build_project.py creates data/processed/workforce.sqlite.
-- SQLite supports the window functions used below.

WITH yearly_total AS (
    SELECT
        year,
        frontier_workers,
        LAG(frontier_workers) OVER (ORDER BY year) AS previous_year_workers
    FROM frontier_worker_trend
), residence_mix AS (
    SELECT
        year,
        residence_country,
        frontier_workers,
        ROUND(
            100.0 * frontier_workers
            / SUM(frontier_workers) OVER (PARTITION BY year),
            1
        ) AS share_pct,
        RANK() OVER (
            PARTITION BY year
            ORDER BY frontier_workers DESC
        ) AS residence_rank
    FROM frontier_workers_by_residence
)
SELECT
    t.year,
    t.frontier_workers,
    ROUND(
        100.0 * (t.frontier_workers - t.previous_year_workers)
        / t.previous_year_workers,
        1
    ) AS yoy_growth_pct,
    m.residence_country,
    m.share_pct,
    m.residence_rank
FROM yearly_total t
LEFT JOIN residence_mix m ON m.year = t.year
ORDER BY t.year, m.residence_rank;

-- Earnings comparison for the latest observation (2022 in the included source).
WITH earnings AS (
    SELECT
        year,
        sector,
        residence_status,
        avg_hourly_earnings_eur,
        AVG(avg_hourly_earnings_eur) OVER (
            PARTITION BY year, sector
        ) AS sector_mean
    FROM hourly_earnings
)
SELECT
    year,
    sector,
    residence_status,
    ROUND(avg_hourly_earnings_eur, 2) AS avg_hourly_earnings_eur,
    ROUND(avg_hourly_earnings_eur - sector_mean, 2) AS difference_from_sector_mean
FROM earnings
ORDER BY year DESC, sector, residence_status;
