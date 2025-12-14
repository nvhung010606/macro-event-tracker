import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

INPUT_FILE = "data/processed/event_panel.parquet"
OUTDIR = "outputs/plots"

# Scientific plot styling
def setup_scientific_style():
    """Configure matplotlib for publication-quality figures."""
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    rcParams['font.size'] = 10
    rcParams['axes.labelsize'] = 11
    rcParams['axes.titlesize'] = 12
    rcParams['axes.titleweight'] = 'bold'
    rcParams['xtick.labelsize'] = 9
    rcParams['ytick.labelsize'] = 9
    rcParams['legend.fontsize'] = 9
    rcParams['figure.titlesize'] = 13
    rcParams['axes.linewidth'] = 1.2
    rcParams['grid.linewidth'] = 0.5
    rcParams['lines.linewidth'] = 1.5
    rcParams['patch.linewidth'] = 0.8
    rcParams['xtick.major.width'] = 1.2
    rcParams['ytick.major.width'] = 1.2
    rcParams['xtick.minor.width'] = 0.8
    rcParams['ytick.minor.width'] = 0.8

def _normal_pdf(x: np.ndarray, mu: float, sd: float) -> np.ndarray:
    return (1.0 / (sd * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sd) ** 2)

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    setup_scientific_style()

    df = pd.read_parquet(INPUT_FILE).dropna(subset=["severity"]).copy()
    sev = df["severity"].astype(float)

    # ---------------------------
    # Plot 1: Severity distribution (enhanced scientific style)
    # ---------------------------
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
    ax.set_facecolor('#F8F9FA')
    
    # Histogram with professional color
    n, bins, patches = ax.hist(
        sev, 
        bins=30, 
        density=True, 
        alpha=0.7,
        color='#2E86AB',
        edgecolor='#1A5276', 
        linewidth=0.8
    )

    mu = float(sev.mean())
    med = float(sev.median())
    sd = float(sev.std(ddof=1))

    # Reference lines with distinct colors
    ax.axvline(
        mu, 
        color='#E63946', 
        linestyle='--', 
        linewidth=2.0, 
        label=f'Mean = {mu:.3f}',
        alpha=0.8
    )
    ax.axvline(
        med, 
        color='#F77F00', 
        linestyle=':', 
        linewidth=2.0, 
        label=f'Median = {med:.3f}',
        alpha=0.8
    )

    # Normal overlay with smooth curve
    if sd > 0 and np.isfinite(sd):
        x = np.linspace(sev.min(), sev.max(), 500)
        ax.plot(
            x, 
            _normal_pdf(x, mu, sd), 
            color='#06A77D',
            linewidth=2.5, 
            label='Normal fit',
            alpha=0.9
        )

    ax.set_title(
        'Event Severity Score Distribution', 
        pad=15, 
        fontweight='bold',
        fontsize=13
    )
    ax.set_xlabel('Severity Score (z-normalized composite)', fontweight='semibold')
    ax.set_ylabel('Probability Density', fontweight='semibold')
    
    # Enhanced grid
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.4, color='gray')
    ax.grid(True, which='minor', linestyle=':', linewidth=0.3, alpha=0.2, color='gray')
    ax.minorticks_on()
    
    # Professional legend
    ax.legend(
        frameon=True, 
        fancybox=True, 
        shadow=True, 
        framealpha=0.95,
        loc='best',
        edgecolor='gray'
    )
    
    # Spine styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['bottom'].set_linewidth(1.2)
    
    fig.tight_layout()
    fig.savefig(f"{OUTDIR}/severity_distribution.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # ---------------------------
    # Plot 2: Mean severity by category (enhanced)
    # ---------------------------
    stats = (
        df.groupby("category")["severity"]
        .agg(n="count", mean="mean", sd=lambda x: x.std(ddof=1))
        .reset_index()
    )
    stats["se"] = stats["sd"] / np.sqrt(stats["n"])
    stats["ci95"] = 1.96 * stats["se"]
    stats = stats.sort_values("mean", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    ax.set_facecolor('#F8F9FA')

    y = np.arange(len(stats))
    
    # Color-coded points based on severity
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(stats)))
    
    for i, (idx, row) in enumerate(stats.iterrows()):
        ax.errorbar(
            row["mean"],
            y[i],
            xerr=row["ci95"] if pd.notna(row["ci95"]) else 0,
            fmt='o',
            color=colors[i],
            ecolor=colors[i],
            capsize=4,
            capthick=1.5,
            elinewidth=1.8,
            markersize=8,
            markeredgewidth=1.2,
            markeredgecolor='white',
            alpha=0.85
        )

    # Zero reference line
    ax.axvline(0, color='#2C3E50', linewidth=1.5, linestyle='-', alpha=0.5, zorder=0)
    
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{c} (n={int(n)})" for c, n in zip(stats["category"], stats["n"])],
        fontsize=10
    )
    
    ax.set_title(
        'Average Severity by Category (Mean ± 95% CI)', 
        pad=15, 
        fontweight='bold',
        fontsize=13
    )
    ax.set_xlabel('Mean Severity Score', fontweight='semibold')
    ax.set_ylabel('Event Category', fontweight='semibold')
    
    # Enhanced grid
    ax.grid(True, axis='x', linestyle='--', linewidth=0.6, alpha=0.4, color='gray')
    ax.grid(True, axis='x', which='minor', linestyle=':', linewidth=0.3, alpha=0.2, color='gray')
    ax.minorticks_on()
    
    # Spine styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['bottom'].set_linewidth(1.2)

    fig.tight_layout()
    fig.savefig(f"{OUTDIR}/avg_severity_by_category.png", dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    print("✓ Saved enhanced scientific plots:")
    print(f"  → {OUTDIR}/severity_distribution.png")
    print(f"  → {OUTDIR}/avg_severity_by_category.png")

if __name__ == "__main__":
    main()