import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard UMKM SLS — Kab. Ciamis",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0f766e 0%, #134e4a 50%, #1e293b 100%);
        padding: 2rem 2.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(20,184,166,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -40%;
        left: 10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(245,158,11,0.1) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        color: #f0fdfa;
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #99f6e4;
        font-size: 0.9rem;
        margin: 0;
        font-weight: 500;
    }

    /* Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.875rem;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    .metric-card .metric-icon {
        width: 42px;
        height: 42px;
        border-radius: 0.625rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 0.75rem;
    }
    .metric-card .metric-label {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
    }
    .metric-card .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1;
    }
    .metric-card .metric-sub {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 0.35rem;
        font-weight: 500;
    }
    .metric-card.accent-bar::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
    }

    /* Chart container */
    .chart-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 0.875rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chart-box h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 0.15rem 0;
    }
    .chart-box .chart-subtitle {
        font-size: 0.78rem;
        color: #94a3b8;
        margin: 0 0 1rem 0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f766e 0%, #134e4a 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #ccfbf1 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #99f6e4 !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 0.5rem !important;
        color: #f0fdfa !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: rgba(255,255,255,0.35) !important;
    }
    [data-testid="stSidebar"] section {
        background: transparent !important;
        border: none !important;
    }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f0fdfa !important;
    }

    /* Table */
    .dataframe th {
        background: #0f766e !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.03em !important;
        border: none !important;
    }
    .dataframe td {
        font-size: 0.82rem !important;
        color: #334155 !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    .dataframe tr:hover td {
        background: #f0fdfa !important;
    }

    /* Section title */
    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin: 1.5rem 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-title::before {
        content: '';
        width: 4px;
        height: 20px;
        background: linear-gradient(180deg, #0f766e, #14b8a6);
        border-radius: 2px;
    }

    /* Divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 1.5rem 0;
    }

    /* Progress bar custom */
    .progress-container {
        background: #f1f5f9;
        border-radius: 999px;
        height: 8px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .progress-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s ease;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# DATA FETCHING & PROCESSING
# ============================================================
@st.cache_data(ttl=300, show_spinner="Memuat data dari server...")
def fetch_data():
    url = "https://simpul-jabar.32net.id/api/umkm-sls-by-kab/3207"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


STATUS_COLUMNS = [
    "APPROVED BY Pengawas",
    "SUBMITTED BY Pencacah",
    "OPEN",
    "EDITED BY Pengawas",
    "REJECTED BY Pengawas",
    "REVOKED BY Pengawas",
    "DRAFT",
    "SUBMITTED RESPONDENT",
]

STATUS_LABELS = {
    "APPROVED BY Pengawas": "Approved",
    "SUBMITTED BY Pencacah": "Submitted Pencacah",
    "OPEN": "Open",
    "EDITED BY Pengawas": "Edited",
    "REJECTED BY Pengawas": "Rejected",
    "REVOKED BY Pengawas": "Revoked",
    "DRAFT": "Draft",
    "SUBMITTED RESPONDENT": "Submitted Respondent",
}

STATUS_COLORS = {
    "Approved": "#10b981",
    "Submitted Pencacah": "#3b82f6",
    "Open": "#f59e0b",
    "Edited": "#8b5cf6",
    "Rejected": "#ef4444",
    "Revoked": "#6b7280",
    "Draft": "#06b6d4",
    "Submitted Respondent": "#ec4899",
}

STATUS_ICONS = {
    "TOTAL": ("📦", "#0f766e"),
    "APPROVED BY Pengawas": ("✅", "#10b981"),
    "SUBMITTED BY Pencacah": ("📤", "#3b82f6"),
    "OPEN": ("🔓", "#f59e0b"),
    "EDITED BY Pengawas": ("✏️", "#8b5cf6"),
    "REJECTED BY Pengawas": ("❌", "#ef4444"),
    "REVOKED BY Pengawas": ("🚫", "#6b7280"),
    "DRAFT": ("📝", "#06b6d4"),
    "SUBMITTED RESPONDENT": ("👤", "#ec4899"),
}


def process_data(raw):
    df = pd.DataFrame(raw["data"])

    for col in STATUS_COLUMNS:
        df[col] = pd.to_numeric(df[col].replace("-", 0), errors="coerce").fillna(0).astype(int)

    df["tanggal"] = pd.to_datetime(df["tanggal"])

    df["kec_raw"] = df["kdkec"].astype(str)
    df["desa_raw"] = df["kddesa"].astype(str)
    df["sls_raw"] = df["kdsls"].astype(str)

    df["kec_code"] = df["kec_raw"].str.split(" - ").str[0].str.strip()
    df["kec_name"] = df["kec_raw"].str.split(" - ").str[1].str.strip()
    df["desa_code"] = df["desa_raw"].str.split(" - ").str[0].str.strip()
    df["desa_name"] = df["desa_raw"].str.split(" - ").str[1].str.strip()
    df["sls_code"] = df["sls_raw"].str.split(" - ").str[0].str.strip()
    df["sls_name"] = df["sls_raw"].str.split(" - ").str[1].str.strip()

    df["kec_label"] = df["kec_name"].str.title()
    df["desa_label"] = df["desa_name"].str.title()
    df["sls_label"] = df["sls_name"]

    return df


# ============================================================
# LOAD DATA
# ============================================================
try:
    raw = fetch_data()
    df = process_data(raw)
    DATA_LOADED = True
except Exception as e:
    st.error(f"❌ Gagal memuat data: {e}")
    DATA_LOADED = False
    st.stop()

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.markdown(
    """
<div style="padding: 1.5rem 1rem 0.5rem 1rem;">
    <h2 style="margin:0 0 0.25rem 0; font-size:1.15rem; font-weight:800;">🔍 Filter Wilayah</h2>
    <p style="margin:0; font-size:0.78rem; opacity:0.7;">Pilih tingkat wilayah untuk menyaring data</p>
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

kec_options = sorted(df["kec_raw"].unique())
selected_kec = st.sidebar.selectbox("Kecamatan", ["Semua Kecamatan"] + kec_options, index=0)

selected_desa = "Semua Desa/Kelurahan"
selected_sls = "Semua SLS"

if selected_kec != "Semua Kecamatan":
    df_kec = df[df["kec_raw"] == selected_kec]
    desa_options = sorted(df_kec["desa_raw"].unique())
    selected_desa = st.sidebar.selectbox("Desa/Kelurahan", ["Semua Desa/Kelurahan"] + desa_options, index=0)

    if selected_desa != "Semua Desa/Kelurahan":
        df_desa = df_kec[df_kec["desa_raw"] == selected_desa]
        sls_options = sorted(df_desa["sls_raw"].unique())
        selected_sls = st.sidebar.selectbox("SLS", ["Semua SLS"] + sls_options, index=0)
    else:
        sls_options = []

# Apply filter
if selected_kec != "Semua Kecamatan":
    df_f = df[df["kec_raw"] == selected_kec]
    if selected_desa != "Semua Desa/Kelurahan":
        df_f = df_f[df_f["desa_raw"] == selected_desa]
        if selected_sls != "Semua SLS":
            df_f = df_f[df_f["sls_raw"] == selected_sls]
else:
    df_f = df.copy()

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
<div style="padding: 0 1rem;">
    <div style="background:rgba(255,255,255,0.1); border-radius:0.75rem; padding:1rem;">
        <p style="margin:0 0 0.5rem 0; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em; opacity:0.7; font-weight:700;">Ringkasan Filter</p>
        <p style="margin:0 0 0.2rem 0; font-size:0.85rem; font-weight:600;">📊 Jumlah SLS: <b>{len(df_f)}</b></p>
        <p style="margin:0 0 0.2rem 0; font-size:0.85rem; font-weight:600;">📦 Total UMKM: <b>{df_f['TOTAL'].sum():,}</b></p>
        <p style="margin:0; font-size:0.85rem; font-weight:600;">✅ Approved: <b>{df_f['APPROVED BY Pengawas'].sum():,}</b></p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HEADER
# ============================================================
last_update = df["tanggal"].max().strftime("%d %B %Y, %H:%M WIB")

st.markdown(
    f"""
<div class="main-header">
    <h1>📊 Dashboard Monitoring UMKM SLS</h1>
    <p>Kabupaten Majalengka — Kode Kab: 3210 | Data diperbarui: {last_update}</p>
</div>
""",
    unsafe_allow_html=True,
)

# Breadcrumb filter info
filter_parts = []
if selected_kec != "Semua Kecamatan":
    filter_parts.append(selected_kec.split(" - ")[1].strip().title())
if selected_desa != "Semua Desa/Kelurahan":
    filter_parts.append(selected_desa.split(" - ")[1].strip().title())
if selected_sls != "Semua SLS":
    filter_parts.append(selected_sls.split(" - ")[1].strip())

if filter_parts:
    st.markdown(
        f"<p style='font-size:0.8rem; color:#64748b; margin:0 0 0.5rem 0.25rem;'>"
        f"📍 Kab. Majalengka {' > '.join(filter_parts)}</p>",
        unsafe_allow_html=True,
    )

# ============================================================
# METRIC CARDS
# ============================================================
total = int(df_f["TOTAL"].sum())
approved = int(df_f["APPROVED BY Pengawas"].sum())
submitted = int(df_f["SUBMITTED BY Pencacah"].sum())
open_count = int(df_f["OPEN"].sum())
edited = int(df_f["EDITED BY Pengawas"].sum())
rejected = int(df_f["REJECTED BY Pengawas"].sum())
revoked = int(df_f["REVOKED BY Pengawas"].sum())
draft = int(df_f["DRAFT"].sum())
resp = int(df_f["SUBMITTED RESPONDENT"].sum())
pct_approved = (approved / total * 100) if total > 0 else 0
pct_submitted = (submitted / total * 100) if total > 0 else 0

card_configs = [
    ("TOTAL", total, f"dari {len(df_f)} SLS tercatat", "#0f766e"),
    ("APPROVED BY Pengawas", approved, f"{pct_approved:.1f}% dari total", "#10b981"),
    ("SUBMITTED BY Pencacah", submitted, f"{pct_submitted:.1f}% dari total", "#3b82f6"),
    ("OPEN", open_count, f"{(open_count/total*100) if total else 0:.1f}% dari total", "#f59e0b"),
    ("EDITED BY Pengawas", edited, f"{(edited/total*100) if total else 0:.1f}% dari total", "#8b5cf6"),
    ("REJECTED BY Pengawas", rejected, f"{(rejected/total*100) if total else 0:.1f}% dari total", "#ef4444"),
    ("REVOKED BY Pengawas", revoked, f"{(revoked/total*100) if total else 0:.1f}% dari total", "#6b7280"),
    ("DRAFT", draft, f"{(draft/total*100) if total else 0:.1f}% dari total", "#06b6d4"),
    ("SUBMITTED RESPONDENT", resp, f"{(resp/total*100) if total else 0:.1f}% dari total", "#ec4899"),
]

cols = st.columns(len(card_configs))
for i, (key, value, sub, color) in enumerate(card_configs):
    icon, _ = STATUS_ICONS[key]
    label = STATUS_LABELS.get(key, key)
    with cols[i]:
        st.markdown(
            f"""
        <div class="metric-card accent-bar" style="border-bottom: 3px solid {color};">
            <div class="metric-icon" style="background: {color}15; color: {color};">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value:,}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# ============================================================
# PROGRESS BAR
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Progress Pengisian UMKM</div>', unsafe_allow_html=True)

progress_data = [
    ("Approved", approved, "#10b981"),
    ("Submitted", submitted, "#3b82f6"),
    ("Open / Belum Diisi", open_count, "#f59e0b"),
    ("Lainnya", total - approved - submitted - open_count, "#94a3b8"),
]

pcol1, pcol2 = st.columns([1, 2])
with pcol1:
    st.markdown(
        f"""
    <div style="text-align:center; padding:1rem;">
        <div style="font-size:2.5rem; font-weight:800; color:#0f766e; line-height:1;">{pct_approved:.1f}%</div>
        <div style="font-size:0.8rem; color:#64748b; margin-top:0.25rem;">Tingkat Kelengkapan</div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-top:0.15rem;">(Approved / Total)</div>
    </div>
    """,
        unsafe_allow_html=True,
    )
with pcol2:
    bar_parts = []
    for label, val, clr in progress_data:
        pct = (val / total * 100) if total > 0 else 0
        bar_parts.append(
            f'<div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.35rem;">'
            f'<div style="width:8px; height:8px; border-radius:50%; background:{clr}; flex-shrink:0;"></div>'
            f'<div style="width:140px; font-size:0.78rem; color:#475569; font-weight:500;">{label}</div>'
            f'<div style="flex:1; background:#f1f5f9; border-radius:999px; height:8px; overflow:hidden;">'
            f'<div style="width:{pct}%; height:100%; background:{clr}; border-radius:999px; transition:width 0.6s ease;"></div>'
            f'</div>'
            f'<div style="width:50px; text-align:right; font-size:0.78rem; color:#64748b; font-weight:600;">{val:,} <span style="color:#94a3b8;">({pct:.1f}%)</span></div>'
            f'</div>'
        )
    st.markdown(
        '<div style="padding: 0.75rem 0;">' + "".join(bar_parts) + "</div>",
        unsafe_allow_html=True,
    )

# ============================================================
# CHARTS ROW 1: Donut + Bar per Kecamatan
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Analisis Distribusi Status</div>', unsafe_allow_html=True)

# Prepare status summary
status_sum = {}
for col in STATUS_COLUMNS:
    label = STATUS_LABELS[col]
    status_sum[label] = int(df_f[col].sum())
status_df = pd.DataFrame(list(status_sum.items()), columns=["Status", "Jumlah"])
status_df = status_df[status_df["Jumlah"] > 0].sort_values("Jumlah", ascending=False)
status_df["Color"] = status_df["Status"].map(STATUS_COLORS)

ch1, ch2 = st.columns([1, 2])

with ch1:
    st.markdown(
        '<div class="chart-box"><h3>Komposisi Status</h3><p class="chart-subtitle">Proporsi tiap status pengisian</p></div>',
        unsafe_allow_html=True,
    )
    fig_donut = go.Figure(
        go.Pie(
            labels=status_df["Status"],
            values=status_df["Jumlah"],
            hole=0.62,
            marker=dict(colors=status_df["Color"], line=dict(color="#ffffff", width=2.5)),
            textinfo="percent",
            textfont=dict(size=11, color="#334155", family="Plus Jakarta Sans"),
            hovertemplate="<b>%{label}</b><br>Jumlah: %{value:,}<br>Persentase: %{percent}",
            sort=False,
        )
    )
    fig_donut.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#64748b", family="Plus Jakarta Sans"),
            itemwidth=25,
        ),
        margin=dict(t=10, b=10, l=10, r=10),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=f"<b>{total:,}</b><br><span style='font-size:10px;color:#94a3b8;'>Total UMKM</span>",
                x=0.5,
                y=0.5,
                font=dict(size=18, color="#0f172a", family="Plus Jakarta Sans"),
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with ch2:
    st.markdown(
        '<div class="chart-box"><h3>Status per Kecamatan</h3><p class="chart-subtitle">Perbandingan horizontal antar kecamatan</p></div>',
        unsafe_allow_html=True,
    )
    kec_group = (
        df_f.groupby("kec_label")[STATUS_COLUMNS].sum().reset_index()
    )
    kec_group_melted = kec_group.melt(
        id_vars="kec_label",
        value_vars=STATUS_COLUMNS,
        var_name="Status",
        value_name="Jumlah",
    )
    kec_group_melted["Status"] = kec_group_melted["Status"].map(STATUS_LABELS)
    kec_group_melted["Color"] = kec_group_melted["Status"].map(STATUS_COLORS)

    fig_bar = px.bar(
        kec_group_melted,
        x="Jumlah",
        y="kec_label",
        color="Status",
        orientation="h",
        color_discrete_map=STATUS_COLORS,
        title="",
    )
    fig_bar.update_layout(
        barmode="stack",
        xaxis_title="Jumlah UMKM",
        yaxis_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=9, color="#64748b"),
            itemwidth=20,
        ),
        margin=dict(t=5, b=60, l=5, r=5),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", size=11, color="#475569"),
        xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================
