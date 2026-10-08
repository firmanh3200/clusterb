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
        - 📌 Pilih baris mana yang jadi header
        - 📋 Pilih sheet (untuk file Excel)
        """
    )
    st.caption("Dibuat dengan Streamlit + Pandas")

st.title("📊 Konverter File ke Excel (xlsx)")
st.markdown(
    "Konversi berbagai format file ke Excel, lengkap dengan fitur "
    "**✂️ split data** dan **📌 penentuan baris header**."
)

# ================= Helper Functions =================

def is_excel(name):
    return str(name).lower().endswith((".xlsx", ".xls"))


def is_json(name):
    return str(name).lower().endswith(".json")


def detect_delimiter(uploaded_file, encoding):
    """Deteksi delimiter secara otomatis dari sampel isi file."""
    sample = uploaded_file.read(4096).decode(encoding, errors="replace")
    uploaded_file.seek(0)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def load_dataframe(uploaded_file, delimiter="auto", encoding="utf-8",
                   use_header=True, header_row=1, sheet_name=0):
    """Membaca file upload menjadi DataFrame sesuai ekstensinya."""
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()

    # UI memakai nomor baris basis-1, pandas memakai basis-0
    header_idx = header_row - 1 if use_header else None

    if is_excel(name):
        return pd.read_excel(uploaded_file, sheet_name=sheet_name, header=header_idx)

    if is_json(name):
        try:
            return pd.read_json(uploaded_file)
        except ValueError:
            uploaded_file.seek(0)
            return pd.read_json(uploaded_file, lines=True)

    if name.endswith(".tsv"):
        return pd.read_csv(uploaded_file, sep="\t", encoding=encoding, header=header_idx)

    if delimiter == "auto":
        delimiter = detect_delimiter(uploaded_file, encoding)

    return pd.read_csv(
        uploaded_file, delimiter=delimiter, encoding=encoding, header=header_idx
    )


def load_raw_preview(uploaded_file, delimiter, encoding, sheet_name=0, n_rows=15):
    """Baca beberapa baris pertama TANPA asumsi header (untuk membantu pilih baris header)."""
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()

    if is_excel(name):
        return pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None, nrows=n_rows)

    if is_json(name):
        return None  # JSON tidak punya konsep baris header

    if name.endswith(".tsv"):
        return pd.read_csv(uploaded_file, sep="\t", encoding=encoding,
                           header=None, nrows=n_rows)

    if delimiter == "auto":
        delimiter = detect_delimiter(uploaded_file, encoding)

    return pd.read_csv(uploaded_file, delimiter=delimiter, encoding=encoding,
                       header=None, nrows=n_rows)


def render_read_options(uploaded_file, key_prefix, expanded=True):
    """
    Komponen UI opsi pembacaan: delimiter, encoding, sheet, dan baris header.
    Return dict parameter siap pakai untuk load_dataframe().
    """
    excel = is_excel(uploaded_file.name)
    json_file = is_json(uploaded_file.name)

    with st.expander("⚙️ Opsi Pembacaan File", expanded=expanded):
        # ---------- Pilih sheet (khusus Excel) ----------
        sheet_name = 0
        if excel:
            xls = pd.ExcelFile(uploaded_file)
            sheets = list(xls.sheet_names)
            uploaded_file.seek(0)
            if len(sheets) > 1:
                sheet_name = st.selectbox(
                    "📋 Pilih sheet",
                    sheets,
                    key=f"{key_prefix}_sheet",
                    help="Sheet mana dari file Excel yang akan dibaca.",
                )
            else:
                st.caption(f"📋 Sheet: `{sheets[0]}`")
                sheet_name = sheets[0]

        # ---------- Delimiter & encoding (khusus file teks) ----------
        delimiter, encoding = ",", "utf-8"
        if not excel and not json_file:
            c1, c2 = st.columns(2)
            delimiter = c1.selectbox(
                "Delimiter",
                ["auto", ",", ";", "\t", "|"],
                format_func=lambda x: {"\t": "Tab", "auto": "Auto-detect"}.get(x, x),
                key=f"{key_prefix}_delim",
            )
            encoding = c2.selectbox(
                "Encoding",
                ["utf-8", "utf-8-sig", "latin1", "cp1252"],
                key=f"{key_prefix}_enc",
            )
        elif json_file:
            st.caption("📄 Format JSON tidak memerlukan pengaturan header/delimiter.")

        # ---------- Penentuan baris header ----------
        use_header, header_row = True, 1
        if not json_file:
            st.markdown("**📌 Penentuan Baris Header**")

            # Preview baris mentah agar user tahu harus memilih baris ke berapa
            with st.expander("🔍 Lihat 15 baris mentah (bantu tentukan baris header)"):
                raw = load_raw_preview(uploaded_file, delimiter, encoding, sheet_name)
                if raw is not None and not raw.empty:
                    raw_show = raw.copy()
                    raw_show.index = [f"Baris {i + 1}" for i in raw_show.index]
                    st.dataframe(raw_show, use_container_width=True)
                    st.caption(
                        "💡 Baris yang berisi nama-nama kolom itulah yang "
                        "sebaiknya dipilih sebagai header."
                    )
                uploaded_file.seek(0)

            cA, cB = st.columns(2)
            use_header = cA.checkbox(
                "Gunakan baris sebagai header",
                value=True,
                key=f"{key_prefix}_usehdr",
            )
            header_row = cB.number_input(
                "Nomor baris header (mulai dari 1)",
                min_value=1,
                max_value=1000,
                value=1,
                step=1,
                disabled=not use_header,
                key=f"{key_prefix}_hdrrow",
                help=(
                    "Contoh: jika baris 1–3 berisi judul laporan dan nama kolom ada "
                    "di baris 4, isi dengan 4. Baris di atas header akan dilewati."
                ),
            )

    return {
        "delimiter": delimiter,
        "encoding": encoding,
        "use_header": use_header,
        "header_row": int(header_row),
        "sheet_name": sheet_name,
    }


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
        # ----- Opsi pembacaan (termasuk baris header) -----
        opts = render_read_options(uploaded_file, "conv")

        # ----- Opsi output -----
        with st.expander("⚙️ Opsi Output Excel", expanded=True):
            o1, o2 = st.columns(2)
            sheet_out = o1.text_input("Nama sheet output", value="Sheet1")
            include_index = o2.checkbox("Sertakan nomor index", value=False)

        try:
            df = load_dataframe(uploaded_file, **opts)

            st.success(
                f"✅ File berhasil dimuat! **{df.shape[0]:,} baris** × **{df.shape[1]} kolom**"
            )
            if opts["use_header"] and opts["header_row"] > 1:
                st.caption(
                    f"ℹ️ Baris ke-{opts['header_row']} dipakai sebagai header; "
                    f"{opts['header_row'] - 1} baris di atasnya dilewati."
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
                df.to_excel(writer, sheet_name=sheet_out or "Sheet1", index=include_index)
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
            st.info("💡 Cek kembali **Delimiter**, **Encoding**, atau **Nomor Baris Header**.")

# ------------------- TAB 2: SPLIT -------------------
with tab_split:
    st.markdown(
        "Pecah data menjadi **beberapa sheet** (dalam 1 file Excel) atau "
        "**beberapa file Excel** (ZIP) berdasarkan nilai unik dari kolom pilihan Anda."
    )

    split_file = st.file_uploader(
        "Pilih file sumber",
        type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
        key="split_uploader",
    )

    if split_file is None:
        st.info("👆 Silakan unggah file untuk memulai split.")
    else:
        # ----- Opsi pembacaan (termasuk baris header) -----
        opts_s = render_read_options(split_file, "split", expanded=False)

        try:
            df_split = load_dataframe(split_file, **opts_s)
        except Exception as e:
            st.error(f"❌ Gagal membaca file: {e}")
            st.info("💡 Periksa opsi **Delimiter**, **Encoding**, atau **Nomor Baris Header**.")
            st.stop()

        if df_split.empty:
            st.warning("⚠️ File tidak memiliki data.")
            st.stop()

        st.success(
            f"✅ File dimuat: **{df_split.shape[0]:,} baris** × **{df_split.shape[1]} kolom**"
        )
        if opts_s["use_header"] and opts_s["header_row"] > 1:
            st.caption(f"ℹ️ Header diambil dari baris ke-{opts_s['header_row']}.")

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
        p1, p2, p3 = st.columns(3)
        s_index = p1.checkbox("Sertakan nomor index", value=False, key="split_index")
        s_prefix = p2.text_input("Prefix nama sheet/file", value="", key="split_prefix")
        na_label = p3.text_input("Label untuk sel kosong (NaN)", value="(kosong)", key="split_na")

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
