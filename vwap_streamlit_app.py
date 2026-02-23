# ============================================================
#   SpringPad's VWAP + MA Mean Reversion Strategy
#   🚀 TradingView-Style Streamlit Dashboard
#   Full tabs: Overview · Performance Summary ·
#              List of Trades · Properties
# ============================================================
#   pip install streamlit yfinance pandas numpy plotly
#   streamlit run vwap_streamlit_app.py
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="SpringPad VWAP Strategy",
                   page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp{background:#131722;color:#d1d4dc}
  section[data-testid="stSidebar"]{background:#1e222d;border-right:1px solid #2a2e39}

  /* metric cards */
  div[data-testid="metric-container"]{background:#1e222d;border:1px solid #2a2e39;
    border-radius:6px;padding:10px 14px}
  div[data-testid="metric-container"] label{color:#787b86!important;font-size:11px!important}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"]{
    color:#d1d4dc!important;font-size:17px!important;font-weight:700!important}

  /* tabs */
  .stTabs [data-baseweb="tab-list"]{background:#1e222d;border-radius:6px 6px 0 0;
    border-bottom:1px solid #2a2e39;gap:0;padding:0}
  .stTabs [data-baseweb="tab"]{color:#787b86;border-radius:0;padding:10px 22px;
    font-size:13px;border-bottom:2px solid transparent}
  .stTabs [aria-selected="true"]{background:transparent!important;
    color:#d1d4dc!important;border-bottom:2px solid #2196f3!important}

  /* header */
  .tv-header{background:#1e222d;border:1px solid #2a2e39;border-radius:8px;
    padding:14px 20px;margin-bottom:16px}

  /* stats bar (7-metric row) */
  .stats-bar{display:flex;flex-wrap:wrap;background:#1e222d;
    border:1px solid #2a2e39;border-radius:8px;margin-bottom:16px;overflow:hidden}
  .stat-item{flex:1;min-width:120px;padding:13px 16px;border-right:1px solid #2a2e39}
  .stat-item:last-child{border-right:none}
  .stat-label{font-size:11px;color:#787b86;margin-bottom:3px}
  .stat-value{font-size:14px;font-weight:700;color:#d1d4dc}
  .stat-pct{font-size:11px;margin-left:4px}
  .green{color:#26a69a} .red{color:#ef5350} .blue{color:#2196f3} .orange{color:#ff9800}

  /* section card */
  .sc{background:#1e222d;border:1px solid #2a2e39;border-radius:8px;
      padding:16px 20px;margin-bottom:14px}
  .sc-title{font-size:12px;font-weight:600;color:#d1d4dc;margin-bottom:12px;
    padding-bottom:8px;border-bottom:1px solid #2a2e39}

  /* perf table */
  .pt{width:100%;border-collapse:collapse;font-size:12px}
  .pt td{padding:7px 10px;border-bottom:1px solid #1a1e2b;color:#d1d4dc}
  .pt td:first-child{color:#787b86;width:58%}
  .pt tr:last-child td{border-bottom:none}
  .pt tr:hover td{background:#1c2128}

  /* trade table */
  .tt{width:100%;border-collapse:collapse;font-size:12px}
  .tt th{background:#1e222d;color:#787b86;padding:9px 11px;text-align:left;
    border-bottom:1px solid #2a2e39;font-weight:500;white-space:nowrap}
  .tt td{padding:7px 11px;border-bottom:1px solid #1a1e2b;color:#d1d4dc;white-space:nowrap}
  .tt tr:nth-child(even) td{background:#1a1e2b}
  .tt tr:hover td{background:#2a2e39}

  /* progress bar */
  .pb-wrap{background:#2a2e39;border-radius:4px;height:6px;overflow:hidden;margin-top:4px}
  .pb-fill{height:6px;border-radius:4px}

  /* badge */
  .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}

  hr{border-color:#2a2e39!important}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Strategy Settings")
    st.markdown("---")
    ticker   = st.text_input("Ticker Symbol", "RELIANCE.NS",
                              placeholder="TCS.NS · AAPL · BTC-USD").upper()
    c1, c2   = st.columns(2)
    interval = c1.selectbox("Interval", ["1h","15m","30m","1d","5m"], 0)
    period   = c2.selectbox("Period",   ["60d","30d","3mo","6mo","1y"], 0)
    st.markdown("---")
    ma_length  = st.slider("SMA Length",     5,  50, 14)
    atr_length = st.slider("ATR Length",     5,  50, 14)
    atr_mult   = st.slider("ATR Multiplier", 0.5, 4.0, 1.5, 0.1)
    st.markdown("---")
    starting_cap = st.number_input("Starting Capital", 1_000_000, step=10000)
    currency     = st.selectbox("Currency", ["INR","USD","EUR","GBP"])
    st.markdown("---")
    run_btn = st.button("🚀 Run Strategy", use_container_width=True, type="primary")
    st.markdown("---")
    st.markdown("""<div style='font-size:11px;color:#787b86;line-height:1.8'>
    <b style='color:#d1d4dc'>📖 Signal Logic</b><br>
    🟢 <b>BUY</b> → Close &lt; VWAP &amp; Close &gt; SMA<br>
    🔴 <b>SELL</b> → Close &gt; VWAP &amp; Close &lt; SMA<br>
    🛑 <b>Stop</b> → Entry ± ATR × Multiplier<br><br>
    <b style='color:#d1d4dc'>🇮🇳 NSE Examples</b><br>
    RELIANCE.NS · TCS.NS · INFY.NS<br>
    HDFCBANK.NS · SBIN.NS · ^NSEI
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="tv-header">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
    <div>
      <span style="font-size:16px;font-weight:700;color:#d1d4dc">
        📈 VWAP and MA Mean Reversion Strategy with ATR Stop Loss
      </span>
      <span style="margin-left:10px;font-size:11px;color:#787b86">
        SpringPad · Yahoo Finance
      </span>
    </div>
    <span style="font-size:11px;color:#787b86;background:#131722;
      padding:3px 12px;border-radius:20px;border:1px solid #2a2e39">
      🔵 Deep Backtesting
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(t, i, p):
    df = yf.download(t, interval=i, period=p, auto_adjust=True)
    df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
    return df.dropna()


def calc_indicators(df, ma_len, atr_len):
    df = df.copy()
    df["tp"]    = (df["high"]+df["low"]+df["close"])/3
    df["vwap"]  = (df["tp"]*df["volume"]).cumsum() / df["volume"].cumsum()
    df["ma"]    = df["close"].rolling(ma_len).mean()
    pc          = df["close"].shift(1)
    df["tr"]    = np.maximum(df["high"]-df["low"],
                  np.maximum(abs(df["high"]-pc), abs(df["low"]-pc)))
    df["atr"]   = df["tr"].rolling(atr_len).mean()
    return df.dropna()


def gen_signals(df, mult):
    df = df.copy()
    df["buy_sig"]   = (df["close"] < df["vwap"]) & (df["close"] > df["ma"])
    df["sell_sig"]  = (df["close"] > df["vwap"]) & (df["close"] < df["ma"])
    df["buy_stop"]  = df["close"] - mult * df["atr"]
    df["sell_stop"] = df["close"] + mult * df["atr"]
    return df


def backtest(df, cap):
    capital = float(cap)
    pos = entry_px = stop_px = 0.0
    entry_time = entry_bar = None
    trades, equity = [], []
    bah0 = float(df["close"].iloc[0])

    for i, (_, row) in enumerate(df.iterrows()):
        bar = i + 1
        # check stop
        if pos == 1 and float(row["low"]) <= stop_px:
            pnl = stop_px - entry_px
            capital += pnl
            trades.append(dict(
                num=len(trades)+1, type="Buy",
                entry_time=entry_time, exit_time=row.name,
                entry_bar=entry_bar, exit_bar=bar,
                bars=bar-entry_bar,
                entry_px=round(entry_px,2), exit_px=round(stop_px,2),
                exit_type="Stop Loss",
                pnl=round(pnl,2), pnl_pct=round(pnl/entry_px*100,3),
                result="Win" if pnl>0 else "Loss"
            ))
            pos = 0
        elif pos == -1 and float(row["high"]) >= stop_px:
            pnl = entry_px - stop_px
            capital += pnl
            trades.append(dict(
                num=len(trades)+1, type="Sell",
                entry_time=entry_time, exit_time=row.name,
                entry_bar=entry_bar, exit_bar=bar,
                bars=bar-entry_bar,
                entry_px=round(entry_px,2), exit_px=round(stop_px,2),
                exit_type="Stop Loss",
                pnl=round(pnl,2), pnl_pct=round(pnl/entry_px*100,3),
                result="Win" if pnl>0 else "Loss"
            ))
            pos = 0
        # new entry
        if pos == 0:
            if row["buy_sig"]:
                pos=1; entry_px=float(row["close"]); stop_px=float(row["buy_stop"])
                entry_time=row.name; entry_bar=bar
            elif row["sell_sig"]:
                pos=-1; entry_px=float(row["close"]); stop_px=float(row["sell_stop"])
                entry_time=row.name; entry_bar=bar
        equity.append(capital)

    df = df.copy()
    df["equity"]   = equity[:len(df)]
    df["bah"]      = [cap * float(df["close"].iloc[i]) / bah0 for i in range(len(df))]
    df["dd"]       = df["equity"] - df["equity"].cummax()
    df["dd_pct"]   = df["dd"] / df["equity"].cummax() * 100
    return df, pd.DataFrame(trades), capital


def stats(tdf, cap0, capN, df):
    s = {}
    n = len(tdf)
    s["n"] = n
    if n == 0:
        return s
    pnl   = tdf["pnl"]
    gp    = pnl[pnl>0].sum()
    gl    = abs(pnl[pnl<0].sum())
    wins  = int((pnl>0).sum())
    loss  = int((pnl<0).sum())

    s["net"]          = round(capN - cap0, 2)
    s["net_pct"]      = round((capN-cap0)/cap0*100, 2)
    s["gp"]           = round(gp, 2)
    s["gl"]           = round(gl, 2)
    s["pf"]           = round(gp/gl, 3) if gl else float("inf")
    s["wins"]         = wins
    s["losses"]       = loss
    s["wr"]           = round(wins/n*100, 2)
    s["avg_trade"]    = round(pnl.mean(), 2)
    s["avg_trade_pct"]= round(pnl.mean()/cap0*100, 3)
    s["avg_win"]      = round(pnl[pnl>0].mean(), 2) if wins else 0
    s["avg_loss"]     = round(pnl[pnl<0].mean(), 2) if loss else 0
    s["best"]         = round(pnl.max(), 2)
    s["worst"]        = round(pnl.min(), 2)
    s["avg_bars"]     = round(tdf["bars"].mean(), 1)
    s["avg_bars_win"] = round(tdf.loc[tdf["result"]=="Win","bars"].mean(), 1) if wins else 0
    s["avg_bars_loss"]= round(tdf.loc[tdf["result"]=="Loss","bars"].mean(), 1) if loss else 0

    dd = df["dd"]
    s["max_dd"]       = round(abs(dd.min()), 2)
    s["max_dd_pct"]   = round(abs(df["dd_pct"].min()), 2)

    # consecutive
    res = tdf["result"].tolist()
    mw=ml=cw=cl=0
    for r in res:
        if r=="Win":  cw+=1; cl=0
        else:         cl+=1; cw=0
        mw=max(mw,cw); ml=max(ml,cl)
    s["consec_win"]   = mw
    s["consec_loss"]  = ml

    # monthly breakdown
    tdf2 = tdf.copy()
    tdf2["month"] = pd.to_datetime(tdf2["entry_time"]).dt.to_period("M").astype(str)
    s["monthly"]  = tdf2.groupby("month")["pnl"].sum().reset_index()
    s["monthly"].columns = ["Month","P&L"]

    # win/loss by type
    buys  = tdf[tdf["type"]=="Buy"]
    sells = tdf[tdf["type"]=="Sell"]
    s["buy_n"]  = len(buys)
    s["sell_n"] = len(sells)
    s["buy_wr"] = round((buys["pnl"]>0).sum()/len(buys)*100, 1) if len(buys) else 0
    s["sell_wr"]= round((sells["pnl"]>0).sum()/len(sells)*100, 1) if len(sells) else 0

    return s


# ─────────────────────────────────────────────────────────────
#  CHART BUILDERS
# ─────────────────────────────────────────────────────────────
def overview_chart(df, cap0):
    x  = list(range(1, len(df)+1))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=x, y=df["equity"].tolist(), name="Equity",
        line=dict(color="#26a69a", width=1.5),
        fill="tozeroy", fillcolor="rgba(38,166,154,0.10)",
        hovertemplate="Bar %{x} | Equity: %{y:,.2f}<extra></extra>"
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=x, y=df["bah"].tolist(), name="Buy & Hold",
        line=dict(color="#2196f3", width=1.2, dash="dot"),
        hovertemplate="Bar %{x} | B&H: %{y:,.2f}<extra></extra>"
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=x, y=[cap0]*len(x), name="Start Capital",
        line=dict(color="#787b86", width=0.8, dash="dot"), hoverinfo="skip"
    ), secondary_y=False)
    dd_col = ["rgba(239,83,80,0.55)" if v<0 else "rgba(38,166,154,0.3)"
              for v in df["dd"].tolist()]
    fig.add_trace(go.Bar(
        x=x, y=df["dd"].tolist(), name="Drawdown",
        marker_color=dd_col, opacity=0.85,
        hovertemplate="Bar %{x} | DD: %{y:,.2f}<extra></extra>"
    ), secondary_y=True)
    fig.update_layout(
        height=360, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc", size=11),
        legend=dict(orientation="h", y=-0.22, x=0,
                    bgcolor="rgba(30,34,45,0.9)",
                    bordercolor="#2a2e39", borderwidth=1, font=dict(size=11)),
        hovermode="x unified", bargap=0,
        margin=dict(l=60,r=70,t=10,b=60)
    )
    fig.update_xaxes(gridcolor="#1e222d", title_text="Bar #", title_font_color="#787b86")
    fig.update_yaxes(gridcolor="#1e222d", title_text="Portfolio Value",
                     title_font_color="#787b86", secondary_y=False)
    fig.update_yaxes(gridcolor="#1e222d", title_text="Drawdown",
                     title_font_color="#787b86", secondary_y=True)
    return fig


def price_chart(df, ma_len):
    buys  = df[df["buy_sig"]]
    sells = df[df["sell_sig"]]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75,0.25], vertical_spacing=0.02,
                        subplot_titles=("Price · VWAP · SMA · Signals","ATR"))
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Price",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["vwap"],
        name="VWAP", line=dict(color="#2196f3",width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ma"],
        name=f"SMA {ma_len}", line=dict(color="#ff9800",width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=buys.index, y=buys["close"], mode="markers",
        name=f"Buy ({len(buys)})",
        marker=dict(symbol="triangle-up", color="#26a69a", size=11,
                    line=dict(color="#fff",width=1))), row=1, col=1)
    fig.add_trace(go.Scatter(x=sells.index, y=sells["close"], mode="markers",
        name=f"Sell ({len(sells)})",
        marker=dict(symbol="triangle-down", color="#ef5350", size=11,
                    line=dict(color="#fff",width=1))), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["atr"], name="ATR",
        line=dict(color="#9c27b0",width=1.5),
        fill="tozeroy", fillcolor="rgba(156,39,176,0.10)"), row=2, col=1)
    fig.update_layout(
        height=540, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(orientation="h", y=1.02,
                    bgcolor="rgba(30,34,45,0.8)",
                    bordercolor="#2a2e39",borderwidth=1,font=dict(size=10)),
        xaxis_rangeslider_visible=False,
        hovermode="x unified", margin=dict(l=60,r=20,t=30,b=40)
    )
    for i in [1,2]:
        fig.update_xaxes(gridcolor="#1e222d", row=i, col=1)
        fig.update_yaxes(gridcolor="#1e222d", row=i, col=1)
    fig.update_annotations(font_color="#787b86", font_size=11)
    return fig


def monthly_bar_chart(monthly_df):
    colors = ["#26a69a" if v>=0 else "#ef5350" for v in monthly_df["P&L"]]
    fig = go.Figure(go.Bar(
        x=monthly_df["Month"], y=monthly_df["P&L"],
        marker_color=colors, opacity=0.85,
        hovertemplate="%{x}<br>P&L: %{y:,.2f}<extra></extra>"
    ))
    fig.update_layout(
        height=220, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        margin=dict(l=50,r=20,t=10,b=50),
        showlegend=False, hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#1e222d", tickangle=-30)
    fig.update_yaxes(gridcolor="#1e222d")
    return fig


def pnl_distribution_chart(tdf):
    wins_data  = tdf.loc[tdf["result"]=="Win",  "pnl"]
    loss_data  = tdf.loc[tdf["result"]=="Loss", "pnl"]
    fig = go.Figure()
    if len(wins_data):
        fig.add_trace(go.Histogram(x=wins_data, name="Wins",
            marker_color="#26a69a", opacity=0.75, nbinsx=20,
            hovertemplate="P&L: %{x:,.2f}<br>Count: %{y}<extra></extra>"))
    if len(loss_data):
        fig.add_trace(go.Histogram(x=loss_data, name="Losses",
            marker_color="#ef5350", opacity=0.75, nbinsx=20,
            hovertemplate="P&L: %{x:,.2f}<br>Count: %{y}<extra></extra>"))
    fig.update_layout(
        height=220, barmode="overlay",
        paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(bgcolor="rgba(30,34,45,0.9)", bordercolor="#2a2e39",
                    borderwidth=1, font=dict(size=11)),
        margin=dict(l=50,r=20,t=10,b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#1e222d")
    fig.update_yaxes(gridcolor="#1e222d")
    return fig


def drawdown_chart(df):
    x = list(range(1, len(df)+1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=df["dd"].tolist(),
        fill="tozeroy", fillcolor="rgba(239,83,80,0.18)",
        line=dict(color="#ef5350", width=1.2),
        hovertemplate="Bar %{x}<br>DD: %{y:,.2f}<extra></extra>"
    ))
    fig.update_layout(
        height=180, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=10),
        margin=dict(l=60,r=20,t=8,b=30),
        showlegend=False, hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#1e222d")
    fig.update_yaxes(gridcolor="#1e222d")
    return fig


def equity_vs_bah_chart(df, cap0):
    x = list(range(1, len(df)+1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df["equity"].tolist(), name="Strategy Equity",
        line=dict(color="#26a69a",width=2),
        hovertemplate="Bar %{x} | Equity: %{y:,.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=df["bah"].tolist(), name="Buy & Hold",
        line=dict(color="#2196f3",width=1.5,dash="dot"),
        hovertemplate="Bar %{x} | B&H: %{y:,.2f}<extra></extra>"))
    fig.add_hline(y=cap0, line_color="#787b86", line_dash="dot", line_width=0.8)
    fig.update_layout(
        height=220, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(bgcolor="rgba(30,34,45,0.9)", bordercolor="#2a2e39",
                    borderwidth=1, font=dict(size=11)),
        margin=dict(l=60,r=20,t=10,b=30), hovermode="x unified"
    )
    fig.update_xaxes(gridcolor="#1e222d")
    fig.update_yaxes(gridcolor="#1e222d")
    return fig


# ─────────────────────────────────────────────────────────────
#  WELCOME SCREEN
# ─────────────────────────────────────────────────────────────
if not run_btn:
    st.markdown("""
    <div class="sc" style="text-align:center;padding:48px 24px">
      <div style="font-size:54px;margin-bottom:12px">📊</div>
      <h2 style="color:#d1d4dc;margin-bottom:8px">
        VWAP + MA Mean Reversion Strategy
      </h2>
      <p style="color:#787b86;font-size:13px;max-width:520px;margin:0 auto 24px">
        Configure settings in the sidebar and click
        <b style="color:#2196f3">🚀 Run Strategy</b>.
        Get a full TradingView-style backtest report instantly.
      </p>
      <div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap;margin-top:8px">
        <div style="text-align:center"><div style="font-size:24px">📈</div>
          <div style="color:#26a69a;font-weight:600;font-size:12px;margin-top:4px">Overview</div>
          <div style="color:#787b86;font-size:11px">Equity + Drawdown</div></div>
        <div style="text-align:center"><div style="font-size:24px">📊</div>
          <div style="color:#ff9800;font-weight:600;font-size:12px;margin-top:4px">Performance</div>
          <div style="color:#787b86;font-size:11px">25+ Metrics</div></div>
        <div style="text-align:center"><div style="font-size:24px">📋</div>
          <div style="color:#2196f3;font-weight:600;font-size:12px;margin-top:4px">Trade Log</div>
          <div style="color:#787b86;font-size:11px">Every trade detailed</div></div>
        <div style="text-align:center"><div style="font-size:24px">⚙️</div>
          <div style="color:#9c27b0;font-weight:600;font-size:12px;margin-top:4px">Properties</div>
          <div style="color:#787b86;font-size:11px">Full config breakdown</div></div>
      </div>
    </div>
    <div class="sc">
      <span style="color:#d1d4dc;font-size:12px;font-weight:600">💡 Indian Tickers &nbsp;</span>
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">RELIANCE.NS</code>&nbsp;
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">TCS.NS</code>&nbsp;
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">INFY.NS</code>&nbsp;
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">HDFCBANK.NS</code>&nbsp;
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">SBIN.NS</code>&nbsp;
      <code style="color:#26a69a;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">^NSEI</code>&nbsp;&nbsp;
      <code style="color:#2196f3;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">AAPL</code>&nbsp;
      <code style="color:#2196f3;background:#131722;padding:2px 7px;border-radius:3px;font-size:12px">BTC-USD</code>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────
#  RUN BACKTEST
# ─────────────────────────────────────────────────────────────
with st.spinner(f"📥 Fetching {ticker} …"):
    try:
        raw = fetch_data(ticker, interval, period)
        if raw.empty:
            st.error(f"❌ No data for **{ticker}**. Check the ticker.")
            st.stop()
    except Exception as e:
        st.error(f"❌ {e}")
        st.stop()

with st.spinner("⚙️ Running backtest …"):
    df   = calc_indicators(raw, ma_length, atr_length)
    df   = gen_signals(df, atr_mult)
    df, tdf, final_cap = backtest(df, starting_cap)
    s    = stats(tdf, starting_cap, final_cap, df)

# ── ticker info bar ──
try:
    fi   = yf.Ticker(ticker).fast_info
    lp   = fi.last_price; pc = fi.previous_close
    chg  = lp - pc; pct = chg/pc*100
    pc_  = "#26a69a" if chg>=0 else "#ef5350"
    arr  = "▲" if chg>=0 else "▼"
    px_h = f"""<span style="font-size:20px;font-weight:700;color:{pc_}">{lp:.2f}</span>
               <span style="color:{pc_};font-size:13px">&nbsp;{arr} {chg:+.2f} ({pct:+.2f}%)</span>"""
except Exception:
    px_h = ""

st.markdown(f"""
<div class="sc" style="padding:10px 18px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:10px">
  <span style="font-size:18px;font-weight:700;color:#d1d4dc">{ticker}</span>
  {px_h}
  <span style="color:#787b86;font-size:12px">
    {len(df)} bars &nbsp;|&nbsp; {interval} &nbsp;|&nbsp; {period}
    &nbsp;|&nbsp; {str(df.index[0])[:10]} → {str(df.index[-1])[:10]}
  </span>
</div>
""", unsafe_allow_html=True)

# ── 7-metric stats bar (exactly like TradingView screenshot) ──
if s.get("n", 0) > 0:
    np_c = "green" if s["net"]>=0 else "red"
    pf_c = "green" if s["pf"]>=1  else "red"
    wr_c = "green" if s["wr"]>=50  else "red"
    at_c = "green" if s["avg_trade"]>=0 else "red"
    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-item">
        <div class="stat-label">Net Profit ℹ</div>
        <div class="stat-value {np_c}">{s['net']:+,.2f} {currency}
          <span class="stat-pct {np_c}">({s['net_pct']:+.2f}%)</span></div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Total Closed Trades ℹ</div>
        <div class="stat-value">{s['n']}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Percent Profitable ℹ</div>
        <div class="stat-value {wr_c}">{s['wr']:.2f}%</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Profit Factor ℹ</div>
        <div class="stat-value {pf_c}">{s['pf']:.3f}</div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Max Drawdown ℹ</div>
        <div class="stat-value red">{s['max_dd']:,.2f} {currency}
          <span class="stat-pct red">({s['max_dd_pct']:.2f}%)</span></div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Avg Trade ℹ</div>
        <div class="stat-value {at_c}">{s['avg_trade']:+,.2f} {currency}
          <span class="stat-pct {at_c}">({s['avg_trade_pct']:+.3f}%)</span></div>
      </div>
      <div class="stat-item">
        <div class="stat-label">Avg # Bars in Trades ℹ</div>
        <div class="stat-value">{s['avg_bars']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("🔍 No completed trades. Try a longer period or different ticker.")


# ─────────────────────────────────────────────────────────────
#  TABS
# ─────────────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs(["Overview", "Performance Summary",
                            "List of Trades", "Properties"])


# ══════════════════════════════════════════════════════════════
#  TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════
with t1:
    st.markdown("#### Equity · Drawdown · Buy & Hold")
    st.plotly_chart(overview_chart(df, starting_cap), use_container_width=True)
    lc1,lc2,lc3,_ = st.columns([1,1,1.4,4])
    lc1.markdown("☑️ <span style='color:#26a69a;font-size:12px'>Equity</span>",
                 unsafe_allow_html=True)
    lc2.markdown("☑️ <span style='color:#ef5350;font-size:12px'>Drawdown</span>",
                 unsafe_allow_html=True)
    lc3.markdown("☑️ <span style='color:#2196f3;font-size:12px'>Buy & Hold Equity</span>",
                 unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Price Chart with Signals")
    st.plotly_chart(price_chart(df, ma_length), use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  TAB 2 — PERFORMANCE SUMMARY  (richly detailed)
# ══════════════════════════════════════════════════════════════
with t2:
    if not s.get("n"):
        st.info("No trades to summarize.")
        st.stop()

    # ── Row 1: three main cards ──
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""<div class="sc"><div class="sc-title">💰 P&L Overview</div>""",
                    unsafe_allow_html=True)
        # Net profit progress bar vs starting cap
        np_pct_bar = min(abs(s["net_pct"]), 100)
        bar_col    = "#26a69a" if s["net"]>=0 else "#ef5350"
        st.markdown(f"""
        <table class="pt">
        <tr><td>Net Profit</td>
            <td style="color:{bar_col};font-weight:700">{s['net']:+,.2f} {currency}
              &nbsp;<span style="font-size:11px">({s['net_pct']:+.2f}%)</span>
            </td></tr>
        <tr><td>Gross Profit</td>
            <td style="color:#26a69a;font-weight:600">{s['gp']:,.2f} {currency}</td></tr>
        <tr><td>Gross Loss</td>
            <td style="color:#ef5350;font-weight:600">−{s['gl']:,.2f} {currency}</td></tr>
        <tr><td>Profit Factor</td>
            <td style="color:{'#26a69a' if s['pf']>=1 else '#ef5350'};font-weight:700">
              {s['pf']:.3f}</td></tr>
        <tr><td>Buy & Hold Return</td>
            <td style="color:#2196f3;font-weight:600">
              {round((df['bah'].iloc[-1]-starting_cap)/starting_cap*100,2):+.2f}%</td></tr>
        <tr><td>Starting Capital</td>
            <td>{starting_cap:,.0f} {currency}</td></tr>
        <tr><td>Final Capital</td>
            <td style="font-weight:600">{final_cap:,.2f} {currency}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{np_pct_bar}%;background:{bar_col}"></div>
        </div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">
          Return vs Starting Capital</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""<div class="sc"><div class="sc-title">📊 Trade Statistics</div>""",
                    unsafe_allow_html=True)
        win_bar = min(s["wr"], 100)
        st.markdown(f"""
        <table class="pt">
        <tr><td>Total Closed Trades</td>
            <td style="font-weight:700">{s['n']}</td></tr>
        <tr><td>Winning Trades</td>
            <td style="color:#26a69a;font-weight:600">✅ {s['wins']}</td></tr>
        <tr><td>Losing Trades</td>
            <td style="color:#ef5350;font-weight:600">❌ {s['losses']}</td></tr>
        <tr><td>Percent Profitable</td>
            <td style="color:{'#26a69a' if s['wr']>=50 else '#ef5350'};font-weight:700">
              {s['wr']:.2f}%</td></tr>
        <tr><td>Long (Buy) Trades</td>
            <td style="color:#26a69a">{s['buy_n']}
              &nbsp;<span style="color:#787b86;font-size:11px">
              (WR: {s['buy_wr']}%)</span></td></tr>
        <tr><td>Short (Sell) Trades</td>
            <td style="color:#ef5350">{s['sell_n']}
              &nbsp;<span style="color:#787b86;font-size:11px">
              (WR: {s['sell_wr']}%)</span></td></tr>
        <tr><td>Avg # Bars in Trade</td>
            <td>{s['avg_bars']}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{win_bar}%;background:#26a69a"></div>
        </div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">
          Win Rate: {s['wr']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""<div class="sc"><div class="sc-title">📉 Drawdown & Risk</div>""",
                    unsafe_allow_html=True)
        dd_bar = min(s["max_dd_pct"], 100)
        st.markdown(f"""
        <table class="pt">
        <tr><td>Max Drawdown</td>
            <td style="color:#ef5350;font-weight:700">
              {s['max_dd']:,.2f} {currency}
              &nbsp;<span style="font-size:11px">({s['max_dd_pct']:.2f}%)</span></td></tr>
        <tr><td>Avg Win</td>
            <td style="color:#26a69a;font-weight:600">{s['avg_win']:+,.2f} {currency}</td></tr>
        <tr><td>Avg Loss</td>
            <td style="color:#ef5350;font-weight:600">{s['avg_loss']:+,.2f} {currency}</td></tr>
        <tr><td>Best Trade</td>
            <td style="color:#26a69a;font-weight:600">{s['best']:+,.2f} {currency}</td></tr>
        <tr><td>Worst Trade</td>
            <td style="color:#ef5350;font-weight:600">{s['worst']:+,.2f} {currency}</td></tr>
        <tr><td>Avg Trade</td>
            <td style="color:{'#26a69a' if s['avg_trade']>=0 else '#ef5350'}">
              {s['avg_trade']:+,.2f} {currency}
              <span style="font-size:11px">({s['avg_trade_pct']:+.3f}%)</span></td></tr>
        <tr><td>Avg Win / Avg Loss</td>
            <td>{round(abs(s['avg_win']/s['avg_loss']),2) if s['avg_loss'] else '∞'}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{dd_bar}%;background:#ef5350"></div>
        </div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">
          Max Drawdown: {s['max_dd_pct']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 2: Consecutive + Bars breakdown ──
    col4, col5 = st.columns(2)

    with col4:
        st.markdown("""<div class="sc"><div class="sc-title">🔁 Consecutive Trades</div>""",
                    unsafe_allow_html=True)
        cw_bar = min(s["consec_win"]*10,  100)
        cl_bar = min(s["consec_loss"]*10, 100)
        st.markdown(f"""
        <table class="pt">
        <tr><td>Max Consecutive Wins</td>
            <td style="color:#26a69a;font-weight:700">{s['consec_win']}</td></tr>
        <tr><td>Max Consecutive Losses</td>
            <td style="color:#ef5350;font-weight:700">{s['consec_loss']}</td></tr>
        </table>
        <div style="margin-top:12px">
          <div style="font-size:11px;color:#787b86;margin-bottom:4px">Consecutive Wins</div>
          <div class="pb-wrap">
            <div class="pb-fill" style="width:{cw_bar}%;background:#26a69a"></div></div>
          <div style="font-size:11px;color:#787b86;margin:10px 0 4px">Consecutive Losses</div>
          <div class="pb-wrap">
            <div class="pb-fill" style="width:{cl_bar}%;background:#ef5350"></div></div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown("""<div class="sc"><div class="sc-title">⏱️ Time in Trades</div>""",
                    unsafe_allow_html=True)
        wbars = s["avg_bars_win"]  if s["avg_bars_win"]  else 0
        lbars = s["avg_bars_loss"] if s["avg_bars_loss"] else 0
        max_b  = max(wbars, lbars, 1)
        st.markdown(f"""
        <table class="pt">
        <tr><td>Avg Bars in Winning Trades</td>
            <td style="color:#26a69a;font-weight:600">{wbars}</td></tr>
        <tr><td>Avg Bars in Losing Trades</td>
            <td style="color:#ef5350;font-weight:600">{lbars}</td></tr>
        <tr><td>Overall Avg Bars</td>
            <td style="font-weight:600">{s['avg_bars']}</td></tr>
        </table>
        <div style="margin-top:12px">
          <div style="font-size:11px;color:#787b86;margin-bottom:4px">Win Bars</div>
          <div class="pb-wrap">
            <div class="pb-fill" style="width:{min(wbars/max_b*100,100):.0f}%;background:#26a69a"></div></div>
          <div style="font-size:11px;color:#787b86;margin:10px 0 4px">Loss Bars</div>
          <div class="pb-wrap">
            <div class="pb-fill" style="width:{min(lbars/max_b*100,100):.0f}%;background:#ef5350"></div></div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Row 3: Charts ──
    st.markdown("---")
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("""<div class="sc"><div class="sc-title">📅 Monthly P&L</div></div>""",
                    unsafe_allow_html=True)
        if len(s["monthly"]) > 0:
            st.plotly_chart(monthly_bar_chart(s["monthly"]), use_container_width=True)
        else:
            st.info("Not enough data for monthly breakdown.")

    with ch2:
        st.markdown("""<div class="sc"><div class="sc-title">📊 P&L Distribution (Wins vs Losses)</div></div>""",
                    unsafe_allow_html=True)
        st.plotly_chart(pnl_distribution_chart(tdf), use_container_width=True)

    # ── Row 4: Drawdown + Equity vs B&H ──
    st.markdown("""<div class="sc"><div class="sc-title">📉 Drawdown Over Time</div></div>""",
                unsafe_allow_html=True)
    st.plotly_chart(drawdown_chart(df), use_container_width=True)

    st.markdown("""<div class="sc"><div class="sc-title">📈 Strategy Equity vs Buy & Hold</div></div>""",
                unsafe_allow_html=True)
    st.plotly_chart(equity_vs_bah_chart(df, starting_cap), use_container_width=True)


# ══════════════════════════════════════════════════════════════
#  TAB 3 — LIST OF TRADES  (full detailed table + filters)
# ══════════════════════════════════════════════════════════════
with t3:
    if len(tdf) == 0:
        st.info("No completed trades in this period.")
    else:
        # ── Filter row ──
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
        f_type   = fc1.selectbox("Filter by Type",   ["All","Buy (Long)","Sell (Short)"])
        f_result = fc2.selectbox("Filter by Result", ["All","Win","Loss"])
        f_sort   = fc3.selectbox("Sort by",          ["# (Default)","P&L ↑","P&L ↓",
                                                       "Entry Time","Bars Held"])
        f_n      = fc4.number_input("Show last N trades (0 = all)", 0, step=10)

        disp = tdf.copy()
        if f_type == "Buy (Long)":       disp = disp[disp["type"]=="Buy"]
        elif f_type == "Sell (Short)":   disp = disp[disp["type"]=="Sell"]
        if f_result == "Win":            disp = disp[disp["result"]=="Win"]
        elif f_result == "Loss":         disp = disp[disp["result"]=="Loss"]
        if f_sort == "P&L ↑":           disp = disp.sort_values("pnl", ascending=True)
        elif f_sort == "P&L ↓":         disp = disp.sort_values("pnl", ascending=False)
        elif f_sort == "Entry Time":     disp = disp.sort_values("entry_time")
        elif f_sort == "Bars Held":      disp = disp.sort_values("bars", ascending=False)
        if f_n > 0:                      disp = disp.tail(int(f_n))

        # summary strip
        f_wins   = int((disp["pnl"]>0).sum())
        f_losses = int((disp["pnl"]<0).sum())
        f_pnl    = round(disp["pnl"].sum(), 2)
        f_wr     = round(f_wins/len(disp)*100,1) if len(disp) else 0
        f_pnl_c  = "#26a69a" if f_pnl>=0 else "#ef5350"

        st.markdown(f"""
        <div class="sc" style="padding:10px 16px;display:flex;gap:24px;flex-wrap:wrap;align-items:center;margin-bottom:10px">
          <span style="color:#787b86;font-size:12px">Showing
            <b style="color:#d1d4dc">{len(disp)}</b> trades</span>
          <span style="color:#26a69a;font-size:12px">✅ Wins: <b>{f_wins}</b></span>
          <span style="color:#ef5350;font-size:12px">❌ Losses: <b>{f_losses}</b></span>
          <span style="color:#d1d4dc;font-size:12px">Win Rate: <b>{f_wr:.1f}%</b></span>
          <span style="color:{f_pnl_c};font-size:12px;font-weight:600">
            Total P&L: {f_pnl:+,.2f} {currency}</span>
        </div>
        """, unsafe_allow_html=True)

        # build table
        rows = ""
        running_pnl = 0
        for _, r in disp.iterrows():
            running_pnl += r["pnl"]
            is_buy = r["type"] == "Buy"
            tc     = "#26a69a" if is_buy else "#ef5350"
            pc     = "#26a69a" if r["pnl"]>=0 else "#ef5350"
            rc     = "#26a69a" if r["pnl"]>=0 else "#ef5350"
            sign   = "+" if r["pnl"]>=0 else ""
            rp_c   = "#26a69a" if running_pnl>=0 else "#ef5350"
            t_lbl  = f"<span style='color:{tc};font-weight:600'>{'▲ Long' if is_buy else '▼ Short'}</span>"
            res_b  = f"<span class='badge' style='background:{'#1a3a1f' if r['pnl']>=0 else '#3a1a1a'};color:{rc};border:1px solid {rc}'>{'Win' if r['pnl']>=0 else 'Loss'}</span>"

            rows += f"""
            <tr>
              <td style="color:#787b86">{int(r['num'])}</td>
              <td>{t_lbl}</td>
              <td style="color:#787b86">{str(r['entry_time'])[:16]}</td>
              <td style="color:#787b86">{str(r['exit_time'])[:16]}</td>
              <td>{int(r['entry_bar'])}</td>
              <td>{int(r['exit_bar'])}</td>
              <td style="color:#787b86;text-align:center">{int(r['bars'])}</td>
              <td>{r['entry_px']:.2f}</td>
              <td>{r['exit_px']:.2f}</td>
              <td><span style="color:#ff9800;font-size:11px;background:#1a1e2b;
                padding:2px 6px;border-radius:3px">Stop Loss</span></td>
              <td style="color:{pc};font-weight:600">{sign}{r['pnl']:.2f}</td>
              <td style="color:{pc}">{r['pnl_pct']:+.3f}%</td>
              <td style="color:{rp_c};font-size:11px">{running_pnl:+,.2f}</td>
              <td>{res_b}</td>
            </tr>"""

        st.markdown(f"""
        <div style="overflow:auto;max-height:480px;
          border:1px solid #2a2e39;border-radius:6px">
        <table class="tt">
          <thead><tr>
            <th>#</th><th>Type</th>
            <th>Entry Time</th><th>Exit Time</th>
            <th>Entry Bar</th><th>Exit Bar</th><th>Bars</th>
            <th>Entry {currency}</th><th>Exit {currency}</th>
            <th>Exit Type</th>
            <th>P&L ({currency})</th><th>P&L %</th>
            <th>Cum. P&L</th><th>Result</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        dl1, dl2, _ = st.columns([1.5, 1.5, 5])
        csv_all = tdf.to_csv(index=False).encode("utf-8")
        csv_flt = disp.to_csv(index=False).encode("utf-8")
        dl1.download_button("⬇️ Export All Trades",
                            csv_all, f"{ticker}_all_trades.csv",
                            "text/csv", type="primary")
        dl2.download_button("⬇️ Export Filtered",
                            csv_flt, f"{ticker}_filtered_trades.csv",
                            "text/csv")


# ══════════════════════════════════════════════════════════════
#  TAB 4 — PROPERTIES  (full config breakdown)
# ══════════════════════════════════════════════════════════════
with t4:
    pc1, pc2, pc3 = st.columns(3)

    with pc1:
        st.markdown(f"""
        <div class="sc">
          <div class="sc-title">📌 Asset & Data</div>
          <table class="pt">
            <tr><td>Ticker Symbol</td>
                <td style="color:#d1d4dc;font-weight:700">{ticker}</td></tr>
            <tr><td>Exchange / Suffix</td>
                <td style="color:#787b86">{'.NS (NSE)' if ticker.endswith('.NS') else
                                            '.BO (BSE)' if ticker.endswith('.BO') else
                                            'Global'}</td></tr>
            <tr><td>Chart Interval</td>
                <td style="color:#d1d4dc">{interval}</td></tr>
            <tr><td>Lookback Period</td>
                <td style="color:#d1d4dc">{period}</td></tr>
            <tr><td>Total Bars</td>
                <td style="color:#d1d4dc">{len(df)}</td></tr>
            <tr><td>Data From</td>
                <td style="color:#787b86">{str(df.index[0])[:16]}</td></tr>
            <tr><td>Data To</td>
                <td style="color:#787b86">{str(df.index[-1])[:16]}</td></tr>
            <tr><td>Data Source</td>
                <td style="color:#2196f3">Yahoo Finance</td></tr>
            <tr><td>Currency</td>
                <td style="color:#d1d4dc">{currency}</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    with pc2:
        st.markdown(f"""
        <div class="sc">
          <div class="sc-title">📐 Indicator Parameters</div>
          <table class="pt">
            <tr><td>Strategy Name</td>
                <td style="color:#d1d4dc;font-size:11px">VWAP + MA Mean Reversion</td></tr>
            <tr><td>VWAP Source</td>
                <td style="color:#2196f3;font-weight:600">HLC3 (Typical Price)</td></tr>
            <tr><td>Moving Average Type</td>
                <td style="color:#ff9800;font-weight:600">SMA (Simple)</td></tr>
            <tr><td>MA Length</td>
                <td style="color:#ff9800;font-weight:700">{ma_length} bars</td></tr>
            <tr><td>ATR Length</td>
                <td style="color:#9c27b0;font-weight:700">{atr_length} bars</td></tr>
            <tr><td>ATR Multiplier</td>
                <td style="color:#9c27b0;font-weight:700">{atr_mult}×</td></tr>
            <tr><td>Buy Signals Generated</td>
                <td style="color:#26a69a;font-weight:600">{int(df['buy_sig'].sum())}</td></tr>
            <tr><td>Sell Signals Generated</td>
                <td style="color:#ef5350;font-weight:600">{int(df['sell_sig'].sum())}</td></tr>
            <tr><td>PineScript Version</td>
                <td style="color:#787b86">v5 equivalent</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    with pc3:
        st.markdown(f"""
        <div class="sc">
          <div class="sc-title">💰 Capital & Risk Management</div>
          <table class="pt">
            <tr><td>Starting Capital</td>
                <td style="color:#26a69a;font-weight:700">{starting_cap:,.0f} {currency}</td></tr>
            <tr><td>Final Capital</td>
                <td style="color:#d1d4dc;font-weight:700">{final_cap:,.2f} {currency}</td></tr>
            <tr><td>Net Return</td>
                <td style="color:{'#26a69a' if s.get('net',0)>=0 else '#ef5350'};font-weight:700">
                  {s.get('net_pct',0):+.2f}%</td></tr>
            <tr><td>Stop Loss Type</td>
                <td style="color:#ef5350;font-weight:600">ATR-Based Dynamic</td></tr>
            <tr><td>Take Profit</td>
                <td style="color:#787b86">Not defined</td></tr>
            <tr><td>Position Sizing</td>
                <td style="color:#787b86">1 unit per signal</td></tr>
            <tr><td>Trade Directions</td>
                <td style="color:#d1d4dc">Long & Short</td></tr>
            <tr><td>Max Open Positions</td>
                <td style="color:#d1d4dc">1 at a time</td></tr>
            <tr><td>Commission / Slippage</td>
                <td style="color:#787b86">Not modelled</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Entry/Exit Rules card ──
    st.markdown(f"""
    <div class="sc">
      <div class="sc-title">📖 Entry & Exit Rules (PineScript → Python)</div>
      <table class="pt" style="font-size:12px">
        <tr>
          <td style="width:18%;color:#26a69a;font-weight:600">▲ BUY (Long)</td>
          <td>
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
              close &lt; VWAP</code>
            &nbsp;<b style="color:#787b86">AND</b>&nbsp;
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
              close &gt; SMA({ma_length})</code>
            &nbsp;→&nbsp;
            <span style="color:#787b86">Price is <b style="color:#26a69a">undervalued</b>
            vs VWAP but trend is <b style="color:#26a69a">bullish</b> vs SMA</span>
          </td>
        </tr>
        <tr>
          <td style="color:#ef5350;font-weight:600">▼ SELL (Short)</td>
          <td>
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
              close &gt; VWAP</code>
            &nbsp;<b style="color:#787b86">AND</b>&nbsp;
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
              close &lt; SMA({ma_length})</code>
            &nbsp;→&nbsp;
            <span style="color:#787b86">Price is <b style="color:#ef5350">overvalued</b>
            vs VWAP but trend is <b style="color:#ef5350">bearish</b> vs SMA</span>
          </td>
        </tr>
        <tr>
          <td style="color:#ef5350;font-weight:600">🛑 LONG Stop</td>
          <td>
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#ef5350">
              entry − {atr_mult} × ATR({atr_length})</code>
            &nbsp;→&nbsp;
            <span style="color:#787b86">Dynamic stop widens in volatile markets</span>
          </td>
        </tr>
        <tr>
          <td style="color:#ef5350;font-weight:600">🛑 SHORT Stop</td>
          <td>
            <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#ef5350">
              entry + {atr_mult} × ATR({atr_length})</code>
            &nbsp;→&nbsp;
            <span style="color:#787b86">Dynamic stop widens in volatile markets</span>
          </td>
        </tr>
        <tr>
          <td style="color:#ff9800;font-weight:600">✖ EXIT</td>
          <td>
            <span style="color:#787b86">Stop Loss only. No take-profit target defined.
            Trades exit when stop is hit by Low (long) or High (short).</span>
          </td>
        </tr>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # ── Disclaimer ──
    st.markdown("""
    <div class="sc" style="border-color:#2a2e39;background:#131722;padding:12px 18px">
      <span style="color:#787b86;font-size:11px">
        ⚠️ <b style="color:#d1d4dc">Disclaimer:</b>
        This tool is for educational and research purposes only.
        Backtested results do not guarantee future performance.
        Commission, slippage, and market impact are not modelled.
        Not financial advice. Always conduct your own due diligence before trading.
      </span>
    </div>
    """, unsafe_allow_html=True)

# ── footer ──
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#787b86;font-size:11px;padding:4px">
  SpringPad VWAP Strategy &nbsp;|&nbsp; Streamlit + Plotly + Yahoo Finance
  &nbsp;|&nbsp; Educational purposes only
</div>
""", unsafe_allow_html=True)
