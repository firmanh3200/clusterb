"""
Aplikasi Streamlit — CSV Explorer & Visualizer
Fitur:
  1. Pilih file CSV dari folder data/
  2. Pilih kolom yang ditampilkan
  3. Tampilkan dataframe
  4. Filter per kolom (numerik → range, kategorikal → multiselect)
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
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data")

# ──────────────────────────────────────────────
# Fungsi Utilitas
# ──────────────────────────────────────────────

def get_csv_files() -> list[str]:
    """Mengembalikan daftar file .csv di folder data/."""
    if not DATA_DIR.exists():
        return []
    return sorted([f.name for f in DATA_DIR.glob("*.csv")])


def detect_column_type(series: pd.Series) -> str:
    """
    Mendeteksi tipe kolom untuk keperluan filter.
    Mengembalikan: 'numerik', 'tanggal', 'boolean', atau 'teks'.
    """
    # Cek boolean
    if set(series.dropna().unique()).issubset({True, False, "True", "False", "true", "false"}):
        return "boolean"

    # Cek tanggal
    if series.dtype == "object":
        try:
            pd.to_datetime(series, errors="raise")
            return "tanggal"
        except Exception:
            pass

    # Cek numerik
    if pd.api.types.is_numeric_dtype(series):
        return "numerik"

    # Coba konversi ke numerik (misal angka yang tersimpan sebagai string)
    if series.dtype == "object":
        try:
            pd.to_numeric(series, errors="raise")
            return "numerik"
        except Exception:
            pass

    return "teks"


def apply_filter(
    df: pd.DataFrame, col: str, col_type: str, filter_widget
) -> pd.DataFrame:
    """Menerapkan filter ke dataframe berdasarkan tipe kolom."""
    if filter_widget is None:
        return df

    if col_type == "numerik":
        if len(filter_widget) == 2:
            min_val, max_val = filter_widget
            df = df[(df[col] >= min_val) & (df[col] <= max_val)]

    elif col_type == "tanggal":
        if len(filter_widget) == 2:
            start_date, end_date = filter_widget
            dates = pd.to_datetime(df[col], errors="coerce")
            mask = (dates >= pd.Timestamp(start_date)) & (dates <= pd.Timestamp(end_date))
            df = df[mask]

    elif col_type == "teks":
        if filter_widget:  # list tidak kosong
            df = df[df[col].isin(filter_widget)]

    elif col_type == "boolean":
        if filter_widget:  # list tidak kosong
            # Konversi ke string agar konsisten
            df = df[df[col].astype(str).isin(filter_widget)]

    return df


# ──────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa; }
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
# 1. PILIH FILE CSV
# ──────────────────────────────────────────────
csv_files = get_csv_files()

if not csv_files:
    st.error(
        "❌ Tidak ada file CSV di folder `data/`. "
        "Jalankan `python generate_sample_data.py` terlebih dahulu untuk membuat data sampel."
    )
    st.stop()

with st.expander:
    st.header("📁 Pilih File")
    selected_file = st.selectbox(
        "File CSV",
        options=csv_files,
        index=0,
        format_func=lambda x: f"📄 {x}",
    )

# Baca CSV
file_path = DATA_DIR / selected_file
df_raw = pd.read_csv(file_path)

st.divider()

# ──────────────────────────────────────────────
# 2. PILIH KOLOM
# ──────────────────────────────────────────────
all_columns = df_raw.columns.tolist()
col_types = {col: detect_column_type(df_raw[col]) for col in all_columns}

# Ikon berdasarkan tipe
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
# 4. FILTER BERDASARKAN KOLOM
# ──────────────────────────────────────────────
with st.expander("🔍 **Langkah 2 — Filter Data**", expanded=True):
    st.markdown("Atur filter untuk setiap kolom. Biarkan kosong = tidak difilter.")

    filter_cols = st.columns(len(selected_columns))
    filter_values = {}

    for idx, col in enumerate(selected_columns):
        ct = col_types[col]
        with filter_cols[idx]:
            st.markdown(f"**{type_icons.get(ct, '')} {col}**")

            if ct == "numerik":
                col_min = float(df_selected[col].min())
                col_max = float(df_selected[col].max())
                val = st.slider(
                    "Range",
                    min_value=col_min,
                    max_value=col_max,
                    value=(col_min, col_max),
                    key=f"filter_{col}",
                )
                filter_values[col] = val

            elif ct == "tanggal":
                dates = pd.to_datetime(df_selected[col], errors="coerce").dropna()
                if len(dates) > 0:
                    d_min = dates.min().to_pydatetime().date()
                    d_max = dates.max().to_pydatetime().date()
                    val = st.date_input(
                        "Rentang",
                        value=(d_min, d_max),
                        key=f"filter_{col}",
                    )
                    if len(val) == 2:
                        filter_values[col] = val
                    else:
                        filter_values[col] = None
                else:
                    st.warning("Tidak ada tanggal valid")
                    filter_values[col] = None

            elif ct == "teks":
                unique_vals = sorted(df_selected[col].dropna().unique().tolist())
                val = st.multiselect(
                    "Pilih",
                    options=unique_vals,
                    default=unique_vals,
                    key=f"filter_{col}",
                )
                filter_values[col] = val

            elif ct == "boolean":
                unique_vals = sorted(df_selected[col].astype(str).unique().tolist())
                val = st.multiselect(
                    "Pilih",
                    options=unique_vals,
                    default=unique_vals,
                    key=f"filter_{col}",
                )
                filter_values[col] = val

# ──────────────────────────────────────────────
# 5. TAMPILKAN DATAFRAME HASIL FILTER
# ──────────────────────────────────────────────
df_filtered = df_selected.copy()
for col in selected_columns:
    df_filtered = apply_filter(df_filtered, col, col_types[col], filter_values.get(col))

st.subheader("🔍 Dataframe — Hasil Filter")
rows_removed = len(df_selected) - len(df_filtered)

if rows_removed == 0:
    st.success(f"Menampilkan semua **{len(df_filtered)}** baris (tidak ada data yang terfilter)")
else:
    st.warning(
        f"Menampilkan **{len(df_filtered)}** baris "
        f"({rows_removed} baris dihapus oleh filter)"
    )

st.dataframe(df_filtered, use_container_width=True, height=300)

# Tombol download hasil filter
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

with st.expander("🎨 **Langkah 3 — Pilih Jenis Grafik & Konfigurasi**", expanded=True):

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

    # Tentukan kolom yang cocok untuk sumbu
    numeric_cols = [c for c in selected_columns if col_types[c] == "numerik"]
    text_cols = [c for c in selected_columns if col_types[c] in ("teks", "boolean")]
    date_cols = [c for c in selected_columns if col_types[c] == "tanggal"]
    all_usable = selected_columns  # semua kolom bisa dipakai

    with chart_col2:
        x_col = st.selectbox("Sumbu X", options=all_usable, index=0, key="chart_x")

    with chart_col3:
        # Sumbu Y tidak wajib untuk histogram & box
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
        # Untuk bar & pie: opsi agregasi
        agg_options = ["none", "sum", "mean", "count", "min", "max"]
        agg_func = st.selectbox("Agregasi (jika ada duplikat di X)", options=agg_options, index=0)

# ──────────────────────────────────────────────
# Buat Grafik
# ──────────────────────────────────────────────
def build_chart(df, chart_type, x, y, color, agg):
    """Membuat figure Plotly berdasarkan pilihan user."""
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

    # Siapkan data — agregasi jika diminta
    plot_df = df.copy()

    if agg != "none" and x and y and px_name in ("bar", "line", "area", "scatter"):
        if agg == "count":
            plot_df = plot_df.groupby(x).size().reset_index(name=f"count_of_{x}")
            y = f"count_of_{x}"
        else:
            plot_df = plot_df.groupby(x, as_index=False).agg({y: agg})

    # Konversi tanggal ke datetime untuk sumbu X
    if x and col_types.get(x) == "tanggal":
        plot_df[x] = pd.to_datetime(plot_df[x], errors="coerce")

    # Argumen umum
    common_kwargs = dict(data_frame=plot_df, x=x, color=color)
    if y:
        common_kwargs["y"] = y

    try:
        if px_name == "pie":
            # Pie tidak pakai x/y biasa
            fig = px.pie(
                plot_df,
                values=y if y else None,
                names=x,
                color=color,
                hole=0.35,
            )
        elif px_name == "histogram":
            fig = px.histogram(
                plot_df,
                x=x,
                y=y if y else None,
                color=color,
                nbins=30,
                barmode="overlay",
            )
        elif px_name == "box":
            fig = px.box(
                plot_df,
                x=x,
                y=y,
                color=color,
            )
        elif px_name == "violin":
            fig = px.violin(
                plot_df,
                x=x,
                y=y,
                color=color,
                box=True,
                points="outliers",
            )
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

        # Styling
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

    # Tombol download gambar
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
# Footer Info
# ──────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.caption("📌 **Info Kolom**")
    for col in selected_columns:
        icon = type_icons.get(col_types[col], "❓")
        n_unique = df_raw[col].nunique()
        st.markdown(f"{icon} `{col}` — {col_types[col]} ({n_unique} unique)")

    st.divider()
    st.caption("CSV Explorer v1.0")
