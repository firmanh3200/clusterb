import streamlit as st
import pandas as pd
import io
import csv

# Konfigurasi halaman
st.set_page_config(
    page_title="Konverter CSV ke Excel",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Konverter CSV ke Excel (xlsx)")
st.markdown("Unggah file CSV, atur opsi, lalu unduh hasilnya dalam format Excel.")

# Sidebar untuk opsi
st.sidebar.header("⚙️ Opsi Konversi")

# Upload file
uploaded_file = st.file_uploader(
    "Pilih file CSV",
    type=["csv", "txt"]
)

if uploaded_file is not None:
    # Opsi delimiter
    delimiter = st.sidebar.selectbox(
        "Delimiter (Pemisah)",
        options=[",", ";", "\t", "|"],
        format_func=lambda x: {"\t": "Tab"}.get(x, x)
    )
    
    # Opsi encoding
    encoding = st.sidebar.selectbox(
        "Encoding",
        options=["utf-8", "utf-8-sig", "latin1", "cp1252"]
    )
    
    # Nama sheet
    sheet_name = st.sidebar.text_input("Nama Sheet", value="Sheet1")
    
    # Opsi header
    header_option = st.sidebar.checkbox("Baris pertama sebagai header", value=True)
    
    # Opsi index
    include_index = st.sidebar.checkbox("Sertakan nomor baris (index)", value=False)
    
    try:
        # Baca file CSV
        df = pd.read_csv(
            uploaded_file,
            delimiter=delimiter,
            encoding=encoding,
            header=0 if header_option else None
        )
        
        # Info file
        st.success(f"✅ File berhasil dimuat! **{df.shape[0]:,} baris** × **{df.shape[1]} kolom**")
        
        # Tab untuk preview dan info
        tab1, tab2 = st.tabs(["👀 Preview Data", "ℹ️ Info Kolom"])
        
        with tab1:
            st.dataframe(df.head(20), use_container_width=True)
            if len(df) > 20:
                st.caption(f"Menampilkan 20 dari {len(df):,} baris")
        
        with tab2:
            col_info = pd.DataFrame({
                "Nama Kolom": df.columns,
                "Tipe Data": df.dtypes.astype(str),
                "Data Kosong": df.isnull().sum().values
            })
            st.dataframe(col_info, use_container_width=True)
        
        # Konversi ke Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(
                writer,
                sheet_name=sheet_name or "Sheet1",
                index=include_index
            )
        buffer.seek(0)
        
        # Nama file output
        output_filename = uploaded_file.name.rsplit(".", 1)[0] + ".xlsx"
        
        # Tombol download
        st.subheader("⬇️ Unduh Hasil Konversi")
        st.download_button(
            label="📥 Download File Excel (.xlsx)",
            data=buffer,
            file_name=output_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {str(e)}")
        st.info("💡 Coba ubah opsi **Delimiter** atau **Encoding** di sidebar.")

else:
    st.info("👆 Silakan unggah file CSV untuk memulai konversi.")
