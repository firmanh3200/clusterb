import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard UMKM SLS — Ciamis",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    .landing-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; text-align: center; padding: 2rem; }
    .landing-icon { font-size: 4rem; margin-bottom: 1.5rem; animation: float 3s ease-in-out infinite; }
    @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-10px); } }
    .landing-title { font-size: 2.25rem; font-weight: 800; color: #0f172a; margin: 0 0 0.5rem 0; letter-spacing: -0.03em; }
    .landing-subtitle { font-size: 1rem; color: #64748b; margin: 0 0 2.5rem 0; font-weight: 500; max-width: 500px; }
    .landing-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 1.25rem; padding: 2.5rem; box-shadow: 0 4px 24px rgba(0,0,0,0.06); width: 100%; max-width: 480px; }
    .landing-card label { font-size: 0.8rem; font-weight: 700; color: #0f766e; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.5rem; display: block; text-align: left; }
    .landing-card .stSelectbox > div > div { border-radius: 0.75rem !important; border: 2px solid #e2e8f0 !important; padding: 0.65rem 1rem !important; font-size: 0.95rem !important; font-weight: 600 !important; }
    .landing-footer { margin-top: 3rem; font-size: 0.78rem; color: #94a3b8; }
    .landing-footer a { color: #0f766e; text-decoration: none; font-weight: 600; }

    .main-header { background: linear-gradient(135deg, #0f766e 0%, #134e4a 50%, #1e293b 100%); padding: 1.5rem 2.5rem; border-radius: 1rem; margin-bottom: 1.5rem; position: relative; overflow: hidden; }
    .main-header::before { content: ''; position: absolute; top: -50%; right: -20%; width: 400px; height: 400px; background: radial-gradient(circle, rgba(20,184,166,0.15) 0%, transparent 70%); border-radius: 50%; }
    .main-header::after { content: ''; position: absolute; bottom: -40%; left: 10%; width: 300px; height: 300px; background: radial-gradient(circle, rgba(245,158,11,0.1) 0%, transparent 70%); border-radius: 50%; }
    .main-header h1 { color: #f0fdfa; font-size: 1.75rem; font-weight: 800; margin: 0 0 0.25rem 0; letter-spacing: -0.02em; }
    .main-header p { color: #99f6e4; font-size: 0.9rem; margin: 0; font-weight: 500; }
    .btn-ganti { display: inline-block; margin-top: 0.75rem; padding: 0.4rem 1rem; background: rgba(255,255,255,0.15); color: #ccfbf1; border: 1px solid rgba(255,255,255,0.2); border-radius: 0.5rem; font-size: 0.78rem; font-weight: 600; cursor: pointer; text-decoration: none; }
    .btn-ganti:hover { background: rgba(255,255,255,0.25); }

    .metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0.875rem; padding: 1.25rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03); transition: all 0.25s ease; position: relative; overflow: hidden; }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
    .metric-card .metric-icon { width: 42px; height: 42px; border-radius: 0.625rem; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; margin-bottom: 0.75rem; }
    .metric-card .metric-label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
    .metric-card .metric-value { font-size: 1.75rem; font-weight: 800; color: #0f172a; line-height: 1; }
    .metric-card .metric-sub { font-size: 0.72rem; color: #94a3b8; margin-top: 0.35rem; font-weight: 500; }
    [data-testid="stHorizontalBlock"] .stHorizontalBlock { gap: 0.75rem !important; }

    .filter-bar { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0.875rem; padding: 1.25rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03); margin-bottom: 1.5rem; }
    .filter-bar .filter-title { font-size: 0.78rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.4rem; }
    .filter-bar .filter-summary { display: flex; gap: 1.5rem; margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #f1f5f9; flex-wrap: wrap; }
    .filter-bar .filter-summary-item { font-size: 0.78rem; color: #475569; font-weight: 500; }
    .filter-bar .filter-summary-item b { color: #0f766e; font-weight: 700; }

    .chart-box { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0.875rem; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
    .chart-box h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.15rem 0; }
    .chart-box .chart-subtitle { font-size: 0.78rem; color: #94a3b8; margin: 0 0 1rem 0; }

    .section-title { font-size: 1.05rem; font-weight: 700; color: #0f172a; margin: 1.5rem 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem; }
    .section-title::before { content: ''; width: 4px; height: 20px; background: linear-gradient(180deg, #0f766e, #14b8a6); border-radius: 2px; }
    .divider { height: 1px; background: linear-gradient(90deg, transparent, #e2e8f0, transparent); margin: 1.5rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# INISIALISASI VARIABEL DASHBOARD
# ============================================================
KODE_TERPILIH = "3207"
NAMA_TERPILIH = "Kabupaten Ciamis"
URL_API = f"https://simpul-jabar.32net.id/api/umkm-sls-by-kab/{KODE_TERPILIH}"

STATUS_COLUMNS = ["APPROVED BY Pengawas","SUBMITTED BY Pencacah","OPEN","EDITED BY Pengawas","REJECTED BY Pengawas","REVOKED BY Pengawas","DRAFT","SUBMITTED RESPONDENT"]
STATUS_LABELS = {"APPROVED BY Pengawas":"Approved","SUBMITTED BY Pencacah":"Submitted Pencacah","OPEN":"Open","EDITED BY Pengawas":"Edited","REJECTED BY Pengawas":"Rejected","REVOKED BY Pengawas":"Revoked","DRAFT":"Draft","SUBMITTED RESPONDENT":"Submitted Respondent"}
STATUS_COLORS = {"Approved":"#10b981","Submitted Pencacah":"#3b82f6","Open":"#f59e0b","Edited":"#8b5cf6","Rejected":"#ef4444","Revoked":"#6b7280","Draft":"#06b6d4","Submitted Respondent":"#ec4899"}
STATUS_ICONS = {"TOTAL":("📦","#0f766e"),"APPROVED BY Pengawas":("✅","#10b981"),"SUBMITTED BY Pencacah":("📤","#3b82f6"),"OPEN":("🔓","#f59e0b"),"EDITED BY Pengawas":("✏️","#8b5cf6"),"REJECTED BY Pengawas":("❌","#ef4444"),"REVOKED BY Pengawas":("🚫","#6b7280"),"DRAFT":("📝","#06b6d4"),"SUBMITTED RESPONDENT":("👤","#ec4899")}

def process_data(raw):
    df = pd.DataFrame(raw["data"])
    for col in STATUS_COLUMNS: df[col] = pd.to_numeric(df[col].replace("-", 0), errors="coerce").fillna(0).astype(int)
    df["tanggal"] = pd.to_datetime(df["tanggal"])
    df["kec_raw"] = df["kdkec"].astype(str); df["desa_raw"] = df["kddesa"].astype(str); df["sls_raw"] = df["kdsls"].astype(str)
    df["kec_name"] = df["kec_raw"].str.split(" - ").str[1].str.strip(); df["desa_name"] = df["desa_raw"].str.split(" - ").str[1].str.strip(); df["sls_name"] = df["sls_raw"].str.split(" - ").str[1].str.strip()
    df["kec_label"] = df["kec_name"].str.title(); df["desa_label"] = df["desa_name"].str.title(); df["sls_label"] = df["sls_name"]
    return df

@st.cache_data(ttl=300)
def fetch_data():
    resp = requests.get(URL_API, timeout=30)
    resp.raise_for_status()
    return resp.json()

try:
    raw = fetch_data()
    df = process_data(raw)
except Exception as e:
    st.error(f"Gagal memuat data: {e}")
    st.stop()

# ============================================================
# HEADER & FILTER UTAMA
# ============================================================
last_update = df["tanggal"].max().strftime("%d %B %Y, %H:%M WIB")
st.markdown(f"""<div class="main-header"><h1>📊 Dashboard Monitoring UMKM SLS</h1><p>{NAMA_TERPILIH} — Kode: {KODE_TERPILIH} | Data diperbarui: {last_update}</p><a href="javascript:void(0)" onclick="document.querySelector('[data-testid=\"stBaseButton-secondary\"]')?.click();" class="btn-ganti">↩ Ganti Wilayah</a></div>""", unsafe_allow_html=True)

if st.button("Ganti Wilayah", key="btn_ganti_hidden"):
    st.session_state.selected_kab = None
    st.rerun()

kec_options = sorted(df["kec_raw"].unique())
fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    selected_kec = st.selectbox("Kecamatan", ["Semua Kecamatan"] + kec_options, index=0, label_visibility="collapsed")
    st.markdown(f'<div style="font-size:0.72rem;color:{"#0f766e" if selected_kec != "Semua Kecamatan" else "#64748b"};margin-top:-0.75rem;margin-bottom:0.5rem;">📍 {selected_kec if selected_kec != "Semua Kecamatan" else "Semua Kecamatan"}</div>', unsafe_allow_html=True)

selected_desa = "Semua Desa/Kelurahan"; selected_sls = "Semua SLS"
with fcol2:
    if selected_kec != "Semua Kecamatan":
        df_kec = df[df["kec_raw"] == selected_kec]; desa_options = sorted(df_kec["desa_raw"].unique())
        selected_desa = st.selectbox("Desa/Kelurahan", ["Semua Desa/Kelurahan"] + desa_options, index=0, label_visibility="collapsed")
        st.markdown(f'<div style="font-size:0.72rem;color:{"#0f766e" if selected_desa != "Semua Desa/Kelurahan" else "#64748b"};margin-top:-0.75rem;margin-bottom:0.5rem;">🏘️ {selected_desa if selected_desa != "Semua Desa/Kelurahan" else "Semua Desa/Kelurahan"}</div>', unsafe_allow_html=True)
    else:
        st.selectbox("Desa/Kelurahan", ["Semua Desa/Kelurahan"], index=0, label_visibility="collapsed", disabled=True)
        st.markdown('<div style="font-size:0.72rem;color:#cbd5e1;margin-top:-0.75rem;margin-bottom:0.5rem;">🏘️ Pilih kec. terlebih dahulu</div>', unsafe_allow_html=True)

with fcol3:
    if selected_kec != "Semua Kecamatan" and selected_desa != "Semua Desa/Kelurahan":
        df_desa = df_kec[df_kec["desa_raw"] == selected_desa]; sls_options = sorted(df_desa["sls_raw"].unique())
        selected_sls = st.selectbox("SLS", ["Semua SLS"] + sls_options, index=0, label_visibility="collapsed")
        st.markdown(f'<div style="font-size:0.72rem;color:{"#0f766e" if selected_sls != "Semua SLS" else "#64748b"};margin-top:-0.75rem;margin-bottom:0.5rem;">📋 {selected_sls if selected_sls != "Semua SLS" else "Semua SLS"}</div>', unsafe_allow_html=True)
    else:
        st.selectbox("SLS", ["Semua SLS"], index=0, label_visibility="collapsed", disabled=True)
        st.markdown('<div style="font-size:0.72rem;color:#cbd5e1;margin-top:-0.75rem;margin-bottom:0.5rem;">📋 Pilih desa terlebih dahulu</div>', unsafe_allow_html=True)

if selected_kec != "Semua Kecamatan":
    df_f = df[df["kec_raw"] == selected_kec]
    if selected_desa != "Semua Desa/Kelurahan":
        df_f = df_f[df_f["desa_raw"] == selected_desa]
        if selected_sls != "Semua SLS": df_f = df_f[df_f["sls_raw"] == selected_sls]
else: df_f = df.copy()

filter_parts = [NAMA_TERPILIH]
if selected_kec != "Semua Kecamatan": filter_parts.append(selected_kec.split(" - ")[1].strip().title())
if selected_desa != "Semua Desa/Kelurahan": filter_parts.append(selected_desa.split(" - ")[1].strip().title())
if selected_sls != "Semua SLS": filter_parts.append(selected_sls.split(" - ")[1].strip())

total_preview = int(df_f["TOTAL"].sum()); approved_preview = int(df_f["APPROVED BY Pengawas"].sum())
st.markdown(f"""<div class="filter-bar"><div class="filter-title">🔍 Filter Aktif</div><div style="font-size:0.82rem; color:#334155; font-weight:600; margin-bottom:0.5rem;">📍 {' > '.join(filter_parts)}</div><div class="filter-summary"><div class="filter-summary-item">📊 Jumlah SLS: <b>{len(df_f):,}</b></div><div class="filter-summary-item">📦 Total UMKM: <b>{total_preview:,}</b></div><div class="filter-summary-item">✅ Approved: <b>{approved_preview:,}</b></div><div class="filter-summary-item">📈 Tingkat Kelengkapan: <b>{(approved_preview/total_preview*100) if total_preview else 0:.1f}%</b></div></div></div>""", unsafe_allow_html=True)

# ============================================================
# METRIC CARDS
# ============================================================
total = int(df_f["TOTAL"].sum()); approved = int(df_f["APPROVED BY Pengawas"].sum()); submitted = int(df_f["SUBMITTED BY Pencacah"].sum()); open_count = int(df_f["OPEN"].sum()); edited = int(df_f["EDITED BY Pengawas"].sum()); rejected = int(df_f["REJECTED BY Pengawas"].sum()); revoked = int(df_f["REVOKED BY Pengawas"].sum()); draft = int(df_f["DRAFT"].sum()); resp = int(df_f["SUBMITTED RESPONDENT"].sum())
pct_approved = (approved / total * 100) if total > 0 else 0; pct_submitted = (submitted / total * 100) if total > 0 else 0

card_configs = [("TOTAL", total, f"dari {len(df_f)} SLS tercatat", "#0f766e"),("APPROVED BY Pengawas", approved, f"{pct_approved:.1f}% dari total", "#10b981"),("SUBMITTED BY Pencacah", submitted, f"{pct_submitted:.1f}% dari total", "#3b82f6"),("OPEN", open_count, f"{(open_count/total*100) if total else 0:.1f}% dari total", "#f59e0b"),("EDITED BY Pengawas", edited, f"{(edited/total*100) if total else 0:.1f}% dari total", "#8b5cf6"),("REJECTED BY Pengawas", rejected, f"{(rejected/total*100) if total else 0:.1f}% dari total", "#ef4444"),("REVOKED BY Pengawas", revoked, f"{(revoked/total*100) if total else 0:.1f}% dari total", "#6b7280"),("DRAFT", draft, f"{(draft/total*100) if total else 0:.1f}% dari total", "#06b6d4"),("SUBMITTED RESPONDENT", resp, f"{(resp/total*100) if total else 0:.1f}% dari total", "#ec4899")]

def render_card(key, value, sub, color):
    icon, _ = STATUS_ICONS[key]; label = STATUS_LABELS.get(key, key)
    return f'<div class="metric-card" style="border-bottom: 3px solid {color};"><div class="metric-icon" style="background: {color}15; color: {color};">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{value:,}</div><div class="metric-sub">{sub}</div></div>'

for row_start in range(0, len(card_configs), 3):
    row_items = card_configs[row_start : row_start + 3]; cols = st.columns(3)
    for idx, (key, value, sub, color) in enumerate(row_items):
        with cols[idx]: st.markdown(render_card(key, value, sub, color), unsafe_allow_html=True)

# ============================================================
# PROGRESS BAR
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Progress Pengisian UMKM</div>', unsafe_allow_html=True)
progress_data = [("Approved", approved, "#10b981"),("Submitted", submitted, "#3b82f6"),("Open / Belum Diisi", open_count, "#f59e0b"),("Lainnya", total - approved - submitted - open_count, "#94a3b8")]
pcol1, pcol2 = st.columns([1, 2])

with pcol1:
    st.markdown(f'<div style="text-align:center; padding:1rem;"><div style="font-size:2.5rem; font-weight:800; color:#0f766e; line-height:1;">{pct_approved:.1f}%</div><div style="font-size:0.8rem; color:#64748b; margin-top:0.25rem;">Tingkat Kelengkapan</div><div style="font-size:0.75rem; color:#94a3b8; margin-top:0.15rem;">(Approved / Total)</div></div>', unsafe_allow_html=True)
with pcol2:
    bar_parts = []
    for label, val, clr in progress_data:
        pct = (val / total * 100) if total > 0 else 0
        bar_parts.append(f'<div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.35rem;"><div style="width:8px; height:8px; border-radius:50%; background:{clr}; flex-shrink:0;"></div><div style="width:140px; font-size:0.78rem; color:#475569; font-weight:500;">{label}</div><div style="flex:1; background:#f1f5f9; border-radius:999px; height:8px; overflow:hidden;"><div style="width:{pct}%; height:100%; background:{clr}; border-radius:999px;"></div></div><div style="width:50px; text-align:right; font-size:0.78rem; color:#64748b; font-weight:600;">{val:,} <span style="color:#94a3b8;">({pct:.1f}%)</span></div></div>')
    st.markdown('<div style="padding: 0.75rem 0;">' + "".join(bar_parts) + "</div>", unsafe_allow_html=True)

# ============================================================
# CHARTS
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Analisis Distribusi Status</div>', unsafe_allow_html=True)
status_sum = {STATUS_LABELS[col]: int(df_f[col].sum()) for col in STATUS_COLUMNS}
status_df = pd.DataFrame(list(status_sum.items()), columns=["Status", "Jumlah"])
status_df = status_df[status_df["Jumlah"] > 0].sort_values("Jumlah", ascending=False)
status_df["Color"] = status_df["Status"].map(STATUS_COLORS)

ch1, ch2 = st.columns([1, 2])
with ch1:
    st.markdown('<div class="chart-box"><h3>Komposisi Status</h3><p class="chart-subtitle">Proporsi tiap status pengisian</p></div>', unsafe_allow_html=True)
    fig_donut = go.Figure(go.Pie(labels=status_df["Status"], values=status_df["Jumlah"], hole=0.62, marker=dict(colors=status_df["Color"], line=dict(color="#ffffff", width=2.5)), textinfo="percent", textfont=dict(size=11, color="#334155", family="Plus Jakarta Sans"), sort=False))
    fig_donut.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10, color="#64748b", family="Plus Jakarta Sans"), itemwidth=30), margin=dict(t=10, b=10, l=10, r=10), height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", annotations=[dict(text=f"<b>{total:,}</b><br><span style='font-size:10px;color:#94a3b8;'>Total UMKM</span>", x=0.5, y=0.5, font=dict(size=18, color="#0f172a", family="Plus Jakarta Sans"), showarrow=False)])
    st.plotly_chart(fig_donut, use_container_width=True)

with ch2:
    st.markdown('<div class="chart-box"><h3>Status per Kecamatan</h3><p class="chart-subtitle">Perbandingan horizontal antar kecamatan</p></div>', unsafe_allow_html=True)
    kec_group = df_f.groupby("kec_label")[STATUS_COLUMNS].sum().reset_index()
    kec_group_melted = kec_group.melt(id_vars="kec_label", value_vars=STATUS_COLUMNS, var_name="Status", value_name="Jumlah")
    kec_group_melted["Status"] = kec_group_melted["Status"].map(STATUS_LABELS)
    fig_bar = px.bar(kec_group_melted, x="Jumlah", y="kec_label", color="Status", orientation="h", color_discrete_map=STATUS_COLORS, title="")
    fig_bar.update_layout(barmode="stack", xaxis_title="Jumlah UMKM", yaxis_title="", legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(size=9, color="#64748b"), itemwidth=30), margin=dict(t=5, b=60, l=5, r=5), height=340, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans", size=11, color="#475569"), xaxis=dict(gridcolor="#f1f5f9", zerolinecolor="#e2e8f0"), yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10)))
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Peringkat & Funnel Proses</div>', unsafe_allow_html=True)
ch3, ch4 = st.columns(2)

with ch3:
    st.markdown('<div class="chart-box"><h3>Top 10 Kecamatan (Total UMKM)</h3><p class="chart-subtitle">Kecamatan dengan jumlah UMKM terbanyak</p></div>', unsafe_allow_html=True)
    kec_total = df_f.groupby("kec_label")["TOTAL"].sum().reset_index().sort_values("TOTAL", ascending=True).tail(10)
    fig_top = go.Figure(go.Bar(x=kec_total["TOTAL"], y=kec_total["kec_label"], orientation="h", marker=dict(color=kec_total["TOTAL"], colorscale=[[0, "#ccfbf1"], [0.5, "#14b8a6"], [1, "#0f766e"]], line=dict(color="#ffffff", width=1), cornerradius=4), text=kec_total["TOTAL"], textposition="outside", textfont=dict(size=10, color="#334155", family="Plus Jakarta Sans")))
    fig_top.update_layout(xaxis_title="", yaxis_title="", margin=dict(t=5, b=10, l=5, r=40), height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans", size=11, color="#475569"), xaxis=dict(gridcolor="#f1f5f9", zeroline=False, showticklabels=False), yaxis=dict(gridcolor="#f1f5f9", tickfont=dict(size=10)))
    st.plotly_chart(fig_top, use_container_width=True)

with ch4:
    st.markdown('<div class="chart-box"><h3>Funnel Proses Pengisian</h3><p class="chart-subtitle">Alur dari Open hingga Approved</p></div>', unsafe_allow_html=True)
    funnel_data = [("Open", open_count, "#f59e0b"), ("Submitted Pencacah", submitted, "#3b82f6"), ("Edited Pengawas", edited, "#8b5cf6"), ("Approved", approved, "#10b981")]
    fig_funnel = go.Figure(go.Funnel(y=[f[0] for f in funnel_data], x=[f[1] for f in funnel_data], textinfo="value+percent initial", textfont=dict(size=12, color="#ffffff", family="Plus Jakarta Sans"), marker=dict(color=[f[2] for f in funnel_data], line=dict(color="#ffffff", width=2))))
    fig_funnel.update_layout(margin=dict(t=5, b=10, l=100, r=20), height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans"))
    st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Heatmap & Distribusi per Desa</div>', unsafe_allow_html=True)
ch5, ch6 = st.columns(2)

with ch5:
    st.markdown('<div class="chart-box"><h3>Heatmap: Kecamatan × Status</h3><p class="chart-subtitle">Intensitas tiap status di setiap kecamatan</p></div>', unsafe_allow_html=True)
    kec_heat = df_f.groupby("kec_label")[STATUS_COLUMNS].sum().rename(columns=STATUS_LABELS)
    kec_heat["_sort"] = kec_heat.sum(axis=1); kec_heat = kec_heat.sort_values("_sort", ascending=False).drop("_sort", axis=1)
    kec_heat = kec_heat.loc[:, (kec_heat != 0).any(axis=0)]
    fig_heat = go.Figure(go.Heatmap(z=kec_heat.values, x=kec_heat.columns, y=kec_heat.index, colorscale=[[0, "#f0fdfa"], [0.3, "#99f6e4"], [0.6, "#14b8a6"], [1, "#0f766e"]], text=kec_heat.values, texttemplate="%{text}", textfont=dict(size=10, color="#334155", family="Plus Jakarta Sans"), xgap=3, ygap=3))
    fig_heat.update_layout(margin=dict(t=5, b=60, l=5, r=5), height=max(300, len(kec_heat) * 32 + 80), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans", size=10, color="#475569"), xaxis=dict(tickangle=35, side="bottom", tickfont=dict(size=9)), yaxis=dict(tickfont=dict(size=10)))
    st.plotly_chart(fig_heat, use_container_width=True)

with ch6:
    st.markdown('<div class="chart-box"><h3>Distribusi per Desa</h3><p class="chart-subtitle">Treemap jumlah UMKM per desa</p></div>', unsafe_allow_html=True)
    desa_total = df_f.groupby(["kec_label", "desa_label"])["TOTAL"].sum().reset_index().sort_values("TOTAL", ascending=False)
    fig_treemap = px.treemap(desa_total, path=[px.Constant(NAMA_TERPILIH), "kec_label", "desa_label"], values="TOTAL", color="TOTAL", color_continuous_scale=["#ccfbf1", "#14b8a6", "#0f766e"])
    fig_treemap.update_layout(margin=dict(t=5, b=10, l=5, r=5), height=max(300, len(kec_heat) * 32 + 80), paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Plus Jakarta Sans", size=10, color="#ffffff"), treemapcolorway=["#0f766e", "#14b8a6", "#2dd4bf", "#5eead4", "#99f6e4", "#ccfbf1"])
    fig_treemap.update_traces(textfont=dict(size=10), hovertemplate="<b>%{label}</b><br>Total: %{value:,}<extra></extra>")
    st.plotly_chart(fig_treemap, use_container_width=True)


# ============================================================
# DATA TABLE (DIPERBAIKI: DROPDOWN DEPENDENT & TANPA STYLING)
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Tabel Detail Data SLS</div>', unsafe_allow_html=True)

# Filter Khusus Tabel
tcol1, tcol2 = st.columns(2)
kec_table_opts = sorted(df_f["kec_raw"].unique())

with tcol1:
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:0.25rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Filter Kecamatan</div>', unsafe_allow_html=True)
    default_kec = kec_table_opts[0] if kec_table_opts else None
    selected_table_kec = st.selectbox(
        "TabelKec", 
        kec_table_opts, 
        index=0 if default_kec else 0, 
        key="t_kec", 
        label_visibility="collapsed"
    )

# Filter Desa (Dependent)
df_t_kec = df_f[df_f["kec_raw"] == selected_table_kec] if selected_table_kec else pd.DataFrame()
desa_table_opts = sorted(df_t_kec["desa_raw"].unique()) if not df_t_kec.empty else []

with tcol2:
    st.markdown('<div style="font-size:0.72rem;color:#64748b;margin-bottom:0.25rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Filter Desa/Kelurahan</div>', unsafe_allow_html=True)
    if desa_table_opts:
        selected_table_desa = st.selectbox(
            "TabelDesa", 
            desa_table_opts, 
            index=0, # Default desa terkecil
            key="t_desa", 
            label_visibility="collapsed"
        )
    else:
        selected_table_desa = None
        st.selectbox("TabelDesa", ["Tidak ada data"], index=0, key="t_desa_empty", label_visibility="collapsed", disabled=True)

# Terapkan filter ke dataframe tabel
df_t_final = df_t_kec.copy()
if selected_table_desa and not df_t_final.empty:
    df_t_final = df_t_final[df_t_final["desa_raw"] == selected_table_desa]

# Siapkan kolom untuk ditampilkan
table_cols = ["kec_label", "desa_label", "sls_label"] + STATUS_COLUMNS + ["TOTAL"]
table_df = df_t_final[table_cols].copy()
table_df.columns = ["Kecamatan", "Desa/Kelurahan", "SLS"] + [STATUS_LABELS[c] for c in STATUS_COLUMNS] + ["Total"]

# Tampilkan dataframe langsung tanpa styling (menghindari error applymap)
st.dataframe(table_df, use_container_width=True, height=450, hide_index=True)

# 1. Ekstrak nama dalam kurung ke kolom baru "PPL" dari kolom sls_label
df_f['PPL'] = df_f['sls_label'].str.extract(r'\(\s*([^)]+)\s*\)')

# 2. Definisikan kolom-kolom yang akan diagregasi (nama asli dari API)
kolom_agregasi = STATUS_COLUMNS + ['TOTAL']

# 3. Groupby berdasarkan kec_label dan PPL, lalu sum
df_baru = df_f.groupby(['kec_label', 'PPL'])[kolom_agregasi].sum().reset_index()

# 4. Rename kolom agar sesuai dengan label yang diinginkan
df_baru.columns = ['Kecamatan', 'PPL'] + [STATUS_LABELS[c] for c in STATUS_COLUMNS] + ['Total']

# 5. Atur ulang urutan kolom sesuai keinginan
df_baru = df_baru[['Kecamatan', 'PPL', 'Approved', 'Submitted Pencacah', 'Open', 'Edited', 'Rejected', 'Revoked', 'Draft', 'Submitted Respondent', 'Total']]

st.divider()
st.subheader("PROGRESS PPL")
st.dataframe(df_baru, use_container_width=False, height=450, hide_index=True)

df_baru['DIKERJAKAN'] = df_baru['Total'] - df_baru['Open']
df_baru['CAPAIAN BRUTO (%)'] = (df_baru['DIKERJAKAN']/df_baru['Total']*100).round(2)
df_baru['CAPAIAN NETTO (%)'] = (df_baru['Approved']/df_baru['Total']*100).round(2)

st.divider()
df_baru2 = df_baru[['Kecamatan', 'PPL', 'DIKERJAKAN', 'CAPAIAN BRUTO (%)', 'CAPAIAN NETTO (%)']]

st.subheader("CAPAIAN PPL")
st.dataframe(df_baru2, use_container_width=False, hide_index=True)
st.warning("CAPAIAN BRUTO = DIKERJAKAN = ASSIGNMENT SELAIN OPEN")
st.success("CAPAIAN NETTO = Approved/Total")

# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ Dashboard UMKM SLS — {NAMA_TERPILIH} | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)
