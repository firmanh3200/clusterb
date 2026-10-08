import streamlit as st
import pandas as pd
import io
import csv
import re
import zipfile

# ================= Konfigurasi Halaman =================
st.set_page_config(
    page_title="Konverter File ke Excel",
    page_icon="📊",
    layout="wide"
)

# ================= Sidebar Info =================
with st.sidebar:
    st.header("ℹ️ Tentang Aplikasi")
    st.markdown(
        """
        **Input didukung:**  
        CSV, TXT, TSV, JSON, Excel (xlsx/xls)

        **Output:**  
        Selalu Excel (.xlsx)

        ---
        **Fitur:**
        - 📄 Konversi file ke Excel
        - ✂️ Split data berdasarkan kolom
          - Multi-sheet dalam 1 file
          - Multi-file (dikompres ZIP)
        """
    )
    st.caption("Dibuat dengan Streamlit + Pandas")

st.title("📊 Konverter File ke Excel (xlsx)")
st.markdown(
    "Konversi berbagai format file ke Excel, lengkap dengan fitur "
    "**✂️ split data** berdasarkan kolom pilihan Anda."
)

# ================= Helper Functions =================

def detect_delimiter(uploaded_file, encoding):
    """Deteksi delimiter secara otomatis dari sampel isi file."""
    sample = uploaded_file.read(4096).decode(encoding, errors="replace")
    uploaded_file.seek(0)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def load_dataframe(uploaded_file, delimiter, encoding, header_option=True):
    """Membaca file upload menjadi DataFrame sesuai ekstensinya."""
    name = uploaded_file.name.lower()

    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    if name.endswith(".json"):
        try:
            return pd.read_json(uploaded_file)
        except ValueError:
            uploaded_file.seek(0)
            return pd.read_json(uploaded_file, lines=True)

    if name.endswith(".tsv"):
        return pd.read_csv(
            uploaded_file, sep="\t", encoding=encoding,
            header=0 if header_option else None
        )

    # .csv / .txt
    if delimiter == "auto":
        delimiter = detect_delimiter(uploaded_file, encoding)

    return pd.read_csv(
        uploaded_file, delimiter=delimiter, encoding=encoding,
        header=0 if header_option else None
    )


def sanitize_sheet_name(name, used_names):
    """Nama sheet Excel: maks 31 karakter, tanpa karakter terlarang, tidak duplikat."""
    name = re.sub(r"[:\\\/\?\*\[\]]", "_", str(name)).strip()
    if not name:
        name = "Sheet"
    name = name[:31]

    base, i = name, 1
    while name.lower() in used_names:
        suffix = f"_{i}"
        name = base[:31 - len(suffix)] + suffix
        i += 1

    used_names.add(name.lower())
    return name


def sanitize_filename(name):
    """Hilangkan karakter terlarang pada nama file."""
    name = re.sub(r'[<>:"/\\|?*]', "_", str(name)).strip()
    return name if name else "file"


