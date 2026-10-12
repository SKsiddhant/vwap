import numpy as np
import pandas as pd
import pytest

from vwap_engine import (
    backtest, calc_indicators, clean_ticker, compute_stats, gen_signals,
    is_intraday, resolve_ticker,
)


def intraday_prices(days=6, bars=7, seed=3, volume=True):
    rng = np.random.default_rng(seed)
    idx = []
    for d in pd.bdate_range("2024-03-04", periods=days):
        idx += [d + pd.Timedelta(hours=9, minutes=30) + pd.Timedelta(hours=h) for h in range(bars)]
    idx = pd.DatetimeIndex(idx)
    close = 100 + np.cumsum(rng.normal(0, 0.6, len(idx)))
    return pd.DataFrame({
        "open": close + rng.normal(0, 0.1, len(idx)),
        "high": close + 0.5, "low": close - 0.5, "close": close,
        "volume": rng.integers(100, 1000, len(idx)) if volume else 0,
    }, index=idx)


def frame(opens, highs, lows, closes, buy=None, sell=None, buy_stop=None, sell_stop=None):
    n = len(closes)
    idx = pd.bdate_range("2024-01-01", periods=n)
    df = pd.DataFrame({"open": opens, "high": highs, "low": lows, "close": closes}, index=idx)
    df["buy_sig"] = buy or [False] * n
    df["sell_sig"] = sell or [False] * n
    df["buy_stop"] = buy_stop or [0.0] * n
    df["sell_stop"] = sell_stop or [0.0] * n
    return df


# ---------- ticker handling ----------
def test_resolve_ticker_maps_tradingview_names():
    assert resolve_ticker(" nifty ") == "^NSEI"
    assert resolve_ticker("reliance.ns") == "RELIANCE.NS"


@pytest.mark.parametrize("good", ["aapl", "RELIANCE.NS", "^NSEI", "BTC-USD", "EURUSD=X", "NIFTY1!"])
def test_clean_ticker_accepts(good):
    assert clean_ticker(good) == good.upper()


@pytest.mark.parametrize("bad", ["", "<img src=x>", "a b", "../x", "x" * 25, 'A"B'])
def test_clean_ticker_rejects(bad):
    with pytest.raises(ValueError):
        clean_ticker(bad)


# ---------- indicators ----------
def test_vwap_resets_each_day_for_intraday():
    df = intraday_prices()
    assert is_intraday(df.index)
    out = calc_indicators(df, 3, 3)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    first_bar_each_day = out.groupby(out.index.normalize()).head(1)
    # first bar of a session: VWAP is just that bar's HLC3
    session_starts = set(df.groupby(df.index.normalize()).head(1).index)
    checked = 0
    for ts, row in first_bar_each_day.iterrows():
        if ts in session_starts:  # day 1 is partly consumed by indicator warm-up
            assert row["vwap"] == pytest.approx(tp[ts])
            checked += 1
    assert checked >= 4


