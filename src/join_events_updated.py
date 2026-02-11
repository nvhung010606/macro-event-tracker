import pandas as pd
import os
import sys

# Allow switching between manual and automated events
EVENTS_FILE = os.getenv("EVENTS_FILE", "data/raw/events_auto.csv")
MARKETS_FILE = "data/processed/markets_features.parquet"
OUTFILE = "data/processed/event_panel.parquet"

def main():
    print(f"Using events file: {EVENTS_FILE}")
    
    if not os.path.exists(EVENTS_FILE):
        print(f"\n❌ Error: {EVENTS_FILE} not found!")
        print("\nTo use automated events, run: python src/load_fed_events.py")
        print("To use manual events, run: export EVENTS_FILE='data/raw/events.csv'")
        sys.exit(1)
    
    events = pd.read_csv(EVENTS_FILE)
    events["event_date"] = pd.to_datetime(events["event_date"])
    
    print(f"Loaded {len(events)} events from {EVENTS_FILE}")

    m = pd.read_parquet(MARKETS_FILE)
    m["date"] = pd.to_datetime(m["date"])
    m = m.sort_values("date")

    # Exact-date join
    panel = events.merge(m, left_on="event_date", right_on="date", how="left")
    
    # For events without exact market data, use next available trading day
    missing = panel["severity_1d"].isna()
    if missing.sum() > 0:
        print(f"\n⚠️  {missing.sum()} events missing exact market match - using forward fill...")
        
        for idx in panel[missing].index:
            event_dt = panel.loc[idx, "event_date"]
            # Find next trading day
            future_dates = m[m["date"] > event_dt]
            if len(future_dates) > 0:
                next_trading_day = future_dates.iloc[0]
                # Update with next trading day's data
                market_cols = [c for c in m.columns if c != "date"]
                for col in market_cols:
                    panel.loc[idx, col] = next_trading_day[col]

    # Save outputs
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    
    panel.to_parquet(OUTFILE, index=False)
    panel.to_csv("outputs/event_panel.csv", index=False)

    print(f"\n✅ Saved: {OUTFILE}")
    print(f"✅ Saved: outputs/event_panel.csv")
    print(f"\nRows with market data: {(~panel['severity_1d'].isna()).sum()} / {len(panel)}")
    
    if "subtype" in panel.columns:
        print("\n📊 Events by subtype:")
        print(panel["subtype"].value_counts().to_string())
    
    print("\n🔍 Sample of matched events:")
    print(panel[["event_date","event_name","category","severity_1d","spx_ret_1d","vix_chg_1d","y10_chg_1d_bps"]].head(10).to_string(index=False))

if __name__ == "__main__":
    main()