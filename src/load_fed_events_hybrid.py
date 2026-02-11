"""
Hybrid Fed Events Script
Combines actual rate changes from FEDFUNDS with known FOMC meeting dates
"""
import os
import pandas as pd
from fredapi import Fred
from datetime import datetime

# Known FOMC meeting dates (2-day meetings use the second date when decision is announced)
FOMC_MEETINGS = [
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16",
    "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15",
    "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
    "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    # 2026
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-16",
]

def get_rate_changes():
    """Get actual rate changes from FEDFUNDS series"""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing FRED_API_KEY. In the terminal run:\n"
            "export FRED_API_KEY='YOUR_KEY'"
        )
    
    fred = Fred(api_key=api_key)
    fedfunds = fred.get_series("FEDFUNDS", observation_start="2021-01-01")
    
    df = fedfunds.to_frame(name="rate")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df["rate_change"] = df["rate"].diff()
    
    # Detect rate changes (threshold 0.01%)
    changes = df[df["rate_change"].abs() >= 0.01].copy()
    changes["change_bps"] = (changes["rate_change"] * 100).round(0)
    
    return changes

def main():
    print("="*60)
    print("HYBRID FED EVENTS - MEETINGS + RATE CHANGES")
    print("="*60)
    
    # Get rate changes
    print("\n📊 Fetching rate changes from FRED...")
    rate_changes = get_rate_changes()
    print(f"   Found {len(rate_changes)} rate changes since 2021")
    
    # Convert FOMC meetings to dataframe
    print("\n📅 Loading known FOMC meeting dates...")
    meetings_df = pd.DataFrame({
        'event_date': pd.to_datetime(FOMC_MEETINGS)
    })
    print(f"   Found {len(meetings_df)} FOMC meetings")
    
    # Merge meetings with rate changes using a window approach
    events = meetings_df.copy()
    
    # For each meeting, find the nearest rate change within +/- 15 days
    events['rate'] = None
    events['rate_change'] = None
    events['change_bps'] = None
    
    for idx, row in events.iterrows():
        meeting_date = row['event_date']
        
        # Look for rate changes within 15 days before or after the meeting
        window_start = meeting_date - pd.Timedelta(days=15)
        window_end = meeting_date + pd.Timedelta(days=15)
        
        nearby_changes = rate_changes[
            (rate_changes.index >= window_start) & 
            (rate_changes.index <= window_end)
        ]
        
        if len(nearby_changes) > 0:
            # Use the change closest to the meeting date
            time_diffs = (nearby_changes.index - meeting_date).to_series().abs()
            closest_idx = time_diffs.argmin()
            closest = nearby_changes.iloc[closest_idx]
            events.at[idx, 'rate'] = closest['rate']
            events.at[idx, 'rate_change'] = closest['rate_change']
            events.at[idx, 'change_bps'] = closest['change_bps']
    
    # Classify events
    def classify_event(row):
        if pd.isna(row['change_bps']) or row['change_bps'] == 0:
            return "FOMC Meeting (No Change)", "No Change"
        elif row['change_bps'] > 0:
            if row['change_bps'] >= 50:
                return f"Rate Hike +{int(row['change_bps'])}bps (Large)", "Rate Hike (Large)"
            else:
                return f"Rate Hike +{int(row['change_bps'])}bps", "Rate Hike"
        else:
            if row['change_bps'] <= -50:
                return f"Rate Cut {int(row['change_bps'])}bps (Large)", "Rate Cut (Large)"
            else:
                return f"Rate Cut {int(row['change_bps'])}bps", "Rate Cut"
    
    events[['event_name', 'subtype']] = events.apply(
        lambda row: pd.Series(classify_event(row)), 
        axis=1
    )
    
    # Add metadata
    events['category'] = 'Monetary Policy'
    events['notes'] = 'FOMC meeting date + FEDFUNDS rate data'
    
    # Sort by date
    events = events.sort_values('event_date').reset_index(drop=True)
    
    # Select final columns
    output = events[[
        'event_date',
        'event_name',
        'category',
        'subtype',
        'rate',
        'change_bps',
        'notes'
    ]].copy()
    
    # Save
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    
    output.to_csv("data/raw/events_auto.csv", index=False)
    output.to_csv("outputs/fed_events_hybrid.csv", index=False)
    
    print(f"\n💾 Saved to:")
    print(f"   → data/raw/events_auto.csv (for pipeline)")
    print(f"   → outputs/fed_events_hybrid.csv (for review)")
    
    print(f"\n📅 Date range: {output['event_date'].min().date()} to {output['event_date'].max().date()}")
    print(f"   Total events: {len(output)}")
    
    print("\n📊 Event Summary:")
    print(output['subtype'].value_counts().to_string())
    
    print("\n🔍 Recent Events (Last 10):")
    recent = output[['event_date', 'event_name', 'rate']].tail(10)
    print(recent.to_string(index=False))
    
    print("\n✅ SUCCESS!")
    print("\nThis hybrid approach gives you:")
    print("  ✅ Actual FOMC meeting dates (not monthly averages)")
    print("  ✅ Rate changes from FEDFUNDS data")
    print("  ✅ Meetings where rates held steady")
    print("\nNext: Run 'python src/test_pipeline.py' to process events")

if __name__ == "__main__":
    main()