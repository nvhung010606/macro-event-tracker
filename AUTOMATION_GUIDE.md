# 🤖 Full Automation Guide

Your macro-event-tracker is now **fully automated**! Here's everything you need to know.

---

## 🚀 Quick Start

### **1. Install Required Packages**

```bash
pip install yfinance fredapi pandas
```

### **2. Set Up Automation**

```bash
./setup_automation.sh
```

Choose your schedule:
- **Daily** (Recommended) - Updates every day at 6 PM
- **Weekly** - Updates every Monday at 6 PM
- **Manual** - No automation, run manually

### **3. You're Done!**

The system will now automatically:
- ✅ Fetch daily market data (SPX, VIX, yields)
- ✅ Detect Fed rate changes from FRED
- ✅ Join events with market reactions
- ✅ Regenerate historical plots
- ✅ Update forecasts before FOMC meetings

---

## 📋 What Gets Automated

### **Daily (at 6 PM ET)**
```
1. Update market data → markets_features.parquet
2. Detect new Fed events → events_auto.csv
3. Join with market data → event_panel.parquet
4. Regenerate plots → historical_narrative_fed_cycle.png
5. Update forecasts (if meeting within 60 days)
```

### **After FOMC Meeting (March 18, 2026)**
When the Fed releases a decision:
1. System detects rate change from FRED automatically
2. Captures market reaction (SPX, VIX movements that day)
3. Updates historical plot with new data point
4. Shifts forecast to next meeting (April 29, 2026)

---

## 🎮 Manual Controls

### **Run Full Pipeline Now**
```bash
python src/run_pipeline.py
```

### **Update Just Market Data**
```bash
python src/update_market_data.py
```

### **Check What's Scheduled**
```bash
crontab -l
```

### **View Logs**
```bash
tail -f outputs/pipeline_log.txt
```

### **Remove Automation**
```bash
crontab -e
# Delete the line with 'macro-event-tracker'
```

---

## 📊 How It Works

### **Market Data Updates**
- **Source:** Yahoo Finance (SPX, VIX) + FRED (yields)
- **Frequency:** Daily at 6 PM ET
- **Storage:** `data/processed/markets_features.parquet`
- **Features Calculated:**
  - 1-day, 5-day, 30-day returns
  - VIX changes
  - Yield changes (basis points)
  - Market severity scores

### **Fed Event Detection**
- **Source:** FRED `FEDFUNDS` series
- **Method:** Compares rate changes to known FOMC dates
- **Storage:** `data/raw/events_auto.csv`
- **Classifies:**
  - Rate hikes (small <50bps, large ≥50bps)
  - Rate cuts (small <50bps, large ≥50bps)
  - No change (hold)

### **Forecast Updates**
- **Trigger:** When FOMC meeting is within 60 days
- **Uses:** 4 real-time signals (historical, economic, yield curve, momentum)
- **Auto-updates:** Shifts to next meeting after current one passes
- **Output:** Probability distribution for next decision

---

## 🔧 Troubleshooting

### **Cron Job Not Running?**

**Check permissions (macOS):**
```bash
System Preferences > Security & Privacy > Privacy > Full Disk Access
```
Add Terminal/iTerm to allowed apps.

**Check cron is working:**
```bash
crontab -l  # Should show your job
grep CRON /var/log/system.log  # Check for errors
```

### **Market Data Not Updating?**

**Missing packages:**
```bash
pip install yfinance fredapi
```

**FRED API key not set:**
```bash
export FRED_API_KEY="your_key_here"
# Or add to src/config.py
```

### **Forecast Not Updating to Next Meeting?**

The forecast automatically shifts to the next meeting when:
- Current meeting date has passed
- Next meeting is within 60 days

To force update:
```bash
python src/forecast_dynamic.py
```

---

## 📅 FOMC Meeting Schedule (2026)

The system knows about these dates:
- ✅ Jan 28, 2026
- ✅ **Mar 18, 2026** ← Next meeting
- ✅ Apr 29, 2026
- ✅ Jun 17, 2026
- ✅ Jul 29, 2026
- ✅ Sep 16, 2026
- ✅ Oct 28, 2026
- ✅ Dec 16, 2026

To add 2027 dates, edit: `src/run_pipeline.py` → `get_next_fomc_meeting()`

---

## 🎯 Example Timeline

### **March 17, 2026 (Day Before Meeting)**
```
6:00 PM: Cron job runs
  → Updates market data
  → Forecast shows: "62% maintain, 22% cut 25bps"
  → Historical plot up to March 17
```

### **March 18, 2026 (FOMC Day)**
```
2:00 PM: Fed announces decision (cut 25bps)
6:00 PM: Cron job runs
  → Detects rate cut from FRED
  → Captures market reaction (SPX +1.2%, VIX -3 points)
  → Updates historical plot with new data point
  → Forecast shifts to April 29, 2026 meeting
```

### **March 19, 2026 (Day After)**
```
You check the plots:
  ✅ Historical narrative shows March 18 cut
  ✅ Market reaction captured
  ✅ Forecast now targets April 29 meeting
```

---

## 🛠️ Files Reference

**Automation Scripts:**
- `src/update_market_data.py` - Fetches SPX, VIX, yields
- `src/run_pipeline.py` - Orchestrates full pipeline
- `setup_automation.sh` - Cron job installer

**Core Pipeline:**
- `src/load_fed_events_hybrid.py` - Detects Fed events
- `src/join_events_updated.py` - Joins events + markets
- `src/plot_historical_narrative.py` - Generates plot
- `src/forecast_dynamic.py` - Forecasts next meeting

**Data Files:**
- `data/raw/events_auto.csv` - Detected FOMC events
- `data/processed/markets_features.parquet` - Daily market data
- `data/processed/event_panel.parquet` - Events + reactions
- `outputs/plots/historical_narrative_fed_cycle.png` - Main viz
- `outputs/pipeline_log.txt` - Automation logs

---

## 💡 Pro Tips

1. **First Run:** Run `python src/run_pipeline.py` manually once to verify everything works

2. **Check Logs Regularly:** `tail -20 outputs/pipeline_log.txt` to see latest runs

3. **FRED API Key:** Set it up for real-time economic data:
   ```bash
   export FRED_API_KEY="your_key_here"
   ```

4. **Manual Override:** You can always run scripts individually if needed

5. **Data Validation:** Check `data/processed/markets_features.parquet` date range matches current date

---

## ✅ Success Checklist

- [ ] yfinance and fredapi installed
- [ ] Automation script run (`./setup_automation.sh`)
- [ ] Cron job visible (`crontab -l`)
- [ ] Manual test successful (`python src/run_pipeline.py`)
- [ ] Log file created (`outputs/pipeline_log.txt`)
- [ ] Market data updated (check latest date in parquet)
- [ ] Historical plot generated

**You're all set! The system is now fully autonomous.** 🎉
