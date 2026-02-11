#!/bin/bash
# Automation Setup Script
# Sets up cron jobs for automated market data updates

echo "======================================================================="
echo "🤖 MACRO EVENT TRACKER - AUTOMATION SETUP"
echo "======================================================================="
echo ""

# Get the absolute path to this project
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH=$(which python3 || which python)

echo "📍 Project directory: $PROJECT_DIR"
echo "🐍 Python path: $PYTHON_PATH"
echo ""

# Check if Python is available
if [ -z "$PYTHON_PATH" ]; then
    echo "❌ ERROR: Python not found!"
    echo "   Please install Python 3 and try again."
    exit 1
fi

# Check for required packages
echo "🔍 Checking required packages..."
$PYTHON_PATH -c "import yfinance" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  yfinance not installed"
    echo "   Install with: pip install yfinance"
fi

$PYTHON_PATH -c "import fredapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  fredapi not installed"
    echo "   Install with: pip install fredapi"
fi

echo ""
echo "======================================================================="
echo "CRON JOB OPTIONS"
echo "======================================================================="
echo ""
echo "Choose your automation level:"
echo ""
echo "1. DAILY UPDATES (Recommended)"
echo "   • Market data updates daily at 6:00 PM ET (after market close)"
echo "   • Full pipeline runs on FOMC meeting days"
echo ""
echo "2. WEEKLY UPDATES"
echo "   • Market data updates every Monday at 6:00 PM ET"
echo "   • Full pipeline runs on FOMC meeting days"
echo ""
echo "3. MANUAL ONLY"
echo "   • No automatic updates"
echo "   • Run 'python src/run_pipeline.py' manually when needed"
echo ""
read -p "Enter your choice (1, 2, or 3): " choice

if [ "$choice" = "1" ]; then
    # Daily updates
    CRON_SCHEDULE="0 18 * * *"  # Daily at 6 PM
    DESCRIPTION="daily at 6:00 PM ET"
elif [ "$choice" = "2" ]; then
    # Weekly updates
    CRON_SCHEDULE="0 18 * * 1"  # Monday at 6 PM
    DESCRIPTION="weekly (Mondays) at 6:00 PM ET"
elif [ "$choice" = "3" ]; then
    echo ""
    echo "✅ Manual mode selected"
    echo ""
    echo "To run updates manually:"
    echo "  cd $PROJECT_DIR"
    echo "  python src/run_pipeline.py"
    echo ""
    exit 0
else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi

# Create the cron command
CRON_CMD="cd $PROJECT_DIR && $PYTHON_PATH src/run_pipeline.py >> outputs/pipeline_log.txt 2>&1"

# Check if cron job already exists
existing_cron=$(crontab -l 2>/dev/null | grep -F "macro-event-tracker")

if [ ! -z "$existing_cron" ]; then
    echo ""
    echo "⚠️  Existing cron job found:"
    echo "   $existing_cron"
    echo ""
    read -p "Replace it? (y/n): " replace
    if [ "$replace" != "y" ]; then
        echo "❌ Cancelled"
        exit 0
    fi
    # Remove existing job
    (crontab -l 2>/dev/null | grep -v "macro-event-tracker") | crontab -
fi

# Add new cron job
echo ""
echo "📝 Adding cron job..."
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_CMD  # macro-event-tracker") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ SUCCESS!"
    echo ""
    echo "======================================================================="
    echo "AUTOMATION CONFIGURED"
    echo "======================================================================="
    echo ""
    echo "📅 Schedule: Updates $DESCRIPTION"
    echo "📂 Project: $PROJECT_DIR"
    echo "📋 Logs: $PROJECT_DIR/outputs/pipeline_log.txt"
    echo ""
    echo "What happens automatically:"
    echo "  1. Market data (SPX, VIX, yields) updated"
    echo "  2. Fed events detected from FRED"
    echo "  3. Events joined with market reactions"
    echo "  4. Historical plots regenerated"
    echo "  5. Forecasts updated (when meeting is within 60 days)"
    echo ""
    echo "To view your cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To remove automation:"
    echo "  crontab -e"
    echo "  (then delete the line with 'macro-event-tracker')"
    echo ""
    echo "To run manually right now:"
    echo "  python src/run_pipeline.py"
    echo ""
    echo "To check logs:"
    echo "  tail -f outputs/pipeline_log.txt"
    echo ""
else
    echo "❌ ERROR: Could not set up cron job"
    echo "   You may need to grant cron permissions in System Preferences"
    echo "   (macOS: System Preferences > Security & Privacy > Privacy > Full Disk Access)"
fi
