from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd


def build_payload(workbook_path: Path) -> dict:
    df_daily = pd.read_excel(workbook_path, sheet_name="Daily_Stats")
    df_hourly = pd.read_excel(workbook_path, sheet_name="Hourly_Heatmap")
    df_ranking = pd.read_excel(workbook_path, sheet_name="Junction_Ranking")

    day_categories = ["Weekday", "Weekend", "สงกรานต์"]

    junctions = {}
    for _, row in df_ranking.sort_values("Junction_Name").iterrows():
        junction_name = row["Junction_Name"]
        junctions[junction_name] = {
            "id": int(row["Junction_ID"]),
            "rank": int(row["Rank"]),
            "ranking": {
                "avgDelay": round(float(row["Avg_Delay"]), 2),
                "weightedDelay": round(float(row["Weighted_Delay"]), 2),
                "avgDailyVolume": f"{float(row['Avg_Daily_Volume']):,.2f}",
                "adaptive": round(float(row["Avg_Adaptive_Pct"]), 2),
            },
            "kpi": {day: {} for day in day_categories},
            "hourly": {day: [0] * 24 for day in day_categories},
        }

    grouped_kpi = (
        df_daily.groupby(["Junction_Name", "Day_Category"])
        .agg(
            Weighted_Avg_Delay=("Weighted_Avg_Delay", "mean"),
            Total_Volume_Day=("Total_Volume_Day", "mean"),
            Avg_Adaptive_Pct=("Avg_Adaptive_Pct", "mean"),
        )
        .reset_index()
    )

    for _, row in grouped_kpi.iterrows():
        junction_name = row["Junction_Name"]
        day_category = row["Day_Category"]
        if junction_name not in junctions or day_category not in day_categories:
            continue
        junctions[junction_name]["kpi"][day_category] = {
            "delay": round(float(row["Weighted_Avg_Delay"]), 2),
            "vol": f"{float(row['Total_Volume_Day']):,.2f}",
            "adaptive": round(float(row["Avg_Adaptive_Pct"]), 2),
        }

    for _, row in df_hourly.iterrows():
        junction_name = row["Junction_Name"]
        day_category = row["Day_Category"]
        hour = int(row["Hour_Int"])
        if junction_name not in junctions or day_category not in day_categories or not 0 <= hour <= 23:
            continue
        avg_delay = 0 if pd.isna(row["Avg_Delay"]) else round(float(row["Avg_Delay"]), 2)
        junctions[junction_name]["hourly"][day_category][hour] = avg_delay

    global_kpi_raw = (
        df_daily.groupby("Day_Category")
        .agg(
            Weighted_Avg_Delay=("Weighted_Avg_Delay", "mean"),
            Total_Volume_Day=("Total_Volume_Day", "mean"),
            Avg_Adaptive_Pct=("Avg_Adaptive_Pct", "mean"),
        )
        .to_dict("index")
    )

    global_kpi = {
        day: {
            "delay": round(float(global_kpi_raw[day]["Weighted_Avg_Delay"]), 2),
            "vol": f"{float(global_kpi_raw[day]['Total_Volume_Day']):,.2f}",
            "adaptive": round(float(global_kpi_raw[day]["Avg_Adaptive_Pct"]), 2),
        }
        for day in day_categories
    }

    global_hourly = {}
    hourly_grouped = (
        df_hourly.groupby(["Day_Category", "Hour_Int"])["Avg_Delay"]
        .mean()
        .reset_index()
        .sort_values(["Day_Category", "Hour_Int"])
    )
    for day in day_categories:
        day_series = hourly_grouped[hourly_grouped["Day_Category"] == day]
        global_hourly[day] = [round(float(value), 2) for value in day_series["Avg_Delay"].tolist()]

    top_rankings = []
    for _, row in df_ranking.nsmallest(10, "Rank").iterrows():
        top_rankings.append(
            {
                "name": row["Junction_Name"],
                "rank": int(row["Rank"]),
                "avgDelay": round(float(row["Avg_Delay"]), 2),
                "weightedDelay": round(float(row["Weighted_Delay"]), 2),
                "avgDailyVolume": f"{float(row['Avg_Daily_Volume']):,.2f}",
                "adaptive": round(float(row["Avg_Adaptive_Pct"]), 2),
            }
        )

    asset_version = pd.Timestamp.utcnow().strftime("%Y%m%d%H%M%S")

    return {
        "generatedAt": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "assetVersion": asset_version,
        "studyWindow": "1-21 Apr 2026",
        "junctionCount": int(df_ranking["Junction_Name"].nunique()),
        "dayCategories": day_categories,
        "globalKpi": global_kpi,
        "globalHourly": global_hourly,
        "junctions": junctions,
        "topRankings": top_rankings,
    }


def export_csvs(workbook_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.read_excel(workbook_path, sheet_name="Daily_Stats").to_csv(output_dir / "Daily_Stats.csv", index=False, encoding="utf-8-sig")
    pd.read_excel(workbook_path, sheet_name="Hourly_Heatmap").to_csv(output_dir / "Hourly_Heatmap.csv", index=False, encoding="utf-8-sig")
    pd.read_excel(workbook_path, sheet_name="Junction_Ranking").to_csv(output_dir / "Junction_Ranking.csv", index=False, encoding="utf-8-sig")


def write_payload(payload: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    js_path = output_dir / "dashboard-data.js"
    js_path.write_text(
        "window.BMA_DASHBOARD_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


def update_index_asset_version(repo_root: Path, asset_version: str) -> None:
    index_path = repo_root / "index.html"
    html = index_path.read_text(encoding="utf-8")
    updated_html, replacements = re.subn(
        r'<script src="data/dashboard-data\.js(?:\?v=[^"]*)?"></script>',
        f'<script src="data/dashboard-data.js?v={asset_version}"></script>',
        html,
        count=1,
    )

    if replacements != 1:
        raise RuntimeError("Unable to update dashboard-data.js asset version in index.html")

    index_path.write_text(updated_html, encoding="utf-8")


def main() -> int:
    workbook_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("Statistics_Summary.xlsx")
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = repo_root / "data"

    if not workbook_arg.exists():
        print(f"Workbook not found: {workbook_arg}")
        return 1

    payload = build_payload(workbook_arg)
    export_csvs(workbook_arg, output_dir)
    write_payload(payload, output_dir)
    update_index_asset_version(repo_root, payload["assetVersion"])
    print(f"Generated data files in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())