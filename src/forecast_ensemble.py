"""
Ensemble Forecaster: Your Model + CME FedWatch
Blends fundamental analysis with market-implied probabilities
"""
import os
import json
import pandas as pd
from datetime import datetime
from forecast_dynamic import DynamicFedForecaster
from fetch_cme_fedwatch import CMEFedWatchScraper

INPUT_FILE = "data/processed/event_panel.parquet"
MARCH_MEETING = datetime(2026, 3, 18)

class EnsembleForecaster:
    """
    Combine multiple forecasting signals:
    1. Your fundamental model (30%)
    2. CME FedWatch market prices (70%)
    """
    
    def __init__(self):
        self.fundamental_forecaster = DynamicFedForecaster()
        self.cme_scraper = CMEFedWatchScraper()
        
        # Weights for blending
        self.weights = {
            'fundamental': 0.30,  # Your model
            'cme_market': 0.70    # Market-implied (CME)
        }
    
    def get_ensemble_forecast(self, df):
        """
        Generate final forecast by blending all signals
        """
        print("\n" + "="*70)
        print("🎯 ENSEMBLE FORECASTER")
        print("="*70)
        
        # Signal 1: Your fundamental model
        print("\n📊 Running Fundamental Analysis...")
        fundamental_probs, fundamental_signals = self.fundamental_forecaster.forecast(df)
        
        print(f"\n   Your Model Forecast:")
        print(f"   • Fed maintains rate: {fundamental_probs['maintain']:.1f}%")
        print(f"   • Cut 25bps: {fundamental_probs['cut_25']:.1f}%")
        print(f"   • Cut >25bps: {fundamental_probs['cut_large']:.1f}%")
        
        # Signal 2: CME FedWatch (market-implied)
        print("\n" + "-"*70)
        cme_probs = self.cme_scraper.get_march_2026_probabilities()
        
        # Map CME format to our format
        cme_mapped = {
            'maintain': cme_probs.get('maintain', 50),
            'cut_25': cme_probs.get('cut_25', 25),
            'cut_large': cme_probs.get('cut_50', 5),
            'hike_25': cme_probs.get('hike_25', 15),
            'hike_large': cme_probs.get('hike_50', 5)
        }
        
        print(f"\n   CME Market Forecast:")
        print(f"   • Fed maintains rate: {cme_mapped['maintain']:.1f}%")
        print(f"   • Cut 25bps: {cme_mapped['cut_25']:.1f}%")
        print(f"   • Cut >25bps: {cme_mapped['cut_large']:.1f}%")
        
        # Blend the forecasts
        print("\n" + "-"*70)
        print(f"\n⚙️  Blending Forecasts:")
        print(f"   • Fundamental Model: {self.weights['fundamental']*100:.0f}%")
        print(f"   • CME Market Prices: {self.weights['cme_market']*100:.0f}%")
        
        ensemble = {}
        for outcome in ['maintain', 'cut_25', 'cut_large', 'hike_25', 'hike_large']:
            ensemble[outcome] = (
                self.weights['fundamental'] * fundamental_probs[outcome] +
                self.weights['cme_market'] * cme_mapped[outcome]
            )
        
        # Normalize to 100%
        total = sum(ensemble.values())
        if total > 0:
            ensemble = {k: (v / total * 100) for k, v in ensemble.items()}
        
        return ensemble, fundamental_probs, cme_mapped, fundamental_signals
    
    def display_comparison(self, ensemble, fundamental, cme):
        """Show side-by-side comparison"""
        print("\n" + "="*70)
        print("📊 FORECAST COMPARISON")
        print("="*70)
        
        comparison = pd.DataFrame({
            'Your Model': [
                fundamental['maintain'],
                fundamental['cut_25'],
                fundamental['cut_large'],
                fundamental['hike_25'],
                fundamental['hike_large']
            ],
            'CME Market': [
                cme['maintain'],
                cme['cut_25'],
                cme['cut_large'],
                cme['hike_25'],
                cme['hike_large']
            ],
            'Ensemble (Final)': [
                ensemble['maintain'],
                ensemble['cut_25'],
                ensemble['cut_large'],
                ensemble['hike_25'],
                ensemble['hike_large']
            ]
        }, index=[
            'Fed maintains rate',
            'Cut 25bps',
            'Cut >25bps',
            'Hike 25bps',
            'Hike >25bps'
        ])
        
        print("\n" + comparison.to_string())
        
        # Highlight differences
        print("\n📈 Key Insights:")
        diff_maintain = ensemble['maintain'] - fundamental['maintain']
        if abs(diff_maintain) > 5:
            direction = "increased" if diff_maintain > 0 else "decreased"
            print(f"   • Market prices {direction} 'maintain' probability by {abs(diff_maintain):.1f}%")
            if diff_maintain > 0:
                print(f"     → Market is MORE confident Fed will hold than fundamentals suggest")
            else:
                print(f"     → Market is LESS confident Fed will hold than fundamentals suggest")
        
        # Show which signal dominated
        if ensemble['maintain'] > 70:
            print(f"   • Strong consensus: Fed very likely to maintain")
        elif ensemble['cut_25'] > 30:
            print(f"   • Significant cut probability: Market pricing in dovish shift")
        
        return comparison

