import streamlit as st
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="Data Viewer", layout="wide")

# URL CSV dari Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQaxuhJ0Ourc8ZBFJ564CaAyXnN-_PBHitjlo64IS5kmRzEdWONKOmL2JXs67hE1lx6YgG-kVbTaXP-/pub?gid=0&single=true&output=csv"

# Cache data agar tidak load ulang setiap interaksi (refresh tiap 5 menit)
@st.cache_data(ttl=300)
def load_data(url):
    return pd.read_csv(url)

st.title("📊 Data Viewer")
st.caption("TF METRO INDAH MALL")

# Muat data
try:
    df = load_data(CSV_URL)

    # Tampilkan info ringkas
    col1, col2, col3 = st.columns(3)
    col1.metric("Jumlah Baris", df.shape[0])
    col2.metric("Jumlah Kolom", df.shape[1])

    st.divider()

    # Sidebar untuk opsi pencarian
    with st.container(border=True):
        st.header("🔍 Pencarian")
        search_col = st.selectbox("Cari di kolom:", ["Semua"] + list(df.columns))
        keyword = st.text_input("Kata kunci:")

    # Filter data jika ada keyword
    if keyword:
        if search_col == "Semua":
            mask = df.astype(str).apply(
                lambda row: row.str.contains(keyword, case=False, na=False).any(),
                axis=1
            )
        else:
            mask = df[search_col].astype(str).str.contains(keyword, case=False, na=False)
        df_filtered = df[mask]
        st.info(f"Ditemukan {df_filtered.shape[0]} baris")
    else:
        df_filtered = df

    # Tampilkan dataframe
    st.subheader("Data")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # Opsi download
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    # st.download_button(
    #     label="⬇️ Download data (CSV)",
    #     data=csv,
    #     file_name="data.csv",
    #     mime="text/csv"
    # )

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
