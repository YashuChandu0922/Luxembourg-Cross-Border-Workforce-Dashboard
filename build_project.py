"""Build the Luxembourg Cross-Border Workforce portfolio project from official APIs."""
from __future__ import annotations

import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
ASSETS = ROOT / "assets"
DASHBOARD = ROOT / "dashboard"
for directory in (RAW, PROCESSED, ASSETS, DASHBOARD):
    directory.mkdir(parents=True, exist_ok=True)


def get_bytes(url: str, accept: str = "application/json") -> bytes:
    request = Request(url, headers={"User-Agent": "portfolio-project/1.0", "Accept": accept})
    with urlopen(request, timeout=90) as response:
        return response.read()


def get_csv(url: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(get_bytes(url, "text/csv")))


def statec_frontier_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = "https://lustat.statec.lu/rest/data/LU1,DF_B3107,1.0"
    total = get_csv(f"{base}/L01.A.?startPeriod=2016&dimensionAtObservation=AllDimensions")
    residence = get_csv(f"{base}/SL03+SL04+SL05.A.?startPeriod=2016&dimensionAtObservation=AllDimensions")
    total.to_csv(RAW / "statec_frontier_workers_total.csv", index=False)
    residence.to_csv(RAW / "statec_frontier_workers_residence.csv", index=False)

    trend = total.rename(columns={"TIME_PERIOD": "year", "OBS_VALUE": "frontier_workers_thousands"})[
        ["year", "frontier_workers_thousands"]
    ].copy()
    trend["year"] = trend["year"].astype(int)
    trend["frontier_workers"] = (trend.pop("frontier_workers_thousands") * 1000).round().astype(int)

    labels = {"SL03": "Belgium", "SL04": "France", "SL05": "Germany"}
    country = residence.rename(columns={"TIME_PERIOD": "year", "OBS_VALUE": "frontier_workers_thousands"})[
        ["year", "SPECIFICATION", "frontier_workers_thousands"]
    ].copy()
    country["year"] = country["year"].astype(int)
    country["residence_country"] = country["SPECIFICATION"].map(labels)
    country["frontier_workers"] = (country.pop("frontier_workers_thousands") * 1000).round().astype(int)
    country = country[["year", "residence_country", "frontier_workers"]]
    country["share_pct"] = (
        100 * country["frontier_workers"] / country.groupby("year")["frontier_workers"].transform("sum")
    ).round(1)
    return trend, country


def statec_earnings() -> pd.DataFrame:
    url = (
        "https://lustat.statec.lu/rest/data/"
        "LU1,DSD_ESS_EARN_H@DF_C1214,1.1/"
        "..A4._T+B-E+F+G+H+I+J+K+M+L_N+O+P+Q+R_S.....?"
        "startPeriod=2010&dimensionAtObservation=AllDimensions"
    )
    raw = get_csv(url)
    raw.to_csv(RAW / "statec_hourly_earnings.csv", index=False)
    sector_labels = {
        "_T": "All sectors", "B-E": "Industry", "F": "Construction",
        "G": "Wholesale & retail", "H": "Transport & storage",
        "I": "Accommodation & food", "J": "Information & communication",
        "K": "Financial & insurance", "L": "Real estate",
        "M": "Professional, scientific & technical", "N": "Administrative & support",
        "O": "Public administration", "P": "Education", "Q": "Health & social work",
        "R_S": "Arts, recreation & other services",
    }
    status_labels = {"FRO": "Cross-border workers", "RES": "Residents"}
    frame = raw.loc[raw["RESID_STATUS"].isin(status_labels)].copy()
    frame = frame.rename(columns={"TIME_PERIOD": "year", "OBS_VALUE": "avg_hourly_earnings_eur", "NACE_R2": "sector_code"})
    frame["year"] = frame["year"].astype(int)
    frame["sector"] = frame["sector_code"].map(sector_labels).fillna(frame["sector_code"])
    frame["residence_status"] = frame["RESID_STATUS"].map(status_labels)
    return frame[["year", "sector_code", "sector", "residence_status", "avg_hourly_earnings_eur"]].sort_values(
        ["year", "sector", "residence_status"]
    )


