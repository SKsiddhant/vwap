"""Indicator, signal and back-test logic for the VWAP + SMA mean-reversion app.

Kept free of Streamlit/yfinance so it can be unit-tested offline.
"""
import re

import numpy as np
import pandas as pd

# TradingView-style shorthands -> Yahoo Finance symbols
TV_TO_YF = {
    "NIFTY1!":     "^NSEI",    "BANKNIFTY1!": "^NSEBANK",
    "NIFTY":       "^NSEI",    "BANKNIFTY":   "^NSEBANK",
    "SENSEX":      "^BSESN",   "SPX":         "^GSPC",
    "NDX":         "^IXIC",    "DJX":         "^DJI",
    "GOLD":        "GC=F",     "SILVER":      "SI=F",
    "CRUDEOIL":    "CL=F",     "BITCOIN":     "BTC-USD",
    "ETHEREUM":    "ETH-USD",  "CNXFINANCE":  "^CNXFINANCE",
    "CNXAUTO":     "^CNXAUTO", "CNXPHARMA":   "^CNXPHARMA",
    "CNXFMCG":     "^CNXFMCG", "CNXMETAL":    "^CNXMETAL",
    "CNXREALTY":   "^CNXREALTY", "CNXMIDCAP": "^CNXMIDCAP",
    "CNXSMALLCAP": "^CNXSMALLCAP", "CNXIT":   "^CNXIT",
}

_TICKER_RE = re.compile(r"^[A-Z0-9^][A-Z0-9.\-=^_!]{0,19}$")


def clean_ticker(raw: str) -> str:
    """Upper-case and validate user input. Raises ValueError for anything odd."""
    t = (raw or "").strip().upper()
    if not _TICKER_RE.match(t):
        raise ValueError("Ticker may only contain letters, digits and . - ^ = _ ! (max 20 characters).")
    return t


def resolve_ticker(raw: str) -> str:
    """Convert TV-style or shorthand to a valid yfinance ticker."""
    t = raw.strip().upper()
    return TV_TO_YF.get(t, t)


def is_intraday(index) -> bool:
    """True when more than one bar falls on the same calendar day."""
    return bool(pd.DatetimeIndex(index).normalize().duplicated().any())


