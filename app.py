"""
app.py  —  Kisisel IT Saha Takip ve Gunlugu
Streamlit tabanli kisisel IT faaliyet ve raporlama gunlugu.
Calistirmak: streamlit run app.py
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
# Sayfa konfigurasyonu
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Kisisel IT Saha Takip",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Performans: @st.cache_data (TTL = saniye)
# ─────────────────────────────────────────────
@st.cache_data(ttl=20)
def cached_summary_stats():      return db.get_summary_stats()

@st.cache_data(ttl=45)
def cached_companies():          return db.get_all_companies()

@st.cache_data(ttl=20)
def cached_monthly_trend(year):  return db.get_monthly_trend(year)

@st.cache_data(ttl=30)
def cached_co_dist(top_n=8):     return db.get_company_distribution(top_n)

@st.cache_data(ttl=30)
def cached_category_stats():     return db.get_technician_stats()

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
               cached_co_dist, cached_category_stats, cached_due_reminders,
               cached_overdue_todos, cached_todo_stats, cached_recent_visits]:
        fn.clear()

# ─────────────────────────────────────────────
# CSS  —  Premium Kisisel Koyu Tema + CSS Animasyonlari
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Font & Smooth Scrolling ────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif !important; }

/* ── Animasyon Keyframe Tanimlari ────────────── */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes glowPulse {
    0% { border-color: rgba(33,150,243,0.15); box-shadow: 0 4px 15px rgba(33,150,243,0.05); }
    50% { border-color: rgba(33,150,243,0.45); box-shadow: 0 8px 25px rgba(33,150,243,0.18); }
    100% { border-color: rgba(33,150,243,0.15); box-shadow: 0 4px 15px rgba(33,150,243,0.05); }
}

@keyframes headerGlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Tab Yapilandirmalarinda FadeIn Animasyonu */
div[data-testid="stVerticalBlock"] > div {
    animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* ── Arkaplan & Scrollbar ───────────────────── */
.stApp {
    background: #090F16;
    background-image:
        radial-gradient(ellipse at 15% 15%, rgba(21,101,192,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 85% 85%, rgba(76,175,80,0.06) 0%, transparent 55%);
    min-height: 100vh;
}
.stApp, .stApp p, .stApp li { color: #D4E3F2; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }

/* ── Sekmeler ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 6px;
    gap: 3px;
    flex-wrap: wrap;
    backdrop-filter: blur(8px);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 11px;
    padding: 8px 16px;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: rgba(180,205,230,0.6) !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.25s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #FFFFFF !important;
    background: rgba(255,255,255,0.06) !important;
    transform: translateY(-1px);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 18px rgba(30,136,229,0.35);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"]    { display: none; }

/* ── Metrik Kartlar ──────────────────────────── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 16px 18px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 12px 30px rgba(33,150,243,0.18);
    border-color: rgba(33,150,243,0.4);
    background: rgba(255,255,255,0.05);
}
[data-testid="stMetricValue"] {
    color: #58B0FF !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -.02em;
}
[data-testid="stMetricLabel"] {
    color: rgba(180,210,240,0.65) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: .08em;
}

/* ── Butonlar ────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1565C0, #1E88E5) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 12px !important; padding: 10px 22px !important;
    font-weight: 600 !important; font-size: 13.5px !important;
    font-family: inherit !important;
    transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 15px rgba(21,101,192,0.3) !important;
    width: 100%;
}
.stButton > button:hover {
    opacity: .95 !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(30,136,229,0.45) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    box-shadow: none !important; color: #B0CEF0 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #FFFFFF !important;
}

/* ── Form Elemanlari ─────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #DCE8F5 !important;
    font-size: 14px !important;
    font-family: inherit !important;
    transition: all 0.25s ease !important;
    padding: 10px 14px !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #DCE8F5 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: rgba(33,150,243,0.7) !important;
    box-shadow: 0 0 0 3px rgba(33,150,243,0.18) !important;
    background: rgba(255,255,255,0.06) !important;
}

/* ── Uyari Mesajlari (Alerts) ────────────────── */
.stSuccess > div {
    background: rgba(76,175,80,0.09) !important; border-left: 4px solid #4CAF50 !important;
    border-radius: 12px !important; border-top: none; border-right: none; border-bottom: none;
}
.stError > div {
    background: rgba(239,83,80,0.09) !important; border-left: 4px solid #EF5350 !important;
    border-radius: 12px !important; border-top: none; border-right: none; border-bottom: none;
}
.stWarning > div {
    background: rgba(255,152,0,0.08) !important; border-left: 4px solid #FF9800 !important;
    border-radius: 12px !important; border-top: none; border-right: none; border-bottom: none;
}

/* ── Kart Tasarimi (Hover Efektli) ───────────── */
.card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px; padding: 16px 20px;
    margin-bottom: 10px;
    transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.card:hover {
    background: rgba(255,255,255,0.045);
    border-color: rgba(33,150,243,0.25);
    transform: translateX(3px);
}

.pri-acil   { border-left: 4px solid #EF5350; }
.pri-onemli { border-left: 4px solid #FF9800; }
.pri-normal { border-left: 4px solid #42A5F5; }

/* ── Arama Sonuclari ─────────────────────────── */
.result-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px; padding: 14px 18px; margin-bottom: 8px;
    transition: all 0.2s ease;
}
.result-card:hover {
    background: rgba(33,150,243,0.04);
    border-color: rgba(33,150,243,0.3);
    transform: translateY(-1px);
}

/* ── Rapor Kopyalama Bolumu (Glow) ────────────── */
.glow-box {
    border: 1px solid rgba(33,150,243,0.15);
    background: rgba(13,27,46,0.3);
    border-radius: 16px;
    padding: 20px;
    animation: glowPulse 4s infinite ease-in-out;
}

/* ── Basliklar ───────────────────────────────── */
h1, h2, h3, h4 { color: #E5F1FF !important; }
h1 { font-size: 1.7rem !important; font-weight: 700 !important; letter-spacing: -.03em; }
h2 { font-size: 1.2rem !important; font-weight: 650 !important; }
h3 { font-size: 1.0rem !important; font-weight: 600 !important; }

.section-title {
    font-size: 14.5px; font-weight: 700; color: #8FCAFF;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding-bottom: 8px; margin: 0 0 16px 0;
    display: flex; align-items: center; gap: 8px;
}

/* ── Vega/Altair grafik arka plani ───────────── */
.vega-embed, .vega-embed canvas { background: transparent !important; }

/* ── Sistem Ogelerini Gizleme ────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Mobil ───────────────────────────────────── */
@media (max-width: 768px) {
    h1 { font-size: 1.15rem !important; }
    .stTabs [data-baseweb="tab"] { padding: 6px 10px !important; font-size: 10.5px !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stButton > button { padding: 11px !important; font-size: 13.5px !important; }
}

/* Hide native sidebar and collapse controls entirely */
[data-testid="stSidebar"],
[data-testid="stSidebar"][aria-expanded="true"],
[data-testid="stSidebar"][aria-expanded="false"],
div[data-testid="collapsedControl"],
button[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ── Custom Sidebar Navigasyon Paneli Tasarimi ── */
.nav-container {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 20px !important;
    padding: 16px !important;
    backdrop-filter: blur(10px) !important;
    margin-bottom: 20px !important;
}

/* Custom Navigasyon Butonlari */
.nav-container div[data-testid="stButton"] button {
    text-align: left !important;
    justify-content: flex-start !important;
    width: 100% !important;
    border-radius: 12px !important;
    padding: 9px 15px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    margin-bottom: 5px !important;
    transition: all 0.2s ease !important;
}

/* Aktif Sekme Butonu (Primary) */
.nav-container div[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(30,136,229,0.25) !important;
    color: #FFFFFF !important;
}

/* Aktif Olmayan Sekme Butonlari (Secondary) */
.nav-container div[data-testid="stButton"] button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    color: rgba(180,205,230,0.7) !important;
}
.nav-container div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(33,150,243,0.2) !important;
    color: #FFFFFF !important;
    transform: translateX(3px) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sabitler & Kisisel IT Kategorileri
# ─────────────────────────────────────────────
MONTHS_TR = {
    1:"Ocak",2:"Subat",3:"Mart",4:"Nisan",5:"Mayis",6:"Haziran",
    7:"Temmuz",8:"Agustos",9:"Eylul",10:"Ekim",11:"Kasim",12:"Aralik"
}
DAYS_TR          = ["Pzt","Sal","Car","Per","Cum","Cmt","Paz"]
STATUS_OPTIONS   = ["Tamamlandi", "Devam Ediyor", "Iptal", "Beklemede"]
PRIORITY_OPTIONS = ["Normal", "Onemli", "Acil"]
PRIORITY_COLORS  = {"Acil": "#EF5350", "Onemli": "#FF9800", "Normal": "#42A5F5"}
CHART_H          = 250

# Kisisel IT Kategorileri (Teknisyen sutununa yazilacak)
CATEGORIES = [
    "Sistem & Sunucu Yonetimi",
    "Ag & Altyapi Destegi",
    "Siber Guvenlik & Firewall",
    "Kullanici Destegi & Donanim",
    "Yedekleme & Veri Yonetimi",
    "Yazilim & Lisanslama",
    "Diger IT Isleri"
]

# ─────────────────────────────────────────────
# Yardimci Fonksiyonlar
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
    return {"Acil": "pri-acil", "Onemli": "pri-onemli"}.get(p, "pri-normal")

# ─── Altair Grafik Konfigurasyonu ─────────────

CHART_CFG = {
    "background": "transparent",
    "view":   {"stroke": "transparent", "strokeOpacity": 0},
    "axis": {
        "gridColor":   "rgba(255,255,255,0.05)",
        "gridOpacity": 1,
        "tickColor":   "rgba(255,255,255,0.12)",
        "domainColor": "rgba(255,255,255,0.08)",
        "labelColor":  "#8AAAC8",
        "titleColor":  "#A0BEDC",
        "labelFontSize": 10.5,
        "titleFontSize": 10.5,
        "titleFontWeight": 500,
    },
    "title": {"color": "#D0E8FF", "fontSize": 12.5, "fontWeight": 600, "anchor": "start"},
    "legend": {
        "labelColor": "#8AAAC8", "titleColor": "#A0BEDC",
        "labelFontSize": 10.5, "titleFontSize": 10.5,
    },
    "mark": {"tooltip": True},
}

def ch(chart): return chart.configure(**CHART_CFG)

# ─────────────────────────────────────────────
# App Header (Kisisel Gunluk Konsepti)
# ─────────────────────────────────────────────

def app_header():
    due  = cached_due_reminders()
    tds  = cached_todo_stats()
    badges = ""
    if due:
        badges += f"<span style='background:rgba(239,83,80,.85);border-radius:20px;padding:2px 8px;font-size:11px;font-weight:600;margin-left:8px'>⚠️ {len(due)} Hatirlatma</span>"
    if tds.get("overdue", 0):
        badges += f"<span style='background:rgba(255,152,0,.85);border-radius:20px;padding:2px 8px;font-size:11px;font-weight:600;margin-left:5px'>📋 {tds['overdue']} Gecikmis</span>"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(30,136,229,0.15) 0%,rgba(10,20,32,0.6) 100%);
        border:1px solid rgba(33,150,243,0.18);border-radius:20px;
        padding:16px 24px;margin-bottom:20px;
        backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
        display:flex;align-items:center;gap:14px;">
      <div style="font-size:38px;flex-shrink:0">💻</div>
      <div style="flex:1;min-width:0">
        <h1 style="margin:0;font-size:1.45rem;
            background:linear-gradient(90deg,#64B5F6 0%,#B39DDB 100%);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
          IT Ziyaret & Faaliyet Gunlugum{badges}
        </h1>
        <p style="margin:3px 0 0;color:rgba(160,200,240,.6);font-size:12px;letter-spacing:.02em">
          👤 Kisisel Calisma Kayitlari ve Raporlama Yoneticisi &nbsp;|&nbsp; 📅 {datetime.now().strftime('%d.%m.%Y')}
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEKME 1 — DASHBOARD
# ─────────────────────────────────────────────

def tab_dashboard():
    # Metrikler
    stats = cached_summary_stats()
    tds   = cached_todo_stats()
    c = st.columns(6)
    c[0].metric("🏢 Toplam Ziyaret",   stats["total_visits"])
    c[1].metric("⏱️ Toplam Mesai",      f"{stats['total_hours']:.1f} sa")
    c[2].metric("📅 Bu Ay Ziyaret",    stats["month_visits"])
    c[3].metric("🕐 Bu Ay Sure",       f"{stats['month_hours']:.1f} sa")
    c[4].metric("🏭 Aktif Firma",      stats["unique_companies"])
    c[5].metric("📋 Kisisel Gorev",    tds["pending"],
                delta=f"−{tds['overdue']} gecikmis" if tds["overdue"] else None,
                delta_color="inverse")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Grafik Satiri 1: Trend + Firmalar ──
    gl, gr = st.columns([5, 4], gap="medium")

    with gl:
        st.markdown('<div class="section-title">📈 Aylik Ziyaret Trendi</div>', unsafe_allow_html=True)
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
                "Ziyaret": [all_v[m] for m in range(1,13)],
                "Saat":    [all_h[m]  for m in range(1,13)],
            })

            x_enc = alt.X("Ay:O", sort=list(df_t["Ay"]),
                          axis=alt.Axis(labelAngle=0, labelFontSize=10.5, tickMinStep=1))

            bars = alt.Chart(df_t).mark_bar(
                cornerRadiusTopLeft=5, cornerRadiusTopRight=5,
                opacity=0.8,
                color=alt.Gradient(gradient="linear",
                    stops=[alt.GradientStop(color="#1565C0", offset=0),
                           alt.GradientStop(color="#42A5F5", offset=1)],
                    x1=0, x2=0, y1=1, y2=0)
            ).encode(
                x=x_enc,
                y=alt.Y("Ziyaret:Q", title="Ziyaret Sayisi",
                        axis=alt.Axis(labelFontSize=10, gridOpacity=0.3)),
                tooltip=[alt.Tooltip("Ay:O", title="Ay"),
                         alt.Tooltip("Ziyaret:Q", title="Ziyaret"),
                         alt.Tooltip("Saat:Q", title="Saat (sa)", format=".1f")]
            )

            line = alt.Chart(df_t).mark_line(
                color="#66BB6A", strokeWidth=2.2, interpolate="monotone"
            ).encode(
                x=x_enc,
                y=alt.Y("Saat:Q", title="Toplam Sure (sa)",
                        axis=alt.Axis(labelFontSize=10, gridOpacity=0)),
                tooltip=[alt.Tooltip("Ay:O", title="Ay"),
                         alt.Tooltip("Saat:Q", title="Saat (sa)", format=".1f")]
            )
            dots = alt.Chart(df_t).mark_point(
                color="#66BB6A", size=50, filled=True, opacity=0.9
            ).encode(x=x_enc, y=alt.Y("Saat:Q"))

            chart = (
                alt.layer(bars, line+dots)
                .resolve_scale(y="independent")
                .properties(height=CHART_H)
            )
            st.altair_chart(ch(chart), use_container_width=True)
        else:
            st.markdown(f"<div style='text-align:center;padding:50px;color:#8AAAC8'>"
                        f"📭 {yr} yilina ait veri yok</div>", unsafe_allow_html=True)

    with gr:
        st.markdown('<div class="section-title">🏢 Ziyaret Edilen Firmalar</div>', unsafe_allow_html=True)
        co_data = cached_co_dist(8)
        if co_data:
            df_co = pd.DataFrame(co_data)
            ch_co = alt.Chart(df_co).mark_bar(
                cornerRadiusTopRight=5, cornerRadiusBottomRight=5,
                color=alt.Gradient(gradient="linear",
                    stops=[alt.GradientStop(color="#1565C0", offset=0),
                           alt.GradientStop(color="#00BCD4", offset=1)],
                    x1=0, x2=1, y1=0, y2=0)
            ).encode(
                y=alt.Y("company:N", sort="-x", title=None,
                        axis=alt.Axis(labelFontSize=10.5, labelLimit=120)),
                x=alt.X("visit_count:Q", title="Ziyaret",
                        axis=alt.Axis(labelFontSize=10, tickMinStep=1)),
                tooltip=[alt.Tooltip("company:N", title="Firma"),
                         alt.Tooltip("visit_count:Q", title="Ziyaret"),
                         alt.Tooltip("total_hours:Q", title="Toplam Sure", format=".1f")]
            ).properties(height=CHART_H)
            st.altair_chart(ch(ch_co), use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:50px;color:#8AAAC8'>📭 Veri yok</div>",
                        unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ── Grafik Satiri 2: Kategori Dağilimi + Son Islemler ──
    ga, gb = st.columns([3, 4], gap="medium")

    with ga:
        st.markdown('<div class="section-title">📊 Kategori Dagilimi (Is Tipleri)</div>', unsafe_allow_html=True)
        cat_data = cached_category_stats()
        if cat_data:
            df_cat = pd.DataFrame(cat_data)
            df_cat["technician"] = df_cat["technician"].replace("Belirtilmemis", "Diger IT Isleri")

            base_arc = alt.Chart(df_cat)
            pie = base_arc.mark_arc(
                innerRadius=45, outerRadius=90,
                padAngle=0.015, cornerRadius=4
            ).encode(
                theta=alt.Theta("visit_count:Q", stack=True),
                color=alt.Color("technician:N",
                    scale=alt.Scale(range=["#1E88E5", "#26A69A", "#AB47BC", "#FFA726",
                                           "#EC407A", "#42A5F5", "#26C6DA", "#78909C"]),
                    legend=alt.Legend(orient="bottom", labelFontSize=9, columns=2, symbolSize=60)),
                tooltip=[alt.Tooltip("technician:N", title="Kategori"),
                         alt.Tooltip("visit_count:Q", title="Ziyaret"),
                         alt.Tooltip("total_hours:Q", title="Toplam Sure (sa)", format=".1f")]
            )
            center = base_arc.mark_text(
                fontSize=20, fontWeight=700, color="#60B4FF"
            ).encode(
                text=alt.value(str(sum(r["visit_count"] for r in cat_data)))
            )
            ch_cat = alt.layer(pie, center).properties(height=210)
            st.altair_chart(ch(ch_cat), use_container_width=True)
        else:
            st.markdown("<div style='text-align:center;padding:40px;color:#8AAAC8'>📭 Veri yok</div>",
                        unsafe_allow_html=True)

    with gb:
        st.markdown('<div class="section-title">📝 Son IT Faaliyetlerim</div>', unsafe_allow_html=True)
        recent = cached_recent_visits(8)
        if recent:
            df_r = rpt.build_dataframe(recent)
            show = [c for c in ["Tarih", "Firma", "Konu", "Süre", "Durum", "Kategori"] if c in df_r.columns]
            st.dataframe(df_r[show], use_container_width=True, hide_index=True, height=225)
        else:
            st.markdown("<div style='text-align:center;padding:40px;color:#8AAAC8'>"
                        "📭 Henuz IT kaydi bulunmuyor.</div>",
                        unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEKME 2 — YENI KAYIT
# ─────────────────────────────────────────────

def tab_new_visit():
    st.markdown('<div class="section-title" style="font-size:15px">➕ Yeni Ziyaret & Is Kaydi Ekle</div>',
                unsafe_allow_html=True)
    companies = cached_companies()

    # Hazır Şablonlar
    with st.expander("⚡ Hızlı Not Şablonu Yükle (Zaman Kazan)", expanded=False):
        st.caption("Sık yaptığınız rutin BT işlemlerini tek tıkla forma aktarabilirsiniz:")
        
        TEMPLATES = {
            "🖥️ Sunucu Rutin Bakımı": ("Sunucu Rutin Bakımı ve Sağlık Kontrolü", "— Sunucu diski doluluk oranları kontrol edildi.\n— Windows Update / Güvenlik yamaları uygulandı.\n— Event Viewer (Olay Görüntüleyici) sistem günlükleri incelendi, kritik hata tespit edilmedi.\n— Fiziksel sunucu fan ve sıcaklık değerleri normal."),
            "🔥 Firewall & Ağ Kuralı": ("Firewall ve VLAN Kural Güncellemesi", "— Güvenlik duvarı (Firewall) erişim kuralları güncellendi.\n— Yeni departman için VLAN tanımlaması yapıldı.\n— VPN kullanıcı erişim yetkileri denetlendi.\n— Ağ bant genişliği kullanımı kontrol edildi."),
            "💻 Kullanıcı PC Kurulumu": ("Kullanıcı Bilgisayarı Format ve Kurulum", "— Bilgisayar işletim sistemi yeniden kuruldu (Windows 11).\n— Şirket etki alanına (Domain) dahil edildi.\n— Antivirüs, Office ve gerekli iş yazılımları yüklendi.\n— Yazıcı ve ağ sürücüsü tanımları yapıldı, kullanıcıya teslim edildi."),
            "💾 Yedekleme & Disk Kontrolü": ("Yedekleme Kontrolü ve Veri Sağlığı", "— Günlük ve haftalık yedekleme durumları (Veeam/NAS) kontrol edildi.\n— Örnek dosya geri yükleme (Restore) testi başarıyla tamamlandı.\n— Harici disk/NAS alan durumu kontrol edildi.\n— Yedekleme günlüklerinde hata bulunmadı."),
            "🌐 Uzak Destek & Kullanıcı Sorunu": ("Kullanıcı Uzak Masaüstü Desteği", "— Kullanıcının karşılaştığı yazılım/yazıcı erişim sorunu çözüldü.\n— E-posta (Outlook) senkronizasyon hatası giderildi.\n— Gerekli güvenlik taraması yapıldı.")
        }
        
        selected_template = st.selectbox("Şablon Seçin", [""] + list(TEMPLATES.keys()))
        tpl_subject = ""
        tpl_notes = ""
        if selected_template and selected_template in TEMPLATES:
            tpl_subject, tpl_notes = TEMPLATES[selected_template]
            st.info(f"💡 Şablon Seçildi: **{selected_template}**")

    with st.form("new_visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            visit_date  = st.date_input("📅 Calisma Tarihi *", value=date.today(),
                                        min_value=date(2020,1,1), max_value=date(2030,12,31))
            company_sel = ""
            if companies:
                st.caption("💡 Hizli Secim: Daha once calistiginiz bir firma secin veya asagiya yeni yazin")
                company_sel = st.selectbox("Kayıtlı Firmalar", [""]+companies, index=0)
            company_inp = st.text_input("🏢 Firma / Kurum Adi *",
                                        value=company_sel if company_sel else "",
                                        placeholder="Örn: Microsoft Türkiye, Genel Merkez...")
            company    = company_inp.strip() or company_sel.strip()
            category   = st.selectbox("⚡ Calisma Kategorisi", CATEGORIES)

        with col2:
            contact = st.text_input("📞 Bilgi / Iletisim Kisi", placeholder="Örn: Mehmet Bey (BT Muduru)")
            subject = st.text_input("📌 Calisma Konusu", value=tpl_subject, placeholder="Örn: Firewall Kural Guncelleme...")
            da, db_ = st.columns(2)
            with da: duration = st.number_input("⏱️ Harcanan Sure (Saat)", min_value=0.0, max_value=24.0, value=1.0, step=0.5)
            with db_: status  = st.selectbox("✅ Durum", STATUS_OPTIONS, index=0)

        work_notes = st.text_area("🔧 Yapilan Islemler & Teknik Notlar *", value=tpl_notes, height=140,
            placeholder="— Yedekleme unitesi kontrol edildi, disk sagligi OK.\n— Switch uzerinde VLAN tanimlari guncellendi.\n— 2 adet bilgisayara uzak destek verildi.")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Calismayi Kaydet", use_container_width=True, type="primary")

    if submitted:
        if not company:       st.error("❌ Firma / Kurum adi zorunludur!")
        elif not work_notes.strip(): st.error("❌ Teknik not girilmesi zorunludur!")
        else:
            nid = db.add_visit(visit_date=visit_date.strftime("%Y-%m-%d"), company=company,
                               contact=contact, subject=subject, work_notes=work_notes,
                               duration=duration, technician=category, status=status)
            invalidate_caches()
            st.success(f"✅ Calisma basariyla kaydedildi! (Kayit ID: #{nid})")
            st.balloons()


# ─────────────────────────────────────────────
# SEKME 3 — RAPORLAR & HESAP VERME ASISTANI
# ─────────────────────────────────────────────

def tab_reports():
    st.markdown('<div class="section-title" style="font-size:15px">📊 Rapor Merkezi & Yonetici Ozet Sunumu</div>',
                unsafe_allow_html=True)
    ct, _ = st.columns([2,4])
    with ct: rtype = st.radio("Tur", ["📋 Genel Rapor", "📅 Aylik Rapor"], horizontal=True)

    with st.expander("🔍 Rapor Kapsamini Filtrele", expanded=True):
        f1,f2,f3 = st.columns(3)
        with f1: fco = st.text_input("🏢 Firma / Kurum Filtresi", placeholder="Firma adi...")
        if "Aylık" in rtype:
            with f2:
                ms = st.selectbox("📅 Ay Secimi", [f"{n} — {MONTHS_TR[n]}" for n in range(1,13)],
                                  index=date.today().month-1)
                sm = int(ms.split(" — ")[0])
            with f3:
                cy = date.today().year
                sy = st.selectbox("📆 Yil Secimi", list(range(cy-3,cy+2)), index=3)
        else:
            with f2: df  = st.date_input("📅 Baslangic Tarihi", value=date(date.today().year,1,1))
            with f3: dt  = st.date_input("📅 Bitis Tarihi",     value=date.today())

    if "Aylık" in rtype:
        visits = db.get_visits(company_filter=fco, month=sm, year=sy)
        title  = f"Aylik BT Calisma Raporu — {MONTHS_TR[sm]} {sy}"
    else:
        visits = db.get_visits(company_filter=fco,
                               date_from=df.strftime("%Y-%m-%d"),
                               date_to=dt.strftime("%Y-%m-%d"))
        title  = f"IT Calisma Raporu — {df.strftime('%d.%m.%Y')} / {dt.strftime('%d.%m.%Y')}"

    if not visits:
        st.info("📭 Kriterlere uygun calisma kaydi bulunamadi.")
        return

    dfr   = rpt.build_dataframe(visits)
    thr   = sum(v.get("duration",0) or 0 for v in visits)
    s1,s2,s3 = st.columns(3)
    s1.metric("📋 Toplam Ziyaret", len(visits))
    s2.metric("⏱️ Harcanan Sure", f"{thr:.1f} saat")
    s3.metric("🏭 Firma / Kurum", len(set(v["company"] for v in visits)))

    # ── HESAP VERME / YONETICI OZETI BOLUMU ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">👔 Yonetici Ozet Sunumu (Kopyalamaya Hazir)</div>', unsafe_allow_html=True)

    # Ozet metin olusturma
    completed_tasks = [v for v in visits if v.get("status") == "Tamamlandi"]
    distinct_cos = set(v["company"] for v in visits)
    cat_counts = {}
    for v in visits:
        cat = v.get("technician") or "Diger IT Isleri"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    top_cat_str = "Yok"
    if cat_counts:
        top_cat = max(cat_counts, key=cat_counts.get)
        top_cat_str = f"{top_cat} ({cat_counts[top_cat]} kayit)"

    summary_text = (
        f"**Sayın Yöneticim,**\n\n"
        f"{title} kapsamında gerçekleştirdiğim BT saha ve destek faaliyetlerinin özeti aşağıdadır:\n\n"
        f"🔹 **Genel İstatistikler:**\n"
        f"• Toplam Çalışılan Firma/Departman Sayısı: {len(distinct_cos)}\n"
        f"• Gerçekleştirilen Toplam Faaliyet / Saha Ziyareti: {len(visits)} adet ({len(completed_tasks)} tamamlanan)\n"
        f"• Toplam BT Hizmet / Destek Süresi: {thr:.1f} saat\n"
        f"• En Çok Yoğunlaşılan Alan: {top_cat_str}\n\n"
        f"🔹 **Gerçekleştirilen Önemli Çalışmalar:**\n"
    )
    for i, v in enumerate(visits[:8]):  # En onemli son 8 calisma
        summary_text += f"• **[{fmt_date(v['visit_date'])}] {v['company']}** - {v.get('subject') or 'Genel Bakım'}: {v.get('work_notes', '').replace(chr(10), ' ').strip()[:95]}...\n"

    if len(visits) > 8:
        summary_text += f"• ve diğer {len(visits) - 8} teknik destek faaliyeti.\n"

    summary_text += "\nBilgilerinize sunarım.\n\n*IT Sistem ve Destek Günlüğü tarafından otomatik oluşturulmuştur.*"

    st.markdown("""<div class="glow-box">""", unsafe_allow_html=True)
    st.text_area("Yoneticiye Göndermek İçin Kopyala", summary_text, height=220)
    st.markdown("""</div>""", unsafe_allow_html=True)

    # ── Excel / PDF Rapor ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### 📄 Kayit Listesi")
    st.dataframe(dfr, use_container_width=True, hide_index=True, height=min(400, 60+len(dfr)*38))

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    d1,d2,d3,_ = st.columns([1.2, 1.2, 1.5, 3.1])
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    with d1:
        st.download_button("📥 Excel Raporu (.xlsx)",
            data=rpt.export_to_excel(dfr, title=title[:30]),
            file_name=f"it_faaliyet_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with d2:
        st.download_button("📄 PDF Raporu (.pdf)",
            data=rpt.export_to_pdf(dfr, title=title),
            file_name=f"it_faaliyet_{ts}.pdf",
            mime="application/pdf", use_container_width=True)
    with d3:
        st.download_button("📊 Şık PDF Sunumu",
            data=rpt.export_executive_pdf(visits, cached_summary_stats(), title=title),
            file_name=f"it_sunum_{ts}.pdf",
            mime="application/pdf", use_container_width=True)


# ─────────────────────────────────────────────
# SEKME: E-POSTA RAPORLAMA
# ─────────────────────────────────────────────

def tab_email_report():
    st.markdown('<div class="section-title" style="font-size:15px">📧 E-Posta Rapor Gönderim Paneli</div>', unsafe_allow_html=True)
    
    # Veritabanından mevcut ayarları oku
    smtp_srv = db.get_setting("smtp_server", "smtp.gmail.com")
    smtp_prt = db.get_setting("smtp_port", "587")
    smtp_usr = db.get_setting("smtp_user", "")
    smtp_pwd = db.get_setting("smtp_password", "")
    smtp_from = db.get_setting("smtp_from", "")
    smtp_to = db.get_setting("smtp_to", "")
    smtp_name = db.get_setting("smtp_from_name", "IT Sistem ve Destek Günlüğü")
    
    # Eski verilerden uyumluluk icin smtp_sec ayarla
    smtp_sec_db = db.get_setting("smtp_sec", "")
    if not smtp_sec_db:
        # Geriye donuk uyumluluk
        old_ssl = db.get_setting("smtp_ssl", "False") == "True"
        smtp_sec = "SSL/TLS" if old_ssl else "STARTTLS"
    else:
        smtp_sec = smtp_sec_db
    
    with st.expander("⚙️ SMTP Sunucu & Gönderici Ayarları", expanded=not smtp_usr):
        st.markdown("<p style='font-size:12px; color:rgba(180,210,240,0.6)'>Raporları yöneticinize veya kendinize mail atmak için SMTP (e-posta sunucusu) ayarlarınızı bir kez kaydetmeniz yeterlidir.</p>", unsafe_allow_html=True)
        
        c_name, c_srv, c_prt = st.columns([1.5, 1.5, 1])
        with c_name:
            from_name_val = st.text_input("Gönderen Adı / Unvanı", value=smtp_name, placeholder="Örn. Ahmet Yılmaz - IT Uzmanı")
        with c_srv:
            srv = st.text_input("SMTP Sunucusu", value=smtp_srv, placeholder="smtp.gmail.com")
        with c_prt:
            prt = st.text_input("Port", value=smtp_prt, placeholder="587")
            
        c_proto, c_usr, c_pwd = st.columns([1.2, 1.4, 1.4])
        with c_proto:
            sec_options = ["STARTTLS (Örn. Port 587)", "SSL/TLS (Örn. Port 465)", "Güvenlik Yok (Plain / Şifresiz)"]
            if smtp_sec == "SSL/TLS":
                sec_index = 1
            elif smtp_sec == "None":
                sec_index = 2
            else:
                sec_index = 0
            ssl_choice = st.selectbox("Güvenlik Protokolü", sec_options, index=sec_index)
        with c_usr:
            usr = st.text_input("SMTP Kullanıcı Adı (E-posta) - Şifresiz ise boş bırakın", value=smtp_usr, placeholder="hesap@gmail.com")
        with c_pwd:
            pwd = st.text_input("Şifre / Uygulama Şifresi - Şifresiz ise boş bırakın", value=smtp_pwd, type="password", placeholder="••••••••••••••••")
            
        c_from, c_to = st.columns(2)
        with c_from:
            frm = st.text_input("Gönderen E-Posta (Kimden)", value=smtp_from or smtp_usr, placeholder="hesap@gmail.com")
        with c_to:
            to_mails = st.text_input("Alıcı E-Posta (Kime) - Birden fazla ise virgülle ayırın", value=smtp_to, placeholder="yonetici@sirket.com, kendim@sirket.com")
            
        if st.button("💾 SMTP Ayarlarını Kaydet", key="btn_save_smtp"):
            if "STARTTLS" in ssl_choice:
                sec_val = "STARTTLS"
            elif "SSL/TLS" in ssl_choice:
                sec_val = "SSL/TLS"
            else:
                sec_val = "None"
                
            db.set_setting("smtp_server", srv)
            db.set_setting("smtp_port", prt)
            db.set_setting("smtp_user", usr)
            db.set_setting("smtp_password", pwd)
            db.set_setting("smtp_from", frm)
            db.set_setting("smtp_to", to_mails)
            db.set_setting("smtp_from_name", from_name_val)
            db.set_setting("smtp_sec", sec_val)
            st.success("✅ SMTP Ayarları veritabanına başarıyla kaydedildi!")
            st.rerun()

    # ── 2. RAPOR İÇERİĞİ & MAİL GÖNDERİMİ ──
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("#### 📝 E-Posta Raporu Hazırlama")
    
    col_range, col_type = st.columns([2, 1])
    with col_type:
        report_period = st.selectbox("Rapor Periyodu", ["Haftalık", "Aylık", "Özel Tarih Aralığı"], index=0)
        
    with col_range:
        today = date.today()
        if report_period == "Haftalık":
            default_start = today - timedelta(days=7)
            default_end = today
        elif report_period == "Aylık":
            default_start = today - timedelta(days=30)
            default_end = today
        else:
            default_start = date(today.year, 1, 1)
            default_end = today
            
        date_from = st.date_input("Başlangıç Tarihi", value=default_start)
        date_to = st.date_input("Bitiş Tarihi", value=default_end)

    # Verileri çek
    visits = db.get_visits(
        date_from=date_from.strftime("%Y-%m-%d"),
        date_to=date_to.strftime("%Y-%m-%d")
    )
    
    if not visits:
        st.warning("⚠️ Seçilen tarih aralığında gönderilecek kayıt bulunamadı.")
        return
        
    ts_range = f"{date_from.strftime('%d.%m.%Y')} - {date_to.strftime('%d.%m.%Y')}"
    default_subject = f"IT Faaliyet Raporu ({ts_range})"
    
    # Rapor özetini oluştur
    thr = sum(v.get("duration", 0) or 0 for v in visits)
    distinct_cos = set(v["company"] for v in visits)
    completed_tasks = [v for v in visits if v.get("status") == "Tamamlandi"]
    
    cat_counts = {}
    for v in visits:
        cat = v.get("technician") or "Diger IT Isleri"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    top_cat_str = "Yok"
    if cat_counts:
        top_cat = max(cat_counts, key=cat_counts.get)
        top_cat_str = f"{top_cat} ({cat_counts[top_cat]} kayit)"

    # HTML Tablo Satırları
    table_rows_html = ""
    for v in visits[:15]:
        status_bg = "#e8f5e9" if v.get("status") == "Tamamlandi" else "#fff3e0"
        status_fg = "#2e7d32" if v.get("status") == "Tamamlandi" else "#ef6c00"
        
        notes_clean = v.get('work_notes', '').replace('\n', ' ').strip()
        if len(notes_clean) > 95:
            notes_clean = notes_clean[:92] + "..."
            
        table_rows_html += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 10px; font-size: 13px; color: #334155;">{fmt_date(v['visit_date'])}</td>
            <td style="padding: 10px; font-size: 13px; font-weight: 600; color: #1e293b;">{v['company']}</td>
            <td style="padding: 10px; font-size: 13px; color: #475569;"><strong>{v.get('subject') or 'Genel Destek'}</strong><br/><span style="font-size:12px; color:#64748b;">{notes_clean}</span></td>
            <td style="padding: 10px; text-align: center;">
                <span style="background-color: {status_bg}; color: {status_fg}; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block;">
                    {v.get('status')}
                </span>
            </td>
        </tr>
        """

    if len(visits) > 15:
        table_rows_html += f"""
        <tr>
            <td colspan="4" style="padding: 10px; font-size: 12px; text-align: center; color: #64748b; font-style: italic;">
                ve diğer {len(visits) - 15} adet teknik çalışma detayları ekteki PDF raporunda yer almaktadır.
            </td>
        </tr>
        """

    # Plain Text E-Posta gövdesi (Fallback & Düz Metin)
    default_body = (
        f"Sayın Yöneticim,\n\n"
        f"{ts_range} tarihleri arasında gerçekleştirdiğim bilgi teknolojileri (BT) saha ziyaretleri ve teknik destek faaliyetlerimin özeti aşağıdadır:\n\n"
        f"📊 GENEL İSTATİSTİKLER\n"
        f"• Destek Verilen Toplam Firma Sayısı: {len(distinct_cos)}\n"
        f"• Toplam Faaliyet / Ziyaret Sayısı: {len(visits)} adet ({len(completed_tasks)} tamamlanan)\n"
        f"• Toplam Harcanan Destek Süresi: {thr:.1f} saat\n"
        f"• En Çok Çalışılan IT Kategorisi: {top_cat_str}\n\n"
        f"📋 GERÇEKLEŞTİRİLEN ÖNEMLİ İŞLER\n"
    )
    for i, v in enumerate(visits[:10]):
        notes_clean = v.get('work_notes', '').replace('\n', ' ').strip()
        if len(notes_clean) > 85:
            notes_clean = notes_clean[:85] + "..."
        default_body += f"- [{fmt_date(v['visit_date'])}] {v['company']} - {v.get('subject') or 'Genel Destek'}: {notes_clean}\n"
        
    if len(visits) > 10:
        default_body += f"- ve diğer {len(visits) - 10} teknik çalışma.\n"
        
    default_body += f"\nDetaylı teknik faaliyet raporu ve PDF sunumu e-posta ekinde yer almaktadır.\n\nBilgilerinize sunarım.\n\n{smtp_name}"

    # Zengin HTML E-Posta şablonu
    html_body = f"""
    <div style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; max-width: 700px; margin: 0 auto; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; color: #1e293b; text-align: left;">
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 26px 20px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 700;">IT FAALİYET & TEKNİK DESTEK RAPORU</h1>
            <p style="color: #bfdbfe; margin: 5px 0 0; font-size: 13px; font-weight: 500;">{ts_range}</p>
        </div>
        
        <div style="padding: 20px;">
            <p style="font-size: 14px; line-height: 1.5; margin-top: 0; font-weight: 600;">Sayın Yöneticim,</p>
            <p style="font-size: 13px; line-height: 1.5; color: #475569;">
                Belirtilen tarih aralığında gerçekleştirdiğim bilgi teknolojileri (BT) altyapı, sistem yönetimi ve teknik destek faaliyetlerimin detaylı raporu aşağıda yer almaktadır:
            </p>
            
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0 20px;">
                <tr>
                    <td style="width: 33.33%; padding: 3px;">
                        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center;">
                            <span style="font-size: 20px; font-weight: 700; color: #2563eb; display: block;">{len(visits)}</span>
                            <span style="font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase;">Toplam İş</span>
                        </div>
                    </td>
                    <td style="width: 33.33%; padding: 3px;">
                        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center;">
                            <span style="font-size: 20px; font-weight: 700; color: #10b981; display: block;">{thr:.1f} Saat</span>
                            <span style="font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase;">Toplam Süre</span>
                        </div>
                    </td>
                    <td style="width: 33.33%; padding: 3px;">
                        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center;">
                            <span style="font-size: 20px; font-weight: 700; color: #8b5cf6; display: block;">{len(distinct_cos)}</span>
                            <span style="font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase;">Firma / Kurum</span>
                        </div>
                    </td>
                </tr>
            </table>
            
            <h3 style="font-size: 13.5px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; margin: 20px 0 10px; color: #1e3a8a;">📋 Yapılan Çalışmaların Detayı</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden;">
                <thead>
                    <tr style="background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0;">
                        <th style="padding: 10px; font-size: 11.5px; font-weight: 600; text-align: left; color: #475569;">Tarih</th>
                        <th style="padding: 10px; font-size: 11.5px; font-weight: 600; text-align: left; color: #475569;">Firma/Kurum</th>
                        <th style="padding: 10px; font-size: 11.5px; font-weight: 600; text-align: left; color: #475569;">Çalışma Detayı</th>
                        <th style="padding: 10px; font-size: 11.5px; font-weight: 600; text-align: center; color: #475569;">Durum</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>
            
            <p style="font-size: 11px; color: #64748b; margin-top: 12px; font-style: italic;">*Detaylı teknik faaliyet raporu ve şık grafik sunumu e-posta ekinde PDF olarak yer almaktadır.</p>
            
            <div style="margin-top: 25px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                <p style="margin: 0; font-size: 13.5px; font-weight: 600; color: #1e3a8a;">{smtp_name}</p>
                <p style="margin: 2px 0 0; font-size: 11px; color: #64748b;">Bilgi Teknolojileri Sistem ve Destek Uzmanı</p>
            </div>
        </div>
        
        <div style="background-color: #f1f5f9; padding: 12px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 10.5px; color: #94a3b8;">
            Bu e-posta, IT Sistem ve Ziyaret Takip Otomasyonu tarafından otomatik olarak hazırlanmıştır.
        </div>
    </div>
    """

    mail_subject = st.text_input("E-Posta Konusu", value=default_subject)
    mail_body = st.text_area("E-Posta Gövde Metni (Düz Metin Fallback)", value=default_body, height=180)
    
    # Markdown kod blogu algilama hatasini (girintilerden dolayi) cozmek icin HTML'i temizle
    clean_html = "".join([line.strip() for line in html_body.split("\n")])
    
    with st.expander("👀 Gönderilecek Zengin HTML E-Posta Önizlemesi", expanded=True):
        st.markdown(clean_html, unsafe_allow_html=True)
        
    attach_pdf = st.checkbox("Şık PDF Sunumu Raporunu Ekle (.pdf)", value=True)
    
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("📤 Raporu E-Posta Olarak Gönder", type="primary", key="btn_send_report_email"):
        # Şifresiz/güvenliksiz modlar haricinde, kimlik doğrulama gerekiyorsa kontrol et
        if smtp_sec != "None" and (not smtp_usr or not smtp_pwd):
            st.error("❌ E-posta gönderebilmek için önce yukarıdaki 'SMTP Sunucu & Gönderici Ayarları' bölümünü doldurup kaydetmelisiniz!")
            return
            
        with st.spinner("📧 E-posta hazırlanıyor ve sunucuya gönderiliyor..."):
            pdf_data = None
            if attach_pdf:
                pdf_data = rpt.export_executive_pdf(
                    visits,
                    cached_summary_stats(),
                    title=f"IT Calisma Raporu — {ts_range}"
                )
                
            success, msg = rpt.send_email_report(
                smtp_server=smtp_srv,
                smtp_port=smtp_prt,
                smtp_user=smtp_usr,
                smtp_password=smtp_pwd,
                from_email=smtp_from or smtp_usr,
                from_name=smtp_name,
                to_email=smtp_to,
                security_mode=smtp_sec,
                subject=mail_subject,
                body_text=mail_body,
                html_body=clean_html,
                pdf_data=pdf_data,
                pdf_filename=f"IT_Faaliyet_Raporu_{date_from.strftime('%d%m%Y')}_{date_to.strftime('%d%m%Y')}.pdf"
            )
            
            if success:
                st.success(f"🎉 {msg}")
            else:
                st.error(f"❌ {msg}")