# CHARTS ROW 2: Top Kecamatan + Funnel
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Peringkat & Funnel Proses</div>', unsafe_allow_html=True)

ch3, ch4 = st.columns([1, 1])

with ch3:
    st.markdown(
        '<div class="chart-box"><h3>Top 10 Kecamatan (Total UMKM)</h3><p class="chart-subtitle">Kecamatan dengan jumlah UMKM terbanyak</p></div>',
        unsafe_allow_html=True,
    )
    kec_total = (
        df_f.groupby("kec_label")["TOTAL"]
        .sum()
        .reset_index()
        .sort_values("TOTAL", ascending=True)
        .tail(10)
    )
    fig_top = go.Figure(
        go.Bar(
            x=kec_total["TOTAL"],
            y=kec_total["kec_label"],
            orientation="h",
            marker=dict(
                color=kec_total["TOTAL"],
                colorscale=[
                    [0, "#ccfbf1"],
                    [0.5, "#14b8a6"],
                    [1, "#0f766e"],
                ],
                line=dict(color="#ffffff", width=1),
                cornerradius=4,
            ),
            text=kec_total["TOTAL"],
            textposition="outside",
            textfont=dict(size=10, color="#334155", family="Plus Jakarta Sans"),
            hovertemplate="<b>%{y}</b><br>Total: %{x:,}<extra></extra>",
        )
    )
    fig_top.update_layout(
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=5, b=10, l=5, r=40),
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", size=11, color="#475569"),
        xaxis=dict(gridcolor="#f1f5f9", zeroline=False, showticklabels=False),
        yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_top, use_container_width=True)

