"""
Simple 2-Line Chart: Economic Model vs CME Market
Shows what economics say vs what markets say
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib import rcParams, dates as mdates
from scipy.ndimage import gaussian_filter1d
from scipy import interpolate
import sys

sys.path.insert(0, os.path.dirname(__file__))
from forecast_dynamic import DynamicFedForecaster

INPUT_FILE = "data/processed/event_panel.parquet"
OUTDIR = "outputs/forecasts"
MARCH_MEETING = datetime(2026, 3, 18)

def setup_kalshi_style():
    """Kalshi dark theme styling"""
    plt.style.use('dark_background')
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Arial', 'Helvetica']
    rcParams['figure.facecolor'] = '#0a0a0a'
    rcParams['axes.facecolor'] = '#0a0a0a'
    rcParams['axes.edgecolor'] = '#2a2a2a'
    rcParams['grid.color'] = '#1a1a1a'
    rcParams['text.color'] = '#ffffff'
    rcParams['axes.labelcolor'] = '#808080'
    rcParams['xtick.color'] = '#808080'
    rcParams['ytick.color'] = '#808080'

def get_cme_market_data():
    """
    CME Market probabilities
    In production, this would be fetched from CME API
    For now, using latest market consensus
    """
    return {
        'maintain': 79.0,
        'cut_25': 18.0,
        'cut_large': 2.0
    }

def create_two_line_chart(df, economic_probs, cme_probs, output_path):
    """
    Create clean 2-line comparison chart - TOP 3 OUTCOMES ONLY
    Shows the 3 most likely Fed decisions for both models
    """
    setup_kalshi_style()
    
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')
    
    # Filter to past events only
    df_sorted = df.sort_values("event_date").copy()
    today = datetime.now()
    df_sorted = df_sorted[df_sorted["event_date"] < today]
    
    # Use last 12 months
    lookback_date = today - timedelta(days=365)
    df_filtered = df_sorted[df_sorted["event_date"] >= lookback_date]
    
    print(f"\n📅 Chart Data:")
    print(f"   Past events in last 12 months: {len(df_filtered)}")
    
    # Determine top 3 outcomes based on current probabilities
    all_outcomes = {
        'maintain': economic_probs['maintain'],
        'cut_25': economic_probs['cut_25'],
        'cut_large': economic_probs['cut_large'],
        'hike_25': economic_probs['hike_25'],
        'hike_large': economic_probs['hike_large']
    }
    
    # Get top 3
    top_3 = sorted(all_outcomes.items(), key=lambda x: x[1], reverse=True)[:3]
    top_3_keys = [k for k, v in top_3]
    
    print(f"\n   Top 3 Outcomes:")
    for i, (outcome, prob) in enumerate(top_3, 1):
        print(f"   {i}. {outcome}: {prob:.1f}%")
    
    # Calculate economic model evolution for top 3 outcomes only
    dates = []
    economic_data = {k: [] for k in top_3_keys}
    
    forecaster = DynamicFedForecaster()
    
    for i in range(len(df_filtered)):
        event_date = df_filtered.iloc[i]["event_date"]
        historical_data = df_sorted[df_sorted["event_date"] <= event_date]
        
        if len(historical_data) >= 3:
            hist_probs, _ = forecaster.get_historical_baseline(historical_data, lookback_months=6)
            trend_probs, _ = forecaster.get_recent_trend_signal(historical_data)
            
            if hist_probs and trend_probs:
                dates.append(event_date)
                
                # Calculate for each top 3 outcome
                for outcome_key in top_3_keys:
                    value = (hist_probs[outcome_key] * 0.6 + trend_probs[outcome_key] * 0.4)
                    economic_data[outcome_key].append(value)
    
    # Add current forecast
    dates.append(today)
    for outcome_key in top_3_keys:
        economic_data[outcome_key].append(economic_probs[outcome_key])
    
    # CME probabilities for top 3
    cme_data = {
        'maintain': cme_probs['maintain'],
        'cut_25': cme_probs['cut_25'],
        'cut_large': cme_probs['cut_large'],
        'hike_25': cme_probs.get('hike_25', 1.0),
        'hike_large': cme_probs.get('hike_large', 0.0)
    }
    
    print(f"   Data points for plotting: {len(dates)}")
    
    # Colors and labels
    outcome_config = {
        'maintain': {'color': '#10b981', 'label': 'Maintain'},
        'cut_25': {'color': '#3b82f6', 'label': 'Cut 25bps'},
        'cut_large': {'color': '#8b5cf6', 'label': 'Cut >25bps'},
        'hike_25': {'color': '#f97316', 'label': 'Hike 25bps'},
        'hike_large': {'color': '#ef4444', 'label': 'Hike >25bps'}
    }
    
    # Smooth and plot the lines
    if dates and len(dates) > 3:
        dates_num = mdates.date2num(dates)
        dates_smooth = np.linspace(dates_num[0], dates_num[-1], 500)
        dates_smooth_dt = mdates.num2date(dates_smooth)
        
        for outcome_key in top_3_keys:
            config = outcome_config[outcome_key]
            
            # Interpolate and smooth economic model
            f = interpolate.interp1d(dates_num, economic_data[outcome_key], 
                                    kind='linear', fill_value='extrapolate')
            smooth = np.clip(f(dates_smooth), 0, 100)
            smooth = gaussian_filter1d(smooth, sigma=10)
            
            # Plot economic model (solid)
            ax.plot(dates_smooth_dt, smooth, color=config['color'], linewidth=3, 
                   label=f"Economic: {config['label']}", zorder=3, alpha=0.9, linestyle='-')
            
            # Plot CME market (dashed)
            ax.plot(dates_smooth_dt, [cme_data[outcome_key]] * len(dates_smooth_dt), 
                   color=config['color'], linewidth=2.5, linestyle='--',
                   label=f"CME: {config['label']}", zorder=2, alpha=0.7)
            
            # Dot at today
            ax.scatter([today], [economic_probs[outcome_key]], color=config['color'], 
                      s=150, zorder=5, edgecolor='white', linewidth=2.5)
            
            # Percentage labels
            label_x_offset = timedelta(days=-8)
            
            # Economic label (left)
            ax.text(today + label_x_offset, economic_probs[outcome_key], 
                   f"{economic_probs[outcome_key]:.0f}%",
                   color=config['color'], fontsize=11, fontweight='bold',
                   va='center', ha='right')
            
            # CME label (right)
            ax.text(today + timedelta(days=8), cme_data[outcome_key], 
                   f"{cme_data[outcome_key]:.0f}%",
                   color=config['color'], fontsize=11, fontweight='bold',
                   va='center', ha='left')
    
    # Styling
    ax.set_ylim(0, 100)
    ax.tick_params(labelsize=11, colors='#808080')
    
    # X-axis limits - start from first data point, end at March 18 meeting
    if dates:
        start_date = dates[0] - timedelta(days=5)  # Start from first data point
        end_date = MARCH_MEETING + timedelta(days=10)  # Extend to March 18 meeting
        ax.set_xlim(start_date, end_date)
    
    # Grid
    ax.grid(True, alpha=0.1, linestyle='-', linewidth=0.5, color='#404040')
    ax.set_axisbelow(True)
    
    # Y-axis labels
    yticks = [0, 25, 50, 75, 100]
    ax.set_yticks(yticks)
    ax.set_yticklabels([f'{y}%' for y in yticks], fontsize=11)
    
    # Legend (2 columns) - only top 3
    legend = ax.legend(loc='upper left', frameon=True, fontsize=11, ncol=2,
                      facecolor='#1a1a1a', edgecolor='#404040', framealpha=0.95)
    for text in legend.get_texts():
        text.set_color('white')
    
    # X-axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), fontsize=11)
    
    # Vertical line at TODAY
    ax.axvline(today, color='#606060', linestyle='--', 
              linewidth=1.5, alpha=0.3, zorder=1)
    
    # Label for today
    ax.text(today, 105, f'Today\n{today.strftime("%b %d")}', 
           ha='center', va='bottom', color='#808080', fontsize=9,
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a1a1a', 
                    edgecolor='#606060', linewidth=1, alpha=0.9))
    
    # Vertical line at March 18, 2026 (FOMC meeting)
    ax.axvline(MARCH_MEETING, color='white', linestyle='--', 
              linewidth=2, alpha=0.5, zorder=1)
    
    # Label for March 18 meeting
    ax.text(MARCH_MEETING, 105, 'FOMC Meeting\nMar 18, 2026', 
           ha='center', va='bottom', color='white', fontsize=10, fontweight='bold',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a1a', 
                    edgecolor='white', linewidth=1.5, alpha=0.95))
    
    # Title
    ax.text(0.5, 1.06, 'Economic Model vs Market: Top 3 Outcomes', 
           ha='center', va='bottom', transform=ax.transAxes,
           fontsize=18, fontweight='bold', color='white')
    
    subtitle = "Solid lines = Economic fundamentals  •  Dashed lines = Market consensus"
    ax.text(0.5, 1.02, subtitle, 
           ha='center', va='bottom', transform=ax.transAxes,
           fontsize=11, color='#808080', style='italic')
    
    # Explanation box
    explanation = (
        "Showing top 3 most likely\n"
        "Fed decisions:\n\n"
        "SOLID = Economic Model\n"
        "DASHED = CME Market"
    )
    ax.text(0.98, 0.97, explanation, 
           transform=ax.transAxes, ha='right', va='top',
           fontsize=10, color='white',
           bbox=dict(boxstyle='round,pad=0.7', facecolor='#1a1a1a', 
                    edgecolor='#404040', linewidth=1.5, alpha=0.95))
    
    # Remove spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#2a2a2a')
    ax.spines['bottom'].set_color('#2a2a2a')
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='#0a0a0a', 
                edgecolor='none', pad_inches=0.1)
    plt.close()
    
    print(f"\n📊 Top 3 outcomes chart created: {output_path}")

def main():
    """Create simple 2-line comparison"""
    os.makedirs(OUTDIR, exist_ok=True)
    
    print("="*70)
    print("📊 CREATING ECONOMIC vs MARKET COMPARISON CHART")
    print("="*70)
    
    # Load data
    df = pd.read_parquet(INPUT_FILE)
    df["event_date"] = pd.to_datetime(df["event_date"])
    
    # Get economic model forecast
    print("\n📈 Running Economic Model...")
    forecaster = DynamicFedForecaster()
    economic_probs, signals = forecaster.forecast(df)
    
    # Get CME market data
    print("\n💰 Getting CME Market Data...")
    cme_probs = get_cme_market_data()
    
    print(f"\n   Economic Model:")
    print(f"     • Maintain:     {economic_probs['maintain']:.1f}%")
    print(f"     • Cut 25bps:    {economic_probs['cut_25']:.1f}%")
    print(f"     • Cut >25bps:   {economic_probs['cut_large']:.1f}%")
    print(f"     • Hike 25bps:   {economic_probs['hike_25']:.1f}%")
    print(f"     • Hike >25bps:  {economic_probs['hike_large']:.1f}%")
    
    print(f"\n   CME Market:")
    print(f"     • Maintain:     {cme_probs['maintain']:.1f}%")
    print(f"     • Cut 25bps:    {cme_probs['cut_25']:.1f}%")
    print(f"     • Cut >25bps:   {cme_probs['cut_large']:.1f}%")
    print(f"     • Hike 25bps:   {cme_probs.get('hike_25', 1.0):.1f}%")
    print(f"     • Hike >25bps:  {cme_probs.get('hike_large', 0.0):.1f}%")
    
    # Create chart
    output_path = f"{OUTDIR}/economic_vs_market.png"
    create_two_line_chart(df, economic_probs, cme_probs, output_path)
    
    print("\n✅ Chart complete!")
    print(f"\nView: {output_path}")
    print("\n💡 Interpretation:")
    if economic_probs['maintain'] < cme_probs['maintain']:
        print("   Economic fundamentals suggest more dovish than market expects")
        print("   → Market may be pricing in non-economic factors (Fed speeches, sentiment)")
    else:
        print("   Economic fundamentals align with or exceed market hawkishness")
    
    print("="*70)

if __name__ == "__main__":
    main()