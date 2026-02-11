#!/bin/bash
# Fed Tracker Update Script
# Double-click this file to run the full pipeline

echo "======================================================================="
echo "🚀 FED TRACKER UPDATE"
echo "======================================================================="
echo ""
echo "Starting at: $(date)"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Run the pipeline
python3 src/run_pipeline.py

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================================="
    echo "✅ UPDATE COMPLETE!"
    echo "======================================================================="
    echo ""
    echo "📊 Updated files:"
    echo "   • Market data: data/processed/markets_features.parquet"
    echo "   • Fed events: data/raw/events_auto.csv"
    echo "   • Event panel: data/processed/event_panel.parquet"
    echo "   • Plot: outputs/plots/historical_narrative_fed_cycle.png"
    echo ""
    echo "📋 Log: outputs/pipeline_log.txt"
    echo ""
else
    echo ""
    echo "======================================================================="
    echo "⚠️  UPDATE HAD SOME ISSUES"
    echo "======================================================================="
    echo ""
    echo "Check: outputs/pipeline_log.txt for details"
    echo ""
fi

echo "Finished at: $(date)"
echo ""
echo "Press any key to close..."
read -n 1 -s
