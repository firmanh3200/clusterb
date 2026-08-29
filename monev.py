"""
Aplikasi Streamlit — CSV Explorer & Visualizer
Fitur:
  1. Pilih file CSV dari folder data/
  2. Pilih kolom yang ditampilkan
  3. Tampilkan dataframe
  4. Filter: pilih kolom → pilih nilai unik (default: nofilter)
  5. Tampilkan dataframe hasil filter
  6. Pilih & tampilkan grafik dari Plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pathlib import Path

# ──────────────────────────────────────────────
# Konfigurasi Halaman
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="CSV Explorer & Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_DIR = Path("data")

# ──────────────────────────────────────────────
# Fungsi Utilitas
# ──────────────────────────────────────────────

def get_csv_files() -> list[str]:
    if not DATA_DIR.exists():
        return []
    return sorted([f.name for f in DATA_DIR.glob("*.csv")])


def detect_column_type(series: pd.Series) -> str:
    if set(series.dropna().unique()).issubset({True, False, "True", "False", "true", "false"}):
        return "boolean"
    if series.dtype == "object":
        try:
            pd.to_datetime(series, errors="raise")
            return "tanggal"
        except Exception:
            pass
    if pd.api.types.is_numeric_dtype(series):
        return "numerik"
    if series.dtype == "object":
        try:
            pd.to_numeric(series, errors="raise")
            return "numerik"
        except Exception:
            pass
    return "teks"


# ──────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { color: #1a73e8; }
    h2 { color: #333; border-bottom: 2px solid #1a73e8; padding-bottom: 0.3rem; }
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("📊 CSV Explorer & Visualizer")
st.caption("Pilih file CSV → pilih kolom → filter data → visualisasi dengan grafik interaktif")

# ──────────────────────────────────────────────
# 1. PILIH FILE CSV (Expander)
# ──────────────────────────────────────────────
csv_files = get_csv_files()

if not csv_files:
    st.error(
        "❌ Tidak ada file CSV di folder `data/`. "
        "Jalankan `python generate_sample_data.py` terlebih dahulu."
    )
    st.stop()

with st.expander("📁 **Pilih File CSV**", expanded=True):
    selected_file = st.selectbox(
        "File CSV",
        options=csv_files,
        index=0,
        format_func=lambda x: f"📄 {x}",
        key="file_select",
    )
    file_path = DATA_DIR / selected_file

df_raw = pd.read_csv(file_path)

st.divider()

# ──────────────────────────────────────────────
# 2. PILIH KOLOM (Expander)
# ──────────────────────────────────────────────
all_columns = df_raw.columns.tolist()
col_types = {col: detect_column_type(df_raw[col]) for col in all_columns}

type_icons = {
    "numerik": "🔢",
    "teks": "📝",
    "tanggal": "📅",
    "boolean": "☑️",
}

with st.expander("⚙️ **Langkah 1 — Pilih Kolom yang Ditampilkan**", expanded=True):
    col_options = {
        col: f"{type_icons.get(col_types[col], '❓')} {col}  _({col_types[col]})_"
        for col in all_columns
    }
    selected_columns = st.multiselect(
        "Kolom",
        options=all_columns,
        default=all_columns,
        format_func=lambda x: col_options[x],
        key="col_select",
    )

    if not selected_columns:
        st.warning("Pilih minimal satu kolom.")
        st.stop()

# ──────────────────────────────────────────────
# 3. TAMPILKAN DATAFRAME (KOLOM TERPILIH)
# ──────────────────────────────────────────────
df_selected = df_raw[selected_columns].copy()

st.subheader("📋 Dataframe — Kolom Terpilih")
st.info(f"Menampilkan **{len(df_selected)}** baris × **{len(selected_columns)}** kolom dari `{selected_file}`")
st.dataframe(df_selected, use_container_width=True, height=300)

st.divider()

# ──────────────────────────────────────────────
# 4. FILTER: PILIH KOLOM → PILIH NILAI UNIK
# ──────────────────────────────────────────────
with st.expander("🔍 **Langkah 2 — Filter Data**", expanded=False):
    st.markdown(
        "Pilih kolom yang ingin difilter, lalu pilih nilai unik dari kolom tersebut. "
        "**Default: tidak ada filter aktif.**"
    )

    # --- Pilih kolom mana yang mau difilter ---
    filter_col_options = {
        col: f"{type_icons.get(col_types[col], '❓')} {col}  _({col_types[col]})_"
        for col in selected_columns
    }

    filter_columns = st.multiselect(
        "Kolom yang ingin difilter",
        options=selected_columns,
        default=[],  # DEFAULT: kosong = nofilter
        format_func=lambda x: filter_col_options[x],
        key="filter_col_select",
    )

    # --- Untuk setiap kolom terpilih, tampilkan nilai unik ---
    filter_values = {}

    if filter_columns:
        # Gunakan kolom agar rapi
        n_filter_cols = len(filter_columns)
        cols = st.columns(n_filter_cols)

        for idx, col in enumerate(filter_columns):
            ct = col_types[col]
            unique_vals = sorted(df_selected[col].dropna().unique().tolist())

            with cols[idx]:
                st.markdown(f"**{type_icons.get(ct, '')} {col}**")

                if ct == "numerik":
                    col_min = float(df_selected[col].min())
                    col_max = float(df_selected[col].max())
                    val = st.slider(
                        "Rentang nilai",
                        min_value=col_min,
                        max_value=col_max,
                        value=(col_min, col_max),
                        key=f"filter_val_{col}",
                    )
                    filter_values[col] = ("numerik", val)

                elif ct == "tanggal":
                    dates = pd.to_datetime(df_selected[col], errors="coerce").dropna()
                    if len(dates) > 0:
                        d_min = dates.min().to_pydatetime().date()
                        d_max = dates.max().to_pydatetime().date()
                        val = st.date_input(
                            "Rentang tanggal",
                            value=(d_min, d_max),
                            key=f"filter_val_{col}",
                        )
                        if len(val) == 2:
                            filter_values[col] = ("tanggal", val)
                        else:
                            filter_values[col] = ("tanggal", None)
                    else:
                        st.warning("Tidak ada tanggal valid")
                        filter_values[col] = ("tanggal", None)

                elif ct in ("teks", "boolean"):
                    val = st.multiselect(
                        "Pilih nilai",
                        options=unique_vals,
                        default=[],  # DEFAULT: kosong = nofilter untuk kolom ini
                        key=f"filter_val_{col}",
                    )
                    filter_values[col] = ("teks", val)

    else:
        st.info("✅ **Tidak ada filter aktif** — pilih kolom di atas untuk mulai memfilter.")

# ──────────────────────────────────────────────
# 5. TERAPKAN FILTER & TAMPILKAN DATAFRAME
# ──────────────────────────────────────────────
df_filtered = df_selected.copy()

for col, (ct, val) in filter_values.items():
    if val is None:
        continue

    if ct == "numerik":
        if len(val) == 2:
            df_filtered = df_filtered[(df_filtered[col] >= val[0]) & (df_filtered[col] <= val[1])]

    elif ct == "tanggal":
        if len(val) == 2:
            dates = pd.to_datetime(df_filtered[col], errors="coerce")
            mask = (dates >= pd.Timestamp(val[0])) & (dates <= pd.Timestamp(val[1]))
            df_filtered = df_filtered[mask]

    elif ct == "teks":
        if val:  # hanya terapkan jika user memilih setidaknya 1 nilai
            df_filtered = df_filtered[df_filtered[col].isin(val)]

st.subheader("🔍 Dataframe — Hasil Filter")
rows_removed = len(df_selected) - len(df_filtered)

if not filter_columns:
    st.success(f"Menampilkan semua **{len(df_filtered)}** baris (nofilter)")
elif rows_removed == 0:
    st.success(f"Menampilkan semua **{len(df_filtered)}** baris (filter aktif tapi tidak menghapus data)")
else:
    st.warning(
        f"Menampilkan **{len(df_filtered)}** baris "
        f"({rows_removed} baris dihapus oleh filter)"
    )

st.dataframe(df_filtered, use_container_width=True, height=300)

# Tombol download
csv_filtered = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Unduh Hasil Filter (CSV)",
    data=csv_filtered,
    file_name=f"filtered_{selected_file}",
    mime="text/csv",
)

st.divider()

# ──────────────────────────────────────────────
# 6. PILIH & TAMPILKAN GRAFIK
# ──────────────────────────────────────────────
st.subheader("📈 Visualisasi Grafik")

if len(df_filtered) == 0:
    st.error("Data kosong setelah filter. Tidak bisa membuat grafik.")
    st.stop()

with st.expander("🎨 **Langkah 3 — Pilih Jenis Grafik & Konfigurasi**", expanded=False):

    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        chart_type = st.selectbox(
            "Jenis Grafik",
            options=[
                "Bar Chart",
                "Line Chart",
                "Scatter Plot",
                "Pie Chart",
                "Histogram",
                "Box Plot",
                "Area Chart",
                "Violin Plot",
            ],
            index=0,
        )

    all_usable = selected_columns

    with chart_col2:
        x_col = st.selectbox("Sumbu X", options=all_usable, index=0, key="chart_x")

    with chart_col3:
        y_options = ["— tidak dipilih —"] + all_usable
        y_default_idx = 1 if len(all_usable) > 0 else 0
        y_col = st.selectbox("Sumbu Y", options=y_options, index=y_default_idx, key="chart_y")
        y_col = None if y_col == "— tidak dipilih —" else y_col

    color_col1, color_col2 = st.columns(2)
    with color_col1:
        color_options = ["— tidak dipilih —"] + all_usable
        color_col = st.selectbox(
            "Warna / Group By", options=color_options, index=0, key="chart_color"
        )
        color_col = None if color_col == "— tidak dipilih —" else color_col

    with color_col2:
        agg_options = ["none", "sum", "mean", "count", "min", "max"]
        agg_func = st.selectbox("Agregasi (jika ada duplikat di X)", options=agg_options, index=0)


# ──────────────────────────────────────────────
# Buat Grafik
# ──────────────────────────────────────────────
def build_chart(df, chart_type, x, y, color, agg):
    chart_map = {
        "Bar Chart": "bar",
        "Line Chart": "line",
        "Scatter Plot": "scatter",
        "Pie Chart": "pie",
        "Histogram": "histogram",
        "Box Plot": "box",
        "Area Chart": "area",
        "Violin Plot": "violin",
    }
    px_name = chart_map.get(chart_type, "bar")

    plot_df = df.copy()

    if agg != "none" and x and y and px_name in ("bar", "line", "area", "scatter"):
        if agg == "count":
            plot_df = plot_df.groupby(x).size().reset_index(name=f"count_of_{x}")
            y = f"count_of_{x}"
        else:
            plot_df = plot_df.groupby(x, as_index=False).agg({y: agg})

    if x and col_types.get(x) == "tanggal":
        plot_df[x] = pd.to_datetime(plot_df[x], errors="coerce")

    common_kwargs = dict(data_frame=plot_df, x=x, color=color)
    if y:
        common_kwargs["y"] = y

    try:
        if px_name == "pie":
            fig = px.pie(plot_df, values=y if y else None, names=x, color=color, hole=0.35)
        elif px_name == "histogram":
            fig = px.histogram(plot_df, x=x, y=y if y else None, color=color, nbins=30, barmode="overlay")
        elif px_name == "box":
            fig = px.box(plot_df, x=x, y=y, color=color)
        elif px_name == "violin":
            fig = px.violin(plot_df, x=x, y=y, color=color, box=True, points="outliers")
        elif px_name == "area":
            fig = px.area(plot_df, **common_kwargs)
        elif px_name == "bar":
            fig = px.bar(plot_df, **common_kwargs, barmode="group")
        elif px_name == "line":
            fig = px.line(plot_df, **common_kwargs, markers=True)
        elif px_name == "scatter":
            fig = px.scatter(plot_df, **common_kwargs, size_max=15)
        else:
            fig = px.bar(plot_df, **common_kwargs)

        fig.update_layout(
            template="plotly_white",
            height=500,
            margin=dict(l=40, r=30, t=60, b=60),
            title=dict(font_size=16),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig.update_xaxes(title_text=x)
        if y:
            fig.update_yaxes(title_text=y)
        return fig

    except Exception as e:
        return None, str(e)


fig, error = build_chart(df_filtered, chart_type, x_col, y_col, color_col, agg_func)

if fig:
    st.plotly_chart(fig, use_container_width=True)
    img_bytes = fig.to_image(format="png", scale=2)
    st.download_button(
        label="🖼️ Unduh Grafik (PNG)",
        data=img_bytes,
        file_name=f"chart_{chart_type.lower().replace(' ', '_')}.png",
        mime="image/png",
    )
elif error:
    st.error(f"❌ Gagal membuat grafik: **{error}**")
    st.info(
        "💡 **Tips:** Pastikan kombinasi sumbu X/Y sesuai dengan jenis grafik. "
        "Contoh: Pie Chart butuh kolom kategorikal di X dan kolom numerik di Y."
    )

# ──────────────────────────────────────────────
# Info Kolom (di bawah, bukan sidebar)
# ──────────────────────────────────────────────
with st.expander("📌 **Info Tipe Kolom**"):
    info_cols = st.columns(min(len(selected_columns), 4))
    for idx, col in enumerate(selected_columns):
        with info_cols[idx % len(info_cols)]:
            icon = type_icons.get(col_types[col], "❓")
            n_unique = df_raw[col].nunique()
            st.markdown(f"{icon} `{col}` — **{col_types[col]}** ({n_unique} unique)")
