import os
import zlib
import struct
import hashlib
from collections import defaultdict
import streamlit as st
import pandas as pd
import io
import csv
import re
import zipfile

# ================= Konfigurasi Halaman =================
st.set_page_config(
    page_title="File Toolkit",
    page_icon="📊",
    layout="wide"
)

# ================= Sidebar Info =================
with st.expander("ℹ️ Tentang Aplikasi"):
    #st.header("")
    st.markdown(
    """
    **Input didukung:**  
    CSV, TXT, TSV, JSON, Excel (xlsx/xls), ZIP, dan file lainnya

    **Output:**  
    Excel (.xlsx), CSV, atau ZIP

    ---
    **Fitur (7 tab):**
    - 📄 Konversi file ke Excel
    - ✂️ Split data berdasarkan kolom
    - 🔗 Merge/gabung beberapa file
    - 🗜️ Compress & decompress ZIP
    - 🛠️ Perbaikan file rusak (repair)
    - 🏷️ Batch rename & batch processing
    - 🔍 Deteksi duplikat (antar file & antar baris)
    """
    )
    #st.caption("Dibuat dengan Streamlit + Pandas")

st.title("📊 File Toolkit")
st.divider()
# st.markdown(
#     "Toolkit untuk konversi format file ke Excel, lengkap dengan fitur "
#     "**✂️ split data** dan **📌 penentuan baris header**."
# )

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
    
# ================= Helper Tambahan (Tab Baru) =================