def eurostat_employment() -> pd.DataFrame:
    params = [
        ("geo", "LU"), ("geo", "BE"), ("geo", "DE"), ("geo", "FR"),
        ("sex", "T"), ("age", "Y20-64"), ("indic_em", "EMP_LFS"),
        ("unit", "THS_PER"), ("format", "JSON"),
    ]
    url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsi_emp_a?" + urlencode(params)
    raw = json.loads(get_bytes(url).decode("utf-8"))
    (RAW / "eurostat_employment.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    geo = raw["dimension"]["geo"]["category"]
    times = raw["dimension"]["time"]["category"]
    geo_index = geo["index"]
    time_index = times["index"]
    labels = geo["label"]
    n_time = len(time_index)
    rows = []
    for code, g_index in geo_index.items():
        for year_text, t_index in time_index.items():
            value = raw.get("value", {}).get(str(g_index * n_time + t_index))
            if value is not None:
                rows.append({
                    "year": int(year_text),
                    "country_code": code,
                    "country": labels[code],
                    "employment_thousands": value,
                })
    return pd.DataFrame(rows).query("year >= 2016").sort_values(["country", "year"])


def create_dashboard(trend: pd.DataFrame, residence: pd.DataFrame, earnings: pd.DataFrame, employment: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    colors = {"Belgium": "#4E79A7", "France": "#F28E2B", "Germany": "#59A14F"}
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    fig.suptitle("Luxembourg Cross-Border Workforce Dashboard", fontsize=20, fontweight="bold", x=0.05, ha="left")

    axes[0, 0].plot(trend["year"], trend["frontier_workers"] / 1000, color="#1F4E79", marker="o", linewidth=2.7)
    axes[0, 0].set_title("Frontier workers employed in Luxembourg", loc="left", fontweight="bold")
    axes[0, 0].set_ylabel("Workers (thousands)")
    axes[0, 0].annotate(f"{trend.iloc[-1]['frontier_workers'] / 1000:.1f}k", (trend.iloc[-1]['year'], trend.iloc[-1]['frontier_workers'] / 1000), xytext=(-38, 12), textcoords="offset points", fontweight="bold")

    pivot = residence.pivot(index="year", columns="residence_country", values="frontier_workers").fillna(0)
    for country in ["Belgium", "France", "Germany"]:
        axes[0, 1].plot(pivot.index, pivot[country] / 1000, marker="o", linewidth=2.2, label=country, color=colors[country])
    axes[0, 1].set_title("Residence country mix", loc="left", fontweight="bold")
    axes[0, 1].set_ylabel("Workers (thousands)")
    axes[0, 1].legend(frameon=False, ncol=3, loc="upper left")

    latest_year = earnings["year"].max()
    wage = earnings.loc[(earnings["year"] == latest_year) & (earnings["sector"] != "All sectors")].pivot(index="sector", columns="residence_status", values="avg_hourly_earnings_eur").dropna()
    wage = wage.sort_values("Cross-border workers", ascending=True).tail(8)
    wage.plot.barh(ax=axes[1, 0], color=["#76B7B2", "#E15759"])
    axes[1, 0].set_title(f"Average hourly earnings by sector ({latest_year})", loc="left", fontweight="bold")
    axes[1, 0].set_xlabel("EUR per hour")
    axes[1, 0].legend(frameon=False, fontsize=8)

    for country, frame in employment.groupby("country"):
        axes[1, 1].plot(frame["year"], frame["employment_thousands"], linewidth=2.1, label=country)
    axes[1, 1].set_title("Employment context, ages 20-64", loc="left", fontweight="bold")
    axes[1, 1].set_ylabel("Employed people (thousands)")
    axes[1, 1].legend(frameon=False, ncol=2, fontsize=8, loc="upper left")
    for ax in axes.flat:
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(ASSETS / "dashboard_preview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    latest = trend.iloc[-1]
    france_share = residence.loc[(residence["year"] == latest["year"]) & (residence["residence_country"] == "France"), "share_pct"].iloc[0]
    total_wage = earnings.loc[(earnings["year"] == latest_year) & (earnings["sector"] == "All sectors")]
    wage_text = " / ".join(f"{r.residence_status}: EUR {r.avg_hourly_earnings_eur:.1f}" for r in total_wage.itertuples())
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Luxembourg Cross-Border Workforce Dashboard</title>
    <style>body{{font-family:Arial,sans-serif;margin:40px;color:#17212b}}h1{{margin-bottom:4px}}.sub{{color:#54616d}}.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}.card{{border:1px solid #d8dee4;border-radius:10px;padding:16px;min-width:200px}}.value{{font-size:28px;font-weight:700;color:#1f4e79}}img{{width:100%;max-width:1200px;border:1px solid #d8dee4;border-radius:10px}}</style>
    </head><body><h1>Luxembourg Cross-Border Workforce Dashboard</h1><p class='sub'>Official STATEC/LUSTAT and Eurostat data | Last project refresh: {datetime.now(timezone.utc).date()}</p>
    <section class='cards'><div class='card'><div>Frontier workers ({int(latest.year)})</div><div class='value'>{latest.frontier_workers:,.0f}</div></div><div class='card'><div>France residence share</div><div class='value'>{france_share:.1f}%</div></div><div class='card'><div>All-sector average hourly earnings ({latest_year})</div><div class='value' style='font-size:16px'>{wage_text}</div></div></section>
    <img src='../assets/dashboard_preview.png' alt='Dashboard preview'><p>See the repository README and Power BI guide for data definitions and dashboard build instructions.</p></body></html>"""
    (DASHBOARD / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    trend, residence = statec_frontier_data()
    earnings = statec_earnings()
    employment = eurostat_employment()
    trend.to_csv(PROCESSED / "frontier_worker_trend.csv", index=False)
    residence.to_csv(PROCESSED / "frontier_workers_by_residence.csv", index=False)
    earnings.to_csv(PROCESSED / "hourly_earnings.csv", index=False)
    employment.to_csv(PROCESSED / "greater_region_employment.csv", index=False)
    with sqlite3.connect(PROCESSED / "workforce.sqlite") as connection:
        trend.to_sql("frontier_worker_trend", connection, if_exists="replace", index=False)
        residence.to_sql("frontier_workers_by_residence", connection, if_exists="replace", index=False)
        earnings.to_sql("hourly_earnings", connection, if_exists="replace", index=False)
        employment.to_sql("greater_region_employment", connection, if_exists="replace", index=False)
    create_dashboard(trend, residence, earnings, employment)
    print("Luxembourg project built successfully.")


if __name__ == "__main__":
    main()