# ─────────────────────────────────────────────
# SEKME 4 — TUM KAYITLAR
# ─────────────────────────────────────────────

def tab_all_records():
    st.markdown('<div class="section-title" style="font-size:15px">🗂️ Tum Kayitlarimi Duzenle / Yonet</div>',
                unsafe_allow_html=True)
    cs1,cs2,cs3 = st.columns([2,1,1], gap="small")
    with cs1: sch = st.text_input("🔍 Firma adına göre süz...", placeholder="Aranacak firma...", key="ar_s")
    with cs2: df_f = st.date_input("📅 Baslangic", value=date(date.today().year,1,1), key="ar_f")
    with cs3: df_t = st.date_input("📅 Bitis",     value=date.today(), key="ar_t")

    visits = db.get_visits(company_filter=sch,
                           date_from=df_f.strftime("%Y-%m-%d"),
                           date_to=df_t.strftime("%Y-%m-%d"))
    if not visits:
        st.info("📭 Kriterlere uygun kayıt bulunamadı.")
        return

    st.caption(f"Toplam **{len(visits)}** faaliyet kaydı")

    for v in visits:
        vid = v["id"]
        lbl = f"#{vid:03d} · 📅 {fmt_date(v['visit_date'])} · 🏢 {v['company']} · {(v.get('subject') or '—')[:45]}"
        with st.expander(lbl):
            vc, ec = st.columns([3,2], gap="medium")
            with vc:
                for k,val in [("Tarih", fmt_date(v["visit_date"])), ("Firma/Bölüm", v["company"]),
                              ("İlgili Kişi", v.get("contact") or "—"), ("Konu", v.get("subject") or "—"),
                              ("Kategori", v.get("technician") or "Diğer IT İşleri"),
                              ("Süre", f"{v.get('duration',0):.1f} saat"), ("Durum", v.get("status") or "—")]:
                    st.markdown(f"<span style='color:rgba(160,200,240,.65);font-size:12.5px'>{k}:</span> "
                                f"<span style='font-weight:500'>{val}</span>", unsafe_allow_html=True)
                st.markdown("<br>**🔧 Yapılan Teknik İşlemler:**")
                st.markdown(f"<div style='background:rgba(255,255,255,0.035);border-radius:10px;"
                            f"padding:10px 14px;font-size:13px;color:#B0C8E0;white-space:pre-wrap'>"
                            f"{v.get('work_notes','—')}</div>", unsafe_allow_html=True)
            with ec:
                st.markdown("**✏️ Kaydi Guncelle**")
                with st.form(f"ef_{vid}"):
                    ed  = st.date_input("Tarih",     value=datetime.strptime(v["visit_date"],"%Y-%m-%d").date(), key=f"ed_{vid}")
                    ec2 = st.text_input("Firma/Bölüm", value=v["company"],         key=f"eco_{vid}")
                    ect = st.text_input("İlgili Kişi", value=v.get("contact",""),  key=f"ect_{vid}")
                    es  = st.text_input("Konu",      value=v.get("subject",""),    key=f"es_{vid}")
                    et  = st.selectbox("Kategori", CATEGORIES,
                                       index=CATEGORIES.index(v.get("technician")) if v.get("technician") in CATEGORIES else 0,
                                       key=f"et_{vid}")
                    edu = st.number_input("Süre (sa)", value=float(v.get("duration",0)), step=0.5, key=f"edu_{vid}")
                    safe_status = v.get("status","Tamamlandi") if v.get("status") in STATUS_OPTIONS else "Tamamlandi"
                    est = st.selectbox("Durum", STATUS_OPTIONS,
                                       index=STATUS_OPTIONS.index(safe_status), key=f"est_{vid}")
                    en  = st.text_area("Yapılan Teknik İşlem", value=v.get("work_notes",""), height=80, key=f"en_{vid}")
                    sb,db_b = st.columns(2)
                    with sb:  save = st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True)
                    with db_b: dlt = st.form_submit_button("🗑️ Sil", use_container_width=True)
                if save:
                    db.update_visit(vid, ed.strftime("%Y-%m-%d"), ec2, ect, es, en, edu, et, est)
                    invalidate_caches(); st.success("✅ Güncellendi!"); st.rerun()
                if dlt:
                    db.delete_visit(vid); invalidate_caches()
                    st.warning(f"🗑️ #{vid} silindi."); st.rerun()