def human_size(n):
    """Format ukuran bytes menjadi mudah dibaca."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.2f} {unit}"
        n /= 1024
    return f"{n:,.2f} PB"


def detect_file_type(raw):
    """Deteksi tipe file dari magic bytes (bukan sekadar ekstensi)."""
    if raw[:4] == b"PK\x03\x04":
        return "zip"
    if raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "ole"
    sample = raw[:8192]
    for enc in ("utf-8", "cp1252", "latin1"):
        try:
            sample.decode(enc)
            return "text"
        except (UnicodeDecodeError, LookupError):
            continue
    return "binary"


def unique_name(name, used):
    """Pastikan nama unik dalam satu set (untuk isi ZIP)."""
    base, ext = os.path.splitext(name)
    k = 1
    while name.lower() in used:
        name = f"{base}_{k}{ext}"
        k += 1
    used.add(name.lower())
    return name


def repair_text_data(raw, delimiter="auto", fix_encoding=True,
                     remove_empty=True, fix_ragged=True, dedupe_header=True):
    """Perbaiki file data teks (CSV/TXT) yang bermasalah. Return (rows, report, enc, delim, n_before)."""
    report = []

    # --- 1) Encoding dengan fallback otomatis ---
    text, used_enc = None, None
    if fix_encoding:
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
            try:
                text = raw.decode(enc)
                used_enc = enc
                break
            except (UnicodeDecodeError, LookupError):
                continue
        if text is None:
            text = raw.decode("utf-8", errors="replace")
            used_enc = "utf-8 (karakter rusak diganti)"
            report.append("⚠️ Encoding tidak dapat dikenali; karakter tidak valid diganti.")
    else:
        text = raw.decode("utf-8", errors="replace")
        used_enc = "utf-8 (replace)"

    # --- 2) Normalisasi line ending & BOM ---
    n_crlf = text.count("\r\n")
    if n_crlf:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        report.append(f"🔧 {n_crlf:,} akhir baris CRLF dinormalkan.")
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
        report.append("🔧 BOM di awal file dihapus.")

    # --- 3) Deteksi delimiter & parse ---
    if delimiter == "auto":
        try:
            delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","

    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    n_before = len(rows)
    if not rows:
        return [], ["File kosong / tidak berisi data."], used_enc, delimiter, n_before

    # --- 4) Hapus baris kosong ---
    if remove_empty:
        cleaned = [r for r in rows if any(str(c).strip() for c in r)]
        removed = len(rows) - len(cleaned)
        if removed:
            report.append(f"🔧 {removed:,} baris kosong dihapus.")
        rows = cleaned
        if not rows:
            return [], report + ["⚠️ Semua baris kosong — tidak ada data tersisa."], used_enc, delimiter, n_before

    # --- 5) Samakan jumlah kolom (ragged rows) ---
    n_cols = max(len(r) for r in rows)
    if fix_ragged:
        padded = cut = 0
        fixed = []
        for r in rows:
            if len(r) < n_cols:
                fixed.append(r + [""] * (n_cols - len(r)))
                padded += 1
            elif len(r) > n_cols:
                fixed.append(r[:n_cols])
                cut += 1
            else:
                fixed.append(r)
        rows = fixed
        if padded:
            report.append(f"🔧 {padded:,} baris kekurangan kolom — dilengkapi sel kosong.")
        if cut:
            report.append(f"🔧 {cut:,} baris kelebihan kolom — dipotong menjadi {n_cols} kolom.")

    # --- 6) Hapus baris header yang terulang ---
    if dedupe_header and len(rows) > 1:
        header = [str(c).strip().lower() for c in rows[0]]
        dup_idx = [i for i, r in enumerate(rows[1:], start=1)
                   if [str(c).strip().lower() for c in r] == header]
        if dup_idx:
            for i in reversed(dup_idx):
                rows.pop(i)
            report.append(f"🔧 {len(dup_idx)} baris header yang terulang dihapus.")

    if not report:
        report.append("✅ Tidak ditemukan masalah struktural yang perlu diperbaiki.")

    return rows, report, used_enc, delimiter, n_before


def recover_zip_members(raw):
    """Pulihkan isi ZIP rusak dengan memindai local file header (PK\x03\x04) secara mentah."""
    recovered = {}
    sig = b"PK\x03\x04"
    pos = 0
    while True:
        idx = raw.find(sig, pos)
        if idx < 0:
            break
        try:
            (_, _, flags, method, _, _,
             _crc, comp_size, _, name_len, extra_len) = struct.unpack(
                "<4sHHHHHIIIHH", raw[idx:idx + 30]
            )
            name = raw[idx + 30: idx + 30 + name_len].decode("utf-8", errors="replace")
            data_start = idx + 30 + name_len + extra_len
            if comp_size > 0:
                blob = raw[data_start: data_start + comp_size]
            elif flags & 0x08:  # streamed: ukuran tidak diketahui
                blob = raw[data_start:]
            else:
                blob = b""
            if method == zipfile.ZIP_STORED:
                recovered[name] = blob
            elif method == zipfile.ZIP_DEFLATED:
                recovered[name] = zlib.decompressobj(-15).decompress(blob)
            pos = data_start + max(comp_size, 4)
        except Exception:
            pos = idx + 4
    return recovered


# ================= Tabs Utama =================
# ================= Tabs Utama =================
tab_split, tab_convert, tab_merge, tab_zip, tab_repair, tab_batch, tab_dup = st.tabs(
    [
        "✂️ Split File |",
        "📄 Konversi ke Excel |",
        "🔗 Merge File |",
        "🗜️ Compress File |",
        "🛠️ File Repair |",
        "🏷️ Batch Processing |",
        "🔍 Duplikasi",
    ]
)

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

# ------------------- TAB 3: MERGE -------------------
with tab_merge:
    st.markdown(
        "Gabungkan **beberapa file data** menjadi satu file Excel — tumpuk barisnya "
        "(vertikal) atau satukan kolomnya (horizontal)."
    )

    merge_files = st.file_uploader(
        "Pilih beberapa file sumber (min. 2 file)",
        type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
        accept_multiple_files=True,
        key="merge_uploader",
    )

    if not merge_files:
        st.info("👆 Silakan unggah minimal 2 file untuk digabung.")
    else:
        frames, labels = [], []
        for i, mf in enumerate(merge_files):
            st.markdown(f"**📄 {i + 1}. `{mf.name}`**")
            opts_m = render_read_options(mf, f"merge{i}", expanded=False)
            try:
                frames.append(load_dataframe(mf, **opts_m))
                labels.append(mf.name)
            except Exception as e:
                st.error(f"❌ Gagal membaca `{mf.name}`: {e}")

        if len(frames) >= 2:
            merge_mode = st.radio(
                "Mode penggabungan",
                ["Vertikal — menumpuk baris", "Horizontal — menyandingkan kolom"],
                horizontal=True,
                key="merge_mode",
            )

            add_source = False
            if merge_mode.startswith("Vertikal"):
                add_source = st.checkbox(
                    "Tambah kolom `_sumber` (nama file asal tiap baris)",
                    value=True,
                    key="merge_source",
                )
                st.caption("💡 Kolom yang tidak ada di semua file akan diisi sel kosong (gabungan semua kolom).")
            else:
                st.caption("💡 Baris disandingkan berdasarkan urutan; jumlah baris hasil = file terpanjang.")

            n_rows = sum(len(f) for f in frames)
            n_cols = sum(f.shape[1] for f in frames)
            st.markdown(f"🔢 Total: **{n_rows:,} baris / {n_cols} kolom** dari {len(frames)} file siap digabung.")

            if st.button("🚀 Gabungkan Sekarang", type="primary", use_container_width=True, key="merge_run"):
                try:
                    if merge_mode.startswith("Vertikal"):
                        prepared = [
                            f.assign(**{"_sumber": lab}) if add_source else f
                            for f, lab in zip(frames, labels)
                        ]
                        merged = pd.concat(prepared, axis=0, ignore_index=True, sort=False)
                        out_name = "merged.xlsx"
                    else:
                        merged = pd.concat([f.reset_index(drop=True) for f in frames], axis=1)
                        out_name = "merged_horizontal.xlsx"

                    st.session_state["merge_result"] = {
                        "data": df_to_xlsx_bytes(merged, sheet_name="Merged"),
                        "filename": out_name,
                        "rows": merged.shape[0],
                        "cols": merged.shape[1],
                        "preview": merged.head(20),
                    }
                except Exception as e:
                    st.error(f"❌ Gagal menggabungkan: {e}")

            if "merge_result" in st.session_state:
                res = st.session_state["merge_result"]
                st.success(f"✅ Hasil merge: **{res['rows']:,} baris** × **{res['cols']} kolom**")
                with st.expander("👀 Preview hasil (20 baris pertama)"):
                    st.dataframe(res["preview"], use_container_width=True)
                st.download_button(
                    label=f"📥 Download {res['filename']}",
                    data=res["data"],
                    file_name=res["filename"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                    key="merge_download",
                )
        else:
            st.warning("⚠️ Butuh minimal 2 file yang berhasil dibaca untuk melakukan merge.")
            
# ------------------- TAB 4: COMPRESS / DECOMPRESS -------------------
with tab_zip:
    mode_cd = st.radio(
        "Pilih mode",
        ["🗜️ Compress — buat arsip ZIP", "📦 Decompress — ekstrak isi ZIP"],
        horizontal=True,
        key="cd_mode",
    )

    if mode_cd.startswith("🗜️"):
        st.markdown("Kemas beberapa file menjadi **satu arsip ZIP**.")
        zip_files = st.file_uploader(
            "Pilih file yang akan dikompres (jenis apa pun)",
            accept_multiple_files=True,
            key="zip_up",
        )
        if not zip_files:
            st.info("👆 Silakan unggah file untuk dikompres.")
        else:
            zc1, zc2 = st.columns(2)
            arch_name = zc1.text_input("Nama arsip", value="arsip", key="arch_name")
            method_label = zc2.selectbox(
                "Metode kompresi",
                ["Deflate — standar", "BZip2 — kompresi kuat",
                 "LZMA — kompresi terkuat", "Stored — tanpa kompresi (cepat)"],
                key="zip_method",
            )
            method_map = {
                "Deflate — standar": zipfile.ZIP_DEFLATED,
                "BZip2 — kompresi kuat": zipfile.ZIP_BZIP2,
                "LZMA — kompresi terkuat": zipfile.ZIP_LZMA,
                "Stored — tanpa kompresi (cepat)": zipfile.ZIP_STORED,
            }
            total_in = sum(f.size for f in zip_files)
            st.markdown(f"🔢 **{len(zip_files)} file** — total {human_size(total_in)}")

            if st.button("🗜️ Buat ZIP Sekarang", type="primary", use_container_width=True, key="zip_run"):
                try:
                    zbuf = io.BytesIO()
                    used = set()
                    with zipfile.ZipFile(zbuf, "w", method_map[method_label]) as zf:
                        for f in zip_files:
                            zf.writestr(unique_name(sanitize_filename(f.name), used), f.getvalue())
                    zbuf.seek(0)
                    st.session_state["zip_result"] = {
                        "data": zbuf.getvalue(),
                        "filename": sanitize_filename(arch_name or "arsip") + ".zip",
                        "size_in": total_in,
                    }
                except Exception as e:
                    st.error(f"❌ Gagal membuat ZIP: {e}")

            if "zip_result" in st.session_state:
                res = st.session_state["zip_result"]
                ratio = (1 - len(res["data"]) / res["size_in"]) * 100 if res["size_in"] else 0
                st.success(
                    f"✅ ZIP dibuat: **{human_size(len(res['data']))}** "
                    f"(dari {human_size(res['size_in'])}, hemat {max(ratio, 0):.1f}%)"
                )
                st.download_button(
                    label=f"📥 Download {res['filename']}",
                    data=res["data"],
                    file_name=res["filename"],
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="zip_download",
                )

    else:
        st.markdown("Lihat isi, preview, dan **ekstrak file dari arsip ZIP**.")
        zip_in = st.file_uploader("Unggah arsip ZIP", type=["zip"], key="unzip_up")
        if zip_in is None:
            st.info("👆 Silakan unggah file .zip.")
        else:
            zf = None
            try:
                zf = zipfile.ZipFile(io.BytesIO(zip_in.getvalue()))
                infos = zf.infolist()
            except zipfile.BadZipFile:
                st.error("❌ ZIP rusak atau bukan ZIP valid — coba tab **🛠️ File Repair**.")

            if zf is not None:
                if any(i.flag_bits & 0x1 for i in infos):
                    st.warning("🔒 Arsip ini terenkripsi — ekstraksi akan gagal tanpa password.")

                st.success(f"✅ ZIP valid: **{len(infos)} entri** — {human_size(zip_in.size)}")
                st.dataframe(
                    pd.DataFrame([{
                        "Nama": i.filename,
                        "Ukuran Asli": human_size(i.file_size),
                        "Terkompres": human_size(i.compress_size),
                    } for i in infos]),
                    use_container_width=True,
                )

                names = [i.filename for i in infos]
                sel = st.multiselect("📦 Pilih entri yang ingin diekstrak", names, default=names, key="unzip_sel")

                if not sel:
                    st.warning("⚠️ Belum ada entri dipilih.")
                else:
                    for i, info in enumerate(infos):
                        if info.filename not in sel:
                            continue
                        with st.expander(f"📄 `{info.filename}` ({human_size(info.file_size)})"):
                            raw = None
                            try:
                                raw = zf.read(info)
                            except RuntimeError:
                                st.error("🔒 Entri terenkripsi — tidak bisa diekstrak tanpa password.")
                            except Exception as e:
                                st.error(f"❌ Gagal mengekstrak: {e}")

                            if raw is not None:
                                dl_name = os.path.basename(info.filename.replace("\\", "/")) or f"file_{i}"
                                st.download_button(
                                    f"📥 Download `{dl_name}`",
                                    data=raw,
                                    file_name=dl_name,
                                    key=f"unzip_dl_{i}",
                                )
                                # Preview untuk file teks
                                head = raw[:2048]
                                preview_text = None
                                for enc in ("utf-8", "cp1252"):
                                    try:
                                        preview_text = head.decode(enc)
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                if preview_text is not None:
                                    st.text(preview_text[:1500])
                                    st.caption("👀 Preview (maks. 1.500 karakter pertama).")
                                else:
                                    st.caption("🚫 Preview tidak tersedia (file biner).")
                                    
# ------------------- TAB 5: FILE REPAIR -------------------
with tab_repair:
    st.markdown(
        "Perbaiki file bermasalah: **encoding kacau**, **baris tidak rata**, **baris kosong**, "
        "**header terulang**, atau **ZIP rusak**. Hasil perbaikan bersifat *best-effort* — "
        "selalu cek hasil sebelum dipakai."
    )
    rep_file = st.file_uploader("Unggah file yang bermasalah", key="repair_up")

    if rep_file is None:
        st.info("👆 Silakan unggah file yang ingin diperbaiki.")
    else:
        raw = rep_file.getvalue()
        ftype = detect_file_type(raw)
        badge = {
            "zip": "🗜️ ZIP (termasuk .xlsx/.docx modern)",
            "ole": "📄 Dokumen Office lama (.xls/.doc)",
            "text": "📝 File teks (CSV/TXT/JSON/...)",
            "binary": "🧱 File biner tidak dikenal",
        }[ftype]
        st.markdown(f"🔎 **Tipe terdeteksi dari isi file:** {badge} — `{rep_file.name}`")

        if ftype != "zip":
            st.session_state.pop("repair_zip", None)
        if ftype != "text":
            st.session_state.pop("repair_text", None)

        if ftype == "zip":
            recovered, bad, ok_normal = {}, [], True
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zfr:
                    for info in zfr.infolist():
                        if info.is_dir():
                            continue
                        try:
                            recovered[info.filename] = zfr.read(info)
                        except Exception:
                            bad.append(info.filename)
            except zipfile.BadZipFile:
                ok_normal = False
                recovered = {k: v for k, v in recover_zip_members(raw).items() if not k.endswith("/")}

            if not ok_normal:
                st.info("ℹ️ Direktori ZIP rusak — pemulihan dilakukan dengan pemindaian mentah (best-effort).")
            if bad:
                st.warning(f"⚠️ {len(bad)} entri tidak dapat dibaca: {', '.join(bad[:5])}...")
            if recovered:
                st.success(f"✅ {len(recovered)} file berhasil dipulihkan.")
                st.session_state["repair_zip"] = recovered
            else:
                st.error("❌ Tidak ada file yang bisa dipulihkan dari arsip ini.")

        elif ftype == "ole":
            try:
                df_rep = pd.read_excel(io.BytesIO(raw))
                st.success("✅ File lama berhasil dibaca! Tulis ulang ke format .xlsx yang bersih.")
                st.dataframe(df_rep.head(20), use_container_width=True)
                st.download_button(
                    "📥 Download versi .xlsx",
                    data=df_to_xlsx_bytes(df_rep),
                    file_name=sanitize_filename(rep_file.name.rsplit(".", 1)[0]) + "_repaired.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="repair_ole_dl",
                )
            except Exception as e:
                st.error(f"❌ File tidak dapat dibaca: {e}")
                st.info("💡 .xls lama yang rusak parah sulit diperbaiki otomatis. Coba buka di Excel/LibreOffice lalu simpan ulang.")

        elif ftype == "text":
            st.caption(
                "💡 Termasuk kasus umum: **CSV yang di-rename menjadi .xlsx** — tipe asli dideteksi "
                "dari isi file, bukan ekstensinya."
            )
            with st.expander("⚙️ Opsi Perbaikan", expanded=True):
                r1, r2 = st.columns(2)
                fix_enc = r1.checkbox("Perbaiki encoding (fallback otomatis)", value=True, key="rep_enc")
                rm_empty = r2.checkbox("Hapus baris kosong", value=True, key="rep_empty")
                r3, r4 = st.columns(2)
                fix_ragged = r3.checkbox("Samakan jumlah kolom antar baris", value=True, key="rep_ragged")
                dedupe_hdr = r4.checkbox("Hapus baris header yang terulang", value=True, key="rep_hdr")
                rep_delim = st.selectbox(
                    "Delimiter", ["auto", ",", ";", "\t", "|"],
                    format_func=lambda x: {"\t": "Tab", "auto": "Auto-detect"}.get(x, x),
                    key="rep_delim",
                )

            if st.button("🛠️ Jalankan Perbaikan", type="primary", use_container_width=True, key="rep_run"):
                try:
                    rows, report, used_enc, delim_used, n_before = repair_text_data(
                        raw, delimiter=rep_delim, fix_encoding=fix_enc,
                        remove_empty=rm_empty, fix_ragged=fix_ragged, dedupe_header=dedupe_hdr,
                    )
                    st.session_state["repair_text"] = {
                        "rows": rows, "report": report, "enc": used_enc,
                        "delim": delim_used, "n_before": n_before,
                    }
                except Exception as e:
                    st.error(f"❌ Gagal memperbaiki: {e}")

            if "repair_text" in st.session_state:
                rt = st.session_state["repair_text"]
                rows = rt["rows"]
                st.markdown("#### 📋 Laporan Perbaikan")
                st.markdown(f"- Encoding terpakai: `{rt['enc']}` — Delimiter: `{rt['delim']}`")
                st.markdown(
                    f"- Baris terbaca: **{rt['n_before']:,}** → hasil akhir: "
                    f"**{len(rows):,} baris** × **{len(rows[0]) if rows else 0} kolom**"
                )
                for msg in rt["report"]:
                    st.markdown(f"- {msg}")

                if rows:
                    with st.expander("👀 Preview hasil (15 baris pertama)"):
                        prev = pd.DataFrame(rows[1:15], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows[:1])
                        st.dataframe(prev, use_container_width=True)

                    base_rep = sanitize_filename(rep_file.name.rsplit(".", 1)[0]) + "_repaired"
                    sout = io.StringIO()
                    csv.writer(sout, delimiter=rt["delim"]).writerows(rows)
                    col1, col2 = st.columns(2)
                    col1.download_button(
                        "📥 Download CSV hasil perbaikan",
                        data=sout.getvalue().encode("utf-8"),
                        file_name=base_rep + ".csv",
                        mime="text/csv",
                        key="rep_dl_csv",
                    )
                    df_out = pd.DataFrame(rows[1:], columns=rows[0])
                    col2.download_button(
                        "📥 Download Excel hasil perbaikan",
                        data=df_to_xlsx_bytes(df_out, sheet_name="Data"),
                        file_name=base_rep + ".xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="rep_dl_xlsx",
                    )
        else:
            st.error("❌ Tipe file biner tidak dikenal — perbaikan otomatis tidak tersedia untuk format ini.")

        # --- Download hasil pemulihan ZIP ---
        if st.session_state.get("repair_zip"):
            recovered = st.session_state["repair_zip"]
            st.markdown("#### 📦 Hasil Pemulihan ZIP")
            rzbuf = io.BytesIO()
            with zipfile.ZipFile(rzbuf, "w", zipfile.ZIP_DEFLATED) as zout:
                used = set()
                for fname, data in recovered.items():
                    zout.writestr(unique_name(sanitize_filename(fname), used), data)
            rzbuf.seek(0)
            for i, (fname, data) in enumerate(recovered.items()):
                with st.expander(f"📄 `{fname}` ({human_size(len(data))})"):
                    st.download_button(
                        f"📥 Download `{os.path.basename(fname) or f'recovered_{i}'}`",
                        data=data,
                        file_name=os.path.basename(fname) or f"recovered_{i}",
                        key=f"rep_zip_dl_{i}",
                    )
            st.download_button(
                f"📥 Download semua sebagai ZIP ({len(recovered)} file)",
                data=rzbuf.getvalue(),
                file_name="recovered.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
                key="rep_zip_all",
            )
            
# ------------------- TAB 6: BATCH RENAME & PROCESSING -------------------
with tab_batch:
    mode_bp = st.radio(
        "Pilih mode",
        ["🏷️ Batch Rename — ubah banyak nama file sekaligus",
         "⚙️ Batch Processing — olah isi banyak file sekaligus"],
        horizontal=True,
        key="bp_mode",
    )

    if mode_bp.startswith("🏷️"):
        st.markdown("Ubah nama banyak file sekaligus dengan pola tertentu, lalu unduh sebagai ZIP.")
        ren_files = st.file_uploader(
            "Unggah file yang akan di-rename", accept_multiple_files=True, key="ren_up"
        )
        if not ren_files:
            st.info("👆 Silakan unggah satu atau lebih file.")
        else:
            with st.expander("⚙️ Aturan Penggantian Nama", expanded=True):
                a1, a2 = st.columns(2)
                ren_find = a1.text_input("🔍 Cari teks dalam nama (kosongkan = lewati)", key="ren_find")
                ren_repl = a2.text_input("✏️ Ganti dengan", key="ren_repl")

                b1, b2 = st.columns(2)
                ren_prefix = b1.text_input("➕ Prefix", key="ren_prefix")
                ren_suffix = b2.text_input("➕ Suffix (sebelum ekstensi)", key="ren_suffix")

                c1, c2, c3 = st.columns(3)
                ren_case = c1.selectbox(
                    "Capitalization",
                    ["Tetap", "huruf kecil semua", "HURUF BESAR SEMUA", "Kapital Tiap Kata"],
                    key="ren_case",
                )
                ren_ext = c2.selectbox("Ekstensi", ["Ikuti asal", ".csv", ".txt", ".xlsx", ".json", ".zip"], key="ren_ext")
                ren_start = c3.number_input("Nomor urut mulai dari", min_value=0, value=1, step=1, key="ren_start")

                ren_numbering = st.checkbox("Tambahkan nomor urut di depan nama", value=True, key="ren_num")
                if ren_numbering:
                    ren_pattern = st.text_input(
                        "Pola nomor (pakai {i})", value="{i:03d}_", key="ren_pat",
                        help="Contoh: `{i:03d}_` → 001_, 002_, ... | `{i}_` → 1_, 2_, ...",
                    )

            # ---- Hitung nama baru ----
            new_names, used, conflicts = [], set(), 0
            for i, f in enumerate(ren_files, start=int(ren_start)):
                base, ext = os.path.splitext(f.name)
                if ren_find:
                    base = base.replace(ren_find, ren_repl)
                if ren_case == "huruf kecil semua":
                    base = base.lower()
                elif ren_case == "HURUF BESAR SEMUA":
                    base = base.upper()
                elif ren_case == "Kapital Tiap Kata":
                    base = base.title()
                if ren_numbering:
                    try:
                        base = f"{ren_pattern.format(i=i)}{base}"
                    except Exception:
                        base = f"{i}_{base}"
                ext_out = ext if ren_ext == "Ikuti asal" else ren_ext
                new_name = f"{ren_prefix}{base}{ren_suffix}{ext_out}"

                if new_name.lower() in used:
                    conflicts += 1
                    b, e = os.path.splitext(new_name)
                    k = 1
                    while f"{b}_{k}{e}".lower() in used:
                        k += 1
                    new_name = f"{b}_{k}{e}"
                used.add(new_name.lower())
                new_names.append(new_name)

            st.markdown(f"#### 👀 Preview ({len(ren_files)} file)")
            st.dataframe(
                pd.DataFrame({
                    "No": range(1, len(ren_files) + 1),
                    "Nama Lama": [f.name for f in ren_files],
                    "Nama Baru": new_names,
                }),
                use_container_width=True,
            )
            if conflicts:
                st.warning(f"⚠️ {conflicts} nama bentrok — otomatis diberi akhiran _1, _2, dst.")

            if st.button("🏷️ Rename & Unduh sebagai ZIP", type="primary", use_container_width=True, key="ren_run"):
                rbuf = io.BytesIO()
                with zipfile.ZipFile(rbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for f, nn in zip(ren_files, new_names):
                        zf.writestr(sanitize_filename(nn), f.getvalue())
                rbuf.seek(0)
                st.session_state["ren_result"] = {"data": rbuf.getvalue(), "n": len(ren_files)}

            if "ren_result" in st.session_state:
                st.success(f"✅ {st.session_state['ren_result']['n']} file berhasil di-rename.")
                st.download_button(
                    "📥 Download renamed_files.zip",
                    data=st.session_state["ren_result"]["data"],
                    file_name="renamed_files.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="ren_dl",
                )

    else:
        st.markdown("Terapkan **operasi pembersihan/konversi yang sama** ke banyak file data sekaligus.")
        bp_files = st.file_uploader(
            "Unggah file data",
            type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
            accept_multiple_files=True,
            key="bp_up",
        )
        if not bp_files:
            st.info("👆 Silakan unggah file untuk diproses.")
        else:
            with st.expander("⚙️ Opsi pembacaan (berlaku untuk semua file teks)", expanded=False):
                d1, d2, d3 = st.columns(3)
                bp_delim = d1.selectbox(
                    "Delimiter", ["auto", ",", ";", "\t", "|"],
                    format_func=lambda x: {"\t": "Tab", "auto": "Auto-detect"}.get(x, x),
                    key="bp_delim",
                )
                bp_enc = d2.selectbox("Encoding", ["utf-8", "utf-8-sig", "latin1", "cp1252"], key="bp_enc")
                bp_hdr = d3.number_input("Baris header", min_value=1, value=1, key="bp_hdr")

            bp_ops = st.multiselect(
                "🧰 Operasi yang diterapkan",
                [
                    "Rapikan nama kolom (hapus spasi)",
                    "Hapus baris kosong",
                    "Hapus kolom kosong",
                    "Hapus baris duplikat",
                ],
                default=["Hapus baris kosong"],
                key="bp_ops",
            )
            bp_out = st.radio("Format output", ["Excel (.xlsx)", "CSV"], horizontal=True, key="bp_out")

            if st.button("⚙️ Proses Semua File", type="primary", use_container_width=True, key="bp_run"):
                progress = st.progress(0.0, text="Memulai...")
                log = []
                bbuf = io.BytesIO()
                used = set()
                try:
                    with zipfile.ZipFile(bbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, f in enumerate(bp_files, start=1):
                            try:
                                df_b = load_dataframe(
                                    f, delimiter=bp_delim, encoding=bp_enc,
                                    use_header=True, header_row=int(bp_hdr), sheet_name=0,
                                )
                                n_in = df_b.shape[0]
                                if "Rapikan nama kolom (hapus spasi)" in bp_ops:
                                    df_b.columns = [str(c).strip() for c in df_b.columns]
                                if "Hapus baris kosong" in bp_ops:
                                    df_b = df_b.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all")
                                if "Hapus kolom kosong" in bp_ops:
                                    df_b = df_b.dropna(axis=1, how="all")
                                if "Hapus baris duplikat" in bp_ops:
                                    df_b = df_b.drop_duplicates()

                                base = sanitize_filename(f.name.rsplit(".", 1)[0])
                                if bp_out.startswith("Excel"):
                                    out_name = unique_name(base + ".xlsx", used)
                                    data = df_to_xlsx_bytes(df_b, sheet_name="Data")
                                else:
                                    out_name = unique_name(base + ".csv", used)
                                    sb = io.StringIO()
                                    df_b.to_csv(sb, index=False)
                                    data = sb.getvalue().encode("utf-8")
                                zf.writestr(out_name, data)
                                log.append({
                                    "File": f.name, "Baris Masuk": n_in,
                                    "Baris Keluar": df_b.shape[0], "Status": "✅ Berhasil",
                                })
                            except Exception as e:
                                log.append({"File": f.name, "Baris Masuk": "-",
                                            "Baris Keluar": "-", "Status": f"❌ {e}"})
                            progress.progress(i / len(bp_files), text=f"Memproses {i}/{len(bp_files)}: {f.name}")
                    bbuf.seek(0)
                    st.session_state["bp_result"] = {
                        "data": bbuf.getvalue(), "log": log,
                        "n_ok": sum(1 for r in log if str(r["Status"]).startswith("✅")),
                    }
                    progress.progress(1.0, text="Selesai! ✅")
                except Exception as e:
                    progress.empty()
                    st.error(f"❌ Gagal memproses: {e}")

            if "bp_result" in st.session_state:
                res = st.session_state["bp_result"]
                st.success(f"✅ {res['n_ok']} dari {len(res['log'])} file berhasil diproses.")
                st.dataframe(pd.DataFrame(res["log"]), use_container_width=True)
                st.download_button(
                    "📥 Download hasil (ZIP)",
                    data=res["data"],
                    file_name="batch_processed.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                    key="bp_dl",
                )
                
# ------------------- TAB 7: DUPLICATE FINDER -------------------
with tab_dup:
    mode_dup = st.radio(
        "Pilih mode deteksi",
        ["📦 Duplikat antar file", "📋 Duplikat baris dalam satu file"],
        horizontal=True,
        key="dup_mode",
    )

    if mode_dup.startswith("📦"):
        st.markdown("Temukan file yang **isinya identik** di antara sekumpulan unggahan.")
        dup_files = st.file_uploader(
            "Unggah file yang akan diperiksa", accept_multiple_files=True, key="dup_up"
        )
        if not dup_files:
            st.info("👆 Silakan unggah minimal 2 file.")
        else:
            dup_method = st.selectbox(
                "Metode deteksi",
                ["Hash konten — MD5", "Hash konten — SHA-256",
                 "Ukuran + nama file", "Ukuran saja (kurang akurat)"],
                key="dup_method",
            )

            keys, hashes = [], []
            for f in dup_files:
                raw = f.getvalue()
                hashes.append(hashlib.md5(raw).hexdigest())
                if dup_method == "Hash konten — MD5":
                    keys.append(hashes[-1])
                elif dup_method == "Hash konten — SHA-256":
                    keys.append(hashlib.sha256(raw).hexdigest())
                elif dup_method == "Ukuran + nama file":
                    keys.append(f"{len(raw)}::{f.name.lower()}")
                else:
                    keys.append(str(len(raw)))

            groups = defaultdict(list)
            for i, k in enumerate(keys):
                groups[k].append(i)
            dup_keys = {k for k, v in groups.items() if len(v) > 1}

            gmap, nxt, status = {}, 1, []
            for k in keys:
                if k in dup_keys:
                    if k not in gmap:
                        gmap[k] = nxt
                        nxt += 1
                    status.append(f"🔴 Duplikat — Grup {gmap[k]}")
                else:
                    status.append("🟢 Unik")

            n_dup_files = sum(1 for s in status if s.startswith("🔴"))
            st.markdown(
                f"🔢 Hasil: **{n_dup_files} file duplikat** dalam **{len(dup_keys)} grup** "
                f"dari total {len(dup_files)} file."
            )
            st.dataframe(
                pd.DataFrame({
                    "No": range(1, len(dup_files) + 1),
                    "Nama File": [f.name for f in dup_files],
                    "Ukuran": [human_size(f.size) for f in dup_files],
                    "MD5": hashes,
                    "Status": status,
                }),
                use_container_width=True,
            )

            if dup_keys:
                st.markdown("**Anggota tiap grup duplikat:**")
                for k in sorted(dup_keys, key=lambda x: gmap[x]):
                    members = [dup_files[i].name for i in groups[k]]
                    st.markdown(f"- **Grup {gmap[k]}**: " + ", ".join(f"`{m}`" for m in members))

                if st.button("🧹 Simpan 1 Salinan per Grup → ZIP", type="primary", use_container_width=True, key="dup_zip"):
                    keep, seen = [], set()
                    for f, k in zip(dup_files, keys):
                        if k not in seen:
                            seen.add(k)
                            keep.append(f)
                    dbuf = io.BytesIO()
                    used = set()
                    with zipfile.ZipFile(dbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for f in keep:
                            zf.writestr(unique_name(sanitize_filename(f.name), used), f.getvalue())
                    dbuf.seek(0)
                    st.session_state["dup_result"] = {
                        "data": dbuf.getvalue(), "n": len(keep),
                        "removed": len(dup_files) - len(keep),
                    }

                if "dup_result" in st.session_state:
                    res = st.session_state["dup_result"]
                    st.success(f"✅ ZIP siap: {res['n']} file unik disimpan, {res['removed']} duplikat dibuang.")
                    st.download_button(
                        "📥 Download unique_files.zip",
                        data=res["data"],
                        file_name="unique_files.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True,
                        key="dup_dl",
                    )
            else:
                st.success("✅ Tidak ada file duplikat terdeteksi.")

    else:
        st.markdown("Temukan & bersihkan **baris duplikat** di dalam satu file data.")
        dup_row_file = st.file_uploader(
            "Pilih file data",
            type=["csv", "txt", "tsv", "json", "xlsx", "xls"],
            key="duprow_up",
        )
        if dup_row_file is None:
            st.info("👆 Silakan unggah file data.")
        else:
            df_dr = None
            try:
                opts_dr = render_read_options(dup_row_file, "duprow", expanded=False)
                df_dr = load_dataframe(dup_row_file, **opts_dr)
            except Exception as e:
                st.error(f"❌ Gagal membaca file: {e}")

            if df_dr is not None and not df_dr.empty:
                st.success(f"✅ File dimuat: **{df_dr.shape[0]:,} baris** × **{df_dr.shape[1]} kolom**")

                sel_cols = st.multiselect(
                    "🗂️ Kolom acuan duplikasi (kosong = semua kolom)",
                    list(df_dr.columns),
                    key="duprow_cols",
                )
                keep_opt = st.radio(
                    "Baris yang dipertahankan",
                    ["Kemunculan pertama", "Kemunculan terakhir"],
                    horizontal=True,
                    key="duprow_keep",
                )
                subset = sel_cols if sel_cols else list(df_dr.columns)
                keep = "first" if keep_opt.startswith("Kemunculan pertama") else "last"

                try:
                    dup_mask = df_dr.duplicated(subset=subset, keep=keep)
                except TypeError:
                    st.error("❌ Data mengandung tipe yang tidak dapat dibandingkan.")
                    st.stop()

                n_dup = int(dup_mask.sum())
                pct = (n_dup / len(df_dr) * 100) if len(df_dr) else 0
                st.markdown(f"🔢 Ditemukan **{n_dup:,} baris duplikat** ({pct:.1f}% dari data).")

                if n_dup:
                    all_dup = df_dr[df_dr.duplicated(subset=subset, keep=False)]
                    with st.expander(f"👀 Lihat baris yang terlibat duplikasi ({len(all_dup):,} baris)"):
                        st.dataframe(all_dup.head(100), use_container_width=True)
                        if len(all_dup) > 100:
                            st.caption(f"Menampilkan 100 dari {len(all_dup):,} baris")

                    df_clean = df_dr[~dup_mask]
                    c1, c2 = st.columns(2)
                    c1.download_button(
                        f"📥 Download data bersih ({len(df_clean):,} baris)",
                        data=df_to_xlsx_bytes(df_clean, sheet_name="Data"),
                        file_name=sanitize_filename(dup_row_file.name.rsplit(".", 1)[0]) + "_tanpa_duplikat.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="duprow_clean_dl",
                    )

                    report = all_dup.copy()
                    report["_Grup"] = report.groupby(subset, dropna=False).ngroup() + 1
                    ring = (
                        all_dup.groupby(subset, dropna=False).size()
                        .reset_index(name="Jumlah Kemunculan")
                        .sort_values("Jumlah Kemunculan", ascending=False)
                    )
                    rbuf = io.BytesIO()
                    with pd.ExcelWriter(rbuf, engine="openpyxl") as writer:
                        report.head(10000).to_excel(writer, sheet_name="Baris Duplikat", index=False)
                        ring.head(10000).to_excel(writer, sheet_name="Ringkasan", index=False)
                    rbuf.seek(0)
                    c2.download_button(
                        "📥 Download laporan duplikat (.xlsx)",
                        data=rbuf.getvalue(),
                        file_name=sanitize_filename(dup_row_file.name.rsplit(".", 1)[0]) + "_laporan_duplikat.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="duprow_report_dl",
                    )
                else:
                    st.success("✅ Tidak ada baris duplikat — data sudah bersih.")
            elif df_dr is not None:
                st.warning("⚠️ File tidak memiliki data.")
