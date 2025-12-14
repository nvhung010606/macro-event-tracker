# Macro Event Impact Tracker for Financial Markets

## Overview

This project analyzes how U.S. financial markets react to major macroeconomic events by quantifying cross-asset market movements following official economic releases.

Using daily data for equities (S&P 500), volatility (VIX), and Treasury yields (10Y), the model produces a normalized severity score that measures how unusually large market reactions are on event days relative to historical behavior.

The framework follows an event-study style approach and is designed to be **reproducible**, **transparent**, and **extensible**.

---

## Key Questions Addressed

- Which macroeconomic events move markets the most?
- How do inflation and monetary policy events compare in cross-asset impact?
- Are market reactions typically muted or extreme following major releases?

---

## Data Sources

### Market Data

**FRED API (Federal Reserve Economic Data)**
- S&P 500 index (equities)
- VIX index (volatility)
- 10-year Treasury yield (interest rates)

Market data is pulled programmatically to ensure reproducibility and consistent historical coverage.

### Event Data

**Bureau of Labor Statistics (BLS)**
- Consumer Price Index (CPI) release dates

**Federal Reserve**
- FOMC policy decision dates

Event dates are manually sourced from official government release calendars to avoid reliance on scraped or proprietary datasets.

---

## Methodology

### 1. Market Feature Engineering

For each trading day:
- Compute 1-day and 3-day changes in:
  - S&P 500 returns
  - VIX level changes
  - 10Y Treasury yield changes (basis points)
- Convert changes to absolute magnitudes
- Normalize each series using z-scores

### 2. Severity Score

A composite severity score is calculated as the average of normalized cross-asset reactions:
```
Severity = (z(SPX move) + z(VIX move) + z(10Y move)) / 3
```

Higher scores indicate more unusually large market reactions.

### 3. Event Alignment

- Event dates are joined to daily market data
- Each event inherits its corresponding market reactions and severity scores
- Results are aggregated at both event-level and category-level

---

## Outputs

### Tables

- Event-level rankings of the most market-moving macro events
- Category-level summaries (inflation vs. monetary policy)
- Event study summary with average market reactions per category

### Visualizations

- Distribution of severity scores
- Average severity by event category (with statistical context)

All outputs are generated programmatically and saved to disk.

---

## Project Structure
```
macro-event-tracker/
├── src/
│   ├── load_fred.py        # Pulls market data from FRED
│   ├── features.py         # Computes market reactions & severity scores
│   ├── join_events.py      # Aligns event dates with market data
│   ├── report.py           # Generates summary tables
│   └── plots.py            # Creates publication-quality visualizations
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
│   ├── tables/
│   └── plots/
└── README.md
```

---

## How to Run

### 1. Set FRED API key
```bash
export FRED_API_KEY="YOUR_API_KEY"
```

### 2. Run the full pipeline
```bash
python src/load_fred.py
python src/features.py
python src/join_events.py
python src/report.py
python src/plots.py
```

Outputs will be saved to the `data/processed/` and `outputs/` directories.

---

## Limitations & Extensions

### Current Limitations

- The model is **descriptive**, not predictive
- Event coverage currently focuses on CPI and FOMC decisions
- Severity scores capture magnitude, not direction (risk-on vs risk-off)

### Potential Extensions

- Adding labor market releases (NFP)
- Incorporating surprise metrics (actual − expected)
- Rolling or expanding normalization to remove look-ahead bias
- Directional labeling of market reactions

---

## Tools & Libraries

- Python
- Pandas
- Matplotlib
- NumPy
- FRED API

---

## Author

**Viet Hung Nguyen**  
University of South Florida  
Finance & Analytics

---

## License

This project is open source and available for academic and educational purposes.