def test_vwap_cumulative_when_reset_disabled():
    df = intraday_prices()
    out = calc_indicators(df, 3, 3, session_reset=False)
    tp = (df["high"] + df["low"] + df["close"]) / 3
    expected = (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    assert out["vwap"].iloc[-1] == pytest.approx(expected.iloc[-1])


def test_vwap_does_not_look_ahead():
    df = intraday_prices()
    full = calc_indicators(df, 3, 3)
    cut = calc_indicators(df.iloc[:20], 3, 3)
    common = cut.index
    assert np.allclose(full.loc[common, "vwap"], cut["vwap"])


def test_leading_zero_volume_does_not_backfill_future_vwap():
    df = intraday_prices(days=2)
    df.iloc[:3, df.columns.get_loc("volume")] = 0
    out = calc_indicators(df, 3, 3, session_reset=False)
    early = out.iloc[0]
    tp = (early["high"] + early["low"] + early["close"]) / 3
    assert early["vwap"] == pytest.approx(tp)


def test_no_volume_falls_back_to_rolling_hlc3():
    df = intraday_prices(volume=False)
    out = calc_indicators(df, 4, 3)
    assert out["vwap"].notna().all()


def test_too_few_bars_raises_helpful_error():
    with pytest.raises(ValueError, match="need at least"):
        calc_indicators(intraday_prices(days=1, bars=5), 14, 14)


def test_signals_follow_rules():
    out = gen_signals(calc_indicators(intraday_prices(), 3, 3), 1.5)
    assert not (out["buy_sig"] & out["sell_sig"]).any()
    assert (out.loc[out["buy_sig"], "close"] < out.loc[out["buy_sig"], "vwap"]).all()
    assert (out.loc[out["buy_sig"], "close"] > out.loc[out["buy_sig"], "ma"]).all()
    assert (out["buy_stop"] < out["close"]).all() and (out["sell_stop"] > out["close"]).all()


# ---------- backtest ----------
def test_long_stop_loss_basic():
    df = frame(opens=[100, 100, 99], highs=[101, 101, 100], lows=[99, 99, 94],
               closes=[100, 100, 96], buy=[True, False, False], buy_stop=[95, 0, 0])
    out, trades, cap = backtest(df, 1000)
    assert len(trades) == 1
    t = trades.iloc[0]
    assert (t["type"], t["entry_px"], t["exit_px"], t["pnl"], t["result"]) == ("Buy", 100.0, 95.0, -5.0, "Loss")
    assert cap == 995
    assert out.attrs["open_position"] is None


def test_gap_down_fills_at_open_not_at_stop():
    df = frame(opens=[100, 90], highs=[101, 91], lows=[99, 88], closes=[100, 89],
               buy=[True, False], buy_stop=[95, 0])
    _, trades, cap = backtest(df, 1000)
    assert trades.iloc[0]["exit_px"] == 90.0  # old code reported 95
    assert cap == 990


def test_short_stop_and_gap_up():
    df = frame(opens=[100, 110], highs=[101, 112], lows=[99, 109], closes=[100, 111],
               sell=[True, False], sell_stop=[105, 0])
    _, trades, cap = backtest(df, 1000)
    assert trades.iloc[0]["type"] == "Sell"
    assert trades.iloc[0]["exit_px"] == 110.0
    assert cap == 990


def test_units_scale_pnl_and_buy_and_hold_is_comparable():
    df = frame(opens=[100, 100, 99, 100], highs=[101, 101, 100, 130],
               lows=[99, 99, 94, 99], closes=[100, 100, 96, 120],
               buy=[True, False, False, False], buy_stop=[95, 0, 0, 0])
    out, trades, cap = backtest(df, 1000, units=10)
    assert trades.iloc[0]["pnl"] == -50.0 and cap == 950
    # B&H holds the same 10 units from the first close: 1000 + 10*(120-100)
    assert out["bah"].iloc[-1] == pytest.approx(1200)
    assert out["bah"].iloc[0] == pytest.approx(1000)


def test_equity_is_marked_to_market_and_drawdown_sees_open_losses():
    # long entered at 100, price slides to 96 (stop at 90 never hit)
    df = frame(opens=[100, 99, 97], highs=[101, 100, 98], lows=[99, 96, 95],
               closes=[100, 97, 96], buy=[True, False, False], buy_stop=[90, 0, 0])
    out, trades, cap = backtest(df, 1000)
    assert trades.empty and cap == 1000
    assert list(out["equity"]) == [1000, 997, 996]
    assert out["dd"].min() == -4
    op = out.attrs["open_position"]
    assert op["type"] == "Buy" and op["unrealised"] == pytest.approx(-4)


def test_only_one_position_at_a_time():
    df = frame(opens=[100] * 4, highs=[101] * 4, lows=[99] * 4, closes=[100] * 4,
               buy=[True, True, False, False], sell=[False, False, True, False],
               buy_stop=[90] * 4, sell_stop=[110] * 4)
    out, trades, _ = backtest(df, 1000)
    assert trades.empty
    assert out.attrs["open_position"]["entry_time"] == df.index[0]


def test_backtest_validates_input():
    with pytest.raises(ValueError):
        backtest(pd.DataFrame(), 1000)
    with pytest.raises(ValueError):
        backtest(frame([1, 1], [1, 1], [1, 1], [1, 1]), 1000, units=0)


def test_stats_end_to_end_on_synthetic_data():
    df = gen_signals(calc_indicators(intraday_prices(days=40, seed=11), 5, 5), 0.8)
    out, trades, cap = backtest(df, 100_000, units=100)
    stats = compute_stats(trades, 100_000, cap, out)
    assert stats["n"] == len(trades) > 0
    assert stats["wins"] + stats["losses"] <= stats["n"]
    assert stats["net"] == pytest.approx(cap - 100_000)
    assert stats["max_dd"] >= 0