# ─────────────────────────────────────────────
# SEKME 5 — HATIRLATICILAR
# ─────────────────────────────────────────────

def tab_reminders():
    st.markdown('<div class="section-title" style="font-size:15px">🔔 Periyodik Bakim & Hatirlaticilarim</div>',
                unsafe_allow_html=True)

    due = cached_due_reminders()
    if due:
        st.markdown(
            f"<div style='background:rgba(183,28,28,.12);border:1px solid rgba(239,83,80,.35);"
            f"border-radius:12px;padding:12px 18px;margin-bottom:16px;font-size:13px'>"
            f"⚠️ <b style='color:#EF9A9A'>Bugün vadesi gelen {len(due)} hatırlatıcı mevcut!</b></div>",
            unsafe_allow_html=True)
        for r in due:
            pc = PRIORITY_COLORS.get(r["priority"], "#42A5F5")
            dl = (date.today() - datetime.strptime(r["remind_date"], "%Y-%m-%d").date()).days
            rc, rd, rdl = st.columns([5, 1, 1])
            with rc:
                lt = f"<span style='color:#EF5350'>{dl}g gecikti</span>" if dl > 0 else "<span style='color:#FF9800'>Bugün</span>"
                st.markdown(
                    f"<div class='card {pri_class(r['priority'])}' style='margin:0 0 4px'>"
                    f"<b>{r['company']}</b> — {r['title']} &nbsp;{lt}<br>"
                    f"<small style='color:rgba(160,200,240,.6)'>{fmt_date(r['remind_date'])} · {r['priority']}"
                    f"{' · ' + r['notes'] if r['notes'] else ''}</small></div>",
                    unsafe_allow_html=True)
            with rd:
                if st.button("✅", key=f"rd_{r['id']}"):
                    db.complete_reminder(r["id"]); invalidate_caches(); st.rerun()
            with rdl:
                if st.button("🗑️", key=f"rdd_{r['id']}"):
                    db.delete_reminder(r["id"]); invalidate_caches(); st.rerun()
        st.markdown("<hr style='border-color:rgba(255,255,255,.05);margin:16px 0'>", unsafe_allow_html=True)

    cf, cl = st.columns([2, 3], gap="large")

    with cf:
        st.markdown('<div class="section-title">➕ Yeni Hatırlatıcı</div>', unsafe_allow_html=True)
        cos = cached_companies()
        with st.form("add_rem", clear_on_submit=True):
            r_date = st.date_input("📅 Hatırlatma Tarihi *", value=date.today()+timedelta(days=30), min_value=date.today())
            r_co   = st.selectbox("🏢 Firma / Bölüm", [""]+cos) if cos else st.text_input("🏢 Firma / Bölüm")
            r_co_m = st.text_input("veya yeni firma:")
            r_co_f = r_co_m.strip() or (r_co if isinstance(r_co, str) else "")
            r_ttl  = st.text_input("📌 Hatırlatma Konusu *", placeholder="Yıllık sunucu bakım/lisans yenileme")
            r_nts  = st.text_area("📝 Teknik Detay / Not", height=60)
            r_pri  = st.selectbox("⚡ Öncelik Seviyesi", PRIORITY_OPTIONS)
            if st.form_submit_button("🔔 Hatırlatıcı Ekle", type="primary", use_container_width=True):
                if not r_co_f: st.error("❌ Firma/Bölüm gerekli!")
                elif not r_ttl.strip(): st.error("❌ Konu gerekli!")
                else:
                    db.add_reminder(r_date.strftime("%Y-%m-%d"), r_co_f, r_ttl, r_nts, r_pri)
                    invalidate_caches(); st.success("✅ Hatırlatıcı eklendi!"); st.rerun()

    with cl:
        st.markdown('<div class="section-title">📋 Bekleyen Hatırlatıcılarım</div>', unsafe_allow_html=True)
        show_d = st.checkbox("Tamamlananları da göster", value=False, key="show_d_rem")
        rems   = db.get_reminders(include_done=show_d)
        if not rems:
            st.info("📭 Bekleyen hatırlatıcı yok.")
        for r in rems:
            pc = PRIORITY_COLORS.get(r["priority"], "#42A5F5")
            rd_dt = datetime.strptime(r["remind_date"], "%Y-%m-%d").date()
            dl    = (rd_dt - date.today()).days
            dn    = r["is_done"]
            if dn:        badge = "<span style='color:#4CAF50;font-size:11px'>✅ Bitti</span>"
            elif dl < 0:  badge = f"<span style='color:#EF5350;font-size:11px'>⚠️ {abs(dl)}g gecikti</span>"
            elif dl == 0: badge = "<span style='color:#FF9800;font-size:11px'>⏰ Bugün!</span>"
            elif dl <= 7: badge = f"<span style='color:#FF9800;font-size:11px'>⚡ {dl}g kaldı</span>"
            else:         badge = f"<span style='color:rgba(160,200,240,.55);font-size:11px'>📅 {dl}g kaldı</span>"

            rc2, ra = st.columns([7, 1])
            with rc2:
                op = ".45" if dn else "1"
                st.markdown(
                    f"<div class='card {pri_class(r['priority'])}' style='opacity:{op};margin-bottom:4px'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>"
                    f"<b style='font-size:13px'>{r['company']}</b>{badge}</div>"
                    f"<div style='color:#B0C8E0;font-size:12.5px;margin-top:2px'>{r['title']}</div>"
                    f"<div style='color:rgba(160,200,240,.5);font-size:11px;margin-top:4px'>"
                    f"📅 {fmt_date(r['remind_date'])} · {r['priority']}"
                    f"{' · ' + r['notes'][:45] if r['notes'] else ''}</div></div>",
                    unsafe_allow_html=True)
            with ra:
                if not dn and st.button("✅", key=f"cr_{r['id']}"):
                    db.complete_reminder(r["id"]); invalidate_caches(); st.rerun()
                if st.button("🗑️", key=f"dr_{r['id']}"):
                    db.delete_reminder(r["id"]); invalidate_caches(); st.rerun()