def df_to_xlsx_bytes(df, sheet_name="Sheet1", index=False):
    """Konversi DataFrame menjadi bytes file Excel."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=index)
    buf.seek(0)
    return buf.getvalue()


# ================= Tabs Utama =================
tab_convert, tab_split = st.tabs(["📄 Konversi ke Excel", "✂️ Split Berdasarkan Kolom"])

# ------------------- TAB 1: KONVERSI -------------------
with tab_convert:
    uploaded_file = st.file_uploader(
        "Pilih file sumber",
        type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
        key="conv_uploader",
    )

    if uploaded_file is None:
        st.info("👆 Silakan unggah file untuk memulai konversi.")
    else:
        with st.expander("⚙️ Opsi Pembacaan & Output", expanded=True):
            c1, c2, c3 = st.columns(3)
            delimiter = c1.selectbox(
                "Delimiter",
                ["auto", ",", ";", "\t", "|"],
                format_func=lambda x: {"\t": "Tab", "auto": "Auto-detect"}.get(x, x),
            )
            encoding = c2.selectbox("Encoding", ["utf-8", "utf-8-sig", "latin1", "cp1252"])
            sheet_name = c3.text_input("Nama sheet", value="Sheet1")

            c4, c5 = st.columns(2)
            header_option = c4.checkbox("Baris pertama sebagai header", value=True)
            include_index = c5.checkbox("Sertakan nomor index", value=False)

        try:
            df = load_dataframe(uploaded_file, delimiter, encoding, header_option)

            st.success(
                f"✅ File berhasil dimuat! **{df.shape[0]:,} baris** × **{df.shape[1]} kolom**"
            )

            with st.expander("👀 Preview Data (20 baris pertama)", expanded=True):
                st.dataframe(df.head(20), use_container_width=True)
                if len(df) > 20:
                    st.caption(f"Menampilkan 20 dari {len(df):,} baris")

            with st.expander("ℹ️ Info Kolom"):
                info = pd.DataFrame({
                    "Nama Kolom": df.columns,
                    "Tipe Data": df.dtypes.astype(str),
                    "Data Kosong": df.isnull().sum().values,
                })
                st.dataframe(info, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name or "Sheet1", index=include_index)
            buffer.seek(0)

            output_filename = uploaded_file.name.rsplit(".", 1)[0] + ".xlsx"

            st.download_button(
                label="📥 Download File Excel (.xlsx)",
                data=buffer,
                file_name=output_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {e}")
            st.info("💡 Coba ubah opsi **Delimiter** atau **Encoding** di atas.")

# ------------------- TAB 2: SPLIT -------------------
with tab_split:
    st.markdown(
        "Pecah data menjadi **beberapa sheet** (dalam 1 file Excel) atau **beberapa file Excel** "
        "berdasarkan nilai unik dari kolom pilihan Anda."
    )

    split_file = st.file_uploader(
        "Pilih file sumber",
        type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
        key="split_uploader",
    )

    if split_file is None:
        st.info("👆 Silakan unggah file untuk memulai split.")
    else:
        # ---- Opsi pembacaan ----
        with st.expander("⚙️ Opsi Pembacaan File", expanded=False):
            s1, s2, s3 = st.columns(3)
            s_delim = s1.selectbox(
                "Delimiter",
                ["auto", ",", ";", "\t", "|"],
                format_func=lambda x: {"\t": "Tab", "auto": "Auto-detect"}.get(x, x),
                key="split_delim",
            )
            s_enc = s2.selectbox(
                "Encoding", ["utf-8", "utf-8-sig", "latin1", "cp1252"], key="split_enc"
            )
            s_header = s3.checkbox(
                "Baris pertama sebagai header", value=True, key="split_header"
            )

        try:
            df_split = load_dataframe(split_file, s_delim, s_enc, s_header)
        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")
            st.info("💡 Periksa opsi **Delimiter** / **Encoding**, lalu coba lagi.")
            st.stop()

        if df_split.empty:
            st.warning("⚠️ File tidak memiliki data.")
            st.stop()

        st.success(
            f"✅ File dimuat: **{df_split.shape[0]:,} baris** × **{df_split.shape[1]} kolom**"
        )

        # ---- Pilih kolom split ----
        split_col = st.selectbox(
            "🗂️ Pilih kolom untuk memecah data",
            df_split.columns,
            help="Setiap nilai unik pada kolom ini menjadi 1 sheet / 1 file.",
        )

        # ---- Opsi output ----
        st.markdown("#### ⚙️ Opsi Output")
        output_mode = st.radio(
            "Mode output",
            ["📁 Satu file Excel (multi-sheet)", "🗜️ Banyak file Excel (ZIP)"],
            horizontal=True,
            help=(
                "Satu file: setiap nilai unik menjadi sheet terpisah. "
                "ZIP: setiap nilai unik menjadi file Excel tersendiri."
            ),
        )
        o1, o2, o3 = st.columns(3)
        s_index = o1.checkbox("Sertakan nomor index", value=False, key="split_index")
        s_prefix = o2.text_input("Prefix nama sheet/file", value="", key="split_prefix")
        na_label = o3.text_input("Label untuk sel kosong (NaN)", value="(kosong)", key="split_na")

        # ---- Ringkasan nilai unik ----
        keys = df_split[split_col].fillna(na_label).astype(str)
        value_counts = keys.value_counts()
        n_groups = len(value_counts)

        st.markdown(f"🔢 Kolom **`{split_col}`** memiliki **{n_groups} nilai unik**")

        with st.expander("📊 Ringkasan jumlah baris per nilai", expanded=True):
            summary = value_counts.rename_axis(split_col).reset_index(name="Jumlah Baris")
            summary["Persentase"] = (summary["Jumlah Baris"] / len(df_split) * 100).round(2)
            st.dataframe(summary, use_container_width=True, height=250)

        if n_groups > 100:
            st.warning(
                "⚠️ Nilai unik sangat banyak (>100). Proses bisa lambat, dan nama sheet "
                "dibatasi maksimal 31 karakter oleh Excel."
            )

        # ---- Proses split ----
        base_name = sanitize_filename(split_file.name.rsplit(".", 1)[0])

        if st.button("🚀 Proses Split Sekarang", type="primary", use_container_width=True):
            progress = st.progress(0.0, text="Memulai...")
            used = set()

            try:
                if output_mode.startswith("📁"):
                    # === Mode 1: satu file Excel, multi-sheet ===
                    out_buf = io.BytesIO()
                    with pd.ExcelWriter(out_buf, engine="openpyxl") as writer:
                        for i, (val, group_df) in enumerate(
                            df_split.groupby(keys, sort=False), start=1
                        ):
                            sheet = sanitize_sheet_name(f"{s_prefix}{val}", used)
                            group_df.to_excel(writer, sheet_name=sheet, index=s_index)
                            progress.progress(
                                i / n_groups,
                                text=f"Menulis sheet {i}/{n_groups}: {sheet}",
                            )
                    out_buf.seek(0)

                    st.session_state["split_result"] = {
                        "data": out_buf.getvalue(),
                        "filename": f"{base_name}_split.xlsx",
                        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "n": n_groups,
                        "unit": "sheet",
                    }

                else:
                    # === Mode 2: ZIP berisi banyak file Excel ===
                    zip_buf = io.BytesIO()
                    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, (val, group_df) in enumerate(
                            df_split.groupby(keys, sort=False), start=1
                        ):
                            fname = sanitize_filename(f"{s_prefix}{base_name}_{val}.xlsx")
                            xlsx = df_to_xlsx_bytes(
                                group_df,
                                sheet_name=sanitize_sheet_name(val, set()),
                                index=s_index,
                            )
                            zf.writestr(fname, xlsx)
                            progress.progress(
                                i / n_groups,
                                text=f"Membuat file {i}/{n_groups}: {fname}",
                            )
                    zip_buf.seek(0)

                    st.session_state["split_result"] = {
                        "data": zip_buf.getvalue(),
                        "filename": f"{base_name}_split.zip",
                        "mime": "application/zip",
                        "n": n_groups,
                        "unit": "file",
                    }

                progress.progress(1.0, text="Selesai! ✅")

            except Exception as e:
                progress.empty()
                st.error(f"❌ Gagal memproses: {e}")

        # ---- Tombol download hasil ----
        if "split_result" in st.session_state:
            res = st.session_state["split_result"]
            st.success(f"✅ Berhasil! Data dipecah menjadi **{res['n']} {res['unit']}**.")
            st.download_button(
                label=f"📥 Download {res['filename']}",
                data=res["data"],
                file_name=res["filename"],
                mime=res["mime"],
                type="primary",
                use_container_width=True,
                key="split_download",
            )
            st.caption("Ubah pengaturan lalu klik **Proses Split** lagi untuk output baru.")