with ch4:
    st.markdown(
        '<div class="chart-box"><h3>Funnel Proses Pengisian</h3><p class="chart-subtitle">Alur dari Open hingga Approved</p></div>',
        unsafe_allow_html=True,
    )
    funnel_data = [
        ("Open", open_count, "#f59e0b"),
        ("Submitted Pencacah", submitted, "#3b82f6"),
        ("Edited Pengawas", edited, "#8b5cf6"),
        ("Approved", approved, "#10b981"),
    ]
    funnel_labels = [f[0] for f in funnel_data]
    funnel_values = [f[1] for f in funnel_data]
    funnel_colors = [f[2] for f in funnel_data]

    fig_funnel = go.Figure(
        go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textinfo="value+percent initial",
            textfont=dict(size=12, color="#ffffff", family="Plus Jakarta Sans"),
            marker=dict(color=funnel_colors, line=dict(color="#ffffff", width=2)),
            hovertemplate="<b>%{y}</b><br>Jumlah: %{x:,}<br>%{text}<extra></extra>",
        )
    )
    fig_funnel.update_layout(
        margin=dict(t=5, b=10, l=100, r=20),
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans"),
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

# ============================================================
# CHARTS ROW 3: Heatmap Kecamatan vs Status
# ============================================================
st.markdown("<div class="divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Heatmap & Distribusi per Desa</div>', unsafe_allow_html=True)

ch5, ch6 = st.columns([1, 1])

with ch5:
    st.markdown(
        '<div class="chart-box"><h3>Heatmap: Kecamatan × Status</h3><p class="chart-subtitle">Intensitas tiap status di setiap kecamatan</p></div>',
        unsafe_allow_html=True,
    )
    kec_heat = (
        df_f.groupby("kec_label")[STATUS_COLUMNS]
        .sum()
        .rename(columns=STATUS_LABELS)
    )
    # Sort by total descending
    kec_heat["_sort"] = kec_heat.sum(axis=1)
    kec_heat = kec_heat.sort_values("_sort", ascending=False).drop("_sort", axis=1)
    # Remove zero columns
    kec_heat = kec_heat.loc[:, (kec_heat != 0).any(axis=0)]

    fig_heat = go.Figure(
        go.Heatmap(
            z=kec_heat.values,
            x=kec_heat.columns,
            y=kec_heat.index,
            colorscale=[[0, "#f0fdfa"], [0.3, "#99f6e4"], [0.6, "#14b8a6"], [1, "#0f766e"]],
            text=kec_heat.values,
            texttemplate="%{text}",
            textfont=dict(size=10, color="#334155", family="Plus Jakarta Sans"),
            hovertemplate="<b>%{y}</b> — %{x}<br>Jumlah: %{z:,}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig_heat.update_layout(
        margin=dict(t=5, b=60, l=5, r=5),
        height=max(300, len(kec_heat) * 32 + 80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", size=10, color="#475569"),
        xaxis=dict(
            tickangle=35,
            side="bottom",
            tickfont=dict(size=9),
        ),
        yaxis=dict(tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with ch6:
    st.markdown(
        '<div class="chart-box"><h3>Distribusi per Desa</h3><p class="chart-subtitle">Treemap jumlah UMKM per desa</p></div>',
        unsafe_allow_html=True,
    )
    desa_total = (
        df_f.groupby(["kec_label", "desa_label"])["TOTAL"]
        .sum()
        .reset_index()
        .sort_values("TOTAL", ascending=False)
    )
    desa_total["label"] = desa_total["desa_label"] + "<br>" + desa_total["TOTAL"].astype(str)

    fig_treemap = px.treemap(
        desa_total,
        path=[px.Constant("Kab. Majalengka"), "kec_label", "desa_label"],
        values="TOTAL",
        color="TOTAL",
        color_continuous_scale=["#ccfbf1", "#14b8a6", "#0f766e"],
    )
    fig_treemap.update_layout(
        margin=dict(t=5, b=10, l=5, r=5),
        height=max(300, len(kec_heat) * 32 + 80),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans", size=10, color="#ffffff"),
        treemapcolorway=["#0f766e", "#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4", "#ccfbf1"],
    )
    fig_treemap.update_traces(
        textfont=dict(size=10),
        hovertemplate="<b>%{label}</b><br>Total: %{value:,}<extra></extra>",
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

# ============================================================
# DATA TABLE
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Tabel Detail Data SLS</div>', unsafe_allow_html=True)

# Search
search_term = st.text_input("🔍 Cari nama desa atau SLS...", placeholder="Ketik untuk mencari...", key="search_table")

# Prepare table data
table_cols = ["kec_label", "desa_label", "sls_label"] + STATUS_COLUMNS + ["TOTAL"]
table_df = df_f[table_cols].copy()
table_df.columns = ["Kecamatan", "Desa/Kelurahan", "SLS"] + [STATUS_LABELS[c] for c in STATUS_COLUMNS] + ["Total"]

if search_term:
    mask = table_df.apply(
        lambda row: row.astype(str).str.lower().str.contains(search_term.lower()).any(), axis=1
    )
    table_df = table_df[mask]

st.markdown(
    f'<p style="font-size:0.78rem; color:#64748b; margin:0 0 0.5rem 0.25rem;">Menampilkan {len(table_df)} dari {len(df_f)} data</p>',
    unsafe_allow_html=True,
)

# Styling
def highlight_status(val, col_name):
    if col_name == "Approved" and val > 0:
        return "background-color: #d1fae5; color: #065f46; font-weight: 600;"
    elif col_name == "Open" and val > 0:
        return "background-color: #fef3c7; color: #92400e; font-weight: 600;"
    elif col_name == "Rejected" and val > 0:
        return "background-color: #fee2e2; color: #991b1b; font-weight: 600;"
    return ""


styled = table_df.style.format("{:,}")
for col in [STATUS_LABELS[c] for c in STATUS_COLUMNS]:
    styled = styled.applymap(lambda v, c=col: highlight_status(v, c), subset=[col])
styled = styled.set_properties(**{"text-align": "center"}, subset=[STATUS_LABELS[c] for c in STATUS_COLUMNS] + ["Total"])
styled = styled.set_properties(**{"text-align": "left"}, subset=["Kecamatan", "Desa/Kelurahan", "SLS"])

st.dataframe(
    styled,
    use_container_width=True,
    height=450,
    hide_index=True,
)

# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(
    """
<div style="text-align:center; padding:1rem 0;">
    <p style="font-size:0.78rem; color:#94a3b8; margin:0;">
        🏗️ Dashboard UMKM SLS — Kabupaten Majalengka | Sumber: simpul-jabar.32net.id
    </p>
    <p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">
        Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.
    </p>
</div>
""",
    unsafe_allow_html=True,
)