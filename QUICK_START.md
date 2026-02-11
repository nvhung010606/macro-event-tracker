# 🎯 Quick Start Guide - Manual Updates

Your Fed Tracker is ready! Here's how to use it.

---

## 📦 **One-Time Setup**

### 1. Install Required Packages
```bash
pip install yfinance fredapi pandas matplotlib
```

### 2. Set FRED API Key (Optional but Recommended)
```bash
export FRED_API_KEY="your_key_here"
```
Or add it to `src/config.py`:
```python
FRED_API_KEY = "your_key_here"
```

Get a free API key: https://fred.stlouisfed.org/docs/api/api_key.html

---

## 🚀 **How to Update Everything**

### **Method 1: Double-Click (Easiest)** 👆
1. Double-click `UPDATE_FED_TRACKER.command`
2. Wait for it to finish
3. That's it!

### **Method 2: Terminal**
```bash
cd /Users/nguyenviethung/Desktop/macro-event-tracker
python src/run_pipeline.py
```

---

## 📅 **When to Run Updates**

### **After FOMC Meetings:**
Run the update script after each Federal Reserve decision:

**2026 FOMC Schedule:**
- ✅ Jan 28, 2026
- ⏰ **Mar 18, 2026** ← Next meeting
- Apr 29, 2026
- Jun 17, 2026
- Jul 29, 2026
- Sep 16, 2026
- Oct 28, 2026
- Dec 16, 2026

**Timeline:**
- **2:00 PM:** Fed announces decision
- **After 6:00 PM:** Run your update script (after market close)
- **Next day:** Check your updated plots!

### **Optional: Weekly Updates**
Run every Monday evening to keep market data current.

---

## 📊 **What Gets Updated**

When you run the update:

1. ✅ **Market Data** - Latest SPX, VIX, Treasury yields
2. ✅ **Fed Events** - Detects any new rate changes
3. ✅ **Event Analysis** - Joins events with market reactions
4. ✅ **Historical Plot** - Regenerates with new data
5. ✅ **Forecasts** - Updates probabilities for next meeting

---

## 🔍 **Check Your Results**

### **Main Visualization:**
```
outputs/plots/historical_narrative_fed_cycle.png
```
Open this file to see your complete Fed cycle story!

### **Data Files:**
- `data/raw/events_auto.csv` - All FOMC events
- `data/processed/event_panel.parquet` - Events + market reactions
- `outputs/pipeline_log.txt` - Update history

### **Forecasts:**
```bash
python src/forecast_dynamic.py
```
See probability forecast for next FOMC meeting.

---

## 🛠️ **Individual Components**

If you want to run specific parts only:

### **Update Just Market Data:**
```bash
python src/update_market_data.py
```

### **Update Just Fed Events:**
```bash
python src/load_fed_events_hybrid.py
```

### **Regenerate Plot Only:**
```bash
python src/plot_historical_narrative.py
```

### **Run Forecast Only:**
```bash
python src/forecast_dynamic.py
```

---

## 📋 **Example Workflow**

### **March 18, 2026 (FOMC Day)**

**Before the meeting:**
```bash
python src/forecast_dynamic.py
# See: "62% maintain, 22% cut 25bps, ..."
```

**After 6 PM (after market close):**
```bash
# Double-click: UPDATE_FED_TRACKER.command
# Or run: python src/run_pipeline.py
```

**Next morning:**
```bash
# Open: outputs/plots/historical_narrative_fed_cycle.png
# See the March 18 decision + market reaction!
```

---

## 🎯 **Quick Commands Cheat Sheet**

```bash
# Full update (recommended after FOMC)
python src/run_pipeline.py

# Just update market data
python src/update_market_data.py

# View forecast
python src/forecast_dynamic.py

# Check logs
tail -20 outputs/pipeline_log.txt

# Open main plot
open outputs/plots/historical_narrative_fed_cycle.png
```

---

## ⚡ **Pro Tips**

1. **Create a Desktop Alias:**
   - Drag `UPDATE_FED_TRACKER.command` to your Desktop
   - Hold ⌘+Option while dragging to create an alias
   - Now you have a desktop shortcut!

2. **Set Calendar Reminders:**
   - Add FOMC meeting dates to your calendar
   - Set reminder: "Update Fed Tracker"

3. **Check Logs:**
   - If something goes wrong, check `outputs/pipeline_log.txt`
   - Shows exactly what happened

4. **Validate Results:**
   ```bash
   python -c "import pandas as pd; df = pd.read_parquet('data/processed/markets_features.parquet'); print(f'Latest data: {df[\"date\"].max()}')"
   ```

---

## 🔧 **Troubleshooting**

### **"No module named 'yfinance'"**
```bash
pip install yfinance fredapi
```

### **"FRED API key not found"**
Either:
- Set environment variable: `export FRED_API_KEY="your_key"`
- Or add to `src/config.py`

### **"Permission denied"**
```bash
chmod +x UPDATE_FED_TRACKER.command
```

### **Market data not updating?**
Check your internet connection and run:
```bash
python src/update_market_data.py
```

---

## ✅ **You're All Set!**

Your system is production-ready with manual control:

- ✅ No security concerns
- ✅ Full transparency
- ✅ Run when YOU want
- ✅ Simple double-click operation

**Just double-click `UPDATE_FED_TRACKER.command` after FOMC meetings!** 🎉