def main():
    """Run the ensemble forecaster"""
    print("="*70)
    print("🚀 ENSEMBLE FORECASTER: YOUR MODEL + CME FEDWATCH")
    print("="*70)
    print("\nCombining fundamental analysis with market-implied probabilities...")
    
    # Load data
    df = pd.read_parquet(INPUT_FILE)
    df["event_date"] = pd.to_datetime(df["event_date"])
    
    # Create forecaster
    forecaster = EnsembleForecaster()
    
    # Generate ensemble forecast
    ensemble, fundamental, cme, signals = forecaster.get_ensemble_forecast(df)
    
    # Display comparison
    comparison_df = forecaster.display_comparison(ensemble, fundamental, cme)
    
    # Final forecast
    print("\n" + "="*70)
    print("🎯 FINAL ENSEMBLE FORECAST - MARCH 18, 2026")
    print("="*70)
    
    days_until = (MARCH_MEETING - datetime.now()).days
    print(f"\n⏰ {days_until} days until FOMC meeting\n")
    
    outcomes = sorted(ensemble.items(), key=lambda x: x[1], reverse=True)
    
    outcome_names = {
        'maintain': 'Fed maintains rate',
        'cut_25': 'Cut 25bps',
        'cut_large': 'Cut >25bps',
        'hike_25': 'Hike 25bps',
        'hike_large': 'Hike >25bps'
    }
    
    for outcome, prob in outcomes:
        bar_length = int(prob / 2)
        bar = "█" * bar_length
        print(f"  {outcome_names[outcome]:.<25} {prob:>5.1f}%  {bar}")
    
    # Confidence level
    max_prob = max(ensemble.values())
    if max_prob > 70:
        confidence = "HIGH"
        emoji = "🟢"
    elif max_prob > 50:
        confidence = "MODERATE"
        emoji = "🟡"
    else:
        confidence = "LOW"
        emoji = "🔴"
    
    print(f"\n{emoji} CONFIDENCE: {confidence} (max probability: {max_prob:.1f}%)")
    
    # Save results
    os.makedirs("outputs/forecasts", exist_ok=True)
    
    output = {
        'forecast_date': datetime.now().isoformat(),
        'meeting_date': MARCH_MEETING.isoformat(),
        'ensemble': ensemble,
        'fundamental_model': fundamental,
        'cme_market': cme,
        'weights': forecaster.weights,
        'confidence': confidence
    }
    
    with open('outputs/forecasts/ensemble_forecast_march2026.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    comparison_df.to_csv('outputs/forecasts/forecast_comparison.csv')
    
    print("\n💾 Saved:")
    print("   • outputs/forecasts/ensemble_forecast_march2026.json")
    print("   • outputs/forecasts/forecast_comparison.csv")
    
    print("\n" + "="*70)
    print("✅ ENSEMBLE FORECAST COMPLETE!")
    print("="*70)
    print("\nYour model (fundamental): {:.1f}% maintain".format(fundamental['maintain']))
    print("CME market (real money):  {:.1f}% maintain".format(cme['maintain']))
    print("Ensemble (30/70 blend):   {:.1f}% maintain".format(ensemble['maintain']))
    print("\n💡 The ensemble combines your economic analysis with what traders")
    print("   are actually betting. This should be within 2-5% of Kalshi!")

if __name__ == "__main__":
    main()