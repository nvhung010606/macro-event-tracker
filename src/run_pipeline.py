"""
Full Pipeline Orchestrator
Runs the complete macro-event-tracker pipeline
Use this after FOMC meetings to update everything automatically
"""
import subprocess
import sys
import os
from datetime import datetime
import pandas as pd

# Configuration
LOG_FILE = "outputs/pipeline_log.txt"

def log(message):
    """Log to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)

    # Append to log file
    os.makedirs("outputs", exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + "\n")

def run_script(script_name, description):
    """Run a Python script and capture output"""
    log(f"\n{'='*70}")
    log(f"▶️  Running: {description}")
    log(f"{'='*70}")

    try:
        result = subprocess.run(
            [sys.executable, f"src/{script_name}"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            log(f"✅ {description} - SUCCESS")
            return True
        else:
            log(f"❌ {description} - FAILED")
            if result.stderr:
                log(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        log(f"⏱️  {description} - TIMEOUT (>5 minutes)")
        return False
    except Exception as e:
        log(f"❌ {description} - ERROR: {e}")
        return False

def get_next_fomc_meeting():
    """Get the next FOMC meeting date"""
    # Load known FOMC dates
    fomc_dates = [
        # 2026
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
        "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-16",
        # 2027 (add more as needed)
        "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-16",
    ]

    today = pd.Timestamp.now()
    future_meetings = [pd.Timestamp(d) for d in fomc_dates if pd.Timestamp(d) > today]

    if future_meetings:
        return future_meetings[0]
    return None

def main():
    """Run the complete pipeline"""
    log("\n" + "="*70)
    log("🚀 AUTOMATED PIPELINE EXECUTION")
    log("="*70)
    log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Step 1: Update market data
    results['market_data'] = run_script(
        "update_market_data.py",
        "Step 1: Update market data (SPX, VIX, yields)"
    )

    if not results['market_data']:
        log("\n⚠️  Market data update failed - continuing anyway...")

    # Step 2: Update Fed events
    results['fed_events'] = run_script(
        "load_fed_events_hybrid.py",
        "Step 2: Detect Fed events and rate changes"
    )

    # Step 3: Join events with market data
    results['join_data'] = run_script(
        "join_events_updated.py",
        "Step 3: Join events with market data"
    )

    # Step 4: Generate historical narrative plot
    results['plot_narrative'] = run_script(
        "plot_historical_narrative.py",
        "Step 4: Generate historical narrative visualization"
    )

    # Step 5: Update forecasts (optional - only if next meeting is soon)
    next_meeting = get_next_fomc_meeting()
    if next_meeting:
        days_until = (next_meeting - pd.Timestamp.now()).days
        log(f"\n📅 Next FOMC meeting: {next_meeting.date()} ({days_until} days)")

        if days_until <= 60:  # Update forecast if meeting is within 60 days
            log("🔮 Running forecast update...")
            results['forecast'] = run_script(
                "forecast_dynamic.py",
                "Step 5: Update forecast for next FOMC meeting"
            )

    # Summary
    log("\n" + "="*70)
    log("📊 PIPELINE SUMMARY")
    log("="*70)

    total = len(results)
    success = sum(1 for r in results.values() if r)

    for step, status in results.items():
        emoji = "✅" if status else "❌"
        log(f"{emoji} {step.replace('_', ' ').title()}: {'SUCCESS' if status else 'FAILED'}")

    log(f"\n🎯 Overall: {success}/{total} steps completed successfully")

    if success == total:
        log("✅ PIPELINE COMPLETE - ALL SYSTEMS OPERATIONAL")
        return 0
    elif success >= total * 0.75:
        log("⚠️  PIPELINE COMPLETE - SOME WARNINGS")
        return 0
    else:
        log("❌ PIPELINE FAILED - CRITICAL ERRORS")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