# ─────────────────────────────────────────────
# SEKME 6 — TAKVİM
# ─────────────────────────────────────────────

def tab_calendar():
    st.markdown('<div class="section-title" style="font-size:15px">🗓️ Aylık Faaliyet Takvimim</div>',
                unsafe_allow_html=True)

    cy, cm_c = st.columns([1,1], gap="small")
    with cy:
        sy = st.selectbox("Yıl", list(range(date.today().year-3, date.today().year+2)), index=3, key="caly")
    with cm_c:
        sm_s = st.selectbox("Ay", [f"{n} — {MONTHS_TR[n]}" for n in range(1,13)],
                            index=date.today().month-1, key="calm")
        sm   = int(sm_s.split(" — ")[0])

    cal_data  = db.get_calendar_data(sm, sy)
    month_cal = calendar.monthcalendar(sy, sm)
    total_m   = sum(cal_data.values())

    st.markdown(
        f"<div style='text-align:center;font-size:16.5px;font-weight:700;color:#64B5F6;margin:6px 0 12px'>"
        f"{MONTHS_TR[sm]} {sy}"
        f"<span style='font-size:12.5px;color:rgba(160,200,240,.55);font-weight:400;margin-left:8px'>"
        f"({total_m} faaliyet)</span></div>",
        unsafe_allow_html=True)

    hc = st.columns(7)
    for i, dn in enumerate(DAYS_TR):
        clr = "#EF5350" if i==6 else ("#90CAF9" if i==5 else "rgba(160,200,240,.7)")
        hc[i].markdown(f"<div style='text-align:center;font-weight:700;color:{clr};"
                       f"font-size:12px;padding:4px 0;"
                       f"border-bottom:1px solid rgba(255,255,255,.06)'>{dn}</div>",
                       unsafe_allow_html=True)

    if "cal_sel" not in st.session_state: st.session_state.cal_sel = None
    today_str = date.today().strftime("%Y-%m-%d")

    for week in month_cal:
        wc = st.columns(7)
        for ci, day in enumerate(week):
            if day == 0:
                wc[ci].markdown("<div style='min-height:58px'></div>", unsafe_allow_html=True)
                continue
            ds   = f"{sy}-{sm:02d}-{day:02d}"
            cnt  = cal_data.get(ds, 0)
            sel  = st.session_state.cal_sel == ds
            tod  = ds == today_str
            wend = ci >= 5

            if sel:     bg, bdr, tc = "rgba(30,136,229,.35)", "#1E88E5", "#90CAF9"
            elif tod:   bg, bdr, tc = "rgba(30,136,229,.15)", "rgba(30,136,229,.4)", "#90CAF9"
            elif cnt:
                iv = min(cnt*16, 68)
                bg, bdr, tc = f"rgba(76,175,80,{iv/100:.2f})", "rgba(76,175,80,.4)", "#A5D6A7"
            elif wend:  bg, bdr, tc = "rgba(255,255,255,.01)", "rgba(255,255,255,.03)", "#EF5350"
            else:       bg, bdr, tc = "rgba(255,255,255,.03)", "rgba(255,255,255,.05)", "#C8DFF5"

            dot  = f"<div style='width:5px;height:5px;background:#4CAF50;border-radius:50%;margin:2px auto 0'></div>" if cnt else ""
            cntt = f"<div style='font-size:9.5px;color:#A5D6A7;margin-top:1px'>{cnt}</div>" if cnt else ""
            todm = f"<div style='font-size:8.5px;color:#90CAF9;margin-top:1px'>bugün</div>" if tod else ""
            wc[ci].markdown(
                f"<div style='background:{bg};border:1px solid {bdr};border-radius:10px;"
                f"padding:6px 2px;text-align:center;min-height:58px;cursor:pointer;"
                f"transition:all 0.2s ease'>"
                f"<div style='font-weight:600;color:{tc};font-size:13.5px'>{day}</div>"
                f"{todm}{dot}{cntt}</div>",
                unsafe_allow_html=True)
            if wc[ci].button(" ", key=f"cb_{ds}", help=f"{fmt_date(ds)} — {cnt} kayıt"):
                st.session_state.cal_sel = ds; st.rerun()

    if st.session_state.cal_sel:
        sel_d = st.session_state.cal_sel
        dv    = db.get_visits_by_date(sel_d)
        st.markdown(f"<hr style='border-color:rgba(255,255,255,.05);margin:16px 0'>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-title'>📋 {fmt_date(sel_d)} Tarihindeki Calismalarim ({len(dv)} adet)</div>",
                    unsafe_allow_html=True)
        if dv:
            for v in dv:
                with st.expander(f"🏢 {v['company']} — {v.get('subject','—')}", expanded=True):
                    vca, vnb = st.columns(2)
                    with vca:
                        for lbl, val in [("Firma", v["company"]), ("İlgili Kişi", v.get("contact","—")),
                                         ("Kategori", v.get("technician","—")),
                                         ("Harcanan Sure", f"{v.get('duration',0):.1f} saat"), ("Durum", v.get("status","—"))]:
                            st.markdown(f"<span style='color:rgba(160,200,240,.65);font-size:12.5px'>{lbl}:</span> "
                                        f"<b>{val}</b>", unsafe_allow_html=True)
                    with vnb:
                        st.markdown("**🔧 Yapılan Teknik İşlemler:**")
                        st.markdown(f"<div style='background:rgba(255,255,255,.03);border-radius:10px;"
                                    f"padding:10px 14px;font-size:13px;color:#B0C8E0;white-space:pre-wrap'>"
                                    f"{v.get('work_notes','—')}</div>", unsafe_allow_html=True)
        else:
            st.info(f"📭 {fmt_date(sel_d)} tarihinde kayıtlı çalışma bulunmuyor.")


