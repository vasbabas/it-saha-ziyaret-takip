"""
app.py  —  IT Saha Ziyaret Takip Uygulamasi
Streamlit tabanlı ana uygulama.  Calistirmak: streamlit run app.py
"""

import re
import calendar
from datetime import date, datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

import database as db
import reports as rpt

# ─────────────────────────────────────────────
# Sayfa konfigürasyonu
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="IT Saha Takip",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Performans: @st.cache_data  (TTL = saniye)
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def cached_summary_stats():      return db.get_summary_stats()

@st.cache_data(ttl=60)
def cached_companies():          return db.get_all_companies()

@st.cache_data(ttl=30)
def cached_monthly_trend(year):  return db.get_monthly_trend(year)

@st.cache_data(ttl=60)
def cached_co_dist(top_n=8):     return db.get_company_distribution(top_n)

@st.cache_data(ttl=60)
def cached_tech_stats():         return db.get_technician_stats()

@st.cache_data(ttl=15)
def cached_due_reminders():      return db.get_due_reminders_today()

@st.cache_data(ttl=15)
def cached_overdue_todos():      return db.get_overdue_todos()

@st.cache_data(ttl=15)
def cached_todo_stats():         return db.get_todo_stats()

@st.cache_data(ttl=10)
def cached_recent_visits(n=10):  return db.get_visits()[:n]

def invalidate_caches():
    for fn in [cached_summary_stats, cached_companies, cached_monthly_trend,
               cached_co_dist, cached_tech_stats, cached_due_reminders,
               cached_overdue_todos, cached_todo_stats, cached_recent_visits]:
        fn.clear()

