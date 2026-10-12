# VWAP + SMA Mean-Reversion Back-tester

A Streamlit dashboard that back-tests a VWAP / SMA mean-reversion idea with an ATR stop-loss on Yahoo Finance data.

| | Rule |
|---|---|
| **Buy** | close < VWAP **and** close > SMA(n) |
| **Sell (short)** | close > VWAP **and** close < SMA(n) |
| **Exit** | ATR stop only: entry ∓ multiplier × ATR(n). No take-profit, no signal exits |

## Run

```bash
pip install -r requirements.txt
streamlit run vwap_streamlit_app.py
```

Use the symbol search or type a ticker (`RELIANCE.NS`, `^NSEI`, `AAPL`, `BTC-USD`, ...). Yahoo only provides intraday history for the last ~60 days (730 for 1h).

## Modelling notes

* **VWAP** is HLC3 × volume and **restarts each trading day** for intraday bars (switchable in the sidebar). Daily bars use one cumulative VWAP. Indices with no volume use a rolling mean of HLC3 instead.
* Entry is at the signal bar's close. The stop is checked from the next bar on; if a bar **opens** beyond the stop (gap), the fill is at the open, not the stop.
* One position at a time, fixed **units per trade** (sidebar, default 1). Buy & Hold in the charts holds the *same* units, so the two curves are comparable.
* The equity curve is marked to market, so drawdown includes losses inside open trades. Closed-trade statistics (win rate, profit factor, ...) exclude a still-open position, which is shown above the tabs.
* No commission, slippage, or position sizing by risk. Educational use only; past results do not predict future performance.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Logic lives in `vwap_engine.py` and is tested with synthetic prices; the UI tests run the real script with a fake `yfinance`.
