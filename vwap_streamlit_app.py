# ============================================================
#   SpringPad's VWAP + MA Mean Reversion Strategy
#   🚀 TradingView-Style — Symbol Search + Full Dashboard
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

st.set_page_config(page_title="SpringPad VWAP Strategy",
                   page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────
#  SYMBOL DATABASE  (mirrors TradingView categories)
# ─────────────────────────────────────────────────────────────
SYMBOLS = [
    # ── Indices ──
    {"sym":"^NSEI",        "name":"NIFTY 50 INDEX",                  "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^NSEBANK",     "name":"NIFTY BANK INDEX",                "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^BSESN",       "name":"S&P BSE SENSEX",                  "type":"index",   "cat":"Indices",  "exch":"BSE",  "flag":"🇮🇳"},
    {"sym":"^CNXIT",       "name":"NIFTY IT INDEX",                  "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXAUTO",     "name":"NIFTY AUTO INDEX",                "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXPHARMA",   "name":"NIFTY PHARMA INDEX",              "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXFMCG",     "name":"NIFTY FMCG INDEX",                "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXMETAL",    "name":"NIFTY METAL INDEX",               "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXREALTY",   "name":"NIFTY REALTY INDEX",              "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXMIDCAP",   "name":"NIFTY MIDCAP 100",                "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^CNXSMALLCAP", "name":"NIFTY SMALLCAP 100",              "type":"index",   "cat":"Indices",  "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"^GSPC",        "name":"S&P 500 INDEX",                   "type":"index",   "cat":"Indices",  "exch":"NYSE", "flag":"🇺🇸"},
    {"sym":"^DJI",         "name":"DOW JONES INDUSTRIAL AVG",        "type":"index",   "cat":"Indices",  "exch":"NYSE", "flag":"🇺🇸"},
    {"sym":"^IXIC",        "name":"NASDAQ COMPOSITE",                "type":"index",   "cat":"Indices",  "exch":"NASDAQ","flag":"🇺🇸"},
    # ── Stocks — NSE ──
    {"sym":"RELIANCE.NS",  "name":"RELIANCE INDUSTRIES LTD",         "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TCS.NS",       "name":"TATA CONSULTANCY SERVICES",       "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"INFY.NS",      "name":"INFOSYS LTD",                     "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"HDFCBANK.NS",  "name":"HDFC BANK LTD",                   "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ICICIBANK.NS", "name":"ICICI BANK LTD",                  "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"SBIN.NS",      "name":"STATE BANK OF INDIA",             "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"WIPRO.NS",     "name":"WIPRO LTD",                       "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"BAJFINANCE.NS","name":"BAJAJ FINANCE LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TATAMOTORS.NS","name":"TATA MOTORS LTD",                 "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"HINDUNILVR.NS","name":"HINDUSTAN UNILEVER LTD",          "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"MARUTI.NS",    "name":"MARUTI SUZUKI INDIA LTD",         "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"SUNPHARMA.NS", "name":"SUN PHARMACEUTICAL IND LTD",      "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ONGC.NS",      "name":"OIL & NATURAL GAS CORP LTD",      "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"LT.NS",        "name":"LARSEN & TOUBRO LTD",             "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ADANIENT.NS",  "name":"ADANI ENTERPRISES LTD",           "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ADANIPORTS.NS","name":"ADANI PORTS & SEZ LTD",           "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"KOTAKBANK.NS", "name":"KOTAK MAHINDRA BANK LTD",         "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"AXISBANK.NS",  "name":"AXIS BANK LTD",                   "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ITC.NS",       "name":"ITC LTD",                         "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"NTPC.NS",      "name":"NTPC LTD",                        "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"POWERGRID.NS", "name":"POWER GRID CORP OF INDIA",        "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"BAJAJFINSV.NS","name":"BAJAJ FINSERV LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ULTRACEMCO.NS","name":"ULTRATECH CEMENT LTD",            "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"HCLTECH.NS",   "name":"HCL TECHNOLOGIES LTD",            "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TITAN.NS",     "name":"TITAN COMPANY LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TECHM.NS",     "name":"TECH MAHINDRA LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"ASIANPAINT.NS","name":"ASIAN PAINTS LTD",                "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"NESTLEIND.NS", "name":"NESTLE INDIA LTD",                "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"DRREDDY.NS",   "name":"DR REDDYS LABORATORIES LTD",      "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"CIPLA.NS",     "name":"CIPLA LTD",                       "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"DIVISLAB.NS",  "name":"DIVIS LABORATORIES LTD",          "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TATACONSUM.NS","name":"TATA CONSUMER PRODUCTS LTD",      "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"HEROMOTOCO.NS","name":"HERO MOTOCORP LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"EICHERMOT.NS", "name":"EICHER MOTORS LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"INDUSINDBK.NS","name":"INDUSIND BANK LTD",               "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"VEDL.NS",      "name":"VEDANTA LTD",                     "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"TATASTEEL.NS", "name":"TATA STEEL LTD",                  "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"JSWSTEEL.NS",  "name":"JSW STEEL LTD",                   "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"COALINDIA.NS", "name":"COAL INDIA LTD",                  "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"GRASIM.NS",    "name":"GRASIM INDUSTRIES LTD",           "type":"stock",   "cat":"Stocks",   "exch":"NSE",  "flag":"🇮🇳"},
    # ── US Stocks ──
    {"sym":"AAPL",         "name":"APPLE INC",                       "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"MSFT",         "name":"MICROSOFT CORP",                  "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"GOOGL",        "name":"ALPHABET INC CLASS A",            "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"AMZN",         "name":"AMAZON.COM INC",                  "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"TSLA",         "name":"TESLA INC",                       "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"NVDA",         "name":"NVIDIA CORP",                     "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"META",         "name":"META PLATFORMS INC",              "type":"stock",   "cat":"Stocks",   "exch":"NASDAQ","flag":"🇺🇸"},
    {"sym":"JPM",          "name":"JPMORGAN CHASE & CO",             "type":"stock",   "cat":"Stocks",   "exch":"NYSE",  "flag":"🇺🇸"},
    # ── Crypto ──
    {"sym":"BTC-USD",      "name":"BITCOIN USD",                     "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"🟡"},
    {"sym":"ETH-USD",      "name":"ETHEREUM USD",                    "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"🔵"},
    {"sym":"BNB-USD",      "name":"BINANCE COIN USD",                "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"🟠"},
    {"sym":"SOL-USD",      "name":"SOLANA USD",                      "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"🟣"},
    {"sym":"XRP-USD",      "name":"XRP USD",                         "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"⚪"},
    {"sym":"DOGE-USD",     "name":"DOGECOIN USD",                    "type":"crypto",  "cat":"Crypto",   "exch":"Crypto","flag":"🟡"},
    # ── Forex ──
    {"sym":"USDINR=X",     "name":"USD/INR FOREX PAIR",              "type":"forex",   "cat":"Forex",    "exch":"FX",   "flag":"💱"},
    {"sym":"EURUSD=X",     "name":"EUR/USD FOREX PAIR",              "type":"forex",   "cat":"Forex",    "exch":"FX",   "flag":"💱"},
    {"sym":"GBPUSD=X",     "name":"GBP/USD FOREX PAIR",              "type":"forex",   "cat":"Forex",    "exch":"FX",   "flag":"💱"},
    {"sym":"USDJPY=X",     "name":"USD/JPY FOREX PAIR",              "type":"forex",   "cat":"Forex",    "exch":"FX",   "flag":"💱"},
    # ── Futures ──
    {"sym":"^NSEI",        "name":"NIFTY 50 INDEX (Nifty Futures Proxy)","type":"futures","cat":"Futures","exch":"NSE", "flag":"🇮🇳"},
    {"sym":"GC=F",         "name":"GOLD FUTURES",                    "type":"futures", "cat":"Futures",  "exch":"COMEX","flag":"🟡"},
    {"sym":"CL=F",         "name":"CRUDE OIL FUTURES (WTI)",         "type":"futures", "cat":"Futures",  "exch":"NYMEX","flag":"🛢️"},
    {"sym":"SI=F",         "name":"SILVER FUTURES",                  "type":"futures", "cat":"Futures",  "exch":"COMEX","flag":"⚪"},
    {"sym":"ES=F",         "name":"E-MINI S&P 500 FUTURES",          "type":"futures", "cat":"Futures",  "exch":"CME",  "flag":"🇺🇸"},
    {"sym":"NQ=F",         "name":"E-MINI NASDAQ 100 FUTURES",       "type":"futures", "cat":"Futures",  "exch":"CME",  "flag":"🇺🇸"},
    # ── ETFs / Funds ──
    {"sym":"GOLDBEES.NS",  "name":"NIPPON INDIA ETF GOLD BEES",      "type":"etf",     "cat":"Funds",    "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"NIFTYBEES.NS", "name":"NIPPON INDIA ETF NIFTY BEES",     "type":"etf",     "cat":"Funds",    "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"BANKBEES.NS",  "name":"NIPPON INDIA ETF BANK BEES",      "type":"etf",     "cat":"Funds",    "exch":"NSE",  "flag":"🇮🇳"},
    {"sym":"SPY",          "name":"SPDR S&P 500 ETF TRUST",          "type":"etf",     "cat":"Funds",    "exch":"NYSE", "flag":"🇺🇸"},
    {"sym":"QQQ",          "name":"INVESCO QQQ TRUST SERIES 1",      "type":"etf",     "cat":"Funds",    "exch":"NASDAQ","flag":"🇺🇸"},
]

CATEGORIES = ["All","Stocks","Indices","Futures","Forex","Crypto","Funds"]

# ─────────────────────────────────────────────────────────────
#  TRADINGVIEW → YFINANCE SYMBOL MAPPING
# ─────────────────────────────────────────────────────────────
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
    "CNXREALTY":   "^CNXREALTY","CNXMIDCAP":  "^CNXMIDCAP",
    "CNXSMALLCAP": "^CNXSMALLCAP","CNXIT":    "^CNXIT",
}

def resolve_ticker(raw: str) -> str:
    """Convert TV-style or shorthand to valid yfinance ticker."""
    t = raw.strip().upper()
    return TV_TO_YF.get(t, t)

# Period clamps per interval (yfinance limits)
MAX_PERIOD = {
    "1m":"7d","2m":"60d","5m":"60d","15m":"60d",
    "30m":"60d","60m":"730d","1h":"730d","1d":"max",
}


TYPE_COLORS = {
    "stock":   ("#1a3a1f","#26a69a"),
    "index":   ("#1a2a3a","#2196f3"),
    "futures": ("#2a1a3a","#9c27b0"),
    "forex":   ("#2a2a1a","#ff9800"),
    "crypto":  ("#3a2a1a","#ff5722"),
    "etf":     ("#1a1a3a","#4caf50"),
}

def search_symbols(query, category):
    q = query.strip().upper()
    results = []
    for s in SYMBOLS:
        if category != "All" and s["cat"] != category:
            continue
        if q == "":
            results.append(s)
        elif q in s["sym"].upper() or q in s["name"].upper():
            results.append(s)
    return results[:30]


# ─────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .stApp{background:#131722;color:#d1d4dc}
  section[data-testid="stSidebar"]{background:#1e222d;border-right:1px solid #2a2e39}

  div[data-testid="metric-container"]{background:#1e222d;border:1px solid #2a2e39;
    border-radius:6px;padding:10px 14px}
  div[data-testid="metric-container"] label{color:#787b86!important;font-size:11px!important}
  div[data-testid="metric-container"] div[data-testid="stMetricValue"]{
    color:#d1d4dc!important;font-size:17px!important;font-weight:700!important}

  .stTabs [data-baseweb="tab-list"]{background:#1e222d;border-radius:6px 6px 0 0;
    border-bottom:1px solid #2a2e39;gap:0;padding:0}
  .stTabs [data-baseweb="tab"]{color:#787b86;border-radius:0;padding:10px 22px;
    font-size:13px;border-bottom:2px solid transparent}
  .stTabs [aria-selected="true"]{background:transparent!important;
    color:#d1d4dc!important;border-bottom:2px solid #2196f3!important}

  .tv-header{background:#1e222d;border:1px solid #2a2e39;border-radius:8px;
    padding:14px 20px;margin-bottom:16px}

  .stats-bar{display:flex;flex-wrap:wrap;background:#1e222d;
    border:1px solid #2a2e39;border-radius:8px;margin-bottom:16px;overflow:hidden}
  .stat-item{flex:1;min-width:120px;padding:13px 16px;border-right:1px solid #2a2e39}
  .stat-item:last-child{border-right:none}
  .stat-label{font-size:11px;color:#787b86;margin-bottom:3px}
  .stat-value{font-size:14px;font-weight:700;color:#d1d4dc}
  .stat-pct{font-size:11px;margin-left:4px}
  .green{color:#26a69a}.red{color:#ef5350}.blue{color:#2196f3}.orange{color:#ff9800}

  .sc{background:#1e222d;border:1px solid #2a2e39;border-radius:8px;
    padding:16px 20px;margin-bottom:14px}
  .sc-title{font-size:12px;font-weight:600;color:#d1d4dc;margin-bottom:12px;
    padding-bottom:8px;border-bottom:1px solid #2a2e39}

  /* Symbol Search */
  .sym-search-box{background:#131722;border:1px solid #2a2e39;border-radius:10px;
    overflow:hidden;max-width:700px;margin:0 auto}
  .sym-search-header{padding:16px 18px 10px;border-bottom:1px solid #2a2e39}
  .sym-search-title{font-size:16px;font-weight:700;color:#d1d4dc;margin-bottom:10px}
  .sym-row{display:flex;align-items:center;gap:14px;padding:10px 16px;
    cursor:pointer;border-bottom:1px solid #1a1e2b;transition:background 0.15s}
  .sym-row:hover{background:#1c2128}
  .sym-row:last-child{border-bottom:none}
  .sym-icon{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;
    justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}
  .sym-ticker{font-size:13px;font-weight:700;color:#d1d4dc;min-width:120px}
  .sym-name{font-size:12px;color:#787b86;flex:1;white-space:nowrap;
    overflow:hidden;text-overflow:ellipsis}
  .sym-type{font-size:11px;padding:2px 6px;border-radius:4px;margin-right:6px}
  .sym-exch{font-size:11px;color:#787b86}

  /* cat pills */
  .cat-pills{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
  .cat-pill{background:#2a2e39;color:#d1d4dc;border:1px solid #2a2e39;
    border-radius:20px;padding:4px 12px;font-size:12px;cursor:pointer;
    white-space:nowrap}
  .cat-pill.active{background:#2196f3;color:#fff;border-color:#2196f3}

  .pt{width:100%;border-collapse:collapse;font-size:12px}
  .pt td{padding:7px 10px;border-bottom:1px solid #1a1e2b;color:#d1d4dc}
  .pt td:first-child{color:#787b86;width:58%}
  .pt tr:last-child td{border-bottom:none}
  .pt tr:hover td{background:#1c2128}

  .tt{width:100%;border-collapse:collapse;font-size:12px}
  .tt th{background:#1e222d;color:#787b86;padding:9px 11px;text-align:left;
    border-bottom:1px solid #2a2e39;font-weight:500;white-space:nowrap}
  .tt td{padding:7px 11px;border-bottom:1px solid #1a1e2b;color:#d1d4dc;white-space:nowrap}
  .tt tr:nth-child(even) td{background:#1a1e2b}
  .tt tr:hover td{background:#2a2e39}

  .pb-wrap{background:#2a2e39;border-radius:4px;height:6px;overflow:hidden;margin-top:4px}
  .pb-fill{height:6px;border-radius:4px}
  .badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}
  hr{border-color:#2a2e39!important}

  /* radio buttons / selectbox dark */
  div[data-baseweb="select"] > div{background:#1e222d!important;border-color:#2a2e39!important;color:#d1d4dc!important}
  div[data-baseweb="select"] svg{fill:#787b86!important}
  .stTextInput input{background:#1e222d!important;border-color:#2a2e39!important;color:#d1d4dc!important}
  .stTextInput input::placeholder{color:#787b86!important}
  .stButton>button{background:#1e222d;border:1px solid #2a2e39;color:#d1d4dc;
    border-radius:6px;transition:all 0.2s}
  .stButton>button:hover{background:#2a2e39;border-color:#787b86}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────
if "selected_sym"   not in st.session_state: st.session_state.selected_sym   = "RELIANCE.NS"
if "show_search"    not in st.session_state: st.session_state.show_search    = False
if "search_query"   not in st.session_state: st.session_state.search_query   = ""
if "search_cat"     not in st.session_state: st.session_state.search_cat     = "All"


# ─────────────────────────────────────────────────────────────
#  SYMBOL SEARCH PANEL  (shown inline when open)
# ─────────────────────────────────────────────────────────────
def symbol_search_panel():
    st.markdown("""
    <div style="background:#1e222d;border:1px solid #2a2e39;border-radius:12px;
      padding:20px;margin-bottom:16px;max-width:800px">
      <div style="font-size:16px;font-weight:700;color:#d1d4dc;margin-bottom:14px;
        display:flex;align-items:center;gap:10px">
        🔍 Symbol Search
        <span style="font-size:11px;color:#787b86;font-weight:400">
          — search by name or ticker</span>
      </div>
    """, unsafe_allow_html=True)

    # Search input
    sq = st.text_input("", placeholder="Search — e.g. NIFTY, RELIANCE, BTC, AAPL …",
                       value=st.session_state.search_query,
                       key="sym_input", label_visibility="collapsed")
    st.session_state.search_query = sq

    # Category filter pills (using radio as buttons)
    cat = st.radio("Category", CATEGORIES,
                   index=CATEGORIES.index(st.session_state.search_cat),
                   horizontal=True, key="sym_cat",
                   label_visibility="collapsed")
    st.session_state.search_cat = cat

    st.markdown("---")

    # Results
    results = search_symbols(sq, cat)

    if not results:
        st.markdown("<div style='color:#787b86;font-size:13px;padding:12px 0'>No symbols found.</div>",
                    unsafe_allow_html=True)
    else:
        # Build result rows
        cols_header = st.columns([0.5, 2, 4, 1.5, 1])
        cols_header[0].markdown("<span style='color:#787b86;font-size:11px'></span>",
                                unsafe_allow_html=True)
        cols_header[1].markdown("<span style='color:#787b86;font-size:11px'>SYMBOL</span>",
                                unsafe_allow_html=True)
        cols_header[2].markdown("<span style='color:#787b86;font-size:11px'>NAME</span>",
                                unsafe_allow_html=True)
        cols_header[3].markdown("<span style='color:#787b86;font-size:11px'>TYPE · EXCH</span>",
                                unsafe_allow_html=True)
        cols_header[4].markdown("<span style='color:#787b86;font-size:11px'></span>",
                                unsafe_allow_html=True)

        for r in results:
            bg, fc = TYPE_COLORS.get(r["type"], ("#2a2e39","#d1d4dc"))
            short  = r["sym"].split(".")[0][:4]
            cols   = st.columns([0.5, 2, 4, 1.5, 1])

            cols[0].markdown(
                f"<div style='background:{bg};color:{fc};border:1px solid {fc}33;"
                f"border-radius:8px;width:36px;height:36px;display:flex;"
                f"align-items:center;justify-content:center;"
                f"font-size:10px;font-weight:800;margin-top:2px'>"
                f"{r['flag']}</div>",
                unsafe_allow_html=True
            )
            cols[1].markdown(
                f"<div style='padding-top:6px'>"
                f"<span style='color:#d1d4dc;font-weight:700;font-size:13px'>{r['sym']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            cols[2].markdown(
                f"<div style='padding-top:8px;color:#787b86;font-size:12px;"
                f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>"
                f"{r['name']}</div>",
                unsafe_allow_html=True
            )
            cols[3].markdown(
                f"<div style='padding-top:6px'>"
                f"<span style='background:{bg};color:{fc};border:1px solid {fc}55;"
                f"padding:2px 7px;border-radius:4px;font-size:11px'>{r['type']}</span>"
                f"&nbsp;<span style='color:#787b86;font-size:11px'>{r['exch']}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            if cols[4].button("Select", key=f"sel_{r['sym']}"):
                st.session_state.selected_sym = r["sym"]
                st.session_state.show_search  = False
                st.session_state.search_query = ""
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("✖ Close Search", key="close_search"):
        st.session_state.show_search = False
        st.rerun()


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_data(t, i, p):
    yf_ticker = resolve_ticker(t)
    # Clamp period for intraday intervals (yfinance hard limits)
    def to_days(s):
        if s == "max": return 99999
        if s.endswith("d"):  return int(s[:-1])
        if s.endswith("mo"): return int(s[:-2]) * 30
        if s.endswith("y"):  return int(s[:-1]) * 365
        return 60
    limits = {"1m":"7d","2m":"60d","5m":"60d","15m":"60d",
              "30m":"60d","60m":"730d","90m":"60d","1h":"730d"}
    if i in limits and to_days(p) > to_days(limits[i]):
        p = limits[i]

    raw = yf.download(yf_ticker, interval=i, period=p,
                      auto_adjust=True, progress=False, threads=False)
    if raw is None or raw.empty:
        raise ValueError(
            f"No data returned for '{t}'"
            + (f" (tried as '{yf_ticker}')" if yf_ticker != t else "")
            + ". Check the ticker symbol or try a different interval/period."
        )

    # ── Robust column flattening ──────────────────────────────
    # yfinance v0.2+ returns MultiIndex: ("Close","RELIANCE.NS")
    # We need flat lowercase single-level columns
    if isinstance(raw.columns, pd.MultiIndex):
        # take only the first level (price type), drop ticker level
        raw.columns = [str(c[0]).strip().lower() for c in raw.columns]
    else:
        raw.columns = [str(c).strip().lower() for c in raw.columns]

    # Drop duplicate columns that can appear after flattening
    raw = raw.loc[:, ~raw.columns.duplicated()]

    # Force every column to a plain 1-D float Series
    # (sometimes yfinance nests a DataFrame inside a column)
    clean_cols = {}
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in raw.columns:
            continue
        s = raw[col]
        # If it came back as a DataFrame, take the first column
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        clean_cols[col] = pd.to_numeric(s, errors="coerce")

    if "close" not in clean_cols:
        raise ValueError(
            f"Cannot find 'close' column for '{t}'. "
            f"Available columns: {list(raw.columns)}"
        )

    df = pd.DataFrame(clean_cols, index=raw.index)
    df = df.dropna(subset=["open","high","low","close"])
    df = df.sort_index()

    if df.empty:
        raise ValueError(
            f"Data for '{t}' is empty after cleaning NaN rows. "
            "Try a longer period or a different interval."
        )
    return df

def calc_indicators(df, ma_len, atr_len):
    df = df.copy()

    # ── Ensure all OHLCV are plain 1-D float Series ───────────
    for col in ["open","high","low","close","volume"]:
        if col not in df.columns:
            continue
        s = df[col]
        if isinstance(s, pd.DataFrame):   # nested DataFrame → take 1st col
            s = s.iloc[:, 0]
        df[col] = pd.to_numeric(s, errors="coerce")

    # Drop rows where price data is missing
    df = df.dropna(subset=["open","high","low","close"])
    df = df.sort_index()

    n_bars = len(df)
    min_bars = max(ma_len, atr_len) + 2
    if n_bars < min_bars:
        raise ValueError(
            f"Only {n_bars} valid bars after cleaning — need at least {min_bars}. "
            f"Try a longer period (e.g. 3mo or 6mo) or "
            f"reduce SMA/ATR length below {n_bars - 2}."
        )

    # ── VWAP ──────────────────────────────────────────────────
    tp = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].fillna(0).replace(0, np.nan)   # avoid div-by-zero
    df["vwap"] = (tp * vol).cumsum() / vol.cumsum()

    # ── SMA ───────────────────────────────────────────────────
    df["ma"] = df["close"].rolling(window=ma_len, min_periods=ma_len).mean()

    # ── ATR ───────────────────────────────────────────────────
    pc        = df["close"].shift(1)
    hl        = df["high"] - df["low"]
    hc        = (df["high"] - pc).abs()
    lc        = (df["low"]  - pc).abs()
    df["tr"]  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["atr"] = df["tr"].rolling(window=atr_len, min_periods=atr_len).mean()

    # Drop only rows where MA or ATR is NaN (first ma_len/atr_len rows)
    df = df.dropna(subset=["ma","atr","vwap"])

    if df.empty:
        raise ValueError(
            f"Zero rows remain after indicator warmup period. "
            f"Your period has {n_bars} bars but SMA={ma_len}, ATR={atr_len} "
            f"need {min_bars}+ bars. Use a longer period or smaller indicator lengths."
        )
    return df

def gen_signals(df, mult):
    df = df.copy()
    close = df["close"].squeeze()
    vwap  = df["vwap"].squeeze()
    ma    = df["ma"].squeeze()
    atr   = df["atr"].squeeze()
    df["buy_sig"]   = (close < vwap) & (close > ma)
    df["sell_sig"]  = (close > vwap) & (close < ma)
    df["buy_stop"]  = close - mult * atr
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

def backtest(df, cap):
    if df is None or df.empty:
        raise ValueError("Cannot run backtest: DataFrame is empty.")
    if len(df) < 2:
        raise ValueError(f"Cannot run backtest: only {len(df)} row(s). Need at least 2.")
    # Flatten all columns to plain Series
    for col in list(df.columns):
        s = df[col]
        if isinstance(s, pd.DataFrame):
            df[col] = s.iloc[:, 0]
    capital = float(cap)
    pos = entry_px = stop_px = 0.0
    entry_time = entry_bar = None
    trades, equity = [], []
    bah0 = safe_float(df["close"].iloc[0])
    if bah0 == 0.0:
        raise ValueError("First close price is zero or invalid — cannot run backtest.")
    for i, (_, row) in enumerate(df.iterrows()):
        bar = i + 1
        if pos == 1 and safe_float(row["low"]) <= stop_px:
            pnl = stop_px - entry_px; capital += pnl
            trades.append(dict(num=len(trades)+1, type="Buy",
                entry_time=entry_time, exit_time=row.name,
                entry_bar=entry_bar, exit_bar=bar, bars=bar-entry_bar,
                entry_px=round(entry_px,2), exit_px=round(stop_px,2),
                exit_type="Stop Loss", pnl=round(pnl,2),
                pnl_pct=round(pnl/entry_px*100,3),
                result="Win" if pnl>0 else "Loss"))
            pos = 0
        elif pos == -1 and safe_float(row["high"]) >= stop_px:
            pnl = entry_px - stop_px; capital += pnl
            trades.append(dict(num=len(trades)+1, type="Sell",
                entry_time=entry_time, exit_time=row.name,
                entry_bar=entry_bar, exit_bar=bar, bars=bar-entry_bar,
                entry_px=round(entry_px,2), exit_px=round(stop_px,2),
                exit_type="Stop Loss", pnl=round(pnl,2),
                pnl_pct=round(pnl/entry_px*100,3),
                result="Win" if pnl>0 else "Loss"))
            pos = 0
        if pos == 0:
            if row["buy_sig"]:
                pos=1; entry_px=safe_float(row["close"]); stop_px=safe_float(row["buy_stop"])
                entry_time=row.name; entry_bar=bar
            elif row["sell_sig"]:
                pos=-1; entry_px=safe_float(row["close"]); stop_px=safe_float(row["sell_stop"])
                entry_time=row.name; entry_bar=bar
        equity.append(capital)
    df = df.copy()
    df["equity"] = equity[:len(df)]
    df["bah"]    = [cap * safe_float(df["close"].iloc[i]) / bah0 for i in range(len(df))]
    df["dd"]     = df["equity"] - df["equity"].cummax()
    df["dd_pct"] = df["dd"] / df["equity"].cummax() * 100
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


# ─────────────────────────────────────────────────────────────
#  CHART BUILDERS
# ─────────────────────────────────────────────────────────────
def overview_chart(df, cap0):
    x = list(range(1, len(df)+1))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=x, y=df["equity"].tolist(), name="Equity",
        line=dict(color="#26a69a",width=1.5), fill="tozeroy",
        fillcolor="rgba(38,166,154,0.10)",
        hovertemplate="Bar %{x} | Equity: %{y:,.2f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=df["bah"].tolist(), name="Buy & Hold",
        line=dict(color="#2196f3",width=1.2,dash="dot"),
        hovertemplate="Bar %{x} | B&H: %{y:,.2f}<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=[cap0]*len(x), name="Start Capital",
        line=dict(color="#787b86",width=0.8,dash="dot"), hoverinfo="skip"), secondary_y=False)
    dc = ["rgba(239,83,80,0.55)" if v<0 else "rgba(38,166,154,0.3)" for v in df["dd"].tolist()]
    fig.add_trace(go.Bar(x=x, y=df["dd"].tolist(), name="Drawdown",
        marker_color=dc, opacity=0.85,
        hovertemplate="Bar %{x} | DD: %{y:,.2f}<extra></extra>"), secondary_y=True)
    fig.update_layout(height=340, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(orientation="h",y=-0.22,x=0,bgcolor="rgba(30,34,45,0.9)",
                    bordercolor="#2a2e39",borderwidth=1,font=dict(size=11)),
        hovermode="x unified", bargap=0, margin=dict(l=60,r=70,t=10,b=60))
    fig.update_xaxes(gridcolor="#1e222d",title_text="Bar #",title_font_color="#787b86")
    fig.update_yaxes(gridcolor="#1e222d",title_text="Portfolio Value",title_font_color="#787b86",secondary_y=False)
    fig.update_yaxes(gridcolor="#1e222d",title_text="Drawdown",title_font_color="#787b86",secondary_y=True)
    return fig

def price_chart(df, ma_len):
    buys=df[df["buy_sig"]]; sells=df[df["sell_sig"]]
    fig = make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[0.75,0.25],
        vertical_spacing=0.02,subplot_titles=("Price · VWAP · SMA · Signals","ATR"))
    fig.add_trace(go.Candlestick(x=df.index,open=df["open"],high=df["high"],
        low=df["low"],close=df["close"],name="Price",
        increasing_line_color="#26a69a",decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a",decreasing_fillcolor="#ef5350"),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df["vwap"],name="VWAP",
        line=dict(color="#2196f3",width=2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df["ma"],name=f"SMA {ma_len}",
        line=dict(color="#ff9800",width=2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=buys.index,y=buys["close"],mode="markers",
        name=f"Buy ({len(buys)})",
        marker=dict(symbol="triangle-up",color="#26a69a",size=11,
                    line=dict(color="#fff",width=1))),row=1,col=1)
    fig.add_trace(go.Scatter(x=sells.index,y=sells["close"],mode="markers",
        name=f"Sell ({len(sells)})",
        marker=dict(symbol="triangle-down",color="#ef5350",size=11,
                    line=dict(color="#fff",width=1))),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df["atr"],name="ATR",
        line=dict(color="#9c27b0",width=1.5),fill="tozeroy",
        fillcolor="rgba(156,39,176,0.10)"),row=2,col=1)
    fig.update_layout(height=520, paper_bgcolor="#131722", plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(orientation="h",y=1.02,bgcolor="rgba(30,34,45,0.8)",
                    bordercolor="#2a2e39",borderwidth=1,font=dict(size=10)),
        xaxis_rangeslider_visible=False, hovermode="x unified",
        margin=dict(l=60,r=20,t=30,b=40))
    for i in [1,2]:
        fig.update_xaxes(gridcolor="#1e222d",row=i,col=1)
        fig.update_yaxes(gridcolor="#1e222d",row=i,col=1)
    fig.update_annotations(font_color="#787b86",font_size=11)
    return fig

def monthly_chart(mdf):
    col = ["#26a69a" if v>=0 else "#ef5350" for v in mdf["P&L"]]
    fig = go.Figure(go.Bar(x=mdf["Month"],y=mdf["P&L"],marker_color=col,opacity=0.85,
        hovertemplate="%{x}<br>P&L: %{y:,.2f}<extra></extra>"))
    fig.update_layout(height=200,paper_bgcolor="#131722",plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),margin=dict(l=50,r=20,t=10,b=50),
        showlegend=False,hovermode="x unified")
    fig.update_xaxes(gridcolor="#1e222d",tickangle=-30)
    fig.update_yaxes(gridcolor="#1e222d")
    return fig

def dist_chart(tdf):
    fig = go.Figure()
    w = tdf.loc[tdf["result"]=="Win","pnl"]
    l = tdf.loc[tdf["result"]=="Loss","pnl"]
    if len(w): fig.add_trace(go.Histogram(x=w,name="Wins",marker_color="#26a69a",opacity=0.75,nbinsx=20))
    if len(l): fig.add_trace(go.Histogram(x=l,name="Losses",marker_color="#ef5350",opacity=0.75,nbinsx=20))
    fig.update_layout(height=200,barmode="overlay",paper_bgcolor="#131722",plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(bgcolor="rgba(30,34,45,0.9)",bordercolor="#2a2e39",borderwidth=1,font=dict(size=11)),
        margin=dict(l=50,r=20,t=10,b=40),hovermode="x unified")
    fig.update_xaxes(gridcolor="#1e222d"); fig.update_yaxes(gridcolor="#1e222d")
    return fig

def dd_chart(df):
    x = list(range(1,len(df)+1))
    fig = go.Figure(go.Scatter(x=x,y=df["dd"].tolist(),fill="tozeroy",
        fillcolor="rgba(239,83,80,0.18)",line=dict(color="#ef5350",width=1.2),
        hovertemplate="Bar %{x}<br>DD: %{y:,.2f}<extra></extra>"))
    fig.update_layout(height=160,paper_bgcolor="#131722",plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=10),margin=dict(l=60,r=20,t=8,b=30),
        showlegend=False,hovermode="x unified")
    fig.update_xaxes(gridcolor="#1e222d"); fig.update_yaxes(gridcolor="#1e222d")
    return fig

def eq_bah_chart(df, cap0):
    x = list(range(1,len(df)+1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x,y=df["equity"].tolist(),name="Strategy",
        line=dict(color="#26a69a",width=2),
        hovertemplate="Bar %{x} | Equity: %{y:,.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x,y=df["bah"].tolist(),name="Buy & Hold",
        line=dict(color="#2196f3",width=1.5,dash="dot"),
        hovertemplate="Bar %{x} | B&H: %{y:,.2f}<extra></extra>"))
    fig.add_hline(y=cap0,line_color="#787b86",line_dash="dot",line_width=0.8)
    fig.update_layout(height=200,paper_bgcolor="#131722",plot_bgcolor="#131722",
        font=dict(color="#d1d4dc",size=11),
        legend=dict(bgcolor="rgba(30,34,45,0.9)",bordercolor="#2a2e39",borderwidth=1,font=dict(size=11)),
        margin=dict(l=60,r=20,t=10,b=30),hovermode="x unified")
    fig.update_xaxes(gridcolor="#1e222d"); fig.update_yaxes(gridcolor="#1e222d")
    return fig


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Strategy Settings")
    st.markdown("---")

    # ── Symbol picker ──
    st.markdown("**📌 Symbol**")

    # Find selected symbol info
    sym_info = next((x for x in SYMBOLS if x["sym"]==st.session_state.selected_sym), None)
    if sym_info:
        bg, fc = TYPE_COLORS.get(sym_info["type"], ("#2a2e39","#d1d4dc"))
        st.markdown(f"""
        <div style="background:#131722;border:1px solid #2a2e39;border-radius:8px;
          padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:12px">
          <div style="background:{bg};color:{fc};border:1px solid {fc}55;
            border-radius:6px;padding:4px 8px;font-size:18px;line-height:1">
            {sym_info['flag']}</div>
          <div>
            <div style="color:#d1d4dc;font-weight:700;font-size:14px">
              {sym_info['sym']}</div>
            <div style="color:#787b86;font-size:11px;margin-top:2px">
              {sym_info['name'][:30]}…</div>
          </div>
          <div style="margin-left:auto">
            <span style="background:{bg};color:{fc};border:1px solid {fc}55;
              padding:2px 7px;border-radius:4px;font-size:10px">
              {sym_info['type']}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:#131722;border:1px solid #2a2e39;border-radius:8px;
          padding:10px 14px;margin-bottom:8px">
          <span style="color:#d1d4dc;font-weight:700">{st.session_state.selected_sym}</span>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🔍 Search Symbol", use_container_width=True):
        st.session_state.show_search = not st.session_state.show_search
        st.rerun()

    # Manual override
    manual = st.text_input("Or type ticker directly", value="",
                           placeholder="e.g. SBIN.NS", key="manual_ticker")
    if manual.strip():
        st.session_state.selected_sym = manual.strip().upper()

    ticker = st.session_state.selected_sym

    st.markdown("---")
    c1, c2 = st.columns(2)
    interval = c1.selectbox("Interval", ["1h","15m","30m","1d","5m"], 0)
    period   = c2.selectbox("Period",   ["60d","30d","3mo","6mo","1y"], 0)

    st.markdown("---")
    st.markdown("**📐 Indicators**")
    ma_length  = st.slider("SMA Length",     5,  50, 14)
    atr_length = st.slider("ATR Length",     5,  50, 14)
    atr_mult   = st.slider("ATR Multiplier", 0.5, 4.0, 1.5, 0.1)

    st.markdown("---")
    st.markdown("**💰 Capital**")
    starting_cap = st.number_input("Starting Capital", value=1_000_000, step=10000)
    currency     = st.selectbox("Currency", ["INR","USD","EUR","GBP"])

    st.markdown("---")
    run_btn = st.button("🚀 Run Strategy", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("""<div style='font-size:11px;color:#787b86;line-height:1.8'>
    <b style='color:#d1d4dc'>📖 Signal Logic</b><br>
    🟢 BUY → Close &lt; VWAP &amp; Close &gt; SMA<br>
    🔴 SELL → Close &gt; VWAP &amp; Close &lt; SMA<br>
    🛑 Stop → Entry ± ATR × Multiplier
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(f"""
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
#  SYMBOL SEARCH PANEL (shown when open)
# ─────────────────────────────────────────────────────────────
if st.session_state.show_search:
    symbol_search_panel()
    st.markdown("---")


# ─────────────────────────────────────────────────────────────
#  WELCOME / RUN
# ─────────────────────────────────────────────────────────────
if not run_btn and not st.session_state.get("last_run"):
    st.markdown("""
    <div class="sc" style="text-align:center;padding:44px 24px">
      <div style="font-size:52px;margin-bottom:12px">📊</div>
      <h2 style="color:#d1d4dc;margin-bottom:8px">VWAP + MA Mean Reversion Strategy</h2>
      <p style="color:#787b86;font-size:13px;max-width:500px;margin:0 auto 24px">
        Click <b style="color:#2196f3">🔍 Search Symbol</b> in the sidebar to pick any
        stock, index, crypto or forex — then click
        <b style="color:#26a69a">🚀 Run Strategy</b>.
      </p>
      <div style="display:flex;justify-content:center;gap:28px;flex-wrap:wrap">
        <div style="text-align:center"><div style="font-size:24px">🇮🇳</div>
          <div style="color:#26a69a;font-weight:600;font-size:12px;margin-top:4px">NSE/BSE</div>
          <div style="color:#787b86;font-size:11px">50+ Indian Stocks</div></div>
        <div style="text-align:center"><div style="font-size:24px">📊</div>
          <div style="color:#ff9800;font-weight:600;font-size:12px;margin-top:4px">Indices</div>
          <div style="color:#787b86;font-size:11px">Nifty · Sensex · S&P</div></div>
        <div style="text-align:center"><div style="font-size:24px">🟡</div>
          <div style="color:#ff5722;font-weight:600;font-size:12px;margin-top:4px">Crypto</div>
          <div style="color:#787b86;font-size:11px">BTC · ETH · SOL</div></div>
        <div style="text-align:center"><div style="font-size:24px">🇺🇸</div>
          <div style="color:#2196f3;font-weight:600;font-size:12px;margin-top:4px">US Stocks</div>
          <div style="color:#787b86;font-size:11px">AAPL · TSLA · NVDA</div></div>
        <div style="text-align:center"><div style="font-size:24px">💱</div>
          <div style="color:#9c27b0;font-weight:600;font-size:12px;margin-top:4px">Forex</div>
          <div style="color:#787b86;font-size:11px">USD/INR · EUR/USD</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# persist last run symbol
if run_btn:
    st.session_state["last_run"] = ticker
ticker = st.session_state.get("last_run", ticker)

# ─────────────────────────────────────────────────────────────
#  FETCH + BACKTEST
# ─────────────────────────────────────────────────────────────
with st.spinner(f"📥 Fetching {ticker} ({interval} · {period}) …"):
    try:
        yf_sym = resolve_ticker(ticker)
        raw = fetch_data(ticker, interval, period)
        if raw.empty:
            st.error(f"❌ No data returned for **{ticker}**"
                     + (f" (tried yfinance: `{yf_sym}`)" if yf_sym != ticker else "")
                     + ". Try a different interval or period.")
            st.stop()
    except Exception as e:
        yf_sym2 = resolve_ticker(ticker)
        st.error(f"❌ **{ticker}** — {e}")
        # Show helpful suggestions
        st.markdown(f"""
        <div style="background:#1e222d;border:1px solid #ef535055;border-radius:8px;padding:16px 20px;margin-top:8px">
          <b style="color:#d1d4dc">💡 Troubleshooting Tips</b><br><br>
          <div style="font-size:13px;color:#787b86;line-height:2">
          {'<span style="color:#ff9800">⚠️ Ticker mapped to: <b style="color:#d1d4dc">' + yf_sym2 + '</b> — try selecting it directly from Symbol Search.</span><br>' if yf_sym2 != ticker else ''}
          • For <b style="color:#d1d4dc">NSE stocks</b> — add <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">.NS</code>
            e.g. <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">RELIANCE.NS</code><br>
          • For <b style="color:#d1d4dc">BSE stocks</b> — add <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">.BO</code>
            e.g. <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">RELIANCE.BO</code><br>
          • For <b style="color:#d1d4dc">Nifty 50</b> — use
            <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">^NSEI</code><br>
          • For <b style="color:#d1d4dc">Bank Nifty</b> — use
            <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">^NSEBANK</code><br>
          • For <b style="color:#d1d4dc">Sensex</b> — use
            <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">^BSESN</code><br>
          • For <b style="color:#d1d4dc">Crypto</b> — use
            <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">BTC-USD</code>,
            <code style="color:#26a69a;background:#131722;padding:1px 5px;border-radius:3px">ETH-USD</code><br>
          • <b style="color:#d1d4dc">Intraday data</b> (5m/15m/1h) is limited to last <b>60 days</b> by Yahoo Finance<br>
          • Use the <b style="color:#2196f3">🔍 Search Symbol</b> button for verified tickers
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

with st.spinner("⚙️ Running backtest …"):
    try:
        df   = calc_indicators(raw, ma_length, atr_length)
        df   = gen_signals(df, atr_mult)
        df, tdf, final_cap = backtest(df, starting_cap)
        s    = compute_stats(tdf, starting_cap, final_cap, df)
    except (ValueError, IndexError, KeyError) as e:
        st.error(f"❌ Backtest error: {e}")
        st.markdown("""
        <div style="background:#1e222d;border:1px solid #ef535055;border-radius:8px;
          padding:14px 18px;margin-top:8px;font-size:13px;color:#787b86;line-height:2">
        <b style="color:#d1d4dc">💡 Try these fixes:</b><br>
        • Reduce <b style="color:#ff9800">SMA / ATR Length</b> (currently might be larger than available bars)<br>
        • Use a <b style="color:#ff9800">longer Period</b> (e.g. <code>3mo</code> or <code>6mo</code>)<br>
        • Switch to <b style="color:#ff9800">1d interval</b> for more historical data<br>
        • Some tickers have limited data on Yahoo Finance — try a major index like
          <code style="color:#26a69a">^NSEI</code> or <code style="color:#26a69a">RELIANCE.NS</code>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

# ── ticker info bar ──
try:
    yf_sym_info = resolve_ticker(ticker)
    fi  = yf.Ticker(yf_sym_info).fast_info
    lp  = fi.last_price; pc2 = fi.previous_close
    chg = lp - pc2; pct = chg/pc2*100
    pc_ = "#26a69a" if chg>=0 else "#ef5350"
    arr = "▲" if chg>=0 else "▼"
    px_h = f"""<span style="font-size:20px;font-weight:700;color:{pc_}">{lp:.2f}</span>
               <span style="color:{pc_};font-size:13px">&nbsp;{arr} {chg:+.2f} ({pct:+.2f}%)</span>"""
except Exception:
    px_h = ""

# get symbol info for badge
si = next((x for x in SYMBOLS if x["sym"]==ticker), None)
badge_html = ""
if si:
    bg2, fc2 = TYPE_COLORS.get(si["type"], ("#2a2e39","#d1d4dc"))
    badge_html = f"""<span style="background:{bg2};color:{fc2};border:1px solid {fc2}55;
      padding:2px 8px;border-radius:4px;font-size:11px;margin-left:6px">{si['type']}</span>
      <span style="color:#787b86;font-size:11px;margin-left:4px">{si['exch']}</span>
      <span style="font-size:14px;margin-left:6px">{si['flag']}</span>"""

st.markdown(f"""
<div class="sc" style="padding:10px 18px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:10px">
  <span style="font-size:18px;font-weight:700;color:#d1d4dc">{ticker}</span>
  {badge_html} {px_h}
  <span style="color:#787b86;font-size:12px;margin-left:auto">
    {len(df)} bars · {interval} · {period} ·
    {str(df.index[0])[:10]} → {str(df.index[-1])[:10]}
  </span>
</div>
""", unsafe_allow_html=True)

# ── 7-metric stats bar ──
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
t1, t2, t3, t4 = st.tabs(["Overview","Performance Summary","List of Trades","Properties"])

# ── TAB 1: OVERVIEW ──
with t1:
    st.markdown("#### Equity · Drawdown · Buy & Hold")
    st.plotly_chart(overview_chart(df, starting_cap), use_container_width=True)
    lc1,lc2,lc3,_ = st.columns([1,1,1.4,4])
    lc1.markdown("☑️ <span style='color:#26a69a;font-size:12px'>Equity</span>", unsafe_allow_html=True)
    lc2.markdown("☑️ <span style='color:#ef5350;font-size:12px'>Drawdown</span>", unsafe_allow_html=True)
    lc3.markdown("☑️ <span style='color:#2196f3;font-size:12px'>Buy & Hold Equity</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Price Chart with Signals")
    st.plotly_chart(price_chart(df, ma_length), use_container_width=True)


# ── TAB 2: PERFORMANCE SUMMARY ──
with t2:
    if not s.get("n"):
        st.info("No trades to summarize."); st.stop()

    col1, col2, col3 = st.columns(3)
    with col1:
        np_bar = min(abs(s["net_pct"]),100)
        bc = "#26a69a" if s["net"]>=0 else "#ef5350"
        st.markdown(f"""<div class="sc"><div class="sc-title">💰 P&L Overview</div>
        <table class="pt">
        <tr><td>Net Profit</td><td style="color:{bc};font-weight:700">
          {s['net']:+,.2f} {currency} <span style="font-size:11px">({s['net_pct']:+.2f}%)</span></td></tr>
        <tr><td>Gross Profit</td><td style="color:#26a69a;font-weight:600">{s['gp']:,.2f} {currency}</td></tr>
        <tr><td>Gross Loss</td><td style="color:#ef5350;font-weight:600">−{s['gl']:,.2f} {currency}</td></tr>
        <tr><td>Profit Factor</td>
          <td style="color:{'#26a69a' if s['pf']>=1 else '#ef5350'};font-weight:700">{s['pf']:.3f}</td></tr>
        <tr><td>Buy & Hold Return</td>
          <td style="color:#2196f3;font-weight:600">
          {round((df['bah'].iloc[-1]-starting_cap)/starting_cap*100,2):+.2f}%</td></tr>
        <tr><td>Starting Capital</td><td>{starting_cap:,.0f} {currency}</td></tr>
        <tr><td>Final Capital</td><td style="font-weight:600">{final_cap:,.2f} {currency}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{np_bar}%;background:{bc}"></div></div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">Return vs Starting Capital</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        wb = min(s["wr"],100)
        st.markdown(f"""<div class="sc"><div class="sc-title">📊 Trade Statistics</div>
        <table class="pt">
        <tr><td>Total Closed Trades</td><td style="font-weight:700">{s['n']}</td></tr>
        <tr><td>Winning Trades</td><td style="color:#26a69a;font-weight:600">✅ {s['wins']}</td></tr>
        <tr><td>Losing Trades</td><td style="color:#ef5350;font-weight:600">❌ {s['losses']}</td></tr>
        <tr><td>Percent Profitable</td>
          <td style="color:{'#26a69a' if s['wr']>=50 else '#ef5350'};font-weight:700">{s['wr']:.2f}%</td></tr>
        <tr><td>Long (Buy) Trades</td>
          <td style="color:#26a69a">{s['buy_n']}
            <span style="color:#787b86;font-size:11px">(WR: {s['buy_wr']}%)</span></td></tr>
        <tr><td>Short (Sell) Trades</td>
          <td style="color:#ef5350">{s['sell_n']}
            <span style="color:#787b86;font-size:11px">(WR: {s['sell_wr']}%)</span></td></tr>
        <tr><td>Avg Bars in Trade</td><td>{s['avg_bars']}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{wb}%;background:#26a69a"></div></div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">Win Rate: {s['wr']:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        ddb = min(s["max_dd_pct"],100)
        st.markdown(f"""<div class="sc"><div class="sc-title">📉 Drawdown & Risk</div>
        <table class="pt">
        <tr><td>Max Drawdown</td>
          <td style="color:#ef5350;font-weight:700">{s['max_dd']:,.2f} {currency}
            <span style="font-size:11px">({s['max_dd_pct']:.2f}%)</span></td></tr>
        <tr><td>Avg Win</td><td style="color:#26a69a;font-weight:600">{s['avg_win']:+,.2f} {currency}</td></tr>
        <tr><td>Avg Loss</td><td style="color:#ef5350;font-weight:600">{s['avg_loss']:+,.2f} {currency}</td></tr>
        <tr><td>Best Trade</td><td style="color:#26a69a;font-weight:600">{s['best']:+,.2f} {currency}</td></tr>
        <tr><td>Worst Trade</td><td style="color:#ef5350;font-weight:600">{s['worst']:+,.2f} {currency}</td></tr>
        <tr><td>Avg Trade</td>
          <td style="color:{'#26a69a' if s['avg_trade']>=0 else '#ef5350'}">
          {s['avg_trade']:+,.2f} <span style="font-size:11px">({s['avg_trade_pct']:+.3f}%)</span></td></tr>
        <tr><td>Win / Loss Ratio</td>
          <td>{round(abs(s['avg_win']/s['avg_loss']),2) if s['avg_loss'] else '∞'}</td></tr>
        </table>
        <div class="pb-wrap" style="margin-top:10px">
          <div class="pb-fill" style="width:{ddb}%;background:#ef5350"></div></div>
        <div style="font-size:10px;color:#787b86;margin-top:4px">Max Drawdown: {s['max_dd_pct']:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    with col4:
        cw_b = min(s["consec_win"]*10, 100)
        cl_b = min(s["consec_loss"]*10,100)
        st.markdown(f"""<div class="sc"><div class="sc-title">🔁 Consecutive Trades</div>
        <table class="pt">
        <tr><td>Max Consecutive Wins</td>
          <td style="color:#26a69a;font-weight:700">{s['consec_win']}</td></tr>
        <tr><td>Max Consecutive Losses</td>
          <td style="color:#ef5350;font-weight:700">{s['consec_loss']}</td></tr>
        </table>
        <div style="margin-top:12px">
          <div style="font-size:11px;color:#787b86;margin-bottom:4px">Consecutive Wins</div>
          <div class="pb-wrap"><div class="pb-fill" style="width:{cw_b}%;background:#26a69a"></div></div>
          <div style="font-size:11px;color:#787b86;margin:10px 0 4px">Consecutive Losses</div>
          <div class="pb-wrap"><div class="pb-fill" style="width:{cl_b}%;background:#ef5350"></div></div>
        </div></div>""", unsafe_allow_html=True)

    with col5:
        wb2 = s["avg_bars_win"]; lb2 = s["avg_bars_loss"]; mb = max(wb2,lb2,1)
        st.markdown(f"""<div class="sc"><div class="sc-title">⏱️ Time in Trades</div>
        <table class="pt">
        <tr><td>Avg Bars — Winning</td>
          <td style="color:#26a69a;font-weight:600">{wb2}</td></tr>
        <tr><td>Avg Bars — Losing</td>
          <td style="color:#ef5350;font-weight:600">{lb2}</td></tr>
        <tr><td>Overall Avg Bars</td>
          <td style="font-weight:600">{s['avg_bars']}</td></tr>
        </table>
        <div style="margin-top:12px">
          <div style="font-size:11px;color:#787b86;margin-bottom:4px">Win Bars</div>
          <div class="pb-wrap"><div class="pb-fill" style="width:{min(wb2/mb*100,100):.0f}%;background:#26a69a"></div></div>
          <div style="font-size:11px;color:#787b86;margin:10px 0 4px">Loss Bars</div>
          <div class="pb-wrap"><div class="pb-fill" style="width:{min(lb2/mb*100,100):.0f}%;background:#ef5350"></div></div>
        </div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown('<div class="sc"><div class="sc-title">📅 Monthly P&L</div></div>', unsafe_allow_html=True)
        if len(s["monthly"])>0: st.plotly_chart(monthly_chart(s["monthly"]), use_container_width=True)
    with ch2:
        st.markdown('<div class="sc"><div class="sc-title">📊 P&L Distribution</div></div>', unsafe_allow_html=True)
        st.plotly_chart(dist_chart(tdf), use_container_width=True)

    st.markdown('<div class="sc"><div class="sc-title">📉 Drawdown Over Time</div></div>', unsafe_allow_html=True)
    st.plotly_chart(dd_chart(df), use_container_width=True)
    st.markdown('<div class="sc"><div class="sc-title">📈 Strategy Equity vs Buy & Hold</div></div>', unsafe_allow_html=True)
    st.plotly_chart(eq_bah_chart(df, starting_cap), use_container_width=True)


# ── TAB 3: LIST OF TRADES ──
with t3:
    if len(tdf)==0:
        st.info("No completed trades in this period.")
    else:
        fc1,fc2,fc3,fc4 = st.columns([2,2,2,2])
        f_type   = fc1.selectbox("Filter Type",   ["All","Buy (Long)","Sell (Short)"])
        f_result = fc2.selectbox("Filter Result", ["All","Win","Loss"])
        f_sort   = fc3.selectbox("Sort by",       ["# (Default)","P&L ↑","P&L ↓","Entry Time","Bars Held"])
        f_n      = fc4.number_input("Show last N (0=all)", 0, step=10)

        disp = tdf.copy()
        if f_type=="Buy (Long)":     disp = disp[disp["type"]=="Buy"]
        elif f_type=="Sell (Short)": disp = disp[disp["type"]=="Sell"]
        if f_result=="Win":          disp = disp[disp["result"]=="Win"]
        elif f_result=="Loss":       disp = disp[disp["result"]=="Loss"]
        if f_sort=="P&L ↑":         disp = disp.sort_values("pnl",ascending=True)
        elif f_sort=="P&L ↓":       disp = disp.sort_values("pnl",ascending=False)
        elif f_sort=="Entry Time":   disp = disp.sort_values("entry_time")
        elif f_sort=="Bars Held":    disp = disp.sort_values("bars",ascending=False)
        if f_n>0:                    disp = disp.tail(int(f_n))

        fw   = int((disp["pnl"]>0).sum()); fl = int((disp["pnl"]<0).sum())
        fp   = round(disp["pnl"].sum(),2); fwr = round(fw/len(disp)*100,1) if len(disp) else 0
        fpc  = "#26a69a" if fp>=0 else "#ef5350"
        st.markdown(f"""
        <div class="sc" style="padding:10px 16px;display:flex;gap:22px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
          <span style="color:#787b86;font-size:12px">Showing <b style="color:#d1d4dc">{len(disp)}</b> trades</span>
          <span style="color:#26a69a;font-size:12px">✅ Wins: <b>{fw}</b></span>
          <span style="color:#ef5350;font-size:12px">❌ Losses: <b>{fl}</b></span>
          <span style="color:#d1d4dc;font-size:12px">Win Rate: <b>{fwr:.1f}%</b></span>
          <span style="color:{fpc};font-size:12px;font-weight:600">Total P&L: {fp:+,.2f} {currency}</span>
        </div>
        """, unsafe_allow_html=True)

        rows = ""; running = 0
        for _, r in disp.iterrows():
            running += r["pnl"]
            ib = r["type"]=="Buy"
            tc = "#26a69a" if ib else "#ef5350"
            pc3= "#26a69a" if r["pnl"]>=0 else "#ef5350"
            rc = "#26a69a" if r["pnl"]>=0 else "#ef5350"
            sg = "+" if r["pnl"]>=0 else ""
            rpc= "#26a69a" if running>=0 else "#ef5350"
            tl = f"<span style='color:{tc};font-weight:600'>{'▲ Long' if ib else '▼ Short'}</span>"
            rb = f"<span class='badge' style='background:{'#1a3a1f' if r['pnl']>=0 else '#3a1a1a'};color:{rc};border:1px solid {rc}'>{'Win' if r['pnl']>=0 else 'Loss'}</span>"
            rows += f"""<tr>
              <td style="color:#787b86">{int(r['num'])}</td><td>{tl}</td>
              <td style="color:#787b86">{str(r['entry_time'])[:16]}</td>
              <td style="color:#787b86">{str(r['exit_time'])[:16]}</td>
              <td>{int(r['entry_bar'])}</td><td>{int(r['exit_bar'])}</td>
              <td style="text-align:center;color:#787b86">{int(r['bars'])}</td>
              <td>{r['entry_px']:.2f}</td><td>{r['exit_px']:.2f}</td>
              <td><span style="color:#ff9800;font-size:11px;background:#1a1e2b;
                padding:2px 6px;border-radius:3px">Stop Loss</span></td>
              <td style="color:{pc3};font-weight:600">{sg}{r['pnl']:.2f}</td>
              <td style="color:{pc3}">{r['pnl_pct']:+.3f}%</td>
              <td style="color:{rpc};font-size:11px">{running:+,.2f}</td>
              <td>{rb}</td></tr>"""

        st.markdown(f"""
        <div style="overflow:auto;max-height:480px;border:1px solid #2a2e39;border-radius:6px">
        <table class="tt"><thead><tr>
          <th>#</th><th>Type</th><th>Entry Time</th><th>Exit Time</th>
          <th>Entry Bar</th><th>Exit Bar</th><th>Bars</th>
          <th>Entry</th><th>Exit</th><th>Exit Type</th>
          <th>P&L</th><th>P&L %</th><th>Cum. P&L</th><th>Result</th>
        </tr></thead><tbody>{rows}</tbody></table></div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        dl1,dl2,_ = st.columns([1.5,1.5,5])
        dl1.download_button("⬇️ Export All",      tdf.to_csv(index=False).encode(),
                            f"{ticker}_all_trades.csv","text/csv",type="primary")
        dl2.download_button("⬇️ Export Filtered", disp.to_csv(index=False).encode(),
                            f"{ticker}_filtered.csv","text/csv")


# ── TAB 4: PROPERTIES ──
with t4:
    pc1, pc2, pc3 = st.columns(3)
    si2 = next((x for x in SYMBOLS if x["sym"]==ticker), None)
    exch_lbl = si2["exch"] if si2 else "—"
    type_lbl = si2["type"] if si2 else "—"
    flag_lbl = si2["flag"] if si2 else ""
    full_lbl = si2["name"] if si2 else ticker

    with pc1:
        st.markdown(f"""<div class="sc"><div class="sc-title">📌 Asset & Data</div>
        <table class="pt">
        <tr><td>Symbol</td><td style="color:#d1d4dc;font-weight:700">{ticker} {flag_lbl}</td></tr>
        <tr><td>Full Name</td><td style="color:#787b86;font-size:11px">{full_lbl}</td></tr>
        <tr><td>Type</td><td style="color:#d1d4dc">{type_lbl}</td></tr>
        <tr><td>Exchange</td><td style="color:#d1d4dc">{exch_lbl}</td></tr>
        <tr><td>Interval</td><td style="color:#d1d4dc">{interval}</td></tr>
        <tr><td>Period</td><td style="color:#d1d4dc">{period}</td></tr>
        <tr><td>Total Bars</td><td style="color:#d1d4dc">{len(df)}</td></tr>
        <tr><td>From</td><td style="color:#787b86">{str(df.index[0])[:16]}</td></tr>
        <tr><td>To</td><td style="color:#787b86">{str(df.index[-1])[:16]}</td></tr>
        <tr><td>Data Source</td><td style="color:#2196f3">Yahoo Finance</td></tr>
        <tr><td>Currency</td><td style="color:#d1d4dc">{currency}</td></tr>
        </table></div>""", unsafe_allow_html=True)

    with pc2:
        st.markdown(f"""<div class="sc"><div class="sc-title">📐 Indicator Parameters</div>
        <table class="pt">
        <tr><td>VWAP Source</td><td style="color:#2196f3;font-weight:600">HLC3</td></tr>
        <tr><td>MA Type</td><td style="color:#ff9800;font-weight:600">SMA</td></tr>
        <tr><td>MA Length</td><td style="color:#ff9800;font-weight:700">{ma_length} bars</td></tr>
        <tr><td>ATR Length</td><td style="color:#9c27b0;font-weight:700">{atr_length} bars</td></tr>
        <tr><td>ATR Multiplier</td><td style="color:#9c27b0;font-weight:700">{atr_mult}×</td></tr>
        <tr><td>Buy Signals</td><td style="color:#26a69a;font-weight:600">{int(df['buy_sig'].sum())}</td></tr>
        <tr><td>Sell Signals</td><td style="color:#ef5350;font-weight:600">{int(df['sell_sig'].sum())}</td></tr>
        <tr><td>PineScript equiv.</td><td style="color:#787b86">v5</td></tr>
        </table></div>""", unsafe_allow_html=True)

    with pc3:
        st.markdown(f"""<div class="sc"><div class="sc-title">💰 Capital & Risk</div>
        <table class="pt">
        <tr><td>Starting Capital</td>
          <td style="color:#26a69a;font-weight:700">{starting_cap:,.0f} {currency}</td></tr>
        <tr><td>Final Capital</td>
          <td style="color:#d1d4dc;font-weight:700">{final_cap:,.2f} {currency}</td></tr>
        <tr><td>Net Return</td>
          <td style="color:{'#26a69a' if s.get('net',0)>=0 else '#ef5350'};font-weight:700">
          {s.get('net_pct',0):+.2f}%</td></tr>
        <tr><td>Stop Loss</td><td style="color:#ef5350;font-weight:600">ATR-Based Dynamic</td></tr>
        <tr><td>Take Profit</td><td style="color:#787b86">Not defined</td></tr>
        <tr><td>Position Size</td><td style="color:#787b86">1 unit/signal</td></tr>
        <tr><td>Trade Direction</td><td style="color:#d1d4dc">Long & Short</td></tr>
        <tr><td>Max Open Pos.</td><td style="color:#d1d4dc">1 at a time</td></tr>
        <tr><td>Commission</td><td style="color:#787b86">Not modelled</td></tr>
        </table></div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="sc">
    <div class="sc-title">📖 Entry & Exit Rules</div>
    <table class="pt" style="font-size:12px">
    <tr>
      <td style="width:15%;color:#26a69a;font-weight:600;vertical-align:top">▲ BUY</td>
      <td><code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
        close &lt; VWAP</code>&nbsp;<b style="color:#787b86">AND</b>&nbsp;
        <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
        close &gt; SMA({ma_length})</code>
        &nbsp;→&nbsp;<span style="color:#787b86">Price undervalued vs VWAP, trend bullish vs SMA</span>
      </td>
    </tr>
    <tr>
      <td style="color:#ef5350;font-weight:600;vertical-align:top">▼ SELL</td>
      <td><code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
        close &gt; VWAP</code>&nbsp;<b style="color:#787b86">AND</b>&nbsp;
        <code style="background:#131722;padding:2px 7px;border-radius:3px;color:#d1d4dc">
        close &lt; SMA({ma_length})</code>
        &nbsp;→&nbsp;<span style="color:#787b86">Price overvalued vs VWAP, trend bearish vs SMA</span>
      </td>
    </tr>
    <tr>
      <td style="color:#ef5350;font-weight:600">🛑 LONG SL</td>
      <td><code style="background:#131722;padding:2px 7px;border-radius:3px;color:#ef5350">
        entry − {atr_mult} × ATR({atr_length})</code>
        &nbsp;→&nbsp;<span style="color:#787b86">Widens in volatile markets</span></td>
    </tr>
    <tr>
      <td style="color:#ef5350;font-weight:600">🛑 SHORT SL</td>
      <td><code style="background:#131722;padding:2px 7px;border-radius:3px;color:#ef5350">
        entry + {atr_mult} × ATR({atr_length})</code>
        &nbsp;→&nbsp;<span style="color:#787b86">Widens in volatile markets</span></td>
    </tr>
    <tr>
      <td style="color:#ff9800;font-weight:600">✖ EXIT</td>
      <td><span style="color:#787b86">Stop Loss only. No take-profit. Exits on Low (long) or High (short).</span></td>
    </tr>
    </table></div>""", unsafe_allow_html=True)

    st.markdown("""<div class="sc" style="border-color:#2a2e39;background:#131722;padding:12px 18px">
    <span style="color:#787b86;font-size:11px">⚠️ <b style="color:#d1d4dc">Disclaimer:</b>
    Educational & research purposes only. Backtested results ≠ future performance.
    Commission, slippage & market impact not modelled. Not financial advice.
    </span></div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown("""<div style="text-align:center;color:#787b86;font-size:11px;padding:4px">
SpringPad VWAP Strategy · Streamlit + Plotly + Yahoo Finance · Educational only
</div>""", unsafe_allow_html=True)