def calc_indicators(df, ma_len, atr_len, session_reset=True):
    """Add vwap, ma, atr, tr columns.

    VWAP (HLC3 x volume) restarts every trading day for intraday data, which is
    the normal definition. With ``session_reset=False`` (or daily bars) it is
    cumulative from the first bar. Instruments with no volume (indices) fall back
    to a rolling mean of HLC3.
    """
    df = df.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in df.columns:
            continue
        s = df[col]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        df[col] = pd.to_numeric(s, errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close"]).sort_index()

    n_bars = len(df)
    min_bars = max(ma_len, atr_len) + 2
    if n_bars < min_bars:
        raise ValueError(
            f"Only {n_bars} valid bars after cleaning — need at least {min_bars}. "
            f"Try a longer period (e.g. 3mo or 6mo) or "
            f"reduce SMA/ATR length below {n_bars - 2}."
        )

    tp = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].fillna(0) if "volume" in df.columns else pd.Series(0.0, index=df.index)

    has_volume = (vol > 0).sum() > len(vol) * 0.1
    if has_volume:
        if session_reset and is_intraday(df.index):
            groups = pd.DatetimeIndex(df.index).normalize()
            num = (tp * vol).groupby(groups).cumsum()
            den = vol.groupby(groups).cumsum()
        else:
            num = (tp * vol).cumsum()
            den = vol.cumsum()
        # Bars before the first traded volume have no VWAP yet: use their own HLC3
        # (never back-fill, that would leak future prices into the past).
        df["vwap"] = (num / den.where(den > 0)).fillna(tp)
    else:
        df["vwap"] = tp.rolling(window=ma_len, min_periods=1).mean()

    df["ma"] = df["close"].rolling(window=ma_len, min_periods=ma_len).mean()

    pc = df["close"].shift(1)
    hl = df["high"] - df["low"]
    hc = (df["high"] - pc).abs()
    lc = (df["low"] - pc).abs()
    df["tr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["atr"] = df["tr"].rolling(window=atr_len, min_periods=atr_len).mean()

    df = df.dropna(subset=["ma", "atr"])
    if df.empty:
        raise ValueError(
            f"Zero rows remain after indicator warmup. "
            f"Period has {n_bars} bars — SMA={ma_len}, ATR={atr_len} "
            f"need {min_bars}+ bars. Use a longer period or reduce lengths."
        )
    return df


def gen_signals(df, mult):
    df = df.copy()
    close = df["close"].squeeze()
    vwap = df["vwap"].squeeze()
    ma = df["ma"].squeeze()
    atr = df["atr"].squeeze()
    df["buy_sig"] = (close < vwap) & (close > ma)
    df["sell_sig"] = (close > vwap) & (close < ma)
    df["buy_stop"] = close - mult * atr
    df["sell_stop"] = close + mult * atr
    return df


def safe_float(val):
    """Safely extract a Python float from any pandas scalar/Series/DataFrame."""
    if isinstance(val, (pd.Series, pd.DataFrame)):
        val = val.iloc[0]
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def backtest(df, cap, units=1.0):
    """Run the stop-loss-only strategy.

    * One position at a time, ``units`` per trade; entry at the signal bar's close.
    * Exit only via the ATR stop, checked on later bars. If a bar *opens* beyond
      the stop (a gap) the fill is at the open, not at the better stop price.
    * ``equity`` is marked to market every bar (realised + open P&L), so drawdown
      includes losses inside a trade. ``bah`` holds the same ``units`` from the
      first bar, so it is directly comparable with ``equity``.
    * The returned capital is *realised* capital; a still-open position is stored
      in ``df.attrs["open_position"]`` (or None).
    """
    if df is None or df.empty:
        raise ValueError("Cannot run backtest: DataFrame is empty.")
    if len(df) < 2:
        raise ValueError(f"Cannot run backtest: only {len(df)} row(s). Need at least 2.")
    if units <= 0:
        raise ValueError("Units per trade must be positive.")
    df = df.copy()
    for col in list(df.columns):
        s = df[col]
        if isinstance(s, pd.DataFrame):
            df[col] = s.iloc[:, 0]

    capital = float(cap)
    pos = 0
    entry_px = stop_px = 0.0
    entry_time = entry_bar = None
    trades, equity = [], []
    bah0 = safe_float(df["close"].iloc[0])
    if bah0 == 0.0:
        raise ValueError("First close price is zero or invalid — cannot run backtest.")

    def close_trade(kind, row, bar, exit_px):
        nonlocal capital
        gross = (exit_px - entry_px) if kind == "Buy" else (entry_px - exit_px)
        pnl = gross * units
        capital += pnl
        trades.append(dict(
            num=len(trades) + 1, type=kind,
            entry_time=entry_time, exit_time=row.name,
            entry_bar=entry_bar, exit_bar=bar, bars=bar - entry_bar,
            entry_px=round(entry_px, 2), exit_px=round(exit_px, 2),
            exit_type="Stop Loss", pnl=round(pnl, 2),
            pnl_pct=round(gross / entry_px * 100, 3),
            result="Win" if pnl > 0 else "Loss"))

    for i, (_, row) in enumerate(df.iterrows()):
        bar = i + 1
        if pos == 1 and safe_float(row["low"]) <= stop_px:
            close_trade("Buy", row, bar, min(stop_px, safe_float(row["open"])))
            pos = 0
        elif pos == -1 and safe_float(row["high"]) >= stop_px:
            close_trade("Sell", row, bar, max(stop_px, safe_float(row["open"])))
            pos = 0
        if pos == 0:
            if row["buy_sig"]:
                pos = 1
                entry_px = safe_float(row["close"]); stop_px = safe_float(row["buy_stop"])
                entry_time = row.name; entry_bar = bar
            elif row["sell_sig"]:
                pos = -1
                entry_px = safe_float(row["close"]); stop_px = safe_float(row["sell_stop"])
                entry_time = row.name; entry_bar = bar
        unrealised = pos * (safe_float(row["close"]) - entry_px) * units if pos else 0.0
        equity.append(capital + unrealised)

    close = df["close"].astype(float)
    df["equity"] = equity
    df["bah"] = cap + units * (close - bah0)
    peak = df["equity"].cummax()
    df["dd"] = df["equity"] - peak
    df["dd_pct"] = (df["dd"] / peak.where(peak != 0) * 100).fillna(0.0)

    last_close = safe_float(df["close"].iloc[-1])
    df.attrs["open_position"] = None if pos == 0 else dict(
        type="Buy" if pos == 1 else "Sell", entry_px=entry_px, stop_px=stop_px,
        entry_time=entry_time, unrealised=pos * (last_close - entry_px) * units)
    return df, pd.DataFrame(trades), capital


def compute_stats(tdf, cap0, capN, df):
    s = {}; n = len(tdf); s["n"] = n
    if n == 0: return s
    pnl  = tdf["pnl"]
    gp   = pnl[pnl>0].sum(); gl = abs(pnl[pnl<0].sum())
    wins = int((pnl>0).sum()); loss = int((pnl<0).sum())
    s["net"]=round(capN-cap0,2); s["net_pct"]=round((capN-cap0)/cap0*100,2)
    s["gp"]=round(gp,2); s["gl"]=round(gl,2)
    s["pf"]=round(gp/gl,3) if gl else float("inf")
    s["wins"]=wins; s["losses"]=loss
    s["wr"]=round(wins/n*100,2)
    s["avg_trade"]=round(pnl.mean(),2); s["avg_trade_pct"]=round(pnl.mean()/cap0*100,3)
    s["avg_win"]=round(pnl[pnl>0].mean(),2) if wins else 0
    s["avg_loss"]=round(pnl[pnl<0].mean(),2) if loss else 0
    s["best"]=round(pnl.max(),2); s["worst"]=round(pnl.min(),2)
    s["avg_bars"]=round(tdf["bars"].mean(),1)
    s["avg_bars_win"]=round(tdf.loc[tdf["result"]=="Win","bars"].mean(),1) if wins else 0
    s["avg_bars_loss"]=round(tdf.loc[tdf["result"]=="Loss","bars"].mean(),1) if loss else 0
    dd = df["dd"]
    s["max_dd"]=round(abs(dd.min()),2)
    s["max_dd_pct"]=round(abs(df["dd_pct"].min()),2)
    res=tdf["result"].tolist(); mw=ml=cw=cl=0
    for r in res:
        if r=="Win": cw+=1; cl=0
        else:        cl+=1; cw=0
        mw=max(mw,cw); ml=max(ml,cl)
    s["consec_win"]=mw; s["consec_loss"]=ml
    tdf2=tdf.copy()
    tdf2["month"]=pd.to_datetime(tdf2["entry_time"]).dt.to_period("M").astype(str)
    s["monthly"]=tdf2.groupby("month")["pnl"].sum().reset_index()
    s["monthly"].columns=["Month","P&L"]
    buys=tdf[tdf["type"]=="Buy"]; sells=tdf[tdf["type"]=="Sell"]
    s["buy_n"]=len(buys); s["sell_n"]=len(sells)
    s["buy_wr"]=round((buys["pnl"]>0).sum()/len(buys)*100,1) if len(buys) else 0
    s["sell_wr"]=round((sells["pnl"]>0).sum()/len(sells)*100,1) if len(sells) else 0
    return s