# ─────────────────────────────────────────────
# CSS  —  Ferah, Modern, Mobil-Uyumlu
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Font ───────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── Arkaplan ────────────────────────────────── */
.stApp {
    background: #0B1623;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% 10%,  rgba(30,90,160,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%,  rgba(15,60,120,0.12) 0%, transparent 60%);
    min-height: 100vh;
}
.stApp, .stApp p, .stApp li { color: #D6E4F5; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.28); }

/* ── Sekmeler ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 5px 6px;
    gap: 2px;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 11px;
    padding: 9px 18px;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: rgba(180,205,230,0.65) !important;
    border: none !important;
    background: transparent !important;
    transition: color .2s, background .2s;
    letter-spacing: .01em;
}
.stTabs [data-baseweb="tab"]:hover { color: #C8DFF5 !important; background: rgba(255,255,255,0.06) !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 20px rgba(30,136,229,0.35);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"]    { display: none; }

/* ── Metrik Kartlar ──────────────────────────── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.038);
    border: 1px solid rgba(255,255,255,0.075);
    border-radius: 18px;
    padding: 18px 20px;
    transition: transform .22s cubic-bezier(.34,1.56,.64,1), box-shadow .22s ease;
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, rgba(33,150,243,0.06) 0%, transparent 60%);
    pointer-events: none;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 35px rgba(33,150,243,0.15);
    border-color: rgba(33,150,243,0.3);
}
[data-testid="stMetricValue"] {
    color: #60B4FF !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
    letter-spacing: -.02em;
}
[data-testid="stMetricLabel"] {
    color: rgba(180,210,240,0.7) !important;
    font-size: 11.5px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: .06em;
}
[data-testid="stMetricDelta"] > div { font-size: 12px !important; }

/* ── Butonlar ────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1565C0, #1E88E5) !important;
    color: #fff !important; border: none !important;
    border-radius: 11px !important; padding: 9px 22px !important;
    font-weight: 600 !important; font-size: 13.5px !important;
    font-family: inherit !important;
    transition: opacity .18s, transform .18s, box-shadow .18s !important;
    box-shadow: 0 4px 18px rgba(21,101,192,0.35) !important;
    width: 100%;
}
.stButton > button:hover {
    opacity: .9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 7px 25px rgba(30,136,229,0.45) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.13) !important;
    box-shadow: none !important; color: #B0D0F0 !important;
}
.stButton > button[kind="secondary"]:hover { background: rgba(255,255,255,0.12) !important; }

/* ── Form Alanları ───────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: rgba(255,255,255,0.055) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 11px !important;
    color: #DCE9F8 !important;
    font-size: 14px !important;
    font-family: inherit !important;
    transition: border-color .18s, box-shadow .18s !important;
    padding: 10px 14px !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.055) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 11px !important;
    color: #DCE9F8 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: rgba(33,150,243,0.6) !important;
    box-shadow: 0 0 0 3px rgba(33,150,243,0.15) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stDateInput label,
.stRadio > label, .stCheckbox > label > span {
    color: rgba(180,210,245,0.75) !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    letter-spacing: .02em;
}

/* ── Uyarı Mesajları ─────────────────────────── */
.stSuccess > div, div[data-testid="stAlert"][data-baseweb*="success"] {
    background: rgba(46,160,67,0.12) !important; border-left: 3px solid #4CAF50 !important;
    border-radius: 10px !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
}
.stError > div {
    background: rgba(220,53,69,0.12) !important; border-left: 3px solid #EF5350 !important;
    border-radius: 10px !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
}
.stWarning > div {
    background: rgba(255,152,0,0.1) !important; border-left: 3px solid #FF9800 !important;
    border-radius: 10px !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
}
.stInfo > div {
    background: rgba(33,150,243,0.1) !important; border-left: 3px solid #2196F3 !important;
    border-radius: 10px !important; border-top: none !important; border-right: none !important; border-bottom: none !important;
}

/* ── Tablo ───────────────────────────────────── */
[data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden !important; border: 1px solid rgba(255,255,255,0.08) !important; }

/* ── Expander ────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.075) !important;
    border-radius: 14px !important;
    margin-bottom: 6px !important;
    transition: border-color .2s;
}
[data-testid="stExpander"]:hover { border-color: rgba(33,150,243,0.25) !important; }
[data-testid="stExpander"] summary { padding: 12px 16px !important; }

/* ── İndirme Butonu ──────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1B5E20, #388E3C) !important;
    box-shadow: 0 4px 18px rgba(56,142,60,0.3) !important;
}
.stDownloadButton > button:hover { box-shadow: 0 7px 25px rgba(76,175,80,0.4) !important; }

/* ── Başlıklar ───────────────────────────────── */
h1,h2,h3,h4 { color: #E0EFFF !important; font-family: inherit !important; }
h1 { font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -.03em; }
h2 { font-size: 1.25rem !important; font-weight: 650 !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; }

/* ── Sekme içi bölüm başlığı ─────────────────── */
.section-title {
    font-size: 15px; font-weight: 700; color: #90CAF9;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding-bottom: 10px; margin: 0 0 16px 0;
    display: flex; align-items: center; gap: 8px;
}

/* ── Kart ────────────────────────────────────── */
.card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px; padding: 18px 20px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.card:hover { border-color: rgba(33,150,243,0.22); }

/* ── Öncelik renk şeridi ─────────────────────── */
.pri-acil   { border-left: 3px solid #EF5350; }
.pri-onemli { border-left: 3px solid #FF9800; }
.pri-normal { border-left: 3px solid #42A5F5; }

/* ── Arama sonucu ────────────────────────────── */
.result-card {
    background: rgba(255,255,255,0.032);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 8px;
    transition: border-color .18s, background .18s;
}
.result-card:hover { background: rgba(33,150,243,0.06); border-color: rgba(33,150,243,0.3); }

/* ── Vega/Altair şeffaf zemin ────────────────── */
.vega-embed, .vega-embed canvas { background: transparent !important; }
.vega-embed .vega-actions { opacity: .3; }
.vega-embed .vega-actions:hover { opacity: 1; }

/* ── Gizle ───────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Mobil ───────────────────────────────────── */
@media (max-width: 800px) {
    h1 { font-size: 1.2rem !important; }
    .stTabs [data-baseweb="tab"] { padding: 7px 11px !important; font-size: 11px !important; }
    [data-testid="stMetricValue"] { font-size: 1.35rem !important; }
    [data-testid="stHorizontalBlock"] > div { min-width: 48% !important; }
    .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
    [data-testid="stDataFrame"] { overflow-x: auto !important; }
    .stButton > button { padding: 11px !important; font-size: 14px !important; }
}
@media (max-width: 480px) {
    [data-testid="stHorizontalBlock"] > div { min-width: 100% !important; }
    .stTabs [data-baseweb="tab"] { padding: 6px 8px !important; font-size: 10px !important; }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sabitler
# ─────────────────────────────────────────────
MONTHS_TR = {
    1:"Ocak",2:"Subat",3:"Mart",4:"Nisan",5:"Mayis",6:"Haziran",
    7:"Temmuz",8:"Agustos",9:"Eylul",10:"Ekim",11:"Kasim",12:"Aralik"
}
DAYS_TR          = ["Pzt","Sal","Car","Per","Cum","Cmt","Paz"]
STATUS_OPTIONS   = ["Tamamlandi","Devam Ediyor","Iptal","Beklemede"]
PRIORITY_OPTIONS = ["Normal","Onemli","Acil"]
PRIORITY_COLORS  = {"Acil":"#EF5350","Onemli":"#FF9800","Normal":"#42A5F5"}
CHART_H          = 260  # Standart grafik yüksekliği

# ─────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────
db.init_db()

# ─────────────────────────────────────────────
# Yardımcı Fonksiyonlar
# ─────────────────────────────────────────────

def fmt_date(s: str) -> str:
    try:    return datetime.strptime(s, "%Y-%m-%d").strftime("%d.%m.%Y")
    except: return s or "—"

def highlight(text: str, q: str) -> str:
    if not q or not text: return text or ""
    return re.compile(re.escape(q), re.IGNORECASE).sub(
        lambda m: f"<mark style='background:rgba(33,150,243,.3);color:#90CAF9;"
                  f"border-radius:3px;padding:0 2px'>{m.group()}</mark>", str(text))

def pri_class(p: str) -> str:
    return {"Acil":"pri-acil","Onemli":"pri-onemli"}.get(p, "pri-normal")

# ─── Altair tema ─────────────────────────────

CHART_CFG = {
    "background": "transparent",
    "view":   {"stroke": "transparent", "strokeOpacity": 0},
    "axis": {
        "gridColor":   "rgba(255,255,255,0.06)",
        "gridOpacity": 1,
        "tickColor":   "rgba(255,255,255,0.15)",
        "domainColor": "rgba(255,255,255,0.1)",
        "labelColor":  "#8AAAC8",
        "titleColor":  "#A0BEDC",
        "labelFontSize": 11,
        "titleFontSize": 11,
        "titleFontWeight": 500,
    },
    "title": {"color":"#D0E8FF","fontSize":13,"fontWeight":600,"anchor":"start"},
    "legend": {
        "labelColor": "#8AAAC8","titleColor":"#A0BEDC",
        "labelFontSize":11,"titleFontSize":11,
    },
    "mark": {"tooltip": True},
}

def ch(chart): return chart.configure(**CHART_CFG)

# ─────────────────────────────────────────────
# App Header
# ─────────────────────────────────────────────

def app_header():
    due  = cached_due_reminders()
    tds  = cached_todo_stats()
    badges = ""
    if due:
        badges += f"<span style='background:rgba(239,83,80,.85);border-radius:20px;padding:2px 10px;font-size:12px;font-weight:600;margin-left:10px'>⚠️ {len(due)} Hatırlatıcı</span>"
    if tds.get("overdue",0):
        badges += f"<span style='background:rgba(255,152,0,.85);border-radius:20px;padding:2px 10px;font-size:12px;font-weight:600;margin-left:6px'>📋 {tds['overdue']} Gecikmiş</span>"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(21,101,192,0.18) 0%,rgba(11,22,35,0.5) 100%);
        border:1px solid rgba(33,150,243,0.2);border-radius:20px;
        padding:20px 28px;margin-bottom:22px;
        backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);
        display:flex;align-items:center;gap:16px;">
      <div style="font-size:42px;flex-shrink:0">🛠️</div>
      <div style="flex:1;min-width:0">
        <h1 style="margin:0;font-size:1.55rem;
            background:linear-gradient(90deg,#60B4FF 0%,#A5D4FF 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
          IT Saha Ziyaret Takip{badges}
        </h1>
        <p style="margin:5px 0 0;color:rgba(160,200,240,.65);font-size:12.5px;letter-spacing:.02em">
          📅 {datetime.now().strftime('%d %B %Y, %A — %H:%M')}
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEKME 1 — DASHBOARD
# ─────────────────────────────────────────────

def tab_dashboard():
    # Uyarı bandı
    due_r = cached_due_reminders()
    due_t = cached_overdue_todos()
    if due_r or due_t:
        items = []
        if due_r: items.append(f"<b style='color:#EF9A9A'>⚠️ {len(due_r)} hatırlatıcı</b>: " + " · ".join(r["company"]+" — "+r["title"] for r in due_r[:2]))
        if due_t: items.append(f"<b style='color:#FFCC80'>📋 {len(due_t)} gecikmiş görev</b>: " + " · ".join(t["title"] for t in due_t[:2]))
        st.markdown(
            "<div style='background:rgba(183,28,28,.13);border:1px solid rgba(239,83,80,.35);"
            "border-radius:12px;padding:11px 18px;margin-bottom:16px;font-size:13.5px'>"
            + " &nbsp;|&nbsp; ".join(items) + "</div>", unsafe_allow_html=True)

    # ── Metrikler ──
    stats = cached_summary_stats()
    tds   = cached_todo_stats()
    c = st.columns(6)
    c[0].metric("🏢 Toplam Ziyaret",   stats["total_visits"])
    c[1].metric("⏱️ Toplam Süre",      f"{stats['total_hours']:.1f} sa")
    c[2].metric("📅 Bu Ay",            stats["month_visits"])
    c[3].metric("🕐 Bu Ay Süre",       f"{stats['month_hours']:.1f} sa")
    c[4].metric("🏭 Firma",            stats["unique_companies"])
    c[5].metric("📋 Bekleyen Görev",   tds["pending"],
                delta=f"−{tds['overdue']} gecikmiş" if tds["overdue"] else None,
                delta_color="inverse")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Grafik Satırı 1: Trend + Firmalar ──
    gl, gr = st.columns([5, 4], gap="medium")

    with gl:
        st.markdown('<div class="section-title">📈 Aylık Ziyaret Trendi</div>', unsafe_allow_html=True)
        cy   = date.today().year
        yr   = st.selectbox("", list(range(cy-3, cy+1)), index=3, key="dash_yr",
                            label_visibility="collapsed")
        trend = cached_monthly_trend(yr)

        if trend:
            all_v = {m:0   for m in range(1,13)}
            all_h = {m:0.0 for m in range(1,13)}
            for r in trend:
                all_v[r["month_num"]] = r["visit_count"]
                all_h[r["month_num"]] = r["total_hours"] or 0

            df_t = pd.DataFrame({
                "Ay":      [MONTHS_TR[m][:3] for m in range(1,13)],
                "Sira":    list(range(1,13)),
                "Ziyaret": [all_v[m] for m in range(1,13)],
                "Saat":    [all_h[m]  for m in range(1,13)],
            })

            x_enc = alt.X("Ay:O", sort=list(df_t["Ay"]),
                          axis=alt.Axis(labelAngle=0, labelFontSize=11, tickMinStep=1))

            bars = alt.Chart(df_t).mark_bar(
                cornerRadiusTopLeft=6, cornerRadiusTopRight=6,
                opacity=0.82,
                color=alt.Gradient(gradient="linear",
                    stops=[alt.GradientStop(color="#0D47A1",offset=0),
                           alt.GradientStop(color="#42A5F5",offset=1)],
                    x1=0,x2=0,y1=1,y2=0)
            ).encode(
                x=x_enc,
                y=alt.Y("Ziyaret:Q", title="Ziyaret Sayısı",
                        axis=alt.Axis(labelFontSize=10, gridOpacity=0.4)),
                tooltip=[alt.Tooltip("Ay:O",title="Ay"),
                         alt.Tooltip("Ziyaret:Q",title="Ziyaret"),
                         alt.Tooltip("Saat:Q",title="Saat",format=".1f")]
            )

            line = alt.Chart(df_t).mark_line(
                color="#4CAF50", strokeWidth=2.5, interpolate="monotone"
            ).mark_line(color="#4CAF50",strokeWidth=2.5,interpolate="monotone"
            ).encode(
                x=x_enc,
                y=alt.Y("Saat:Q", title="Toplam Saat",
                        axis=alt.Axis(labelFontSize=10, gridOpacity=0)),
                tooltip=[alt.Tooltip("Ay:O",title="Ay"),
                         alt.Tooltip("Saat:Q",title="Saat",format=".1f")]
            )
            dots = alt.Chart(df_t).mark_point(
                color="#4CAF50", size=55, filled=True, opacity=0.9
            ).encode(x=x_enc, y=alt.Y("Saat:Q"))

            chart = (
                alt.layer(bars, line+dots)
                .resolve_scale(y="independent")
                .properties(height=CHART_H, padding={"left":8,"right":8,"top":8,"bottom":4})
            )
            st.altair_chart(ch(chart), use_container_width=True)
        else:
            st.markdown(f"<div style='text-align:center;padding:60px;color:#8AAAC8'>"
                        f"📭 {yr} yılına ait veri yok</div>", unsafe_allow_html=True)

    with gr:
        st.markdown('<div class="section-title">🏭 En Çok Ziyaret Edilen Firmalar</div>', unsafe_allow_html=True)
        co_data = cached_co_dist(8)
        if co_data:
            df_co = pd.DataFrame(co_data)
            ch_co = alt.Chart(df_co).mark_bar(
                cornerRadiusTopRight=6, cornerRadiusBottomRight=6,
                color=alt.Gradient(gradient="linear",
                    stops=[alt.GradientStop(color="#1A3A6C",offset=0),
                           alt.GradientStop(color="#1E88E5",offset=1)],
                    x1=0,x2=1,y1=0,y2=0)
            ).encode(
                y=alt.Y("company:N", sort="-x", title=None,
                        axis=alt.Axis(labelFontSize=11,labelLimit=130)),
                x=alt.X("visit_count:Q", title="Ziyaret",
                        axis=alt.Axis(labelFontSize=10,tickMinStep=1)),
                opacity=alt.condition(alt.datum.visit_count > 0,
                                      alt.value(0.88), alt.value(0.4)),
                tooltip=[alt.Tooltip("company:N",title="Firma"),
                         alt.Tooltip("visit_count:Q",title="Ziyaret"),
                         alt.Tooltip("total_hours:Q",title="Saat",format=".1f")]
            ).properties(height=CHART_H, padding={"left":4,"right":8,"top":8,"bottom":4})
            st.altair_chart(ch(ch_co), use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:60px;color:#8AAAC8'>📭 Veri yok</div>",
                        unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Grafik Satırı 2: Teknisyen + Son Ziyaretler ──
    ga, gb = st.columns([3, 4], gap="medium")

    with ga:
        st.markdown('<div class="section-title">👤 Teknisyen Dağılımı</div>', unsafe_allow_html=True)
        tech = cached_tech_stats()
        if tech:
            df_tech = pd.DataFrame(tech)
            base_arc = alt.Chart(df_tech)
            pie = base_arc.mark_arc(
                innerRadius=50, outerRadius=95,
                padAngle=0.015, cornerRadius=4
            ).encode(
                theta=alt.Theta("visit_count:Q", stack=True),
                color=alt.Color("technician:N",
                    scale=alt.Scale(range=["#1565C0","#1E88E5","#42A5F5","#90CAF9",
                                           "#0D47A1","#1976D2","#64B5F6","#BBDEFB"]),
                    legend=alt.Legend(orient="bottom",labelFontSize=10,
                                      columns=2,symbolSize=80)),
                tooltip=[alt.Tooltip("technician:N",title="Teknisyen"),
                         alt.Tooltip("visit_count:Q",title="Ziyaret"),
                         alt.Tooltip("total_hours:Q",title="Saat",format=".1f")]
            )
            # Merkez metin
            center = base_arc.mark_text(
                fontSize=22, fontWeight=700, color="#60B4FF"
            ).encode(
                text=alt.value(str(sum(r["visit_count"] for r in tech)))
            )
            ch_tech = alt.layer(pie, center).properties(
                height=220, padding={"left":4,"right":4,"top":4,"bottom":4})
            st.altair_chart(ch(ch_tech), use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:40px;color:#8AAAC8'>📭 Veri yok</div>",
                        unsafe_allow_html=True)

    with gb:
        st.markdown('<div class="section-title">📋 Son Ziyaretler</div>', unsafe_allow_html=True)
        recent = cached_recent_visits(8)
        if recent:
            df_r = rpt.build_dataframe(recent)
            show = [c for c in ["Tarih","Firma","Konu","Sure","Durum"] if c in df_r.columns]
            st.dataframe(df_r[show], use_container_width=True, hide_index=True, height=235)
        else:
            st.markdown("<div style='text-align:center;padding:40px;color:#8AAAC8'>"
                        "📭 Henüz kayıt yok. Yeni Kayıt sekmesinden başlayın!</div>",
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEKME 2 — YENİ KAYIT
# ─────────────────────────────────────────────

def tab_new_visit():
    st.markdown('<div class="section-title" style="font-size:16px">➕ Yeni Saha Ziyareti Ekle</div>',
                unsafe_allow_html=True)
    companies = cached_companies()

    with st.form("new_visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            visit_date  = st.date_input("📅 Ziyaret Tarihi *", value=date.today(),
                                        min_value=date(2020,1,1), max_value=date(2030,12,31))
            company_sel = ""
            if companies:
                st.caption("💡 Kayıtlı firmadan seç veya aşağıya yeni firma yaz")
                company_sel = st.selectbox("Kayıtlı Firmalar", [""]+companies, index=0)
            company_inp = st.text_input("🏢 Firma Adı *",
                                        value=company_sel if company_sel else "",
                                        placeholder="Örn: Microsoft Türkiye, Vodafone...")
            company    = company_inp.strip() or company_sel.strip()
            technician = st.text_input("👤 Teknisyen Adı", placeholder="Örn: Ahmet Yılmaz")

        with col2:
            contact = st.text_input("📞 İletişim Kişisi", placeholder="Örn: Mehmet Bey — IT Müdürü")
            subject = st.text_input("📌 Ziyaret Konusu", placeholder="Örn: Sunucu Bakımı, AD Kurulumu...")
            da, db_ = st.columns(2)
            with da: duration = st.number_input("⏱️ Süre (Saat)", min_value=0.0, max_value=24.0, value=1.0, step=0.5)
            with db_: status  = st.selectbox("✅ Durum", STATUS_OPTIONS, index=0)

        work_notes = st.text_area("🔧 Yapılan İşlem Notları *", height=145,
            placeholder="— Windows Update uygulandı\n— AD'de kullanıcı oluşturuldu\n— Switch konfigürasyonu kontrol edildi")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾  Kaydet", use_container_width=True, type="primary")

    if submitted:
        if not company:       st.error("❌ Firma adı zorunludur!")
        elif not work_notes.strip(): st.error("❌ İşlem notları zorunludur!")
        else:
            nid = db.add_visit(visit_date=visit_date.strftime("%Y-%m-%d"), company=company,
                               contact=contact, subject=subject, work_notes=work_notes,
                               duration=duration, technician=technician, status=status)
            invalidate_caches()
            st.success(f"✅ Ziyaret kaydedildi! (#{nid})")
            st.balloons()


# ─────────────────────────────────────────────
# SEKME 3 — RAPORLAR
# ─────────────────────────────────────────────

def tab_reports():
    st.markdown('<div class="section-title" style="font-size:16px">📊 Rapor Merkezi</div>',
                unsafe_allow_html=True)
    ct, _ = st.columns([2,4])
    with ct: rtype = st.radio("Tür", ["📋 Genel Rapor","📅 Aylık Rapor"], horizontal=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    with st.expander("🔍 Filtreler", expanded=True):
        f1,f2,f3 = st.columns(3)
        with f1: fco = st.text_input("🏢 Firma Filtrele", placeholder="Firma adı ile ara...")
        if "Aylık" in rtype:
            with f2:
                ms = st.selectbox("📅 Ay", [f"{n} — {MONTHS_TR[n]}" for n in range(1,13)],
                                  index=date.today().month-1)
                sm = int(ms.split(" — ")[0])
            with f3:
                cy = date.today().year
                sy = st.selectbox("📆 Yıl", list(range(cy-3,cy+2)), index=3)
        else:
            with f2: df  = st.date_input("📅 Başlangıç", value=date(date.today().year,1,1))
            with f3: dt  = st.date_input("📅 Bitiş",     value=date.today())

    if "Aylık" in rtype:
        visits = db.get_visits(company_filter=fco, month=sm, year=sy)
        title  = f"Aylık Ziyaret Raporu — {MONTHS_TR[sm]} {sy}"
    else:
        visits = db.get_visits(company_filter=fco,
                               date_from=df.strftime("%Y-%m-%d"),
                               date_to=dt.strftime("%Y-%m-%d"))
        title  = f"Genel Ziyaret Raporu — {df.strftime('%d.%m.%Y')} / {dt.strftime('%d.%m.%Y')}"

    if not visits:
        st.info("📭 Kriterlere uygun kayıt bulunamadı.")
        return

    dfr   = rpt.build_dataframe(visits)
    thr   = sum(v.get("duration",0) or 0 for v in visits)
    s1,s2,s3 = st.columns(3)
    s1.metric("📋 Kayıt", len(visits))
    s2.metric("⏱️ Toplam", f"{thr:.1f} saat")
    s3.metric("🏭 Firma", len(set(v["company"] for v in visits)))

    st.markdown(f"<div style='font-size:14px;font-weight:600;color:#90CAF9;margin:14px 0 8px'>📄 {title}</div>",
                unsafe_allow_html=True)
    st.dataframe(dfr, use_container_width=True, hide_index=True, height=min(400, 60+len(dfr)*38))

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    d1,d2,_ = st.columns([1,1,4])
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    with d1:
        st.download_button("📥 Excel (.xlsx)",
            data=rpt.export_to_excel(dfr, title=title[:30]),
            file_name=f"ziyaret_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with d2:
        st.download_button("📄 PDF (.pdf)",
            data=rpt.export_to_pdf(dfr, title=title),
            file_name=f"ziyaret_{ts}.pdf",
            mime="application/pdf", use_container_width=True)


# ─────────────────────────────────────────────
# SEKME 4 — TÜM KAYITLAR
# ─────────────────────────────────────────────

def tab_all_records():
    st.markdown('<div class="section-title" style="font-size:16px">🗂️ Tüm Ziyaret Kayıtları</div>',
                unsafe_allow_html=True)
    cs1,cs2,cs3 = st.columns([2,1,1], gap="small")
    with cs1: sch = st.text_input("🔍 Firma Ara", placeholder="Firma adına göre ara...", key="ar_s")
    with cs2: df_f = st.date_input("📅 Başlangıç", value=date(date.today().year,1,1), key="ar_f")
    with cs3: df_t = st.date_input("📅 Bitiş",     value=date.today(), key="ar_t")

    visits = db.get_visits(company_filter=sch,
                           date_from=df_f.strftime("%Y-%m-%d"),
                           date_to=df_t.strftime("%Y-%m-%d"))
    if not visits:
        st.info("📭 Kriterlere uygun kayıt bulunamadı.")
        return

    st.caption(f"Toplam **{len(visits)}** kayıt")

    for v in visits:
        vid = v["id"]
        lbl = f"#{vid:03d} · 📅 {fmt_date(v['visit_date'])} · 🏢 {v['company']} · {(v.get('subject') or '—')[:40]}"
        with st.expander(lbl):
            vc, ec = st.columns([3,2], gap="medium")
            with vc:
                for k,val in [("Tarih",fmt_date(v["visit_date"])),("Firma",v["company"]),
                              ("İletişim",v.get("contact") or "—"),("Konu",v.get("subject") or "—"),
                              ("Teknisyen",v.get("technician") or "—"),
                              ("Süre",f"{v.get('duration',0):.1f} saat"),("Durum",v.get("status") or "—")]:
                    st.markdown(f"<span style='color:rgba(160,200,240,.65);font-size:12.5px'>{k}:</span> "
                                f"<span style='font-weight:500'>{val}</span>", unsafe_allow_html=True)
                st.markdown("<br>**🔧 Yapılan İşlemler:**")
                st.markdown(f"<div style='background:rgba(255,255,255,0.04);border-radius:10px;"
                            f"padding:10px 14px;font-size:13px;color:#B0C8E0;white-space:pre-wrap'>"
                            f"{v.get('work_notes','—')}</div>", unsafe_allow_html=True)
            with ec:
                st.markdown("**✏️ Düzenle**")
                with st.form(f"ef_{vid}"):
                    ed  = st.date_input("Tarih",     value=datetime.strptime(v["visit_date"],"%Y-%m-%d").date(), key=f"ed_{vid}")
                    ec2 = st.text_input("Firma",     value=v["company"],           key=f"eco_{vid}")
                    ect = st.text_input("İletişim",  value=v.get("contact",""),    key=f"ect_{vid}")
                    es  = st.text_input("Konu",      value=v.get("subject",""),    key=f"es_{vid}")
                    et  = st.text_input("Teknisyen", value=v.get("technician",""), key=f"et_{vid}")
                    edu = st.number_input("Süre",    value=float(v.get("duration",0)), step=0.5, key=f"edu_{vid}")
                    safe_status = v.get("status","Tamamlandi") if v.get("status") in STATUS_OPTIONS else "Tamamlandi"
                    est = st.selectbox("Durum", STATUS_OPTIONS,
                                       index=STATUS_OPTIONS.index(safe_status), key=f"est_{vid}")
                    en  = st.text_area("Notlar", value=v.get("work_notes",""), height=80, key=f"en_{vid}")
                    sb,db_b = st.columns(2)
                    with sb:  save = st.form_submit_button("💾 Güncelle", type="primary", use_container_width=True)
                    with db_b: dlt = st.form_submit_button("🗑️ Sil", use_container_width=True)
                if save:
                    db.update_visit(vid,ed.strftime("%Y-%m-%d"),ec2,ect,es,en,edu,et,est)
                    invalidate_caches(); st.success("✅ Güncellendi!"); st.rerun()
                if dlt:
                    db.delete_visit(vid); invalidate_caches()
                    st.warning(f"🗑️ #{vid} silindi."); st.rerun()


# ─────────────────────────────────────────────
# SEKME 5 — HATIRLATICLAR
# ─────────────────────────────────────────────

def tab_reminders():
    st.markdown('<div class="section-title" style="font-size:16px">🔔 Hatırlatıcı Sistemi</div>',
                unsafe_allow_html=True)

    due = cached_due_reminders()
    if due:
        st.markdown(
            f"<div style='background:rgba(183,28,28,.14);border:1px solid rgba(239,83,80,.4);"
            f"border-radius:12px;padding:12px 18px;margin-bottom:16px;font-size:13.5px'>"
            f"⚠️ <b style='color:#EF9A9A'>Bugün veya öncesinde {len(due)} bekleyen hatırlatıcı!</b></div>",
            unsafe_allow_html=True)
        for r in due:
            pc = PRIORITY_COLORS.get(r["priority"],"#42A5F5")
            dl = (date.today() - datetime.strptime(r["remind_date"],"%Y-%m-%d").date()).days
            rc,rd,rdl = st.columns([5,1,1])
            with rc:
                lt = f"<span style='color:#EF5350'>{dl}g gecikti</span>" if dl>0 else "<span style='color:#FF9800'>Bugün</span>"
                st.markdown(
                    f"<div class='card {pri_class(r['priority'])}' style='margin:0 0 4px'>"
                    f"<b>{r['company']}</b> — {r['title']} &nbsp;{lt}<br>"
                    f"<small style='color:rgba(160,200,240,.6)'>{fmt_date(r['remind_date'])} · {r['priority']}"
                    f"{' · ' + r['notes'][:40] if r['notes'] else ''}</small></div>",
                    unsafe_allow_html=True)
            with rd:
                if st.button("✅",key=f"rd_{r['id']}"):
                    db.complete_reminder(r["id"]); invalidate_caches(); st.rerun()
            with rdl:
                if st.button("🗑️",key=f"rdd_{r['id']}"):
                    db.delete_reminder(r["id"]); invalidate_caches(); st.rerun()
        st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:18px 0'>", unsafe_allow_html=True)

    cf, cl = st.columns([2,3], gap="large")

    with cf:
        st.markdown('<div class="section-title">➕ Yeni Hatırlatıcı</div>', unsafe_allow_html=True)
        cos = cached_companies()
        with st.form("add_rem", clear_on_submit=True):
            r_date = st.date_input("📅 Tarih *", value=date.today()+timedelta(days=30), min_value=date.today())
            r_co   = st.selectbox("🏢 Firma", [""]+cos) if cos else st.text_input("🏢 Firma")
            r_co_m = st.text_input("veya yeni firma:", placeholder="Yeni firma adı...")
            r_co_f = r_co_m.strip() or (r_co if isinstance(r_co,str) else "")
            r_ttl  = st.text_input("📌 Başlık *", placeholder="3 Aylık Periyodik Bakım")
            r_nts  = st.text_area("📝 Notlar", height=68)
            r_pri  = st.selectbox("⚡ Öncelik", PRIORITY_OPTIONS)
            if st.form_submit_button("🔔 Ekle", type="primary", use_container_width=True):
                if not r_co_f: st.error("❌ Firma gerekli!")
                elif not r_ttl.strip(): st.error("❌ Başlık gerekli!")
                else:
                    db.add_reminder(r_date.strftime("%Y-%m-%d"),r_co_f,r_ttl,r_nts,r_pri)
                    invalidate_caches(); st.success("✅ Eklendi!"); st.rerun()

    with cl:
        st.markdown('<div class="section-title">📋 Bekleyen Hatırlatıcılar</div>', unsafe_allow_html=True)
        show_d = st.checkbox("Tamamlananları da göster", value=False)
        rems   = db.get_reminders(include_done=show_d)
        if not rems:
            st.info("📭 Bekleyen hatırlatıcı yok.")
        for r in rems:
            pc = PRIORITY_COLORS.get(r["priority"],"#42A5F5")
            rd_dt = datetime.strptime(r["remind_date"],"%Y-%m-%d").date()
            dl    = (rd_dt - date.today()).days
            dn    = r["is_done"]
            if dn:        badge = "<span style='color:#4CAF50;font-size:11px'>✅ Tamamlandı</span>"
            elif dl < 0:  badge = f"<span style='color:#EF5350;font-size:11px'>⚠️ {abs(dl)}g gecikti</span>"
            elif dl == 0: badge = "<span style='color:#FF9800;font-size:11px'>⏰ Bugün!</span>"
            elif dl <= 7: badge = f"<span style='color:#FF9800;font-size:11px'>⚡ {dl}g kaldı</span>"
            else:         badge = f"<span style='color:rgba(160,200,240,.6);font-size:11px'>📅 {dl}g kaldı</span>"

            rc2,ra = st.columns([7,1])
            with rc2:
                op = ".45" if dn else "1"
                st.markdown(
                    f"<div class='card {pri_class(r['priority'])}' style='opacity:{op};margin-bottom:4px'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>"
                    f"<b style='font-size:13.5px'>{r['company']}</b>{badge}</div>"
                    f"<div style='color:#B0C8E0;font-size:13px;margin-top:3px'>{r['title']}</div>"
                    f"<div style='color:rgba(160,200,240,.55);font-size:11.5px;margin-top:5px'>"
                    f"📅 {fmt_date(r['remind_date'])} · {r['priority']}"
                    f"{' · ' + r['notes'][:45] if r['notes'] else ''}</div></div>",
                    unsafe_allow_html=True)
            with ra:
                if not dn and st.button("✅",key=f"cr_{r['id']}"):
                    db.complete_reminder(r["id"]); invalidate_caches(); st.rerun()
                if st.button("🗑️",key=f"dr_{r['id']}"):
                    db.delete_reminder(r["id"]); invalidate_caches(); st.rerun()


# ─────────────────────────────────────────────
# SEKME 6 — TAKVİM
# ─────────────────────────────────────────────

def tab_calendar():
    st.markdown('<div class="section-title" style="font-size:16px">🗓️ Ziyaret Takvimi</div>',
                unsafe_allow_html=True)

    cy, cm_c = st.columns([1,1], gap="small")
    with cy:
        sy = st.selectbox("Yıl", list(range(date.today().year-3, date.today().year+2)),
                          index=3, key="caly")
    with cm_c:
        sm_s = st.selectbox("Ay", [f"{n} — {MONTHS_TR[n]}" for n in range(1,13)],
                            index=date.today().month-1, key="calm")
        sm   = int(sm_s.split(" — ")[0])

    cal_data  = db.get_calendar_data(sm, sy)
    month_cal = calendar.monthcalendar(sy, sm)
    total_m   = sum(cal_data.values())

    st.markdown(
        f"<div style='text-align:center;font-size:18px;font-weight:700;color:#60B4FF;"
        f"margin:8px 0 14px;letter-spacing:-.01em'>"
        f"{MONTHS_TR[sm]} {sy}"
        f"<span style='font-size:13px;color:rgba(160,200,240,.6);font-weight:400;margin-left:10px'>"
        f"({total_m} ziyaret)</span></div>",
        unsafe_allow_html=True)

    hc = st.columns(7)
    for i,dn in enumerate(DAYS_TR):
        clr = "#EF5350" if i==6 else ("#90CAF9" if i==5 else "rgba(160,200,240,.75)")
        hc[i].markdown(f"<div style='text-align:center;font-weight:700;color:{clr};"
                       f"font-size:12.5px;padding:5px 0;"
                       f"border-bottom:1px solid rgba(255,255,255,.07)'>{dn}</div>",
                       unsafe_allow_html=True)

    if "cal_sel" not in st.session_state: st.session_state.cal_sel = None
    today_str = date.today().strftime("%Y-%m-%d")

    for week in month_cal:
        wc = st.columns(7)
        for ci,day in enumerate(week):
            if day == 0:
                wc[ci].markdown("<div style='min-height:58px'></div>", unsafe_allow_html=True)
                continue
            ds   = f"{sy}-{sm:02d}-{day:02d}"
            cnt  = cal_data.get(ds,0)
            sel  = st.session_state.cal_sel == ds
            tod  = ds == today_str
            wend = ci >= 5

            if sel:     bg,bdr,tc = "rgba(30,136,229,.35)","#1E88E5","#90CAF9"
            elif tod:   bg,bdr,tc = "rgba(30,136,229,.18)","rgba(30,136,229,.5)","#90CAF9"
            elif cnt:
                iv = min(cnt*18, 70)
                bg,bdr,tc = f"rgba(76,175,80,{iv/100:.2f})","rgba(76,175,80,.5)","#A5D6A7"
            elif wend:  bg,bdr,tc = "rgba(255,255,255,.02)","rgba(255,255,255,.04)","#EF5350"
            else:       bg,bdr,tc = "rgba(255,255,255,.035)","rgba(255,255,255,.07)","#C8DFF5"

            dot  = f"<div style='width:6px;height:6px;background:#4CAF50;border-radius:50%;margin:2px auto 0'></div>" if cnt else ""
            cntt = f"<div style='font-size:10px;color:#A5D6A7;margin-top:1px'>{cnt}</div>" if cnt else ""
            todm = f"<div style='font-size:9px;color:#90CAF9;margin-top:1px;letter-spacing:.02em'>bugün</div>" if tod else ""
            wc[ci].markdown(
                f"<div style='background:{bg};border:1px solid {bdr};border-radius:10px;"
                f"padding:7px 3px;text-align:center;min-height:58px;cursor:pointer;"
                f"transition:border-color .18s,background .18s'>"
                f"<div style='font-weight:600;color:{tc};font-size:14px'>{day}</div>"
                f"{todm}{dot}{cntt}</div>",
                unsafe_allow_html=True)
            if wc[ci].button(" ",key=f"cb_{ds}",help=f"{fmt_date(ds)} — {cnt} ziyaret"):
                st.session_state.cal_sel = ds; st.rerun()

    if st.session_state.cal_sel:
        sel_d = st.session_state.cal_sel
        dv    = db.get_visits_by_date(sel_d)
        st.markdown(f"<hr style='border-color:rgba(255,255,255,.06);margin:18px 0'>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>📋 {fmt_date(sel_d)} — {len(dv)} Ziyaret</div>",
                    unsafe_allow_html=True)
        if dv:
            for v in dv:
                with st.expander(f"🏢 {v['company']} — {v.get('subject','—')}", expanded=True):
                    vca, vnb = st.columns(2)
                    with vca:
                        for lbl,val in [("Firma",v["company"]),("İletişim",v.get("contact","—")),
                                        ("Teknisyen",v.get("technician","—")),
                                        ("Süre",f"{v.get('duration',0):.1f} saat"),("Durum",v.get("status","—"))]:
                            st.markdown(f"<span style='color:rgba(160,200,240,.65);font-size:12.5px'>{lbl}:</span> "
                                        f"<b>{val}</b>", unsafe_allow_html=True)
                    with vnb:
                        st.markdown("**🔧 Yapılan İşlemler:**")
                        st.markdown(f"<div style='background:rgba(255,255,255,.04);border-radius:10px;"
                                    f"padding:10px 14px;font-size:13px;color:#B0C8E0;white-space:pre-wrap'>"
                                    f"{v.get('work_notes','—')}</div>", unsafe_allow_html=True)
        else:
            st.info(f"📭 {fmt_date(sel_d)} tarihinde ziyaret kaydı yok.")


# ─────────────────────────────────────────────
# SEKME 7 — YAPILACAKLAR (TO-DO)
# ─────────────────────────────────────────────

def tab_todos():
    st.markdown('<div class="section-title" style="font-size:16px">📋 Yapılacaklar Listesi</div>',
                unsafe_allow_html=True)

    tds = cached_todo_stats()
    m1,m2,m3 = st.columns(3)
    m1.metric("📌 Bekleyen",    tds["pending"])
    m2.metric("⚠️ Gecikmiş",   tds["overdue"],  delta_color="inverse")
    m3.metric("✅ Tamamlanan",  tds["done"])

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    cf, cl = st.columns([2,3], gap="large")

    with cf:
        st.markdown('<div class="section-title">➕ Yeni Görev</div>', unsafe_allow_html=True)
        cos = cached_companies()
        with st.form("add_todo_form", clear_on_submit=True):
            t_ttl  = st.text_input("📌 Görev Başlığı *", placeholder="Firewall güncellemesi...")
            t_co   = st.selectbox("🏢 Firma", [""]+cos) if cos else st.text_input("🏢 Firma")
            t_co_m = st.text_input("veya yeni firma:")
            t_co_f = t_co_m.strip() or (t_co if isinstance(t_co,str) else "")
            t_desc = st.text_area("📝 Açıklama", height=72, placeholder="Detaylar...")
            t_due  = st.date_input("📅 Son Tarih", value=date.today()+timedelta(days=7))
            t_pri  = st.selectbox("⚡ Öncelik", PRIORITY_OPTIONS)
            if st.form_submit_button("➕ Görev Ekle", type="primary", use_container_width=True):
                if not t_ttl.strip(): st.error("❌ Başlık gerekli!")
                else:
                    db.add_todo(t_ttl, t_co_f, t_desc, t_due.strftime("%Y-%m-%d"), t_pri)
                    invalidate_caches(); st.success("✅ Görev eklendi!"); st.rerun()

    with cl:
        st.markdown('<div class="section-title">📋 Görev Listesi</div>', unsafe_allow_html=True)
        show_d2 = st.checkbox("Tamamlananları da göster", value=False, key="td_done")
        todos   = db.get_todos(include_done=show_d2)
        if not todos:
            st.info("📭 Görev yok — soldan ekleyebilirsiniz.")
        for t in todos:
            pc    = PRIORITY_COLORS.get(t["priority"],"#42A5F5")
            is_dn = t["is_done"]
            due_d = t.get("due_date")
            if due_d:
                dl2 = (datetime.strptime(due_d,"%Y-%m-%d").date()-date.today()).days
                if is_dn:     db2 = f"<span style='color:#4CAF50;font-size:11px'>✅ Bitti</span>"
                elif dl2<0:   db2 = f"<span style='color:#EF5350;font-size:11px'>🔴 {abs(dl2)}g gecikti</span>"
                elif dl2==0:  db2 = "<span style='color:#FF9800;font-size:11px'>⏰ Bugün!</span>"
                elif dl2<=3:  db2 = f"<span style='color:#FF9800;font-size:11px'>⚡ {dl2}g kaldı</span>"
                else:         db2 = f"<span style='color:rgba(160,200,240,.6);font-size:11px'>📅 {dl2}g kaldı</span>"
            else: db2 = "<span style='color:rgba(160,200,240,.5);font-size:11px'>Tarih yok</span>"

            tc2,ta1,ta2 = st.columns([5,1,1])
            with tc2:
                op2 = ".42" if is_dn else "1"
                cotxt = f" · <span style='color:rgba(160,200,240,.6)'>{t['company']}</span>" if t.get("company") else ""
                st.markdown(
                    f"<div class='card {pri_class(t['priority'])}' style='opacity:{op2};margin-bottom:4px'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>"
                    f"<b style='font-size:13.5px;text-decoration:{'line-through' if is_dn else 'none'}'>"
                    f"{t['title']}</b>{db2}</div>"
                    f"<div style='color:rgba(160,200,240,.65);font-size:12px;margin-top:3px'>"
                    f"{t['priority']}{cotxt}"
                    f"{' · ' + t['description'][:50] if t.get('description') else ''}</div></div>",
                    unsafe_allow_html=True)
            with ta1:
                if not is_dn:
                    if st.button("✅",key=f"tdc_{t['id']}"):
                        db.complete_todo(t["id"]); invalidate_caches(); st.rerun()
                else:
                    if st.button("↩️",key=f"tdr_{t['id']}"):
                        db.reopen_todo(t["id"]); invalidate_caches(); st.rerun()
            with ta2:
                if st.button("🗑️",key=f"tdd_{t['id']}"):
                    db.delete_todo(t["id"]); invalidate_caches(); st.rerun()


# ─────────────────────────────────────────────
# SEKME 8 — GLOBAL ARAMA
# ─────────────────────────────────────────────

def tab_global_search():
    st.markdown('<div class="section-title" style="font-size:16px">🔎 Global Arama</div>',
                unsafe_allow_html=True)
    st.caption("Firma adı, ziyaret konusu, teknisyen ve işlem notlarında aynı anda arama yapar.")

    query = st.text_input("",
        placeholder="🔍  Kelime veya ifade girin... (Örn: Active Directory, backup, firewall)",
        key="gq", label_visibility="collapsed")

    if not query or len(query.strip()) < 2:
        st.markdown(
            "<div style='text-align:center;padding:56px 20px;color:rgba(160,200,240,.55)'>"
            "<div style='font-size:52px;margin-bottom:14px'>🔍</div>"
            "<div style='font-size:16px;font-weight:600;color:rgba(190,220,250,.8)'>Aramak istediğiniz kelimeyi yazın</div>"
            "<div style='font-size:13px;margin-top:7px;max-width:340px;margin-left:auto;margin-right:auto'>"
            "Tüm ziyaret notları, firma adları, konular ve teknisyen bilgilerinde arama yapılır"
            "</div></div>", unsafe_allow_html=True)
        return

    with st.spinner("Aranıyor…"):
        results = db.global_search(query.strip())

    if not results:
        st.markdown(
            f"<div style='text-align:center;padding:40px;color:rgba(160,200,240,.55)'>"
            f"<div style='font-size:40px;margin-bottom:10px'>😕</div>"
            f"<div style='font-size:15px;color:rgba(200,225,255,.75)'>"
            f"<b>\"{query}\"</b> için sonuç bulunamadı</div>"
            f"<div style='font-size:13px;margin-top:6px'>Farklı bir kelime deneyin</div></div>",
            unsafe_allow_html=True)
        return

    st.markdown(
        f"<div style='color:#60B4FF;font-weight:600;font-size:14px;margin-bottom:14px'>"
        f"🎯 <b>{len(results)}</b> sonuç — \"<em>{query}</em>\"</div>",
        unsafe_allow_html=True)

    q_low = query.lower()
    for r in results:
        mf = []
        if q_low in (r.get("company") or "").lower():    mf.append("Firma")
        if q_low in (r.get("subject") or "").lower():    mf.append("Konu")
        if q_low in (r.get("work_notes") or "").lower(): mf.append("Notlar")
        if q_low in (r.get("contact") or "").lower():    mf.append("İletişim")
        if q_low in (r.get("technician") or "").lower(): mf.append("Teknisyen")
        badges_html = " ".join(
            f"<span style='background:rgba(33,150,243,.18);color:#90CAF9;"
            f"border:1px solid rgba(33,150,243,.25);border-radius:4px;padding:1px 7px;font-size:11px'>{f}</span>"
            for f in mf)

        notes = r.get("work_notes") or ""
        snippet = ""
        if q_low in notes.lower():
            idx   = notes.lower().find(q_low)
            start = max(0, idx-55)
            end   = min(len(notes), idx+len(query)+55)
            snippet = ("…" if start else "") + notes[start:end] + ("…" if end<len(notes) else "")
            snippet = highlight(snippet, query)

        ch_hl  = highlight(r.get("company",""), query)
        sub_hl = highlight(r.get("subject","") or "—", query)

        st.markdown(
            f"<div class='result-card'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>"
            f"<span style='font-size:15px;font-weight:700'>{ch_hl}</span>"
            f"<span style='color:rgba(160,200,240,.5);font-size:12px;white-space:nowrap'>"
            f"#{r['id']:03d} · 📅 {fmt_date(r['visit_date'])}</span></div>"
            f"<div style='margin-top:5px;color:#B0C8E0;font-size:13px'>📌 {sub_hl}"
            f"{'&nbsp;·&nbsp;👤 '+r['technician'] if r.get('technician') else ''}</div>"
            f"<div style='margin-top:7px'>{badges_html}</div>"
            + (f"<div style='margin-top:8px;background:rgba(255,255,255,.035);border-radius:8px;"
               f"padding:8px 12px;font-size:12.5px;color:rgba(160,200,240,.75);font-style:italic'>{snippet}</div>"
               if snippet else "")
            + "</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ANA UYGULAMA
# ─────────────────────────────────────────────

def main():
    app_header()

    t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs([
        "🏠 Dashboard",
        "➕ Yeni Kayıt",
        "📊 Raporlar",
        "🗂️ Tüm Kayıtlar",
        "🔔 Hatırlatıcılar",
        "🗓️ Takvim",
        "📋 Yapılacaklar",
        "🔎 Arama",
    ])

    with t1: tab_dashboard()
    with t2: tab_new_visit()
    with t3: tab_reports()
    with t4: tab_all_records()
    with t5: tab_reminders()
    with t6: tab_calendar()
    with t7: tab_todos()
    with t8: tab_global_search()


if __name__ == "__main__":
    main()
