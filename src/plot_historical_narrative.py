"""
The Historical Narrative: Zero to Five and Back (2021-2025)
A storytelling visualization of the most dramatic Fed cycle in 40+ years
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
INPUT_FILE = "data/processed/event_panel.parquet"
MARKETS_FILE = "data/processed/markets_features.parquet"
OUTPUT_DIR = "outputs/plots"

def setup_professional_style():
    """Sleek dark theme for historical narrative"""
    plt.style.use('dark_background')

    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    rcParams['figure.facecolor'] = '#000000'
    rcParams['axes.facecolor'] = '#0a0a0a'
    rcParams['axes.edgecolor'] = '#2a2a2a'
    rcParams['grid.color'] = '#1a1a1a'
    rcParams['grid.alpha'] = 0.6
    rcParams['text.color'] = '#ffffff'
    rcParams['axes.labelcolor'] = '#ffffff'
    rcParams['xtick.color'] = '#cccccc'
    rcParams['ytick.color'] = '#cccccc'

def create_historical_narrative():
    """Create the complete 5-act narrative visualization"""

    print("\n" + "="*70)
    print("📖 CREATING HISTORICAL NARRATIVE")
    print("="*70)

    # Load data
    print("\n📊 Loading data...")
    events_df = pd.read_parquet(INPUT_FILE)
    events_df['event_date'] = pd.to_datetime(events_df['event_date'])
    events_df = events_df.sort_values('event_date')

    markets_df = pd.read_parquet(MARKETS_FILE)
    markets_df['date'] = pd.to_datetime(markets_df['date'])
    markets_df = markets_df.sort_values('date')

    # Filter to our narrative period (2021-2026)
    start_date = pd.Timestamp('2021-01-01')
    end_date = pd.Timestamp('2026-01-01')

    events_df = events_df[(events_df['event_date'] >= start_date) &
                          (events_df['event_date'] <= end_date)]
    markets_df = markets_df[(markets_df['date'] >= start_date) &
                            (markets_df['date'] <= end_date)]

    print(f"   Events: {len(events_df)}")
    print(f"   Market days: {len(markets_df)}")

    # Define the 5 acts (dark theme colors)
    acts = [
        {
            'name': 'ACT 1: COVID Hangover',
            'start': '2021-01-01',
            'end': '2022-02-28',
            'color': "#03914a",
            'description': '"Transitory" inflation',
            'y_pos': 0.95
        },
        {
            'name': 'ACT 2: The Panic',
            'start': '2022-03-01',
            'end': '2022-06-30',
            'color': "#c2821b",
            'description': 'Inflation hits 9%',
            'y_pos': 0.90
        },
        {
            'name': 'ACT 3: Fastest Hikes in History',
            'start': '2022-07-01',
            'end': '2023-07-31',
            'color': "#7d2020",
            'description': '0% → 5.33% in 16 months',
            'y_pos': 0.85
        },
        {
            'name': 'ACT 4: The Long Pause',
            'start': '2023-08-01',
            'end': '2024-09-01',
            'color': "#1e4a77",
            'description': '"Higher for longer"',
            'y_pos': 0.80
        },
        {
            'name': 'ACT 5: The Pivot',
            'start': '2024-09-01',
            'end': '2026-01-01',
            'color': "#1c6b43",
            'description': 'Cutting cycle begins',
            'y_pos': 0.75
        }
    ]

    # Create figure with 3 panels
    setup_professional_style()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 12),
                                         gridspec_kw={'height_ratios': [2, 1.5, 1.5]})

    fig.suptitle('The 2021-2025 Fed Cycle\n' +
                 'The Most Dramatic Monetary Policy Shift in 40+ Years',
                 fontsize=20, fontweight='bold', y=0.995)

    # ================================================================
    # PANEL 1: Fed Funds Rate Journey
    # ================================================================
    print("\n📈 Panel 1: Fed Funds Rate...")

    # Draw act backgrounds with labels
    for act in acts:
        act_start = pd.Timestamp(act['start'])
        act_end = pd.Timestamp(act['end'])
        ax1.axvspan(act_start, act_end, alpha=0.3, color=act['color'])

        # Add act label directly on the graph
        act_mid = act_start + (act_end - act_start) / 2
        ax1.text(act_mid, 5.7, act['name'].split(':')[1].strip(),
                ha='center', va='top', fontsize=10, fontweight='bold',
                color='white', alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=act['color'],
                         edgecolor='white', linewidth=1, alpha=0.7))

    # Plot Fed Funds Rate
    if 'rate' in events_df.columns:
        # Remove NaN values for cleaner plotting
        rate_data = events_df[['event_date', 'rate']].dropna()
        ax1.plot(rate_data['event_date'], rate_data['rate'],
                linewidth=3, color='#00bfff', marker='o', markersize=6,
                label='Fed Funds Rate', zorder=5)

    # Annotate key moments
    annotations = [
        {'date': '2021-06-01', 'text': 'Powell: "Transitory"', 'y': 0.5, 'color': '#00ff88'},
        {'date': '2022-06-15', 'text': '75bp hike!\n(Largest since 1994)', 'y': 2.0, 'color': '#ff4444'},
        {'date': '2022-11-02', 'text': 'Peak pace:\n75bp again', 'y': 3.8, 'color': '#ff4444'},
        {'date': '2023-07-26', 'text': '5.33% Peak', 'y': 5.5, 'color': '#bb66ff'},
        {'date': '2024-09-18', 'text': 'First cut\nin 4 years!', 'y': 3.5, 'color': '#00ff88'},
    ]

    for i, ann in enumerate(annotations):
        try:
            ann_date = pd.Timestamp(ann['date'])
            if start_date <= ann_date <= end_date:
                # Special positioning for "First cut" annotation (last one)
                if i == len(annotations) - 1:  # "First cut" annotation
                    xytext_pos = (ann_date, ann['y'] - 1.2)  # Below the point
                    arrowstyle = '->'
                else:
                    xytext_pos = (ann_date, ann['y'] + 0.3)  # Above the point
                    arrowstyle = '->'

                ax1.annotate(ann['text'],
                           xy=(ann_date, ann['y']),
                           xytext=xytext_pos,
                           fontsize=9, fontweight='bold',
                           color=ann['color'],
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='#1a1a1a',
                                   edgecolor=ann['color'],
                                   alpha=0.9),
                           arrowprops=dict(arrowstyle=arrowstyle,
                                         color=ann['color'],
                                         lw=1.5))
        except:
            pass

    ax1.set_ylabel('Fed Funds Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_ylim(-0.2, 6)
    ax1.grid(True, alpha=0.3)
    # Add legend for Fed Funds Rate line only
    ax1.plot([], [], linewidth=3, color='#00bfff', marker='o', markersize=6,
            label='Fed Funds Rate')
    ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)

    # ================================================================
    # PANEL 2: Market Pain (SPX & VIX)
    # ================================================================
    print("📊 Panel 2: Market reactions...")

    # Draw act backgrounds with labels
    for act in acts:
        act_start = pd.Timestamp(act['start'])
        act_end = pd.Timestamp(act['end'])
        ax2.axvspan(act_start, act_end, alpha=0.3, color=act['color'])

        # Add act label
        act_mid = act_start + (act_end - act_start) / 2
        ax2.text(act_mid, 185, act['name'].split(':')[1].strip(),
                ha='center', va='top', fontsize=9, fontweight='bold',
                color='white', alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=act['color'],
                         edgecolor='white', linewidth=1, alpha=0.7))

    # Plot SPX (normalized to 100 at start)
    spx_max = 140  # default
    if 'spx' in markets_df.columns:
        spx = markets_df[['date', 'spx']].dropna()
        spx_normalized = (spx['spx'] / spx['spx'].iloc[0]) * 100
        spx_max = max(spx_normalized.max() * 1.05, 140)  # 5% headroom above max

        ax2.plot(spx['date'], spx_normalized,
                linewidth=2, color='#00bfff', label='S&P 500 (Normalized)', zorder=5)

        # Fill drawdown zones in red
        baseline = 100
        ax2.fill_between(spx['date'], spx_normalized, baseline,
                        where=(spx_normalized < baseline),
                        alpha=0.3, color='#ff4444', label='Drawdown')

    # Twin axis for VIX
    ax2_twin = ax2.twinx()
    if 'vix' in markets_df.columns:
        vix = markets_df[['date', 'vix']].dropna()
        ax2_twin.plot(vix['date'], vix['vix'],
                     linewidth=1.5, color='#ff8800', alpha=0.8,
                     label='VIX (Fear Index)', zorder=3)

        # Highlight extreme fear (VIX > 30)
        ax2_twin.axhline(y=30, color='#ff4444', linestyle='--',
                        alpha=0.5, linewidth=1, label='Extreme Fear (VIX>30)')

    ax2.set_ylabel('S&P 500 (Jan 2021 = 100)', fontsize=11, fontweight='bold')
    ax2_twin.set_ylabel('VIX (Volatility)', fontsize=11, fontweight='bold', color='#ff8800')
    ax2_twin.tick_params(axis='y', labelcolor='#ff8800')

    # Combine legends
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2,
              loc='upper left', fontsize=9, framealpha=0.9)

    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(60, spx_max)  # Dynamic y-axis based on actual data
    ax2_twin.set_ylim(10, 50)

    # ================================================================
    # PANEL 3: Economic Context (Why the Fed did what they did)
    # ================================================================
    print("📉 Panel 3: Economic context...")

    # Draw act backgrounds with labels
    for act in acts:
        act_start = pd.Timestamp(act['start'])
        act_end = pd.Timestamp(act['end'])
        ax3.axvspan(act_start, act_end, alpha=0.3, color=act['color'])

        # Add act label
        act_mid = act_start + (act_end - act_start) / 2
        ax3.text(act_mid, 9.7, act['name'].split(':')[1].strip(),
                ha='center', va='top', fontsize=9, fontweight='bold',
                color='white', alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=act['color'],
                         edgecolor='white', linewidth=1, alpha=0.7))

    # Simulate inflation data (in real version, you'd fetch from FRED)
    # Creating stylized inflation narrative
    inflation_dates = pd.date_range(start='2021-01-01', end='2025-12-31', freq='MS')
    inflation_values = [
        1.4, 1.7, 2.6, 4.2, 5.0, 5.4, 5.4, 5.3, 5.4, 6.2, 6.8, 7.0,  # 2021
        7.5, 7.9, 8.5, 8.3, 8.6, 9.1, 8.5, 8.3, 8.2, 7.7, 7.1, 6.5,  # 2022
        6.4, 6.0, 5.0, 4.9, 4.0, 3.0, 3.2, 3.7, 3.7, 3.2, 3.1, 3.4,  # 2023
        3.4, 3.2, 3.5, 3.4, 3.3, 3.3, 2.9, 2.5, 2.4, 2.6, 2.7, 2.9,  # 2024
        2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.3, 2.2, 2.1, 2.0, 2.0   # 2025
    ]

    inflation_df = pd.DataFrame({
        'date': inflation_dates[:len(inflation_values)],
        'inflation': inflation_values
    })

    ax3.plot(inflation_df['date'], inflation_df['inflation'],
            linewidth=2.5, color='#ff4444', label='CPI Inflation (YoY %)', zorder=5)
    ax3.fill_between(inflation_df['date'], inflation_df['inflation'], 0,
                     alpha=0.3, color='#ff4444')

    # Fed's 2% target line
    ax3.axhline(y=2.0, color='#00ff88', linestyle='--',
               linewidth=2, label="Fed's 2% Target", zorder=4)

    # Annotate key inflation moments
    inflation_annotations = [
        {'date': '2022-06-01', 'text': '9.1% Peak!\n40-year high', 'y': 9.1},
        {'date': '2023-06-01', 'text': 'Inflation\ncooling', 'y': 3.0},
        {'date': '2024-12-01', 'text': 'Near target', 'y': 2.0},
    ]

    for ann in inflation_annotations:
        try:
            ann_date = pd.Timestamp(ann['date'])
            if start_date <= ann_date <= end_date:
                ax3.annotate(ann['text'],
                           xy=(ann_date, ann['y']),
                           xytext=(ann_date, ann['y'] + 1.5),
                           fontsize=9, fontweight='bold',
                           color='#ff4444',
                           ha='center',
                           bbox=dict(boxstyle='round,pad=0.3',
                                   facecolor='#1a1a1a',
                                   edgecolor='#ff4444',
                                   alpha=0.9),
                           arrowprops=dict(arrowstyle='->',
                                         color='#ff4444',
                                         lw=1.5))
        except:
            pass

    ax3.set_ylabel('Inflation Rate (%)', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Timeline', fontsize=12, fontweight='bold')
    ax3.set_ylim(0, 10)
    ax3.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax3.grid(True, alpha=0.3)

    # Format x-axis for all panels
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # Note: Act labels now integrated directly on each panel
    plt.tight_layout(rect=[0, 0.01, 1, 0.99])

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, 'historical_narrative_fed_cycle.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#000000')
    print(f"\n💾 Saved: {output_path}")

    plt.close()  # Close instead of show for non-interactive mode

    # Print summary statistics
    print("\n" + "="*70)
    print("📊 HISTORICAL SUMMARY STATISTICS")
    print("="*70)

    if 'rate' in events_df.columns:
        rate_data = events_df[['event_date', 'rate']].dropna()
        if len(rate_data) > 0:
            min_rate = rate_data['rate'].min()
            max_rate = rate_data['rate'].max()
            total_increase = max_rate - min_rate

            print(f"\n🎯 Fed Funds Rate Journey:")
            print(f"   Starting rate (2021): {min_rate:.2f}%")
            print(f"   Peak rate (2023):     {max_rate:.2f}%")
            print(f"   Total increase:       {total_increase:.2f} percentage points")
            print(f"   Speed:                ~16 months to peak")

    if 'spx_ret_1d' in events_df.columns:
        avg_return_hikes = events_df[events_df['subtype'].str.contains('Hike', na=False)]['spx_ret_1d'].mean()
        avg_return_cuts = events_df[events_df['subtype'].str.contains('Cut', na=False)]['spx_ret_1d'].mean()

        print(f"\n📈 Market Reactions (1-day SPX returns):")
        print(f"   Average on rate hikes: {avg_return_hikes:.2f}%")
        print(f"   Average on rate cuts:  {avg_return_cuts:.2f}%")

    print("\n" + "="*70)
    print("✅ NARRATIVE COMPLETE")
    print("="*70)
    print("\nThis visualization tells the story of:")
    print("  • The fastest Fed hiking cycle since the 1980s")
    print("  • How markets survived 5+ percentage points of rate hikes")
    print("  • The inflation battle from 9% back to 2%")
    print("  • A complete monetary policy arc in one chart")

def main():
    create_historical_narrative()

if __name__ == "__main__":
    main()