# ─────────────────────────────────────────────
# SEKME 7 — YAPILACAKLAR (TO-DO)
# ─────────────────────────────────────────────

def tab_todos():
    st.markdown('<div class="section-title" style="font-size:15px">📋 Kisisel Gorev ve BT Takip Listesi</div>',
                unsafe_allow_html=True)

    tds = cached_todo_stats()
    m1,m2,m3 = st.columns(3)
    m1.metric("📌 Bekleyen Gorev",    tds["pending"])
    m2.metric("⚠️ Gecikmis Gorev",   tds["overdue"],  delta_color="inverse")
    m3.metric("✅ Bitirilen Gorev",  tds["done"])

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    cf, cl = st.columns([2, 3], gap="large")

    with cf:
        st.markdown('<div class="section-title">➕ Yeni Görev Tanımla</div>', unsafe_allow_html=True)
        cos = cached_companies()
        with st.form("add_todo_form", clear_on_submit=True):
            t_ttl  = st.text_input("📌 Görev Başlığı *", placeholder="Firewall kural yedeklemesi alınacak...")
            t_co   = st.selectbox("🏢 Firma / Bölüm", [""]+cos) if cos else st.text_input("🏢 Firma / Bölüm")
            t_co_m = st.text_input("veya yeni firma:")
            t_co_f = t_co_m.strip() or (t_co if isinstance(t_co, str) else "")
            t_desc = st.text_area("📝 Görev Açıklaması", height=70, placeholder="Yedekleme sonrası disk kontrolü...")
            t_due  = st.date_input("📅 Son Tarih", value=date.today()+timedelta(days=7))
            t_pri  = st.selectbox("⚡ Öncelik Seviyesi", PRIORITY_OPTIONS)
            if st.form_submit_button("➕ Görev Ekle", type="primary", use_container_width=True):
                if not t_ttl.strip(): st.error("❌ Başlık gerekli!")
                else:
                    db.add_todo(t_ttl, t_co_f, t_desc, t_due.strftime("%Y-%m-%d"), t_pri)
                    invalidate_caches(); st.success("✅ Görev eklendi!"); st.rerun()

    with cl:
        st.markdown('<div class="section-title">📋 Gorev Listem</div>', unsafe_allow_html=True)
        show_d2 = st.checkbox("Tamamlananları da göster", value=False, key="td_done")
        todos   = db.get_todos(include_done=show_d2)
        if not todos:
            st.info("📭 Görev yok — soldan ekleyebilirsiniz.")
        for t in todos:
            pc    = PRIORITY_COLORS.get(t["priority"], "#42A5F5")
            is_dn = t["is_done"]
            due_d = t.get("due_date")
            if due_d:
                dl2 = (datetime.strptime(due_d, "%Y-%m-%d").date() - date.today()).days
                if is_dn:     db2 = f"<span style='color:#4CAF50;font-size:11px'>✅ Tamamlandı</span>"
                elif dl2<0:   db2 = f"<span style='color:#EF5350;font-size:11px'>🔴 {abs(dl2)}g gecikti</span>"
                elif dl2==0:  db2 = "<span style='color:#FF9800;font-size:11px'>⏰ Bugün!</span>"
                elif dl2<=3:  db2 = f"<span style='color:#FF9800;font-size:11px'>⚡ {dl2}g kaldı</span>"
                else:         db2 = f"<span style='color:rgba(160,200,240,.55);font-size:11px'>📅 {dl2}g kaldı</span>"
            else: db2 = "<span style='color:rgba(160,200,240,.45);font-size:11px'>Tarih yok</span>"

            tc2, ta1, ta2 = st.columns([5, 1, 1])
            with tc2:
                op2 = ".4" if is_dn else "1"
                cotxt = f" · <span style='color:rgba(160,200,240,.5)'>{t['company']}</span>" if t.get("company") else ""
                st.markdown(
                    f"<div class='card {pri_class(t['priority'])}' style='opacity:{op2};margin-bottom:4px'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px'>"
                    f"<b style='font-size:13px;text-decoration:{'line-through' if is_dn else 'none'}'>"
                    f"{t['title']}</b>{db2}</div>"
                    f"<div style='color:rgba(160,200,240,.6);font-size:12px;margin-top:2px'>"
                    f"{t['priority']}{cotxt}"
                    f"{' · ' + t['description'][:50] if t.get('description') else ''}</div></div>",
                    unsafe_allow_html=True)
            with ta1:
                if not is_dn:
                    if st.button("✅", key=f"tdc_{t['id']}"):
                        db.complete_todo(t["id"]); invalidate_caches(); st.rerun()
                else:
                    if st.button("↩️", key=f"tdr_{t['id']}"):
                        db.reopen_todo(t["id"]); invalidate_caches(); st.rerun()
            with ta2:
                if st.button("🗑️", key=f"tdd_{t['id']}"):
                    db.delete_todo(t["id"]); invalidate_caches(); st.rerun()


