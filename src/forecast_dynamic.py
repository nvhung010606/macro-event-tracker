"""
Dynamic Fed Decision Forecasting System
Integrates real market signals, economic data, and historical patterns
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fredapi import Fred
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

INPUT_FILE = "data/processed/event_panel.parquet"
OUTDIR = "outputs/forecasts"
MARCH_MEETING = datetime(2026, 3, 18)

class DynamicFedForecaster:
    """
    Multi-signal Fed decision forecaster combining:
    1. Historical patterns
    2. Current economic data (inflation, unemployment)
    3. Market signals (yield curve)
    4. Recent Fed actions trend
    """
    
    def __init__(self, fred_api_key=None):
        # Try multiple sources for API key
        self.fred_api_key = (
            fred_api_key or 
            os.getenv("FRED_API_KEY") or
            self._load_from_config()
        )
        
        if self.fred_api_key:
            self.fred = Fred(self.fred_api_key)
        else:
            self.fred = None
            print("⚠️  FRED API key not found - economic data signals will be skipped")
    
    def _load_from_config(self):
        """Try to load API key from config.py"""
        try:
            import sys
            sys.path.insert(0, os.path.dirname(__file__))
            from config import FRED_API_KEY
            return FRED_API_KEY
        except:
            return None
    
    def get_historical_baseline(self, df, lookback_months=6):
        """
        Signal 1: Historical pattern baseline
        Weight: 25%
        """
        cutoff = datetime.now() - timedelta(days=lookback_months * 30)
        recent = df[df["event_date"] >= cutoff].copy()
        
        if len(recent) == 0:
            recent = df.tail(10).copy()
        
        if "subtype" in recent.columns:
            total = len(recent)
            
            maintain = ((recent["subtype"] == "No Change") | 
                       (recent["subtype"] == "FOMC Meeting (No Change)")).sum()
            cut_25 = (recent["subtype"] == "Rate Cut").sum()
            cut_large = (recent["subtype"] == "Rate Cut (Large)").sum()
            hike_25 = (recent["subtype"] == "Rate Hike").sum()
            hike_large = (recent["subtype"] == "Rate Hike (Large)").sum()
            
            probs = {
                "maintain": maintain / total * 100 if total > 0 else 50,
                "cut_25": cut_25 / total * 100 if total > 0 else 25,
                "cut_large": cut_large / total * 100 if total > 0 else 5,
                "hike_25": hike_25 / total * 100 if total > 0 else 15,
                "hike_large": hike_large / total * 100 if total > 0 else 5,
            }
            
            return probs, "Historical pattern (last 6 months)"
        
        return None, None
    
    def get_economic_signals(self):
        """
        Signal 2: Current economic conditions
        Weight: 35%
        
        Uses: Inflation (CPI), Unemployment, GDP growth
        """
        if not self.fred:
            return None, None
        
        signals = {}
        
        try:
            # Get latest inflation (CPI)
            cpi = self.fred.get_series("CPIAUCSL", observation_start="2024-01-01")
            if len(cpi) > 1:
                latest_cpi = cpi.iloc[-1]
                prev_cpi = cpi.iloc[-13] if len(cpi) > 13 else cpi.iloc[0]
                inflation_rate = ((latest_cpi / prev_cpi) - 1) * 100
                signals['inflation'] = inflation_rate
            
            # Get unemployment rate
            unemployment = self.fred.get_series("UNRATE", observation_start="2024-01-01")
            if len(unemployment) > 0:
                signals['unemployment'] = unemployment.iloc[-1]
            
            # Get Fed Funds effective rate (current rate)
            fedfunds = self.fred.get_series("FEDFUNDS", observation_start="2024-01-01")
            if len(fedfunds) > 0:
                signals['current_rate'] = fedfunds.iloc[-1]
            
            # Decision logic based on economic data
            probs = {"maintain": 50, "cut_25": 25, "cut_large": 5, "hike_25": 15, "hike_large": 5}
            explanation = []
            
            # Inflation signal
            if 'inflation' in signals:
                if signals['inflation'] > 3.0:
                    # High inflation → likely maintain or hike
                    probs['maintain'] += 15
                    probs['hike_25'] += 10
                    probs['cut_25'] -= 15
                    probs['cut_large'] -= 10
                    explanation.append(f"High inflation ({signals['inflation']:.1f}%) → hawkish bias")
                elif signals['inflation'] < 2.0:
                    # Low inflation → likely cut
                    probs['cut_25'] += 20
                    probs['cut_large'] += 10
                    probs['maintain'] -= 15
                    probs['hike_25'] -= 15
                    explanation.append(f"Low inflation ({signals['inflation']:.1f}%) → dovish bias")
                else:
                    probs['maintain'] += 10
                    explanation.append(f"Moderate inflation ({signals['inflation']:.1f}%) → neutral")
            
            # Unemployment signal
            if 'unemployment' in signals:
                if signals['unemployment'] > 5.0:
                    # High unemployment → cut likely
                    probs['cut_25'] += 15
                    probs['cut_large'] += 5
                    probs['maintain'] -= 10
                    explanation.append(f"High unemployment ({signals['unemployment']:.1f}%) → dovish")
                elif signals['unemployment'] < 4.0:
                    # Low unemployment → maintain/hike
                    probs['maintain'] += 10
                    probs['hike_25'] += 5
                    explanation.append(f"Low unemployment ({signals['unemployment']:.1f}%) → hawkish")
            
            # Normalize
            total = sum(probs.values())
            probs = {k: max(0, v / total * 100) for k, v in probs.items()}
            
            return probs, " | ".join(explanation)
            
        except Exception as e:
            print(f"⚠️  Could not fetch economic data: {e}")
            return None, None
    
    def get_yield_curve_signal(self):
        """
        Signal 3: Yield curve positioning
        Weight: 20%
        
        Uses: 2-year vs 10-year Treasury spread
        Inverted curve → recession fears → cuts likely
        """
        if not self.fred:
            return None, None
        
        try:
            # Get 2-year and 10-year yields
            y2 = self.fred.get_series("DGS2", observation_start="2024-01-01")
            y10 = self.fred.get_series("DGS10", observation_start="2024-01-01")
            
            if len(y2) > 0 and len(y10) > 0:
                latest_y2 = y2.iloc[-1]
                latest_y10 = y10.iloc[-1]
                spread = latest_y10 - latest_y2
                
                probs = {"maintain": 50, "cut_25": 25, "cut_large": 5, "hike_25": 15, "hike_large": 5}
                
                if spread < -0.5:
                    # Deeply inverted → recession signal → cuts
                    probs['cut_25'] += 25
                    probs['cut_large'] += 15
                    probs['maintain'] -= 20
                    probs['hike_25'] -= 15
                    probs['hike_large'] -= 5
                    explanation = f"Deeply inverted curve ({spread:.2f}%) → recession fears → cuts likely"
                elif spread < 0:
                    # Slightly inverted
                    probs['cut_25'] += 15
                    probs['maintain'] -= 5
                    probs['hike_25'] -= 10
                    explanation = f"Inverted curve ({spread:.2f}%) → slight dovish bias"
                elif spread > 1.0:
                    # Steep curve → economy strong
                    probs['maintain'] += 15
                    probs['hike_25'] += 10
                    probs['cut_25'] -= 15
                    explanation = f"Steep curve ({spread:.2f}%) → economy strong → hawkish"
                else:
                    probs['maintain'] += 5
                    explanation = f"Normal curve ({spread:.2f}%) → neutral"
                
                # Normalize
                total = sum(probs.values())
                probs = {k: max(0, v / total * 100) for k, v in probs.items()}
                
                return probs, explanation
                
        except Exception as e:
            print(f"⚠️  Could not fetch yield data: {e}")
            return None, None
        
        return None, None
    
    def get_recent_trend_signal(self, df):
        """
        Signal 4: Recent Fed momentum
        Weight: 20%
        
        If Fed has been cutting → likely to continue
        If Fed paused → likely to maintain
        """
        recent_3 = df.tail(3)
        
        if "subtype" in recent_3.columns and len(recent_3) >= 2:
            last_action = recent_3.iloc[-1]["subtype"]
            
            probs = {"maintain": 50, "cut_25": 25, "cut_large": 5, "hike_25": 15, "hike_large": 5}
            
            # Count recent actions
            cuts = (recent_3["subtype"].str.contains("Cut", na=False)).sum()
            hikes = (recent_3["subtype"].str.contains("Hike", na=False)).sum()
            maintains = ((recent_3["subtype"] == "No Change") | 
                        (recent_3["subtype"] == "FOMC Meeting (No Change)")).sum()
            
            if cuts >= 2:
                # Cutting cycle
                probs['cut_25'] += 30
                probs['cut_large'] += 10
                probs['maintain'] -= 20
                probs['hike_25'] -= 15
                probs['hike_large'] -= 5
                explanation = f"Cutting cycle (last 3: {cuts} cuts) → continue cutting"
            elif hikes >= 2:
                # Hiking cycle
                probs['hike_25'] += 25
                probs['hike_large'] += 10
                probs['cut_25'] -= 20
                probs['cut_large'] -= 10
                probs['maintain'] -= 5
                explanation = f"Hiking cycle (last 3: {hikes} hikes) → continue hiking"
            elif maintains >= 2:
                # Pause pattern
                probs['maintain'] += 30
                probs['cut_25'] -= 10
                probs['hike_25'] -= 10
                explanation = f"Pause pattern (last 3: {maintains} holds) → stay on hold"
            else:
                # Mixed signals
                probs['maintain'] += 10
                explanation = "Mixed recent actions → maintain likely"
            
            # Normalize
            total = sum(probs.values())
            probs = {k: max(0, v / total * 100) for k, v in probs.items()}
            
            return probs, explanation
        
        return None, None
    
    def combine_signals(self, signals_dict):
        """
        Combine all signals with weights
        """
        weights = {
            'historical': 0.25,
            'economic': 0.35,
            'yield_curve': 0.20,
            'recent_trend': 0.20
        }
        
        combined = {"maintain": 0, "cut_25": 0, "cut_large": 0, "hike_25": 0, "hike_large": 0}
        total_weight = 0
        
        for signal_name, signal_data in signals_dict.items():
            if signal_data['probs'] is not None:
                weight = weights.get(signal_name, 0)
                total_weight += weight
                
                for outcome, prob in signal_data['probs'].items():
                    combined[outcome] += prob * weight
        
        # Normalize
        if total_weight > 0:
            combined = {k: v / total_weight for k, v in combined.items()}
        
        return combined
    
    def forecast(self, df):
        """
        Generate complete forecast with all signals
        """
        print("\n🔮 DYNAMIC FED FORECAST ENGINE")
        print("="*70)
        print("Analyzing multiple data sources...\n")
        
        signals = {}
        
        # Signal 1: Historical
        print("📊 Signal 1: Historical Patterns...")
        hist_probs, hist_exp = self.get_historical_baseline(df)
        if hist_probs:
            signals['historical'] = {'probs': hist_probs, 'explanation': hist_exp, 'weight': 25}
            print(f"   ✓ {hist_exp}")
        
        # Signal 2: Economic data
        print("\n📈 Signal 2: Economic Indicators...")
        econ_probs, econ_exp = self.get_economic_signals()
        if econ_probs:
            signals['economic'] = {'probs': econ_probs, 'explanation': econ_exp, 'weight': 35}
            print(f"   ✓ {econ_exp}")
        else:
            print("   ⚠️  Skipped (no FRED API key)")
        
        # Signal 3: Yield curve
        print("\n📉 Signal 3: Yield Curve...")
        yield_probs, yield_exp = self.get_yield_curve_signal()
        if yield_probs:
            signals['yield_curve'] = {'probs': yield_probs, 'explanation': yield_exp, 'weight': 20}
            print(f"   ✓ {yield_exp}")
        else:
            print("   ⚠️  Skipped (no FRED API key)")
        
        # Signal 4: Recent trend
        print("\n🔄 Signal 4: Recent Fed Momentum...")
        trend_probs, trend_exp = self.get_recent_trend_signal(df)
        if trend_probs:
            signals['recent_trend'] = {'probs': trend_probs, 'explanation': trend_exp, 'weight': 20}
            print(f"   ✓ {trend_exp}")
        
        # Combine all signals
        print("\n⚙️  Combining signals...")
        final_probs = self.combine_signals(signals)
        
        return final_probs, signals

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    
    # Load historical data
    df = pd.read_parquet(INPUT_FILE)
    df["event_date"] = pd.to_datetime(df["event_date"])
    
    # Initialize forecaster
    forecaster = DynamicFedForecaster()
    
    # Generate forecast
    final_probs, signals = forecaster.forecast(df)
    
    # Display results
    print("\n" + "="*70)
    print("🎯 FINAL FORECAST FOR MARCH 18-19, 2026")
    print("="*70)
    
    days_until = (MARCH_MEETING - datetime.now()).days
    print(f"⏰ {days_until} days until meeting\n")
    
    # Sort by probability
    sorted_outcomes = sorted(final_probs.items(), key=lambda x: x[1], reverse=True)
    
    outcome_names = {
        "maintain": "Fed maintains rate",
        "cut_25": "Cut 25bps",
        "cut_large": "Cut >25bps",
        "hike_25": "Hike 25bps",
        "hike_large": "Hike >25bps"
    }
    
    for outcome, prob in sorted_outcomes:
        bar_length = int(prob / 2)
        bar = "█" * bar_length
        print(f"  {outcome_names[outcome]:.<25} {prob:>5.1f}%  {bar}")
    
    # Show signal breakdown
    print("\n" + "="*70)
    print("📋 SIGNAL BREAKDOWN")
    print("="*70)
    
    for signal_name, signal_data in signals.items():
        weight = signal_data.get('weight', 0)
        print(f"\n{signal_name.upper().replace('_', ' ')} (Weight: {weight}%)")
        print(f"  → {signal_data['explanation']}")
        
        top_outcome = max(signal_data['probs'].items(), key=lambda x: x[1])
        print(f"  → This signal favors: {outcome_names[top_outcome[0]]} ({top_outcome[1]:.1f}%)")
    
    # Confidence assessment
    max_prob = max(final_probs.values())
    if max_prob > 70:
        confidence = "HIGH"
        confidence_color = "🟢"
    elif max_prob > 50:
        confidence = "MODERATE"
        confidence_color = "🟡"
    else:
        confidence = "LOW"
        confidence_color = "🔴"
    
    print("\n" + "="*70)
    print(f"{confidence_color} CONFIDENCE: {confidence} (max probability: {max_prob:.1f}%)")
    print("="*70)
    
    # Save forecast
    forecast_df = pd.DataFrame({
        'outcome': [outcome_names[k] for k in final_probs.keys()],
        'probability_pct': list(final_probs.values()),
        'forecast_date': datetime.now(),
        'meeting_date': MARCH_MEETING,
        'method': 'multi_signal_dynamic'
    })
    forecast_df = forecast_df.sort_values('probability_pct', ascending=False)
    forecast_df.to_csv(f"{OUTDIR}/dynamic_forecast_march2026.csv", index=False)
    
    print(f"\n💾 Forecast saved to: {OUTDIR}/dynamic_forecast_march2026.csv")
    
    return final_probs, signals

if __name__ == "__main__":
    main()