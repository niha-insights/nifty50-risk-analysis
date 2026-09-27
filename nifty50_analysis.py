# NIFTY-50 Stock Risk & Volatility Analysis
#
# Dataset: Kaggle "NIFTY-50 Stock Market Data"
# (https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data)
#
# The dataset ships 50 individual per-stock CSVs plus two convenience files,
# used directly here rather than re-unioning the individual files:
#   - NIFTY50_all.csv: all 50 stocks already combined (235,192 rows,
#     2000-01-03 to 2021-04-30)
#   - stock_metadata.csv: one row per current company (Company Name,
#     Industry, Symbol, Series, ISIN Code) — used as the sector-mapping
#     table for the merge below
#
# Run in Google Colab (colab.research.google.com) if pandas isn't set up
# locally — upload both CSVs and run cell by cell.

import pandas as pd
import numpy as np

df = pd.read_csv("data/NIFTY50_all.csv")
meta = pd.read_csv("data/stock_metadata.csv")


# ══════════════════════════════════════════════════════════════════════
# PART 1 — DATA CLEANING
# ══════════════════════════════════════════════════════════════════════

# ── Resolve ticker renames ────────────────────────────────────────────
# Some companies changed their listed Symbol during the dataset's 21-year
# span. These show up as symbols in the price data that don't exist in
# the current metadata table.
old_symbols = set(df['Symbol'].unique()) - set(meta['Symbol'])
print("Old/renamed symbols found in price data:", sorted(old_symbols))

symbol_renames = {
    'MUNDRAPORT': 'ADANIPORTS', 'BAJAUTOFIN': 'BAJFINANCE',
    'BHARTI': 'BHARTIARTL', 'HEROHONDA': 'HEROMOTOCO',
    'HINDALC0': 'HINDALCO', 'HINDLEVER': 'HINDUNILVR',
    'INFOSYSTCH': 'INFY', 'JSWSTL': 'JSWSTEEL',
    'KOTAKMAH': 'KOTAKBANK', 'SESAGOA': 'VEDL', 'SSLT': 'VEDL',
    'TELCO': 'TATAMOTORS', 'TISCO': 'TATASTEEL', 'UNIPHOS': 'UPL',
    'UTIBANK': 'AXISBANK', 'ZEETELE': 'ZEEL',
    # SESAGOA and SSLT both map to VEDL, reflecting the Sesa Goa /
    # Sterlite Industries merger into Vedanta — a genuine corporate
    # merger, not a simple ticker rename.
}
df['Symbol'] = df['Symbol'].replace(symbol_renames)
# Note: INFRATEL appears in metadata but never in the price data — likely
# delisted, or added to the index after this dataset's 2021 cutoff.

# ── Missing values ─────────────────────────────────────────────────────
# Trades and Deliverable Volume are null in a substantial share of rows,
# consistent with reporting requirements that changed partway through the
# dataset's 21-year span rather than a data-quality error. Core price and
# volume fields have zero nulls, so no rows are dropped.
print(df.isnull().sum())

# ── Sector join ─────────────────────────────────────────────────────────
df = df.merge(meta[['Symbol', 'Industry']], on='Symbol', how='left')
df.to_csv("nifty50_cleaned.csv", index=False)


# ══════════════════════════════════════════════════════════════════════
# PART 2 — RISK ANALYSIS: VOLATILITY & DRAWDOWN
# ══════════════════════════════════════════════════════════════════════

df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(['Symbol', 'Date'])

# ── Daily returns and rolling volatility ──────────────────────────────
df['Daily_Return'] = df.groupby('Symbol')['Close'].pct_change()
df['Rolling_Volatility_30D'] = (
    df.groupby('Symbol')['Daily_Return'].transform(lambda x: x.rolling(30).std())
)
df['Annualized_Volatility'] = df['Rolling_Volatility_30D'] * np.sqrt(252)

# ── Split/bonus-issue correction ──────────────────────────────────────
# An initial pass showed implausible ~90%+ drawdowns for nearly every
# stock. Investigation traced this to unadjusted stock splits and bonus
# issues — isolated single-stock price jumps near clean ratios (~50%,
# ~80%, ~90%) on dates no other stock reacted to. Genuine market-wide
# events (identified by requiring several stocks to move together on the
# same date) are left untouched.
big_moves = df[df['Daily_Return'].abs() > 0.20].copy()
date_counts = big_moves.groupby('Date').size()
market_wide_dates = set(date_counts[date_counts >= 4].index)
split_events = big_moves[~big_moves['Date'].isin(market_wide_dates)]

price_cols = ['Prev Close', 'Open', 'High', 'Low', 'Last', 'Close', 'VWAP']
for symbol in split_events['Symbol'].unique():
    stock_splits = split_events[split_events['Symbol'] == symbol].sort_values('Date')
    for _, row in stock_splits.iterrows():
        ratio = row['Close'] / row['Prev Close']
        mask = (df['Symbol'] == symbol) & (df['Date'] < row['Date'])
        df.loc[mask, price_cols] = df.loc[mask, price_cols] * ratio

# Recompute returns and volatility on the corrected prices
df = df.sort_values(['Symbol', 'Date'])
df['Daily_Return'] = df.groupby('Symbol')['Close'].pct_change()
df['Rolling_Volatility_30D'] = (
    df.groupby('Symbol')['Daily_Return'].transform(lambda x: x.rolling(30).std())
)
df['Annualized_Volatility'] = df['Rolling_Volatility_30D'] * np.sqrt(252)

# ── Maximum drawdown ───────────────────────────────────────────────────
# A more aggressive multi-day version of the split correction was tested
# and found to overcorrect, producing less plausible results — reverted
# in favor of this single-day-event version. Drawdown figures still carry
# some residual distortion from unresolved multi-stage corporate actions;
# volatility is treated as the more reliable risk metric in this analysis.
df['Cumulative_Max'] = df.groupby('Symbol')['Close'].transform(lambda x: x.cummax())
df['Drawdown'] = (df['Close'] - df['Cumulative_Max']) / df['Cumulative_Max']

# ── Per-stock risk summary ─────────────────────────────────────────────
risk_summary = df.groupby('Symbol').agg(
    Avg_Annualized_Volatility=('Annualized_Volatility', 'mean'),
    Max_Drawdown=('Drawdown', 'min'),
    Industry=('Industry', 'first')
).reset_index()
risk_summary['Max_Drawdown_Pct'] = (risk_summary['Max_Drawdown'] * 100).round(2)
risk_summary['Avg_Annualized_Volatility_Pct'] = (
    risk_summary['Avg_Annualized_Volatility'] * 100
).round(2)

print("\nTop 10 riskiest stocks by average annualized volatility:")
print(risk_summary.sort_values('Avg_Annualized_Volatility_Pct', ascending=False)
      [['Symbol', 'Industry', 'Avg_Annualized_Volatility_Pct', 'Max_Drawdown_Pct']].head(10))

risk_summary.to_csv("nifty50_risk_summary.csv", index=False)
df.to_csv("nifty50_with_risk_metrics.csv", index=False)
print("\nSaved.")