# ─────────────────────────────────────────────
# SEKME 8 — GLOBAL ARAMA
# ─────────────────────────────────────────────

def tab_global_search():
    st.markdown('<div class="section-title" style="font-size:15px">🔎 Teknik Kayitlarda Arama</div>',
                unsafe_allow_html=True)
    st.caption("Faaliyet notları, firma adları, konular veya kategorilerde kelime bazlı arama yapın.")

    query = st.text_input("",
        placeholder="🔍  BT faaliyet notlarında ara... (Örn: update, AD, firewall, disk)",
        key="gq", label_visibility="collapsed")

    if not query or len(query.strip()) < 2:
        st.markdown(
            "<div style='text-align:center;padding:50px 20px;color:rgba(160,200,240,.55)'>"
            "<div style='font-size:48px;margin-bottom:12px'>🔍</div>"
            "<div style='font-size:15px;font-weight:600;color:rgba(190,220,250,.85)'>Aramak istediğiniz teknik ifadeyi girin</div>"
            "<div style='font-size:12.5px;margin-top:6px;max-width:320px;margin-left:auto;margin-right:auto'>"
            "Tüm çalışma notları, firma adları, işlem başlıkları ve kategorilerde arama yapılır."
            "</div></div>", unsafe_allow_html=True)
        return

    with st.spinner("Teknik kayıtlar aranıyor…"):
        results = db.global_search(query.strip())

    if not results:
        st.markdown(
            f"<div style='text-align:center;padding:36px;color:rgba(160,200,240,.5)'>"
            f"<div style='font-size:38px;margin-bottom:8px'>😕</div>"
            f"<div style='font-size:14px;color:rgba(200,225,255,.7)'>"
            f"<b>\"{query}\"</b> için eşleşen kayıt bulunamadı.</div>"
            f"<div style='font-size:12px;margin-top:4px'>Lütfen farklı teknik anahtar kelimeler deneyin.</div></div>",
            unsafe_allow_html=True)
        return

    st.markdown(
        f"<div style='color:#60B4FF;font-weight:600;font-size:13.5px;margin-bottom:12px'>"
        f"🎯 <b>{len(results)}</b> teknik kayıt bulundu — \"<em>{query}</em>\"</div>",
        unsafe_allow_html=True)

    q_low = query.lower()
    for r in results:
        mf = []
        if q_low in (r.get("company") or "").lower():    mf.append("Firma")
        if q_low in (r.get("subject") or "").lower():    mf.append("Konu")
        if q_low in (r.get("work_notes") or "").lower(): mf.append("Teknik Not")
        if q_low in (r.get("contact") or "").lower():    mf.append("İletişim")
        if q_low in (r.get("technician") or "").lower(): mf.append("Kategori")
        badges_html = " ".join(
            f"<span style='background:rgba(33,150,243,.12);color:#90CAF9;"
            f"border:1px solid rgba(33,150,243,.22);border-radius:4px;padding:1px 6px;font-size:10.5px'>{f}</span>"
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
            f"<span style='font-size:14.5px;font-weight:700'>{ch_hl}</span>"
            f"<span style='color:rgba(160,200,240,.45);font-size:11.5px;white-space:nowrap'>"
            f"#{r['id']:03d} · 📅 {fmt_date(r['visit_date'])}</span></div>"
            f"<div style='margin-top:4px;color:#B0C8E0;font-size:12.5px'>📌 {sub_hl}"
            f"{'&nbsp;·&nbsp;⚡ '+r['technician'] if r.get('technician') else ''}</div>"
            f"<div style='margin-top:6px'>{badges_html}</div>"
            + (f"<div style='margin-top:8px;background:rgba(255,255,255,.03);border-radius:8px;"
               f"padding:8px 12px;font-size:12px;color:rgba(160,200,240,.7);font-style:italic'>{snippet}</div>"
               if snippet else "")
            + "</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SEKME 9 — BT ENVANTER DEFTERI
# ─────────────────────────────────────────────

def tab_inventory():
    st.markdown('<div class="section-title" style="font-size:15px">🔑 Firma IP & BT Envanter Defteri</div>', unsafe_allow_html=True)
    cos = cached_companies()
    
    col_sel, col_add = st.columns([2, 1], gap="medium")
    
    with col_sel:
        if cos:
            sel_co = st.selectbox("📂 Kayitli Firma Secin", [""] + cos, key="inv_co_select")
        else:
            sel_co = ""
            st.info("💡 Henuz kayitli firma yok. Once faaliyet kaydi ekleyin veya yeni envanter tanimlayin.")
            
    with col_add:
        new_co = st.text_input("➕ Veya Yeni Firma Tanimla:", placeholder="Yeni firma adi...")
    
    active_co = new_co.strip() or sel_co
    
    if active_co:
        notes = db.get_company_notes(active_co)
        
        with st.form(f"inv_form_{active_co}"):
            st.markdown(f"### 🏢 {active_co} — BT Altyapi ve Erisim Bilgileri")
            ip_subnet = st.text_input("🌐 IP Bloklari / Local Subnet", value=notes.get("ip_subnet", "") if notes else "", placeholder="Orn: 192.168.10.0/24, Gateway: 10.1")
            vpn_details = st.text_area("🔒 VPN / Uzak Baglanti Bilgileri", value=notes.get("vpn_details", "") if notes else "", placeholder="Orn: SSL VPN adresi, Cisco AnyConnect, AnyDesk ID...")
            credentials = st.text_area("🔑 Cihaz & Giris Bilgileri / Notlar", value=notes.get("credentials", "") if notes else "", placeholder="Orn: Firewall Admin, Switch IP ve erisim portlari...")
            other_notes = st.text_area("📝 Diger BT Notlari", value=notes.get("other_notes", "") if notes else "", placeholder="Orn: BT Sorumlusu Iletisim, Lisans tarihleri...")
            
            sub_save, sub_del = st.columns(2)
            with sub_save:
                save_btn = st.form_submit_button("💾 Bilgileri Kaydet", type="primary", use_container_width=True)
            with sub_del:
                del_btn = st.form_submit_button("🗑️ Notlari Sil", use_container_width=True)
                
            if save_btn:
                db.save_company_notes(active_co, ip_subnet, vpn_details, credentials, other_notes)
                invalidate_caches()
                st.success(f"✅ {active_co} BT envanter bilgileri basariyla kaydedildi!")
                st.rerun()
                
            if del_btn:
                db.delete_company_notes(active_co)
                invalidate_caches()
                st.warning(f"🗑️ {active_co} envanter bilgileri silindi.")
                st.rerun()
    else:
        st.info("💡 Bilgilerini goruntulemek veya duzenlemek istediginiz firmayi yukaridan secin veya yeni bir tane girin.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📂 Tum Firma BT Notlari Hizli Listesi</div>', unsafe_allow_html=True)
    all_notes = db.get_all_company_notes()
    if all_notes:
        for n in all_notes:
            with st.expander(f"🏢 {n['company']} — En Son Guncelleme: {n.get('updated_at', '—')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🌐 Local Subnet:** `{n.get('ip_subnet') or '—'}`")
                    st.markdown(f"**🔒 VPN / Erisim:**\n```\n{n.get('vpn_details') or '—'}\n```")
                with c2:
                    st.markdown(f"**🔑 Erisim Bilgileri:**\n```\n{n.get('credentials') or '—'}\n```")
                    st.markdown(f"**📝 Diger Notlar:** {n.get('other_notes') or '—'}")
    else:
        st.caption("Henuz envanter defterinde kayit bulunmuyor.")


# ─────────────────────────────────────────────
# SEKME 10 — SISTEM YEDEKLER
# ─────────────────────────────────────────────

def tab_backups():
    st.markdown('<div class="section-title" style="font-size:15px">💾 Veri Transferi, Yedekleme ve Sistem Yönetimi</div>', unsafe_allow_html=True)
    
    # ── 1. CİHAZLAR ARASI VERİ TRANSFERİ (EXPORT / IMPORT) ──
    st.markdown("### 🌐 Cihazlar Arası Veri Transferi (Farklı PC'ye Taşıma)")
    st.caption("Tüm kayıtlarınızı, firmalarınızı, yapılacakları, hatırlatıcıları ve ayarlarınızı tek bir dosya ile başka bir bilgisayara taşıyabilirsiniz.")
    
    col_exp, col_imp = st.columns(2, gap="large")
    
    with col_exp:
        st.markdown("""
        <div style='background:rgba(33,150,243,0.05); border:1px solid rgba(33,150,243,0.2); border-radius:14px; padding:16px;'>
            <h4 style='margin:0 0 8px 0; color:#60B4FF;'>📤 Tüm Verileri Dışa Aktar</h4>
            <p style='font-size:12px; color:rgba(180,210,240,0.7); margin-bottom:12px;'>
                Mevcut tüm verilerinizi tek bir <b>JSON paket dosyası</b> olarak bilgisayarınıza indirir.
            </p>
        """, unsafe_allow_html=True)
        
        json_data = db.export_data_json()
        ts_now = datetime.now().strftime("%Y%m%d_%H%M")
        
        st.download_button(
            label="📥 Tüm Verileri Paket Olarak İndir (.json)",
            data=json_data,
            file_name=f"IT_Saha_Takip_PaketYedek_{ts_now}.json",
            mime="application/json",
            use_container_width=True,
            type="primary"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_imp:
        st.markdown("""
        <div style='background:rgba(76,175,80,0.05); border:1px solid rgba(76,175,80,0.2); border-radius:14px; padding:16px;'>
            <h4 style='margin:0 0 8px 0; color:#81C784;'>📥 Başka Cihazdan Veri İçe Aktar</h4>
            <p style='font-size:12px; color:rgba(180,210,240,0.7); margin-bottom:12px;'>
                Başka bir PC'den indirdiğiniz <b>.json yedek paketini</b> seçin ve yükleyin.
            </p>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Yedek Dosyası Seç (.json)", type=["json"], key="json_import_uploader")
        
        if uploaded_file is not None:
            import_mode = st.radio("İçe Aktarım Modu", [
                "🔄 Birleştir (Çift Kayıtları Atla - Güvenli)",
                "⚠️ Üzerine Yaz (Tüm Yerel Verileri Sil ve Yükle)"
            ], index=0)
            
            mode_code = "overwrite" if "Üzerine Yaz" in import_mode else "merge"
            
            if st.button("🚀 Verileri Veritabanına Yükle", type="primary", use_container_width=True):
                file_content = uploaded_file.getvalue().decode("utf-8")
                success, msg = db.import_data_json(file_content, mode=mode_code)
                if success:
                    invalidate_caches()
                    st.success(f"🎉 {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
                    
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin: 30px 0;'>", unsafe_allow_html=True)
    
    # ── 2. LOKAL DİSK YEDEKLEME ──
    st.markdown("### 💾 Bu Bilgisayardaki Otomatik SQLite Yedeği")
    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        st.markdown("#### 💾 Yeni Disk Yedeği Oluştur")
        st.write("Veritabanı dosyasının tam bir kopyasını backups/ klasörüne kaydeder.")
        if st.button("💾 Veritabanını Şimdi Yedekle", type="secondary", use_container_width=True):
            fn = db.create_backup()
            st.success(f"✅ Yeni yedek başarıyla oluşturuldu: {fn}")
            st.rerun()
            
    with c2:
        st.markdown("#### 📋 Mevcut Sistem Yedekleri")
        backups = db.list_backups()
        if not backups:
            st.info("📭 Henüz oluşturulmuş bir yedek dosyası bulunmuyor.")
        else:
            for b in backups:
                bc1, bc2, bc3 = st.columns([3, 1, 1])
                with bc1:
                    st.markdown(
                        f"<div class='card' style='margin:0 0 4px; padding:10px 14px'>"
                        f"📁 <b>{b['filename']}</b><br>"
                        f"<small style='color:rgba(160,200,240,.6)'>Tarih: {b['date']} · Boyut: {b['size']}</small></div>",
                        unsafe_allow_html=True
                    )
                with bc2:
                    if st.button("↩️ Geri Yükle", key=f"rest_{b['filename']}", help="Bu yedek dosyasını aktif veritabanı olarak geri yükler"):
                        if db.restore_backup(b['filename']):
                            invalidate_caches()
                            st.success("✅ Veritabanı yedekten başarıyla geri yüklendi! Sayfa yenileniyor...")
                            st.rerun()
                with bc3:
                    if st.button("🗑️ Sil", key=f"del_bak_{b['filename']}", help="Yedek dosyasını kalıcı olarak siler"):
                        if db.delete_backup(b['filename']):
                            st.warning("🗑️ Yedek dosyası silindi.")
                            st.rerun()


# ─────────────────────────────────────────────
# ANA UYGULAMA
# ─────────────────────────────────────────────

def main():
    # ── Session State Kontrolleri ──
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "🏠 Özet & Analiz"
    if "show_sidebar" not in st.session_state:
        st.session_state.show_sidebar = True

    # ── RENDER YARDIMCISI ──
    def render_active_tab(tab_name):
        if tab_name == "🏠 Özet & Analiz":
            tab_dashboard()
        elif tab_name == "➕ Yeni BT Kaydı":
            tab_new_visit()
        elif tab_name == "📊 Raporlama & Sunum":
            tab_reports()
        elif tab_name == "📧 E-Posta Gönder":
            tab_email_report()
        elif tab_name == "🔑 BT Envanter Defteri":
            tab_inventory()
        elif tab_name == "🗂️ Tüm Günlükler":
            tab_all_records()
        elif tab_name == "🔔 Hatırlatıcılarım":
            tab_reminders()
        elif tab_name == "🗓️ Faaliyet Takvimi":
            tab_calendar()
        elif tab_name == "📋 Görev Listem":
            tab_todos()
        elif tab_name == "🔎 Detaylı Arama":
            tab_global_search()
        elif tab_name == "💾 Sistem Yedekleme":
            tab_backups()

    # ── ÜST BAŞLIK & KONTROLLER ──
    # Başlık ve Menü Açma/Kapama butonu tek satırda şık bir şekilde listelenir
    col_head_left, col_head_right = st.columns([8.2, 1.8])
    with col_head_left:
        app_header()
    with col_head_right:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        toggle_lbl = "📂 Menüyü Kapat" if st.session_state.show_sidebar else "📂 Menüyü Göster"
        if st.button(toggle_lbl, key="nav_sidebar_toggle", type="secondary"):
            st.session_state.show_sidebar = not st.session_state.show_sidebar
            st.rerun()

    # ── DİNAMİK YERLEŞİM (SÜTUN SİSTEMİ) ──
    if st.session_state.show_sidebar:
        col_nav, col_content = st.columns([1.1, 3.8], gap="medium")
        
        with col_nav:
            st.markdown('<div class="nav-container">', unsafe_allow_html=True)
            st.markdown('<p style="font-size:10.5px; color:rgba(180,210,240,0.4); font-weight:600; text-transform:uppercase; letter-spacing:0.06em; margin: 0 0 10px 0;">NAVİGASYON</p>', unsafe_allow_html=True)
            
            menu_items = [
                ("🏠 Özet & Analiz", "🏠 Özet & Analiz"),
                ("➕ Yeni BT Kaydı", "➕ Yeni BT Kaydı"),
                ("📊 Raporlama & Sunum", "📊 Raporlama & Sunum"),
                ("📧 E-Posta Gönder", "📧 E-Posta Gönder"),
                ("🔑 BT Envanter Defteri", "🔑 BT Envanter Defteri"),
                ("🗂️ Tüm Günlükler", "🗂️ Tüm Günlükler"),
                ("🔔 Hatırlatıcılarım", "🔔 Hatırlatıcılarım"),
                ("🗓️ Faaliyet Takvimi", "🗓️ Faaliyet Takvimi"),
                ("📋 Görev Listem", "📋 Görev Listem"),
                ("🔎 Detaylı Arama", "🔎 Detaylı Arama"),
                ("💾 Sistem Yedekleme", "💾 Sistem Yedekleme")
            ]
            
            for label, tab_name in menu_items:
                is_active = st.session_state.active_tab == tab_name
                btn_type = "primary" if is_active else "secondary"
                if st.button(label, key=f"nav_btn_{tab_name}", type=btn_type):
                    st.session_state.active_tab = tab_name
                    st.rerun()

            # Sol panel altındaki sistem durumu kartı
            due_r = cached_due_reminders()
            td_stats = cached_todo_stats()
            status_html = ""
            if due_r:
                status_html += f"<div style='font-size:11px; color:#EF5350; margin-bottom:5px;'>🔔 {len(due_r)} Hatırlatıcı</div>"
            if td_stats.get("overdue", 0):
                status_html += f"<div style='font-size:11px; color:#FF9800; margin-bottom:5px;'>📋 {td_stats['overdue']} Gecikmiş</div>"
            if not due_r and not td_stats.get("overdue", 0):
                status_html += "<div style='font-size:11px; color:#66BB6A; font-weight:500;'>✅ Tüm işler güncel!</div>"
                
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 12px; margin-top:16px;'>
                <span style='font-size:9.5px; color:rgba(180,210,240,0.4); font-weight:600; text-transform:uppercase; letter-spacing:0.05em;'>SİSTEM DURUMU</span>
                <div style='margin-top:5px;'>{status_html}</div>
            </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_content:
            render_active_tab(st.session_state.active_tab)
            
    else:
        # Menü gizliyken içerik tam ekran genişliğinde gösterilir
        render_active_tab(st.session_state.active_tab)


if __name__ == "__main__":
    main()
