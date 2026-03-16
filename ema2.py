# -*- coding: utf-8 -*-
"""
Akıllı EMA 200 — 2  (MA Crossover Panel)
Kullanım: streamlit run smart_ema200_2.py

Pine Script indikatörünün Python karşılığı:
  - MA Crossover → AL / SAT sinyali
  - Sinyal Fiyatı: kesişim anındaki close
  - % Değişim: sinyal fiyatından bu yana hareket
  - Z-Skor: % değişimin gruba içi standart sapma cinsinden konumu

Akış:
  Binance 24hr ticker
    → Hacim Top-N  →  Hareket Top-M  (Akıllı Liste)
    → Her coin için MA Crossover analizi
    → Otomatik periyodik yenileme
"""

import math, time, json
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ══════════════════════════════════════════════════════════════════
# SAYFA
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Akıllı EMA 200 — 2",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;700;900&display=swap');

*, *::before, *::after { box-sizing:border-box; }
html, body, [class*="css"] {
    font-family:'Inter',sans-serif !important;
    background:#050d1a !important;
    color:#c8dff0 !important;
}
.main .block-container { padding:0 2rem 2rem; max-width:100%; }
.stApp { background:#050d1a; }
.stApp::before {
    content:''; position:fixed; inset:0; z-index:0; pointer-events:none;
    background-image:
        linear-gradient(rgba(0,212,255,.02) 1px,transparent 1px),
        linear-gradient(90deg,rgba(0,212,255,.02) 1px,transparent 1px);
    background-size:48px 48px;
}
section[data-testid="stSidebar"] {
    background:#070f1f !important; border-right:1px solid #0d1f35 !important;
}
section[data-testid="stSidebar"] > div { padding:0 !important; }

.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background:#0a1628 !important; border:1px solid #0d1f35 !important;
    color:#c8dff0 !important; font-family:'Share Tech Mono',monospace !important;
    border-radius:4px !important;
}
.stSelectbox svg { fill:#3a5a7a !important; }
label {
    color:#3a6080 !important; font-size:10px !important;
    font-weight:600 !important; letter-spacing:2px !important;
    text-transform:uppercase !important;
}
.stCheckbox label { font-size:11px !important; text-transform:none !important; color:#5a8aaa !important; }
.stSlider > div > div > div { background:linear-gradient(90deg,#00ff88,#00d4ff) !important; }

.stButton > button {
    background:linear-gradient(135deg,#00b8d9,#0052cc) !important;
    color:#fff !important; font-weight:700 !important;
    font-size:12px !important; letter-spacing:2px !important;
    text-transform:uppercase !important; border:none !important;
    border-radius:4px !important; width:100% !important; transition:all .2s !important;
}
.stButton > button:hover { transform:translateY(-1px) !important; box-shadow:0 6px 24px rgba(0,184,217,.35) !important; }

[data-testid="stMetric"] {
    background:#070f1f !important; border:1px solid #0d1f35 !important;
    border-radius:6px !important; padding:14px 18px !important;
}
[data-testid="stMetricLabel"] {
    font-size:9px !important; letter-spacing:2.5px !important;
    text-transform:uppercase !important; color:#3a6080 !important;
}
[data-testid="stMetricValue"] {
    font-family:'Share Tech Mono',monospace !important;
    font-size:24px !important; color:#e8f4ff !important;
}
[data-testid="stMetricDelta"] { font-family:'Share Tech Mono',monospace !important; }

.stTabs [data-baseweb="tab-list"] { background:#070f1f !important; border-bottom:1px solid #0d1f35 !important; }
.stTabs [data-baseweb="tab"] {
    font-family:'Inter',sans-serif !important; font-size:11px !important;
    font-weight:600 !important; letter-spacing:2px !important;
    text-transform:uppercase !important; color:#3a6080 !important;
    background:transparent !important; border:none !important;
    border-bottom:2px solid transparent !important; padding:14px 20px !important;
}
.stTabs [aria-selected="true"] { color:#00d4ff !important; border-bottom:2px solid #00d4ff !important; }
.stTabs [data-baseweb="tab-panel"] { padding:0 !important; }

.stProgress > div > div > div > div {
    background:linear-gradient(90deg,#00ff88,#00d4ff) !important; border-radius:2px !important;
}
.stProgress > div > div { background:#0a1628 !important; height:4px !important; border-radius:2px !important; }

hr { border-color:#0d1f35 !important; margin:14px 0 !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#050d1a; }
::-webkit-scrollbar-thumb { background:#0d1f35; border-radius:2px; }

.header-bar {
    background:#070f1f; border:1px solid #0d1f35; border-radius:8px;
    padding:18px 24px; margin-bottom:16px; position:relative; overflow:hidden;
}
.header-bar::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,#00ff88,#00d4ff,#a78bfa,#00ff88);
    background-size:200%; animation:hbAnim 3s linear infinite;
}
@keyframes hbAnim { 0%{background-position:0%} 100%{background-position:200%} }

.live-bar {
    display:flex; align-items:center; gap:12px;
    background:#070f1f; border:1px solid rgba(0,255,136,.25);
    border-radius:6px; padding:10px 16px;
    font-family:'Share Tech Mono',monospace; font-size:13px; margin:8px 0;
}
.pulse {
    width:8px; height:8px; border-radius:50%;
    background:#00ff88; box-shadow:0 0 10px #00ff88; flex-shrink:0;
    animation:pulseAnim 1s ease-in-out infinite;
}
@keyframes pulseAnim { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(.8)} }

.countdown-bar {
    display:flex; align-items:center; gap:12px;
    background:#070f1f; border:1px solid rgba(0,212,255,.25);
    border-radius:6px; padding:10px 18px;
    font-family:'Share Tech Mono',monospace; margin:8px 0;
}
.section-head {
    font-size:9px; letter-spacing:3px; text-transform:uppercase;
    color:#2a4a6a; font-weight:700; padding:10px 0 7px;
    border-bottom:1px solid #0d1f35; margin-bottom:10px;
}
.badge-al  { background:rgba(0,255,136,.15); border:1px solid rgba(0,255,136,.4);
             border-radius:4px; padding:2px 8px; color:#00ff88; font-family:monospace; font-size:11px; }
.badge-sat { background:rgba(255,51,102,.15); border:1px solid rgba(255,51,102,.4);
             border-radius:4px; padding:2px 8px; color:#ff3366; font-family:monospace; font-size:11px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AYARLAR & GEÇMİŞ
# ══════════════════════════════════════════════════════════════════
SETTINGS_FILE = Path("sema2_settings.json")
HIST_FILE     = Path("sema2_history.json")

DEFAULT_CFG = {
    "top_vol":      200,
    "top_move":     20,
    "abs_change":   True,
    "interval":     "1h",
    "ma_period":    200,
    "sort_by":      "pct",     # pct | zscore | al_first | signal_price
    "auto_opt_idx": 0,
}

def load_cfg():
    if SETTINGS_FILE.exists():
        try:
            d = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            cfg = dict(DEFAULT_CFG); cfg.update(d); return cfg
        except Exception: pass
    return dict(DEFAULT_CFG)

def save_cfg(d):
    try: SETTINGS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass

def load_history(n=100):
    if not HIST_FILE.exists(): return []
    try: return json.loads(HIST_FILE.read_text(encoding="utf-8"))[-n:]
    except Exception: return []

def save_history(hist):
    try: HIST_FILE.write_text(json.dumps(hist[-200:], ensure_ascii=False), encoding="utf-8")
    except Exception: pass

# ══════════════════════════════════════════════════════════════════
# BİNANCE API
# ══════════════════════════════════════════════════════════════════
# Yeni hali (Bunlardan birini dene):
API_BASE = "https://fapi.binance.us" # Eğer sorun ABD kaynaklıysa
# VEYA
API_BASE = "https://fapi1.binance.com" 
# VEYA 
API_BASE = "https://fapi2.binance.com"
BATCH_SIZE = 1499
REQ_DELAY  = 0.12

_sess = requests.Session()
_sess.headers["User-Agent"] = "SmartEMA2/1.0"

def api_get(path, params=None, retries=3):
    for i in range(retries):
        try:
            r = _sess.get(API_BASE + path, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception:
            if i == retries - 1: raise
            time.sleep(1.5)

@st.cache_data(ttl=90, show_spinner=False)
def get_symbols():
    data = api_get("/fapi/v1/exchangeInfo")
    return sorted({
        s["symbol"] for s in data["symbols"]
        if s.get("contractType") == "PERPETUAL"
        and s.get("quoteAsset")  == "USDT"
        and s.get("status")      == "TRADING"
    })

@st.cache_data(ttl=25, show_spinner=False)
def get_ticker_map():
    return {d["symbol"]: d for d in api_get("/fapi/v1/ticker/24hr")}

def fetch_klines(symbol, interval, needed):
    all_k, end_time = [], None
    for b in range(math.ceil(needed / BATCH_SIZE)):
        params = {"symbol": symbol, "interval": interval, "limit": BATCH_SIZE}
        if end_time: params["endTime"] = end_time
        try:
            batch = api_get("/fapi/v1/klines", params)
        except Exception:
            break
        if not batch: break
        all_k    = batch + all_k
        end_time = batch[0][0] - 1
        if len(all_k) >= needed: break
        if b < math.ceil(needed / BATCH_SIZE) - 1: time.sleep(REQ_DELAY)
    return all_k or None

# ══════════════════════════════════════════════════════════════════
# AKILLI LİSTE
# ══════════════════════════════════════════════════════════════════
def smart_list(valid_syms, top_vol, top_move, abs_chg):
    tm = get_ticker_map()
    items = [
        {"symbol": s,
         "volume": float(t.get("quoteVolume", 0)),
         "change": float(t.get("priceChangePercent", 0))}
        for s, t in tm.items() if s in set(valid_syms)
    ]
    items.sort(key=lambda x: x["volume"], reverse=True)
    items = items[:top_vol]
    items.sort(key=lambda x: abs(x["change"]) if abs_chg else x["change"], reverse=True)
    return [i["symbol"] for i in items[:top_move]]

# ══════════════════════════════════════════════════════════════════
# MA CROSSOVER ANALİZİ — Pine Script getCoinData() karşılığı
# ══════════════════════════════════════════════════════════════════
def calc_sma_series(closes, period):
    """Her bar için SMA dizisi döner (Pine Script ta.sma ile birebir)."""
    result = [None] * (period - 1)
    for i in range(period - 1, len(closes)):
        result.append(sum(closes[i - period + 1: i + 1]) / period)
    return result

def calc_ma_crossover(closes, ma_period):
    """
    Pine Script getCoinData() fonksiyonunun tam karşılığı.

    Döner:
        close_now   : son kapanış fiyatı
        ma_now      : son MA değeri
        signal      : "AL" | "SAT" | "-"
        signal_price: kesişim anındaki close (ta.valuewhen)
        pct_change  : (close_now - signal_price) / signal_price * 100
        cross_bar   : kesişimin kaç bar önce gerçekleştiği (0 = henüz yok)
    """
    n = len(closes)
    if n < ma_period + 1:
        return None

    ma = calc_sma_series(closes, ma_period)

    # Tüm barlar için crossover / crossunder tespiti
    # ta.crossover(close, ma) → closes[i-1] < ma[i-1] AND closes[i] >= ma[i]
    # ta.crossunder(close, ma) → closes[i-1] > ma[i-1] AND closes[i] < ma[i]
    last_cross_idx   = None   # son kesişim bar indeksi
    last_cross_type  = None   # "AL" ya da "SAT"
    last_cross_price = None   # kesişim anındaki close

    for i in range(1, n):
        if ma[i] is None or ma[i-1] is None:
            continue
        cross_up   = closes[i-1] < ma[i-1] and closes[i] >= ma[i]
        cross_down = closes[i-1] > ma[i-1] and closes[i] <  ma[i]
        if cross_up or cross_down:
            last_cross_idx   = i
            last_cross_type  = "AL" if cross_up else "SAT"
            last_cross_price = closes[i]

    close_now = closes[-1]
    ma_now    = ma[-1]

    if last_cross_idx is None:
        # Hiç kesişim yok
        return {
            "close":       close_now,
            "ma":          ma_now,
            "signal":      "-",
            "signal_price":None,
            "pct_change":  0.0,
            "cross_bar":   0,
        }

    pct = ((close_now - last_cross_price) / last_cross_price * 100) if last_cross_price else 0
    bars_since = n - 1 - last_cross_idx

    return {
        "close":       close_now,
        "ma":          ma_now,
        "signal":      last_cross_type,
        "signal_price":last_cross_price,
        "pct_change":  round(pct, 4),
        "cross_bar":   bars_since,
    }

def calc_zscore(values):
    """
    Pine Script Z-skor hesabı — (değer - ortalama) / std_sapma
    Gruba göre normalize eder.
    """
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return [0.0] * len(values)
    avg = sum(vals) / len(vals)
    variance = sum((v - avg) ** 2 for v in vals) / (len(vals) - 1)
    std = math.sqrt(variance) if variance > 0 else 0.0
    return [
        round((v - avg) / std, 4) if (v is not None and std > 0) else 0.0
        for v in values
    ]

# ══════════════════════════════════════════════════════════════════
# FORMATTERS
# ══════════════════════════════════════════════════════════════════
def fp(p):
    if p is None: return "—"
    if p >= 10000: return f"{p:,.0f}"
    if p >= 1000:  return f"{p:,.2f}"
    if p >= 1:     return f"{p:.4f}"
    return f"{p:.6f}"

def fv(v):
    if v >= 1e9: return f"{v/1e9:.2f}B"
    if v >= 1e6: return f"{v/1e6:.1f}M"
    if v >= 1e3: return f"{v/1e3:.0f}K"
    return f"{v:.0f}"

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
def _ss(k, v):
    if k not in st.session_state: st.session_state[k] = v

_ss("cfg",        load_cfg())
_ss("results",    [])
_ss("scan_count", 0)
_ss("last_time",  None)
_ss("sel_syms",   [])
_ss("auto_on",    False)
_ss("stop_flag",  False)
_ss("scan_hist",  load_history())

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:22px 18px 18px;border-bottom:1px solid #0d1f35">
      <div style="font-size:10px;letter-spacing:4px;color:#1a3a5a;font-weight:700;
                  text-transform:uppercase;margin-bottom:5px">Binance Futures</div>
      <div style="font-size:26px;font-weight:900;letter-spacing:1px;
                  background:linear-gradient(135deg,#00ff88,#00d4ff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent">
        📊 AKILLI EMA 200 — 2
      </div>
      <div style="font-size:10px;letter-spacing:3px;color:#1a3a5a;margin-top:3px">
        MA CROSSOVER PANEL · USDT-M
      </div>
    </div>
    """, unsafe_allow_html=True)

    cfg = st.session_state.cfg
    st.markdown('<div style="padding:0 14px">', unsafe_allow_html=True)

    # ── Akıllı Liste
    st.markdown('<div class="section-head">Akıllı Liste Filtresi</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    top_vol  = c1.number_input("Hacim Top-N",  10, 500, int(cfg.get("top_vol",  200)), key="tv")
    top_move = c2.number_input("Hareket Top-M", 3, 100, int(cfg.get("top_move",  20)), key="tm")
    abs_chg  = st.checkbox("Mutlak değişim (±)", bool(cfg.get("abs_change", True)), key="ac")

    # ── MA Crossover Ayarları
    st.markdown('<div class="section-head">MA Crossover Ayarları</div>', unsafe_allow_html=True)
    iv_opts = ["1m","3m","5m","15m","30m","1h","2h","4h","6h","12h","1d"]
    iv_def  = cfg.get("interval","1h")
    iv_idx  = iv_opts.index(iv_def) if iv_def in iv_opts else 5
    interval  = st.selectbox("Zaman Dilimi", iv_opts, index=iv_idx,
                              key="iv", label_visibility="collapsed")
    ma_period = st.number_input("MA Periyodu", 2, 500,
                                int(cfg.get("ma_period", 200)), 10,
                                key="ma_p",
                                help="Pine Script ta.sma ile birebir hesaplanır")

    sort_opts_map = {
        "% Değişim (büyük→küçük)":  "pct_desc",
        "% Değişim (küçük→büyük)":  "pct_asc",
        "Z-Skor (büyük→küçük)":     "z_desc",
        "Z-Skor (küçük→büyük)":     "z_asc",
        "AL önce":                   "al_first",
        "SAT önce":                  "sat_first",
        "Sinyal Fiyatı":             "signal_price",
        "Kesişim Bar (eski→yeni)":   "cross_old",
        "Kesişim Bar (yeni→eski)":   "cross_new",
    }
    sort_labels = list(sort_opts_map.keys())
    sort_def    = cfg.get("sort_by", "pct_desc")
    sort_vals   = list(sort_opts_map.values())
    sort_idx    = sort_vals.index(sort_def) if sort_def in sort_vals else 0
    sort_by = sort_opts_map[
        st.selectbox("Sıralama", sort_labels, index=sort_idx,
                     key="sb", label_visibility="collapsed")
    ]

    # ── Otomatik Tarama
    st.markdown('<div class="section-head">Otomatik Tarama</div>', unsafe_allow_html=True)
    auto_opts_map = {
        "Kapalı":0,"30 saniye":30,"1 dakika":60,"2 dakika":120,
        "5 dakika":300,"10 dakika":600,"15 dakika":900,
        "30 dakika":1800,"1 saat":3600,"2 saat":7200,"4 saat":14400
    }
    auto_opts = list(auto_opts_map.keys())
    auto_idx  = int(cfg.get("auto_opt_idx", 0))
    if auto_idx >= len(auto_opts): auto_idx = 0
    auto_opt = st.selectbox("Aralık", auto_opts, index=auto_idx,
                             key="ao", label_visibility="collapsed")
    auto_sec = auto_opts_map[auto_opt]

    if st.session_state.auto_on:
        lt_ = st.session_state.last_time
        st.markdown(
            f'<div style="background:rgba(0,255,136,.08);border:1px solid rgba(0,255,136,.25);'
            f'border-radius:4px;padding:6px 10px;font-family:monospace;font-size:10px;'
            f'color:#00ff88;margin-top:6px">'
            f'● Oto aktif · #{st.session_state.scan_count} '
            f'· {lt_.strftime("%H:%M:%S") if lt_ else "—"}</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    if st.button("💾  Ayarları Kaydet", use_container_width=True):
        save_cfg({
            "top_vol": top_vol, "top_move": top_move, "abs_change": abs_chg,
            "interval": interval, "ma_period": ma_period, "sort_by": sort_by,
            "auto_opt_idx": auto_opts.index(auto_opt),
        })
        st.session_state.cfg = load_cfg()
        st.success("✅ Kaydedildi")

    st.markdown("</div>", unsafe_allow_html=True)

    n_h = len(st.session_state.scan_hist)
    st.markdown(
        f'<div style="padding:10px 14px;border-top:1px solid #0d1f35;'
        f'font-family:monospace;font-size:10px;color:#1a3a5a">'
        f'Geçmiş: <span style="color:#2a5a7a">{n_h}</span> tarama</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
hd_l, hd_r = st.columns([3, 1])
with hd_l:
    sc  = st.session_state.scan_count
    lt  = st.session_state.last_time
    lts = lt.strftime("%d.%m.%Y %H:%M:%S") if lt else "—"
    st.markdown(f"""
    <div class="header-bar">
      <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap">
        <div style="font-size:26px;font-weight:900;letter-spacing:1px;
                    background:linear-gradient(135deg,#00ff88 30%,#00d4ff);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent">
          📊 AKILLI EMA 200 — 2
        </div>
        <div style="font-size:10px;letter-spacing:3px;color:#2a4a6a;font-weight:700;text-transform:uppercase">
          MA CROSSOVER PANEL
        </div>
      </div>
      <div style="display:flex;gap:20px;margin-top:8px;
                  font-family:'Share Tech Mono',monospace;font-size:11px;color:#2a4a6a">
        <span>Top-<span style="color:#00ff88">{top_vol}→{top_move}</span></span>
        <span>TF:<span style="color:#00ff88">{interval}</span></span>
        <span>MA-<span style="color:#00ff88">{ma_period}</span></span>
        <span>#{sc} tarama</span>
        <span>Son: <span style="color:#2a6a5a">{lts}</span></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with hd_r:
    res = st.session_state.results
    if res:
        al_n  = sum(1 for r in res if r["signal"] == "AL")
        sat_n = sum(1 for r in res if r["signal"] == "SAT")
        n_all = len(res)
        avg_z = sum(r["zscore"] for r in res) / n_all if n_all else 0
        st.markdown(f"""
        <div style="background:#070f1f;border:1px solid #0d1f35;border-radius:6px;
                    padding:14px;font-family:'Share Tech Mono',monospace;margin-top:4px">
          <div style="font-size:9px;letter-spacing:3px;color:#2a4a6a;margin-bottom:10px">ÖZET</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;text-align:center">
            <div>
              <div style="font-size:20px;color:#00ff88;font-weight:bold">{al_n}</div>
              <div style="font-size:9px;color:#2a4a6a">● AL</div>
            </div>
            <div>
              <div style="font-size:20px;color:#ff3366;font-weight:bold">{sat_n}</div>
              <div style="font-size:9px;color:#2a4a6a">● SAT</div>
            </div>
            <div>
              <div style="font-size:16px;color:#ffd700;font-weight:bold">{avg_z:+.2f}</div>
              <div style="font-size:9px;color:#2a4a6a">Ort Z</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# KONTROL BUTONLARI
# ══════════════════════════════════════════════════════════════════
b1, b2, b3, _ = st.columns([1, 1, 1.5, 2.5])
scan_btn = b1.button("⚡  TARA", use_container_width=True)
stop_btn = b2.button("■  DURDUR", use_container_width=True)
auto_lbl = "⏹  OTO DURDUR" if st.session_state.auto_on else "📊  OTO TARA"
auto_btn = b3.button(
    auto_lbl, use_container_width=True,
    disabled=(auto_sec == 0 and not st.session_state.auto_on),
    key="auto_toggle"
)

if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.auto_on   = False

if auto_btn:
    if st.session_state.auto_on:
        st.session_state.auto_on   = False
        st.session_state.stop_flag = True
    else:
        st.session_state.auto_on   = True
        st.session_state.stop_flag = False

# ══════════════════════════════════════════════════════════════════
# TARAMA FONKSİYONU
# ══════════════════════════════════════════════════════════════════
def run_scan():
    # MA hesabı için yeterli bar: ma_period * 3 (güvenlik payı)
    needed = max(ma_period * 3 + 50, 500)
    now    = datetime.now()
    st.session_state.stop_flag = False

    sp = st.empty()
    pp = st.empty()
    tp = st.empty()

    sp.markdown("""
    <div class="live-bar">
      <span class="pulse"></span>
      <span style="color:#00ff88;font-weight:700;letter-spacing:2px;font-size:11px">
        📊 AKILLI EMA 200 — 2
      </span>
      <span style="color:#e8f4ff">akıllı liste hesaplanıyor...</span>
    </div>""", unsafe_allow_html=True)

    try:
        # Adım 1: Akıllı Liste
        all_syms = get_symbols()
        selected = smart_list(all_syms, top_vol, top_move, abs_chg)
        total    = len(selected)
        t24      = get_ticker_map()

        sp.markdown(f"""
        <div class="live-bar">
          <span class="pulse"></span>
          <span style="color:#00ff88;font-weight:700;letter-spacing:2px;font-size:11px">
            📊 MA CROSSOVER
          </span>
          <span style="color:#e8f4ff">
            <b style="color:#00ff88">{total}</b> coin seçildi →
            MA{ma_period} crossover analizi başlıyor
          </span>
        </div>""", unsafe_allow_html=True)

        pbar = pp.progress(0.0, text=f"0 / {total}")

        # Adım 2: Her coin için MA crossover analizi
        raw_results = []
        for idx, sym in enumerate(selected):
            if st.session_state.stop_flag: break
            coin = sym.replace("USDT", "")
            pbar.progress(idx / max(total, 1),
                          text=f"Analiz: {idx}/{total}  ▸  {coin}")
            tp.markdown(
                f'<div class="live-bar">'
                f'<span class="pulse"></span>'
                f'<span style="color:#00ff88;font-size:10px;letter-spacing:2px">MA {ma_period}</span>'
                f'<span style="font-size:18px;font-weight:700;color:#fff;margin-left:4px">{coin}</span>'
                f'<span style="color:#2a4a6a;font-size:11px">{interval}</span>'
                f'<span style="margin-left:auto;color:#2a4a6a">{idx+1}/{total}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            try:
                kl = fetch_klines(sym, interval, needed)
                if not kl or len(kl) < ma_period + 1:
                    continue
                closes = [float(k[4]) for k in kl]
                res_ma = calc_ma_crossover(closes, ma_period)
                if res_ma is None:
                    continue
                tk = t24.get(sym, {})
                raw_results.append({
                    "symbol":       sym,
                    "signal":       res_ma["signal"],
                    "signal_price": res_ma["signal_price"],
                    "pct_change":   res_ma["pct_change"],
                    "cross_bar":    res_ma["cross_bar"],
                    "close":        res_ma["close"],
                    "ma":           round(res_ma["ma"], 6) if res_ma["ma"] else None,
                    "price":        float(tk.get("lastPrice", res_ma["close"])),
                    "change24":     float(tk.get("priceChangePercent", 0)),
                    "volume":       float(tk.get("quoteVolume", 0)),
                })
            except Exception:
                pass
            time.sleep(REQ_DELAY)

        # Adım 3: Z-Skor hesapla (gruba göre)
        pct_vals = [r["pct_change"] for r in raw_results]
        zscores  = calc_zscore(pct_vals)
        for i, r in enumerate(raw_results):
            r["zscore"] = zscores[i]

        # Adım 4: Sıralama — Pine Script'teki gibi: AL → - → SAT
        def _sort_key(r):
            sig_order = {"AL": 0, "-": 1, "SAT": 2}
            if sort_by == "pct_desc":     return (-r["pct_change"],)
            if sort_by == "pct_asc":      return (r["pct_change"],)
            if sort_by == "z_desc":       return (-r["zscore"],)
            if sort_by == "z_asc":        return (r["zscore"],)
            if sort_by == "al_first":     return (sig_order.get(r["signal"],1), -r["pct_change"])
            if sort_by == "sat_first":    return (2 - sig_order.get(r["signal"],1), r["pct_change"])
            if sort_by == "signal_price": return (r["signal_price"] or 0,)
            if sort_by == "cross_old":    return (-r["cross_bar"],)
            if sort_by == "cross_new":    return (r["cross_bar"],)
            # default: AL önce, sonra % değişim büyükten küçüğe
            return (sig_order.get(r["signal"], 1), -r["pct_change"])

        raw_results.sort(key=_sort_key)

        pbar.progress(1.0, text=f"Tamamlandı: {len(raw_results)} coin")

        st.session_state.results    = raw_results
        st.session_state.sel_syms   = selected
        st.session_state.scan_count += 1
        st.session_state.last_time   = now

        # Geçmiş kaydı
        al_  = sum(1 for r in raw_results if r["signal"] == "AL")
        sat_ = sum(1 for r in raw_results if r["signal"] == "SAT")
        hist_entry = {
            "time":     now.strftime("%Y-%m-%dT%H:%M:%S"),
            "n_sel":    total,
            "n_res":    len(raw_results),
            "al":       al_,
            "sat":      sat_,
            "avg_pct":  round(sum(r["pct_change"] for r in raw_results) / len(raw_results), 2)
                        if raw_results else 0,
            "avg_z":    round(sum(r["zscore"] for r in raw_results) / len(raw_results), 3)
                        if raw_results else 0,
        }
        hist = st.session_state.scan_hist
        hist.append(hist_entry)
        st.session_state.scan_hist = hist
        save_history(hist)

        sp.success(
            f"✅  #{st.session_state.scan_count}. tarama — "
            f"**{total}** seçildi → **{len(raw_results)}** analiz — "
            f"AL:{al_}  SAT:{sat_} — {now.strftime('%H:%M:%S')}"
        )
        tp.empty()

    except Exception as e:
        sp.error(f"Hata: {e}")
        tp.empty()

# Tetikle
if scan_btn or (auto_btn and not st.session_state.auto_on):
    run_scan()

# ══════════════════════════════════════════════════════════════════
# METRİK KARTLARI
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
res = st.session_state.results
sel = st.session_state.sel_syms

if res:
    n    = len(res)
    al_c = sum(1 for r in res if r["signal"] == "AL")
    sat_c= sum(1 for r in res if r["signal"] == "SAT")
    dash = n - al_c - sat_c
    avg_pct = sum(r["pct_change"] for r in res) / n
    avg_z   = sum(r["zscore"]    for r in res) / n
    max_z_r = max(res, key=lambda r: r["zscore"])
    min_z_r = min(res, key=lambda r: r["zscore"])

    m1,m2,m3,m4,m5,m6,m7 = st.columns(7)
    m1.metric("Seçilen",     len(sel))
    m2.metric("Analiz",      n)
    m3.metric("● AL",        al_c,  f"{al_c/n*100:.0f}%")
    m4.metric("● SAT",       sat_c, f"{sat_c/n*100:.0f}%", delta_color="inverse")
    m5.metric("○ —",         dash)
    m6.metric("Ort. % Değ.", f"{avg_pct:+.2f}%")
    m7.metric("Ort. Z-Skor", f"{avg_z:+.3f}")
    st.markdown("")

# ══════════════════════════════════════════════════════════════════
# TABLAR
# ══════════════════════════════════════════════════════════════════
tab_panel, tab_grafik, tab_zscore, tab_gecmis = st.tabs([
    "  📋  PANEL  ",
    "  📈  GRAFİK  ",
    "  📊  Z-SKOR  ",
    "  📜  GEÇMİŞ  ",
])

# ────────────────────────────────────────────────────
# TAB 1 — PANEL (Pine Script tablo karşılığı)
# ────────────────────────────────────────────────────
with tab_panel:
    if not res:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px">
          <div style="font-size:64px;opacity:.1;margin-bottom:16px">📊</div>
          <div style="font-size:13px;letter-spacing:3px;color:#1a3a5a;text-transform:uppercase">
            ⚡ TARA veya 📊 OTO TARA butonuna basın
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Filtre satırı
        pf1, pf2 = st.columns([1, 5])
        filt = pf1.selectbox("Filtre",
            ["Tümü","● AL","● SAT","○ —"],
            key="pf", label_visibility="collapsed")

        def _f(r):
            if filt == "● AL":  return r["signal"] == "AL"
            if filt == "● SAT": return r["signal"] == "SAT"
            if filt == "○ —":   return r["signal"] == "-"
            return True
        filt_res = [r for r in res if _f(r)]

        st.markdown(
            f'<div style="font-family:monospace;font-size:11px;color:#2a4a6a;margin-bottom:8px">'
            f'Gösterilen: <b style="color:#00d4ff">{len(filt_res)}</b> / {len(res)}'
            f' &nbsp;|&nbsp; {interval} MA{ma_period}'
            f'</div>',
            unsafe_allow_html=True
        )

        # ── HTML Tablo (Pine Script panel birebir karşılığı)
        th = "".join(
            f'<th style="background:#040b17;color:#2a5080;font-size:9px;letter-spacing:2px;'
            f'text-transform:uppercase;border:1px solid #0d1f35;padding:9px 8px;'
            f'font-family:Inter;font-weight:700;white-space:nowrap">{h}</th>'
            for h in ["#", "Coin", "Sinyal", "Sinyal Fiyatı",
                      "Mevcut Fiyat", "MA Değeri", "% Değişim",
                      "Z-Skor", "Kesişim Bar", "24s %", "Hacim"]
        )
        tr = ""
        for i, r in enumerate(filt_res, 1):
            coin = r["symbol"].replace("USDT","")
            sig  = r["signal"]

            # Renk mantığı — Pine Script ile birebir
            if sig == "AL":
                sig_col = "#00ff88"; sig_bg = "rgba(0,255,136,.12)"
            elif sig == "SAT":
                sig_col = "#ff3366"; sig_bg = "rgba(255,51,102,.12)"
            else:
                sig_col = "#888888"; sig_bg = "rgba(100,100,100,.08)"

            pct   = r["pct_change"]
            pct_col = "#00ff88" if pct >= 0 else "#ff3366"

            z     = r["zscore"]
            # Z-skor rengi: |z|>2 → turuncu, |z|>1 → sarı, diğer → gri
            z_col = "#ff8844" if abs(z) > 2 else "#ffd700" if abs(z) > 1 else "#5a8aaa"
            z_bg  = "rgba(255,136,68,.1)" if abs(z)>2 else "rgba(255,215,0,.07)" if abs(z)>1 else "transparent"

            chg24 = r.get("change24", 0)
            cc    = "#00ff88" if chg24 >= 0 else "#ff3366"

            # Kesişim bar rengi: yeni kesişim parlak, eski soluk
            cb    = r["cross_bar"]
            cb_col= "#00d4ff" if cb <= 5 else "#5a8aaa" if cb <= 20 else "#2a4a6a"

            tr += (
                f'<tr style="transition:background .1s" '
                f'onmouseover="this.style.background=\'#0a1628\'" '
                f'onmouseout="this.style.background=\'transparent\'">'
                f'<td style="color:#2a4a6a;font-size:10px;border:1px solid #0d1f35;'
                f'padding:6px 7px;text-align:center">{i}</td>'
                f'<td style="color:#ffd700;font-weight:700;font-size:13px;'
                f'border:1px solid #0d1f35;padding:6px 8px;font-family:monospace">{coin}</td>'
                f'<td style="color:{sig_col};font-weight:700;font-size:12px;'
                f'border:1px solid #0d1f35;padding:6px 8px;background:{sig_bg}">{sig}</td>'
                f'<td style="color:#c8dff0;font-size:12px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:right;font-family:monospace">'
                f'{fp(r["signal_price"])}</td>'
                f'<td style="color:#e8f4ff;font-size:12px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:right;font-family:monospace">'
                f'{fp(r["price"])}</td>'
                f'<td style="color:#3a6080;font-size:11px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:right;font-family:monospace">'
                f'{fp(r["ma"])}</td>'
                f'<td style="color:{pct_col};font-weight:bold;font-size:13px;'
                f'border:1px solid #0d1f35;padding:6px 8px;text-align:right;'
                f'background:{"rgba(0,255,136,.06)" if pct>=0 else "rgba(255,51,102,.06)"};'
                f'font-family:monospace">{pct:+.2f}%</td>'
                f'<td style="color:{z_col};font-weight:{"bold" if abs(z)>1 else "normal"};'
                f'font-size:12px;border:1px solid #0d1f35;padding:6px 8px;'
                f'text-align:right;background:{z_bg};font-family:monospace">{z:+.2f}</td>'
                f'<td style="color:{cb_col};font-size:11px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:center;font-family:monospace">{cb}</td>'
                f'<td style="color:{cc};font-size:11px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:right;font-family:monospace">{chg24:+.2f}%</td>'
                f'<td style="color:#3a6080;font-size:10px;border:1px solid #0d1f35;'
                f'padding:6px 8px;text-align:right;font-family:monospace">'
                f'{fv(r["volume"])}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<div style="overflow-x:auto;overflow-y:auto;max-height:640px;'
            f'border:1px solid #0d1f35;border-radius:6px">'
            f'<table style="width:100%;border-collapse:collapse;background:#070f1f">'
            f'<thead style="position:sticky;top:0;z-index:10"><tr>{th}</tr></thead>'
            f'<tbody>{tr}</tbody></table></div>',
            unsafe_allow_html=True
        )

        with st.expander("ℹ️  Sütun Açıklamaları"):
            st.markdown("""
            | Sütun | Açıklama |
            |---|---|
            | **Sinyal** | MA crossover: fiyat MA'yı yukarı keserse AL, aşağı keserse SAT |
            | **Sinyal Fiyatı** | Kesişim anındaki kapanış fiyatı (`ta.valuewhen`) |
            | **% Değişim** | `(mevcut - sinyal_fiyatı) / sinyal_fiyatı × 100` |
            | **Z-Skor** | % değişimin gruba göre standart sapma cinsinden konumu: |z|>2 turuncu, |z|>1 sarı |
            | **Kesişim Bar** | Son kesişimden bu yana geçen bar (0=henüz yok, mavi=taze) |
            """)

        with st.expander("⬇  CSV İndir"):
            csv_df = pd.DataFrame([{
                "Coin":          r["symbol"].replace("USDT",""),
                "Sinyal":        r["signal"],
                "Sinyal Fiyatı": fp(r["signal_price"]),
                "Mevcut Fiyat":  fp(r["price"]),
                "MA":            fp(r["ma"]),
                "% Değişim":     round(r["pct_change"], 4),
                "Z-Skor":        round(r["zscore"], 4),
                "Kesişim Bar":   r["cross_bar"],
                "24s %":         round(r.get("change24", 0), 2),
                "Hacim":         fv(r["volume"]),
            } for r in filt_res])
            st.download_button(
                "📥 CSV İndir",
                csv_df.to_csv(index=False).encode("utf-8"),
                f"smart_ema2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                key="csv_dl"
            )

# ────────────────────────────────────────────────────
# TAB 2 — GRAFİK
# ────────────────────────────────────────────────────
with tab_grafik:
    if not res:
        st.info("Tarama yapın.")
    else:
        # Pine Script'teki gibi % değişim çizgi grafiği — her coin renkte
        st.markdown("#### % Değişim — MA Kesişiminden Bu Yana (Pine Script plot() karşılığı)")

        palette = [
            "#00ff88","#ff3366","#00d4ff","#ffd700","#a78bfa",
            "#ff8844","#f472b6","#34d399","#60a5fa","#fb923c",
            "#00ffaa","#ff6688","#44aaff","#ffdd44","#cc88ff",
            "#ffaa66","#ff99cc","#66ffcc","#88ccff","#ffcc88",
        ]
        gc1, gc2 = st.columns([3, 1])

        with gc1:
            # Scatter: X=coin, Y=% değişim, renk=sinyal, boyut=hacim
            coins_g  = [r["symbol"].replace("USDT","") for r in res]
            pcts_g   = [r["pct_change"] for r in res]
            vols_g   = [r["volume"] for r in res]
            sigs_g   = [r["signal"] for r in res]
            zs_g     = [r["zscore"] for r in res]
            maxv     = max(vols_g) if vols_g else 1
            sizes_g  = [max(10, min(55, (v/maxv)**0.4*50)) for v in vols_g]
            cols_g   = ["#00ff88" if s=="AL" else "#ff3366" if s=="SAT" else "#888888"
                        for s in sigs_g]

            # Z>2 halkası
            hrx, hry, hrc = [], [], []
            for i, z in enumerate(zs_g):
                if abs(z) > 1:
                    hrx.append(i); hry.append(pcts_g[i])
                    hrc.append("#ff8844" if abs(z)>2 else "#ffd700")

            fig_sc = go.Figure()
            fig_sc.add_hline(y=0, line_color="#5a8aaa", line_width=1.5,
                line_dash="dash", opacity=0.5,
                annotation_text="  0%", annotation_position="right",
                annotation_font_color="#5a8aaa", annotation_font_size=11)

            if hrx:
                fig_sc.add_trace(go.Scatter(
                    x=hrx, y=hry, mode="markers",
                    marker=dict(size=[sizes_g[xi]+14 for xi in hrx],
                                color="rgba(0,0,0,0)",
                                line=dict(color=hrc, width=2.5)),
                    hoverinfo="skip", showlegend=False,
                ))

            fig_sc.add_trace(go.Scatter(
                x=list(range(len(coins_g))), y=pcts_g,
                mode="markers+text",
                marker=dict(size=sizes_g, color=cols_g, opacity=0.90,
                            line=dict(color="rgba(0,0,0,.25)", width=0.5)),
                text=coins_g,
                textposition="top center",
                textfont=dict(size=10, color="#fff", family="Inter"),
                hovertext=[
                    f"<b>{c}</b><br>"
                    f"% Değişim: <b>{p:+.2f}%</b><br>"
                    f"Z-Skor: {z:+.2f}<br>"
                    f"Sinyal: {s}<br>"
                    f"Kesişim: {cb} bar önce"
                    for c, p, z, s, cb in zip(
                        coins_g, pcts_g, zs_g, sigs_g,
                        [r["cross_bar"] for r in res]
                    )
                ],
                hoverinfo="text", showlegend=False,
            ))
            step_g = max(1, len(coins_g) // 30)
            fig_sc.update_layout(
                plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
                font=dict(color="#8aaccc", family="Inter"),
                xaxis=dict(showgrid=False, zeroline=False,
                    tickvals=list(range(len(coins_g)))[::step_g],
                    ticktext=coins_g[::step_g],
                    tickangle=45, tickfont=dict(size=9, color="#3a6080"),
                    range=[-0.5, len(coins_g)-0.5]),
                yaxis=dict(gridcolor="#0d1f35",
                    tickfont=dict(size=10, color="#5a8aaa"),
                    title=dict(text="% Değişim (MA kesişiminden)",
                               font=dict(size=11, color="#3a6080"))),
                height=500,
                margin=dict(t=20, b=80, l=60, r=100),
                hovermode="closest",
                hoverlabel=dict(bgcolor="#0a1628", bordercolor="#0d2035",
                    font=dict(color="#c8dff0", size=12, family="Share Tech Mono")),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        with gc2:
            st.markdown("#### Sinyal")
            al_n  = sum(1 for r in res if r["signal"] == "AL")
            sat_n = sum(1 for r in res if r["signal"] == "SAT")
            dsh_n = len(res) - al_n - sat_n
            fig_p = go.Figure(go.Pie(
                labels=["● AL","○ —","● SAT"],
                values=[al_n, dsh_n, sat_n],
                marker_colors=["#00ff88","#888888","#ff3366"],
                hole=0.55, textinfo="label+value+percent",
                textfont=dict(size=11), pull=[0.05,0,0.05],
            ))
            fig_p.update_layout(
                plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
                font=dict(color="#5a8aaa", family="Share Tech Mono"),
                height=300, margin=dict(t=10,b=10,l=10,r=10),
                showlegend=False,
                annotations=[dict(text=f"<b>{len(res)}</b><br>Coin",
                    x=0.5, y=0.5, font_size=16, font_color="#e8f4ff", showarrow=False)]
            )
            st.plotly_chart(fig_p, use_container_width=True)

            # Kesişim bar dağılımı (histogram mini)
            st.markdown("#### Kesişim Tazeliği")
            cbs = [r["cross_bar"] for r in res if r["signal"] != "-"]
            if cbs:
                fig_cb = go.Figure(go.Histogram(
                    x=cbs, nbinsx=20,
                    marker_color="#00d4ff", opacity=0.8,
                ))
                fig_cb.update_layout(
                    plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
                    font=dict(color="#5a8aaa", family="Share Tech Mono"),
                    xaxis=dict(gridcolor="#0d1f35",
                               title=dict(text="Bar Sayısı", font=dict(size=10, color="#3a6080"))),
                    yaxis=dict(gridcolor="#0d1f35"),
                    height=200, margin=dict(t=10,b=40,l=40,r=10),
                    showlegend=False,
                )
                st.plotly_chart(fig_cb, use_container_width=True)

# ────────────────────────────────────────────────────
# TAB 3 — Z-SKOR ANALİZİ
# ────────────────────────────────────────────────────
with tab_zscore:
    if not res:
        st.info("Tarama yapın.")
    else:
        st.markdown("#### Z-Skor Dağılımı — % Değişimin Gruba Göre Normalize Konumu")
        st.markdown("""
        <div style="font-family:monospace;font-size:11px;color:#2a4a6a;margin-bottom:12px">
          <span style="color:#ff8844">■</span> |Z|>2 — Aşırı sapma (nadir)
          &nbsp;&nbsp;
          <span style="color:#ffd700">■</span> |Z|>1 — Belirgin sapma
          &nbsp;&nbsp;
          <span style="color:#5a8aaa">■</span> |Z|≤1 — Normal aralık
        </div>
        """, unsafe_allow_html=True)

        # Z-skor bar grafiği — Pine Script'teki gibi sıralı
        sorted_by_z = sorted(res, key=lambda r: r["zscore"], reverse=True)
        z_coins = [r["symbol"].replace("USDT","") for r in sorted_by_z]
        z_vals  = [r["zscore"] for r in sorted_by_z]
        z_cols  = ["#ff8844" if abs(z)>2 else "#ffd700" if abs(z)>1 else "#5a8aaa"
                   for z in z_vals]

        fig_z = go.Figure(go.Bar(
            x=z_coins, y=z_vals,
            marker_color=z_cols,
            hovertext=[
                f"<b>{r['symbol'].replace('USDT','')}</b><br>"
                f"Z-Skor: <b>{r['zscore']:+.3f}</b><br>"
                f"% Değişim: {r['pct_change']:+.2f}%<br>"
                f"Sinyal: {r['signal']}"
                for r in sorted_by_z
            ],
            hoverinfo="text",
        ))
        # ±1 ve ±2 çizgileri
        for yv, lc, lbl in [
            ( 2, "#ff8844", "+2σ"),
            ( 1, "#ffd700", "+1σ"),
            ( 0, "#5a8aaa", "0"),
            (-1, "#ffd700", "-1σ"),
            (-2, "#ff8844", "-2σ"),
        ]:
            fig_z.add_hline(
                y=yv, line_color=lc, line_width=1,
                line_dash="dash" if yv != 0 else "solid", opacity=0.5,
                annotation_text=f"  {lbl}",
                annotation_position="right",
                annotation_font_color=lc,
                annotation_font_size=10,
            )
        fig_z.update_layout(
            plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
            font=dict(color="#8aaccc", family="Inter"),
            xaxis=dict(showgrid=False, tickangle=45,
                       tickfont=dict(size=8, color="#3a6080")),
            yaxis=dict(gridcolor="#0d1f35", zeroline=False,
                       tickfont=dict(size=10, color="#5a8aaa"),
                       title=dict(text="Z-Skor", font=dict(size=11, color="#3a6080"))),
            height=420,
            margin=dict(t=20, b=80, l=60, r=100),
            hovermode="closest",
            hoverlabel=dict(bgcolor="#0a1628", bordercolor="#0d2035",
                font=dict(color="#c8dff0", size=12, family="Share Tech Mono")),
        )
        st.plotly_chart(fig_z, use_container_width=True)

        # Öne çıkan Z-skor tablosu
        extreme = [r for r in res if abs(r["zscore"]) > 1]
        extreme.sort(key=lambda r: abs(r["zscore"]), reverse=True)
        if extreme:
            st.markdown("#### Belirgin Sapma (|Z| > 1)")
            ext_df = pd.DataFrame([{
                "Coin":    r["symbol"].replace("USDT",""),
                "Z-Skor":  f'{r["zscore"]:+.3f}',
                "% Değ.":  f'{r["pct_change"]:+.2f}%',
                "Sinyal":  r["signal"],
                "Kes. Bar":r["cross_bar"],
                "Yorum":   (
                    "⚠ Aşırı Yüksek" if r["zscore"] > 2 else
                    "⚠ Aşırı Düşük"  if r["zscore"] < -2 else
                    "↑ Yüksek"        if r["zscore"] > 1 else
                    "↓ Düşük"
                ),
            } for r in extreme])
            st.dataframe(ext_df, use_container_width=True, hide_index=True)

# ────────────────────────────────────────────────────
# TAB 4 — GEÇMİŞ
# ────────────────────────────────────────────────────
with tab_gecmis:
    hist = st.session_state.scan_hist
    if not hist:
        st.info("Henüz tarama geçmişi yok.")
    else:
        st.markdown(f"**{len(hist)}** tarama kaydı")
        hist_df = pd.DataFrame([{
            "Zaman":    h["time"].replace("T"," "),
            "Seçilen":  h["n_sel"],
            "Analiz":   h["n_res"],
            "● AL":     h["al"],
            "● SAT":    h["sat"],
            "○ —":      h["n_res"]-h["al"]-h["sat"],
            "Ort.%":    f"{h['avg_pct']:+.2f}%",
            "Ort.Z":    f"{h.get('avg_z',0):+.3f}",
        } for h in reversed(hist)])
        st.dataframe(hist_df, use_container_width=True, hide_index=True, height=380)

        if len(hist) >= 2:
            st.markdown("---")
            st.markdown("#### AL / SAT Sinyal Trendi")
            times_h = [h["time"].replace("T"," ") for h in hist]
            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(
                x=times_h, y=[h["al"] for h in hist],
                name="● AL", mode="lines+markers",
                line=dict(color="#00ff88", width=2), marker=dict(size=5),
            ))
            fig_h.add_trace(go.Scatter(
                x=times_h, y=[h["sat"] for h in hist],
                name="● SAT", mode="lines+markers",
                line=dict(color="#ff3366", width=2), marker=dict(size=5),
            ))
            fig_h.add_trace(go.Scatter(
                x=times_h, y=[h["avg_pct"] for h in hist],
                name="Ort.%", mode="lines",
                line=dict(color="#00d4ff", width=1.5, dash="dot"),
                yaxis="y2",
            ))
            fig_h.update_layout(
                plot_bgcolor="#050d1a", paper_bgcolor="#050d1a",
                font=dict(color="#8aaccc", family="Inter"),
                xaxis=dict(gridcolor="#0d1f35", tickangle=45,
                           tickfont=dict(size=8, color="#3a6080")),
                yaxis=dict(gridcolor="#0d1f35", title="Sinyal Sayısı",
                           tickfont=dict(size=9, color="#5a8aaa")),
                yaxis2=dict(overlaying="y", side="right",
                            title="Ort. % Değ.", showgrid=False,
                            tickfont=dict(size=9, color="#00d4ff")),
                height=300,
                margin=dict(t=20, b=60, l=50, r=70),
                hovermode="x unified",
                legend=dict(bgcolor="#070f1f", bordercolor="#0d1f35",
                            font=dict(size=10), orientation="h",
                            yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            st.plotly_chart(fig_h, use_container_width=True)

        if st.button("🗑  Geçmişi Temizle", key="clr"):
            st.session_state.scan_hist = []
            HIST_FILE.unlink(missing_ok=True)
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# OTO TARAMA GERİ SAYIM
# ══════════════════════════════════════════════════════════════════
if st.session_state.auto_on and auto_sec > 0:
    cd = st.empty()
    for rem in range(auto_sec, 0, -1):
        if st.session_state.stop_flag or not st.session_state.auto_on: break
        m_, s_ = divmod(rem, 60)
        cd.markdown(f"""
        <div class="countdown-bar">
          <span style="color:#00d4ff;font-size:10px;letter-spacing:2px">📊 OTO TARAMA</span>
          <span style="font-size:24px;font-weight:bold;color:#00d4ff">
            {'%d:%02d' % (m_,s_) if m_ else f'{s_}s'}
          </span>
          <span style="color:#2a4a6a">#{st.session_state.scan_count+1}. tarama</span>
          <span style="color:#2a4a6a;font-size:10px">
            Top-{top_vol}→{top_move} · MA{ma_period} · {interval}
          </span>
          <span style="margin-left:auto;font-size:10px;color:#2a4a6a">■ DURDUR ile iptal</span>
        </div>""", unsafe_allow_html=True)
        time.sleep(1)
    if not st.session_state.stop_flag and st.session_state.auto_on:
        cd.empty()
        run_scan()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;
            font-family:'Share Tech Mono',monospace;font-size:10px;
            color:#1a3a5a;padding:4px 0 16px">
  <span>📊 Akıllı EMA 200 — 2 · MA Crossover Panel · Binance USDT-M Perpetual</span>
  <span>streamlit run smart_ema200_2.py</span>
</div>
""", unsafe_allow_html=True)
