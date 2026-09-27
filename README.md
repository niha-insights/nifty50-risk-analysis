# NIFTY-50 Stock Risk & Volatility Analysis

## Business Question
Which NIFTY-50 constituent stocks carried the most risk historically, and what would a risk-conscious analyst have flagged before major drawdown periods?

## Data
- Source: [Kaggle — NIFTY-50 Stock Market Data](https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data)
- `NIFTY50_all.csv` — daily OHLCV data for all 50 constituents, 2000-01-03 to 2021-04-30 (235,192 rows)
- `stock_metadata.csv` — company name, industry, and ISIN per current ticker

The dataset ships both individual per-stock files and a pre-combined file. The pre-combined file was used directly rather than re-unioning the individual files, since that would duplicate work already done correctly.

## Data Cleaning
- **Ticker renames**: 16 old/renamed symbols identified by comparing tickers present in the price data against the current metadata table (e.g., `MUNDRAPORT` → `ADANIPORTS`, `UTIBANK` → `AXISBANK`, `HEROHONDA` → `HEROMOTOCO`). All resolved and verified against the cleaned dataset.
- **Sector join**: merged against `stock_metadata.csv` on Symbol; zero unmatched rows.
- **Missing values**: `Trades` and `Deliverable Volume` contain nulls (~49% and ~7% of rows respectively), consistent with reporting requirements that changed partway through the dataset's 21-year span rather than a data error. Core price/volume fields have zero nulls.
- **Unmatched company**: `INFRATEL` appears in metadata but never in the price data — likely delisted, or added to the index after this dataset's 2021 cutoff. Left unmatched rather than forcing an incorrect join.

## Methodology
- **Daily returns**: percentage change in closing price, per stock.
- **Rolling volatility**: 30-day rolling standard deviation of daily returns, annualized (× √252 trading days).
- **Maximum drawdown**: largest peak-to-trough decline from each stock's running historical high.

## Data Quality Investigation
Initial drawdown results showed implausible ~90%+ declines across nearly every stock — too extreme even accounting for the 2008 financial crisis and 2020 COVID crash. Investigation traced this to **unadjusted stock splits and bonus issues**: isolated single-stock price jumps near clean ratios (~50%, ~80%, ~90%) on dates no other stock reacted to, distinct from genuine market-wide events (2008-10-31, 2009-05-18 — the NSE's 20% circuit-breaker day following the 2009 election result, and 2020-03-23).

A back-adjustment was built and applied for identified splits. This meaningfully corrected volatility figures to a plausible range. Drawdown figures still show some residual distortion likely caused by complex or multi-stage corporate actions (mergers, multi-day circuit-breaker-smoothed splits) not fully resolved by standard back-adjustment — **volatility is treated as the more reliable risk metric in this analysis**, and drawdown figures should be read with that caveat.

## Key Findings
Top 5 riskiest stocks by average annualized volatility:

| Symbol | Industry | Avg. Annualized Volatility |
|---|---|---|
| VEDL | Metals | 47.8% |
| ZEEL | Media & Entertainment | 45.2% |
| INDUSINDBK | Financial Services | 43.1% |
| JSWSTEEL | Metals | 42.4% |
| TATAMOTORS | Automobile | 42.2% |

Metals and Financial Services sectors show consistently elevated volatility relative to the broader NIFTY-50 universe.

## Recommendation
A risk-conscious portfolio manager would size positions in high-volatility names (VEDL, ZEEL, INDUSINDBK) more conservatively and consider sector-level volatility (Metals, Financial Services) as a factor in rebalancing decisions, particularly ahead of known high-volatility macro windows.

## Tools
Python (pandas, numpy) — data cleaning, split detection and adjustment, volatility and drawdown calculation.

## Limitations
- Drawdown figures carry residual distortion from unresolved multi-stage corporate actions; volatility is the primary risk metric relied on in this analysis.
- Analysis covers 2000–2021; does not reflect post-2021 market conditions.
