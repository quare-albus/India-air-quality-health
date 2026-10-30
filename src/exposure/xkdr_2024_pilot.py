#!/usr/bin/env python3
"""Build city-level 2024 PM2.5/PM10 annual means from XKDR CPCB CAAQM data.

Requires XKDR_API_KEY, requests and duckdb. Raw Parquet files are cached locally;
no raw observations are committed to Git.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

import duckdb
import requests

BASE_URL = "https://airquality.xkdr.org"
YEAR = 2024
MONTHS = range(1, 13)
EXPECTED_HOURS = 366 * 24  # 2024 is a leap year
SOURCE = "cpcb_caaqm"


def download(url: str, destination: Path, key: str, force: bool = False) -> None:
    if destination.exists() and destination.stat().st_size > 0 and not force:
        print(f"Cached: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {key}"}
    temporary = destination.with_suffix(destination.suffix + ".part")
    with requests.get(url, headers=headers, stream=True, timeout=(30, 300)) as response:
        response.raise_for_status()
        with temporary.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    temporary.replace(destination)
    print(f"Downloaded: {destination} ({destination.stat().st_size:,} bytes)")


def sql_path(path: Path) -> str:
    return "'" + str(path.resolve()).replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data/processed/2024_pilot")
    parser.add_argument("--raw-dir", default="data/raw/xkdr/2024")
    parser.add_argument("--min-completeness", type=float, default=0.75,
                        help="Minimum fraction of 8,784 calendar hours per station/pollutant (default: 0.75).")
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    if not 0 < args.min_completeness <= 1:
        parser.error("--min-completeness must be >0 and <=1")

    key = os.environ.get("XKDR_API_KEY")
    if not key:
        print(
            "Missing XKDR_API_KEY. Obtain a key at https://airquality.xkdr.org/signup "
            "and set it as an environment variable. The public demo key is restricted "
            "to 2024 bulk files and may be used for a small pilot.",
            file=sys.stderr,
        )
        return 2

    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    monthly_files = []
    for month in MONTHS:
        destination = raw_dir / f"month={month:02d}" / "data.parquet"
        url = f"{BASE_URL}/v1/files/v1/measurements/year=2024/month={month:02d}/data.parquet"
        download(url, destination, key, args.force_download)
        monthly_files.append(destination)

    stations_file = raw_dir / "stations.parquet"
    download(f"{BASE_URL}/v1/files/v1/stations.parquet", stations_file, key, args.force_download)

    files_sql = "[" + ", ".join(sql_path(p) for p in monthly_files) + "]"
    stations_sql = sql_path(stations_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET threads = 4")

    # Keep only CPCB CAAQM hourly PM observations. Negative values are invalid;
    # high positive values are retained because XKDR has not performed outlier validation.
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW raw_pm AS
        SELECT station_id, station_name, state_name, city_name, parameter_name,
               collected_at, value, unit
        FROM read_parquet({files_sql}, union_by_name = true)
        WHERE source = '{SOURCE}'
          AND parameter_name IN ('PM2.5', 'PM10')
          AND collected_at >= TIMESTAMP '2024-01-01 00:00:00'
          AND collected_at <  TIMESTAMP '2025-01-01 00:00:00'
    """)

    # One value per station/pollutant/hour; duplicate source rows are averaged.
    con.execute("""
        CREATE OR REPLACE TEMP VIEW hourly AS
        SELECT station_id, any_value(station_name) AS station_name,
               any_value(state_name) AS state_name,
               any_value(city_name) AS city_name,
               parameter_name, collected_at, avg(value) AS hourly_value,
               count(*) AS source_rows,
               any_value(unit) AS unit
        FROM raw_pm
        WHERE value IS NOT NULL AND value >= 0
        GROUP BY station_id, parameter_name, collected_at
    """)

    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW station_annual AS
        SELECT station_id, any_value(station_name) AS station_name,
               any_value(state_name) AS state_name,
               any_value(city_name) AS city_name,
               parameter_name,
               count(*) AS valid_hours,
               count(*) / {EXPECTED_HOURS}.0 AS completeness,
               avg(hourly_value) AS annual_mean_ug_m3,
               sum(source_rows - 1) AS duplicate_rows_collapsed,
               min(collected_at) AS first_observation_2024,
               max(collected_at) AS last_observation_2024
        FROM hourly
        GROUP BY station_id, parameter_name
    """)

    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW eligible_station AS
        SELECT *, completeness >= {args.min_completeness} AS eligible
        FROM station_annual
    """)

    # City estimate: equal-weight mean of eligible station annual means.
    con.execute("""
        CREATE OR REPLACE TEMP VIEW city_annual AS
        SELECT city_name, state_name,
               avg(annual_mean_ug_m3) FILTER (WHERE parameter_name = 'PM2.5' AND eligible)
                   AS pm25_annual_mean_ug_m3,
               avg(annual_mean_ug_m3) FILTER (WHERE parameter_name = 'PM10' AND eligible)
                   AS pm10_annual_mean_ug_m3,
               count(*) FILTER (WHERE parameter_name = 'PM2.5' AND eligible)
                   AS pm25_stations_included,
               count(*) FILTER (WHERE parameter_name = 'PM10' AND eligible)
                   AS pm10_stations_included,
               count(*) FILTER (WHERE parameter_name = 'PM2.5' AND NOT eligible)
                   AS pm25_stations_excluded,
               count(*) FILTER (WHERE parameter_name = 'PM10' AND NOT eligible)
                   AS pm10_stations_excluded
        FROM eligible_station
        WHERE city_name IS NOT NULL AND trim(city_name) <> ''
        GROUP BY city_name, state_name
    """)

    station_csv = output_dir / "station_annual_2024.csv"
    city_csv = output_dir / "city_annual_2024.csv"
    qc_csv = output_dir / "qc_summary_2024.csv"
    con.execute(f"COPY (SELECT * FROM eligible_station ORDER BY state_name, city_name, station_name, parameter_name) TO {sql_path(station_csv)} (HEADER, DELIMITER ',')")
    con.execute(f"COPY (SELECT * FROM city_annual ORDER BY state_name, city_name) TO {sql_path(city_csv)} (HEADER, DELIMITER ',')")

    con.execute("""
        CREATE OR REPLACE TEMP VIEW qc AS
        SELECT 'raw_rows_for_PM' AS metric, count(*)::BIGINT AS value FROM raw_pm
        UNION ALL SELECT 'hourly_station_pollutant_records', count(*) FROM hourly
        UNION ALL SELECT 'station_pollutant_pairs', count(*) FROM station_annual
        UNION ALL SELECT 'eligible_station_pollutant_pairs', count(*) FROM eligible_station WHERE eligible
        UNION ALL SELECT 'city_state_groups', count(*) FROM city_annual
        UNION ALL SELECT 'negative_or_null_values_excluded',
            (SELECT count(*) FROM raw_pm WHERE value IS NULL OR value < 0)
        UNION ALL SELECT 'duplicate_rows_collapsed',
            (SELECT coalesce(sum(duplicate_rows_collapsed), 0) FROM station_annual)
    """)
    con.execute(f"COPY (SELECT * FROM qc ORDER BY metric) TO {sql_path(qc_csv)} (HEADER, DELIMITER ',')")

    print(f"\nCompleted 2024 pilot. Outputs in: {output_dir}")
    print(f"- {city_csv}")
    print(f"- {station_csv}")
    print(f"- {qc_csv}")
    print(f"Completeness threshold: {args.min_completeness:.0%} of {EXPECTED_HOURS:,} calendar hours.")
    print("Interpretation: station means are equally weighted within city; estimates are not population-weighted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
