import pandas as pd
import os

PANEL_FILE = "data/processed/event_panel.parquet"

def main():
    df = pd.read_parquet(PANEL_FILE).copy()
    df = df.dropna(subset=["severity"]).copy()

    os.makedirs("outputs/tables", exist_ok=True)

    top = df.sort_values("severity", ascending=False).head(20)
    top.to_csv("outputs/tables/top20_events.csv", index=False)

    by_cat = (
        df.groupby("category")["severity"]
          .agg(count="count", mean="mean", median="median", max="max")
          .sort_values("mean", ascending=False)
    )
    by_cat.to_csv("outputs/tables/severity_by_category.csv")

    print("Saved outputs/tables/top20_events.csv")
    print("Saved outputs/tables/severity_by_category.csv")
    print(by_cat)

    # Event study summary by category
# Event study summary by category
    event_study = (
        df.groupby("category")
        .agg(
            n_events=("severity", "count"),
            avg_spx_ret_1d=("spx_ret_1d", "mean"),
            avg_vix_chg_1d=("vix_chg_1d", "mean"),
            avg_y10_chg_bps=("y10_chg_1d_bps", "mean"),
            avg_severity=("severity", "mean"),
        )
        .sort_values("avg_severity", ascending=False)
    )

    event_study.to_csv("outputs/tables/event_study_summary.csv")
    print("Saved outputs/tables/event_study_summary.csv")
    print(event_study)



if __name__ == "__main__":
    main()
