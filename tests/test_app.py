"""Run the real Streamlit script against fake Yahoo data."""
import os

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from tests.test_engine import intraday_prices

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vwap_streamlit_app.py")


@pytest.fixture
def app(monkeypatch):
    import yfinance as yf

    calls = []

    def fake_download(sym, **kw):
        calls.append(sym)
        if sym == "EMPTY":
            return pd.DataFrame()
        df = intraday_prices(days=30, seed=5).rename(columns=str.title)
        df.columns = pd.MultiIndex.from_product([df.columns, [sym]])
        return df

    monkeypatch.setattr(yf, "download", fake_download)
    monkeypatch.setattr(yf, "Ticker", lambda s: (_ for _ in ()).throw(RuntimeError("offline")))
    at = AppTest.from_file(APP, default_timeout=90)
    at.calls = calls
    return at


def run(at, ticker=None):
    at.run()
    if ticker:
        at.sidebar.text_input[0].set_value(ticker)
        at.run()
    at.sidebar.button[-1].click()
    at.run()
    return at


def test_default_run_renders_all_tabs(app):
    at = run(app)
    assert not at.exception, at.exception
    assert len(at.tabs) == 4
    assert app.calls == ["RELIANCE.NS"]


def test_manual_ticker_is_used(app):
    at = run(app, "sbin.ns")
    assert not at.exception, at.exception
    assert app.calls == ["SBIN.NS"]


def test_picked_symbol_is_not_overridden_by_typed_ticker(app):
    at = app
    at.run()
    at.sidebar.text_input[0].set_value("SBIN.NS").run()
    assert at.session_state["selected_sym"] == "SBIN.NS"
    # picking another symbol (what the Select button does) must stick on the next rerun
    at.session_state["selected_sym"] = "TCS.NS"
    at.run()
    assert at.session_state["selected_sym"] == "TCS.NS"


def test_invalid_ticker_rejected_before_any_fetch(app):
    at = run(app, "<script>alert(1)</script>")
    assert not at.exception
    assert any("Ticker may only contain" in e.value for e in at.error)
    assert app.calls == []


def test_empty_data_shows_error_not_traceback(app):
    at = run(app, "EMPTY")
    assert not at.exception, at.exception
    assert any("EMPTY" in e.value for e in at.error)


def test_no_trades_does_not_hide_other_tabs(app):
    at = app
    at.run()
    # an ATR multiplier so wide that no stop is ever hit -> zero closed trades
    next(s for s in at.sidebar.slider if "ATR Multiplier" in s.label).set_value(4.0)
    next(s for s in at.sidebar.slider if "SMA Length" in s.label).set_value(50)
    at.sidebar.button[-1].click()
    at.run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 4
    # Properties tab (the 4th) must still render; previously st.stop() in tab 2 killed it
    assert any("Entry & Exit Rules" in m.value for m in at.markdown)
