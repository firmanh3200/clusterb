"""
Aplikasi Streamlit — CSV Explorer & Visualizer
Fitur:
  1. Pilih file CSV dari folder data/
  2. Pilih kolom yang ditampilkan
  3. Tentukan tipe data per kolom (default: autodetect)
  4. Tampilkan dataframe
  5. Filter: pilih kolom → pilih nilai unik (default: nofilter)
  6. Tampilkan dataframe hasil filter
  7. Pilih & tampilkan grafik dari Plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
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
    """Autodetect tipe kolom."""
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


def coerce_column(df: pd.DataFrame, col: str, col_type: str) -> pd.Series:
    """Konversi kolom ke tipe yang ditentukan user."""
    s = df[col].copy()
    if col_type == "numerik":
        return pd.to_numeric(s, errors="coerce")
    elif col_type == "tanggal":
        return pd.to_datetime(s, errors="coerce")
    elif col_type == "boolean":
        return s.astype(str).str.lower().map({
            "true": True, "false": False, "1": True, "0": False
        })
    else:
        return s.astype(str)


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
st.caption("Pilih file CSV → pilih kolom → tentukan tipe data → filter → visualisasi")

# ──────────────────────────────────────────────
# 1. PILIH FILE CSV
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
# 2. PILIH KOLOM
# ──────────────────────────────────────────────
all_columns = df_raw.columns.tolist()
auto_types = {col: detect_column_type(df_raw[col]) for col in all_columns}

type_icons = {
    "numerik": "🔢",
    "teks": "📝",
    "tanggal": "📅",
    "boolean": "☑️",
}

type_labels = {
    "numerik": "🔢 Numerik",
    "teks": "📝 Teks / Kategorikal",
    "tanggal": "📅 Tanggal",
    "boolean": "☑️ Boolean",
}

with st.expander("⚙️ **Langkah 1 — Pilih Kolom yang Ditampilkan**", expanded=True):
    col_options = {
        col: f"{type_icons.get(auto_types[col], '❓')} {col}  _({auto_types[col]})_"
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

st.divider()

# ──────────────────────────────────────────────
# 3. TENTUKAN TIPE DATA (default = autodetect)
# ──────────────────────────────────────────────
with st.expander("🔧 **Langkah 2 — Tentukan Tipe Data Kolom**", expanded=False):
    st.markdown(
        "Tipe data ditentukan otomatis saat file dibaca. "
        "Ubah jika deteksi tidak sesuai kebutuhan. "
        "**Jika tidak diubah, mengikuti default.**"
    )

    grid_size = 4
    col_types = {}

    for i in range(0, len(selected_columns), grid_size):
        row_cols = st.columns(grid_size)
        for j in range(grid_size):
            if i + j < len(selected_columns):
                col = selected_columns[i + j]
                detected = auto_types[col]

                with row_cols[j]:
                    st.markdown(f"**`{col}`**")
                    chosen_type = st.selectbox(
                        "Tipe data",
                        options=["numerik", "teks", "tanggal", "boolean"],
                        index=["numerik", "teks", "tanggal", "boolean"].index(detected),
                        format_func=lambda x: type_labels[x],
                        key=f"type_{col}",
                        label_visibility="collapsed",
                    )
                    col_types[col] = chosen_type

                    if chosen_type != detected:
                        st.caption(f"⚠️ default: *{detected}*")

    if st.button("🔄 Kembalikan Semua ke Default", use_container_width=True):
        st.rerun()

st.divider()

# ──────────────────────────────────────────────
# 4. TAMPILKAN DATAFRAME (KOLOM TERPILIH + TIPE)
# ──────────────────────────────────────────────
df_selected = df_raw[selected_columns].copy()

for col in selected_columns:
    df_selected[col] = coerce_column(df_selected, col, col_types[col])

st.subheader("📋 Dataframe — Kolom Terpilih")

type_badges = "  ".join(
    f"{type_icons.get(col_types[c], '❓')} `{c}`:*{col_types[c]}*"
    for c in selected_columns
)
st.markdown(type_badges)

st.info(f"Menampilkan **{len(df_selected)}** baris × **{len(selected_columns)}** kolom dari `{selected_file}`")
st.dataframe(df_selected, use_container_width=True, height=300)

st.divider()

# ──────────────────────────────────────────────
# 5. FILTER: PILIH KOLOM → PILIH NILAI UNIK
# ──────────────────────────────────────────────
with st.expander("🔍 **Langkah 3 — Filter Data**", expanded=False):
    st.markdown(
        "Pilih kolom yang ingin difilter, lalu pilih nilai. "
        "**Default: tidak ada filter aktif.**"
    )

    filter_col_options = {
        col: f"{type_icons.get(col_types[col], '❓')} {col}  _({col_types[col]})_"
        for col in selected_columns
    }

    filter_columns = st.multiselect(
        "Kolom yang ingin difilter",
        options=selected_columns,
        default=[],
        format_func=lambda x: filter_col_options[x],
        key="filter_col_select",
    )

    filter_values = {}

    if filter_columns:
        n_filter_cols = len(filter_columns)
        cols = st.columns(min(n_filter_cols, 4))

        for idx, col in enumerate(filter_columns):
            ct = col_types[col]

            with cols[idx % len(cols)]:
                st.markdown(f"**{type_icons.get(ct, '')} `{col}`**")

                if ct == "numerik":
                    series_num = pd.to_numeric(df_selected[col], errors="coerce").dropna()
                    if len(series_num) > 0:
                        col_min = float(series_num.min())
                        col_max = float(series_num.max())
                        val = st.slider(
                            "Rentang",
                            min_value=col_min,
                            max_value=col_max,
                            value=(col_min, col_max),
                            key=f"filter_val_{col}",
                        )
                        filter_values[col] = ("numerik", val)
                    else:
                        st.warning("Tidak ada nilai numerik valid")
                        filter_values[col] = ("numerik", None)

                elif ct == "tanggal":
                    series_dt = pd.to_datetime(df_selected[col], errors="coerce").dropna()
                    if len(series_dt) > 0:
                        d_min = series_dt.min().to_pydatetime().date()
                        d_max = series_dt.max().to_pydatetime().date()
                        val = st.date_input(
                            "Rentang",
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
                    unique_vals = sorted(df_selected[col].dropna().astype(str).unique().tolist())
                    val = st.multiselect(
                        "Pilih nilai",
                        options=unique_vals,
                        default=[],
                        key=f"filter_val_{col}",
                    )
                    filter_values[col] = ("teks", val)
    else:
        st.info("✅ **Tidak ada filter aktif** — pilih kolom di atas untuk mulai memfilter.")

# ──────────────────────────────────────────────
# 6. TERAPKAN FILTER & TAMPILKAN DATAFRAME
# ──────────────────────────────────────────────
df_filtered = df_selected.copy()

for col, (ct, val) in filter_values.items():
    if val is None:
        continue
    if ct == "numerik":
        if len(val) == 2:
            series_num = pd.to_numeric(df_filtered[col], errors="coerce")
            df_filtered = df_filtered[(series_num >= val[0]) & (series_num <= val[1])]
    elif ct == "tanggal":
        if len(val) == 2:
            dates = pd.to_datetime(df_filtered[col], errors="coerce")
            mask = (dates >= pd.Timestamp(val[0])) & (dates <= pd.Timestamp(val[1]))
            df_filtered = df_filtered[mask]
    elif ct == "teks":
        if val:
            df_filtered = df_filtered[df_filtered[col].astype(str).isin(val)]

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

csv_filtered = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Unduh Hasil Filter (CSV)",
    data=csv_filtered,
    file_name=f"filtered_{selected_file}",
    mime="text/csv",
)

st.divider()

# ──────────────────────────────────────────────
# 7. PILIH & TAMPILKAN GRAFIK
# ──────────────────────────────────────────────
st.subheader("📈 Visualisasi Grafik")

if len(df_filtered) == 0:
    st.error("Data kosong setelah filter. Tidak bisa membuat grafik.")
    st.stop()

with st.expander("🎨 **Langkah 4 — Pilih Jenis Grafik & Konfigurasi**", expanded=False):

    chart_col1, chart_col2, chart_col3 = st.columns(3)

    with chart_col1:
        chart_type = st.selectbox(
            "Jenis Grafik",
            options=[
                "Bar Chart", "Line Chart", "Scatter Plot",
                "Pie Chart", "Histogram", "Box Plot",
                "Area Chart", "Violin Plot",
            ],
            index=0,
        )

    all_usable = selected_columns

    with chart_col2:
        x_col = st.selectbox("Sumbu X", options=all_usable, index=0, key="chart_x")

    with chart_col3:
        y_options = ["— tidak dipilih —"] + all_usable
        y_default_idx = 1 if all_usable else 0
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
        "Bar Chart": "bar", "Line Chart": "line", "Scatter Plot": "scatter",
        "Pie Chart": "pie", "Histogram": "histogram", "Box Plot": "box",
        "Area Chart": "area", "Violin Plot": "violin",
    }
    px_name = chart_map.get(chart_type, "bar")

    plot_df = df.copy()

    # Konversi tanggal di sumbu X
    if x and col_types.get(x) == "tanggal":
        plot_df[x] = pd.to_datetime(plot_df[x], errors="coerce")

    # --- Agregasi ---
    if agg != "none" and x and y and px_name in ("bar", "line", "area", "scatter"):
        # Tentukan kolom groupby: selalu x, plus color jika berbeda dari x
        groupby_cols = [x]
        if color and color != x:
            groupby_cols.append(color)

        if agg == "count":
            plot_df = plot_df.groupby(groupby_cols, dropna=False).size().reset_index(name=f"count_of_{x}")
            y = f"count_of_{x}"
        else:
            agg_dict = {y: agg}
            plot_df = plot_df.groupby(groupby_cols, as_index=False, dropna=False).agg(agg_dict)

    # --- Pastikan kolom yang dipakai ada di plot_df ---
    if x and x not in plot_df.columns:
        return None, f"Kolom sumbu X '`{x}`' tidak ditemukan dalam data setelah agregasi."
    if y and y not in plot_df.columns:
        return None, f"Kolom sumbu Y '`{y}`' tidak ditemukan dalam data setelah agregasi."
    if color and color not in plot_df.columns:
        color = None  # aman: lewati warna daripada crash

    # --- Siapkan kwargs (tanpa data_frame, sudah lewat posisi) ---
    common_kwargs = dict(x=x)
    if y:
        common_kwargs["y"] = y
    if color:
        common_kwargs["color"] = color

    try:
        if px_name == "pie":
            fig = px.pie(
                plot_df,
                values=y if y else None,
                names=x,
                color=color if color and color in plot_df.columns else None,
                hole=0.35,
            )
        elif px_name == "histogram":
            fig = px.histogram(
                plot_df,
                x=x,
                y=y if y else None,
                color=color if color and color in plot_df.columns else None,
                nbins=30,
                barmode="overlay",
            )
        elif px_name == "box":
            fig = px.box(
                plot_df,
                x=x,
                y=y,
                color=color if color and color in plot_df.columns else None,
            )
        elif px_name == "violin":
            fig = px.violin(
                plot_df,
                x=x,
                y=y,
                color=color if color and color in plot_df.columns else None,
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
# ──────────────────────────────────────────────
# Ringkasan Tipe Data
# ──────────────────────────────────────────────
with st.expander("📌 **Ringkasan Tipe Data Kolom**"):
    info_cols = st.columns(min(len(selected_columns), 4))
    for idx, col in enumerate(selected_columns):
        with info_cols[idx % len(info_cols)]:
            icon = type_icons.get(col_types[col], "❓")
            detected = auto_types[col]
            final = col_types[col]
            n_unique = df_selected[col].dropna().nunique()
            if final != detected:
                st.markdown(
                    f"{icon} `{col}` — **{final}** ({n_unique} unique)\n"
                    f"<small>⚠️ default: {detected}</small>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"{icon} `{col}` — **{final}** ({n_unique} unique)"
                )
