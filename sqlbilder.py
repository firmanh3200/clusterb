import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json
import io

# ============================================================
# FUNGSI HELPER
# ============================================================

def load_metadata(filepath):
    """Membaca CSV metadata → dict {tabel: [{kolom, keterangan, tipe}, ...]}"""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(filepath, encoding=enc)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        return None

    df.columns = [c.strip().lower() for c in df.columns]

    col_tabel = next((c for c in df.columns if c in ("tabel", "table", "nama_tabel")), None)
    col_kolom = next((c for c in df.columns if c in ("kolom", "column", "nama_kolom")), None)
    col_label = next((c for c in df.columns if c in ("label", "lable", "Label")), None)
    col_ket   = next((c for c in df.columns if c in ("keterangan", "deskripsi", "description", "info", "ket")), None)
    col_tipe  = next((c for c in df.columns if c in ("tipe", "type", "tipe_data", "data_type")), None)

    if not col_tabel or not col_kolom:
        return None

    tables = {}
    for _, row in df.iterrows():
        tbl  = str(row[col_tabel]).strip()
        kol  = str(row[col_kolom]).strip()
        lab  = str(row[col_label]).strip()
        ket  = str(row[col_ket]).strip() if col_ket else ""
        tipe = str(row[col_tipe]).strip() if col_tipe else ""
        tables.setdefault(tbl, []).append({"kolom": kol, "label": lab, "keterangan": ket, "tipe": tipe})
    return tables


def get_all_columns(tables, selected_tables):
    """Daftar semua kolom dari tabel terpilih."""
    cols = []
    for tbl in selected_tables:
        if tbl in tables:
            for c in tables[tbl]:
                ref = f"{tbl}.{c['kolom']}"
                disp = f"{ref}  —  {c['keterangan']}" if c["keterangan"] else ref
                cols.append({"tabel": tbl, "kolom": c["kolom"], "ref": ref,
                             "label": c["label"], "keterangan": c["keterangan"], "tipe": c["tipe"], "display": disp})
    return cols


def find_join_candidates(tables, selected_tables):
    """Kolom yang namanya SAMA di 2+ tabel terpilih → kandidat JOIN."""
    if len(selected_tables) < 2:
        return []
    col_map = {}
    for tbl in selected_tables:
        if tbl in tables:
            for c in tables[tbl]:
                col_map.setdefault(c["kolom"], []).append(tbl)
    return [{"kolom": n, "tabels": t, "display": f"{n}  →  {', '.join(t)}"}
            for n, t in sorted(col_map.items()) if len(t) >= 2]


def format_where_value(value, operator):
    if operator in ("IS NULL", "IS NOT NULL"):
        return ""
    if operator in ("IN", "NOT IN", "BETWEEN", "NOT BETWEEN"):
        return value
    if operator in ("LIKE", "NOT LIKE"):
        return f"'{value}'"
    try:
        float(value)
        return value
    except (ValueError, TypeError):
        return f"'{value}'"


def build_query(tables, sel_tables, sel_cols, join_cols, wheres, order_bys, limit_val, use_alias):
    if not sel_tables:
        return "-- Pilih minimal satu tabel"

    # --- alias ---
    aliases = {}
    if use_alias:
        used = set()
        for tbl in sel_tables:
            for l in range(1, len(tbl) + 1):
                a = tbl[:l]
                if a not in used:
                    aliases[tbl] = a
                    used.add(a)
                    break

    def fr(ref):
        if use_alias:
            p = ref.split(".", 1)
            if len(p) == 2 and p[0] in aliases:
                return f"{aliases[p[0]]}.{p[1]}"
        return ref

    def ft(tbl):
        return f"{tbl} {aliases[tbl]}" if (use_alias and tbl in aliases) else tbl

    parts = []

    # SELECT
    parts.append("SELECT " + ",\n       ".join([fr(c) for c in sel_cols] if sel_cols else ["*"]))

    # FROM + JOIN
    if len(sel_tables) == 1:
        parts.append(f"FROM {ft(sel_tables[0])}")
    else:
        parts.append(f"FROM {ft(sel_tables[0])}")
        joined = {sel_tables[0]}
        remaining = list(sel_tables[1:])
        safety = len(remaining) ** 2 + 1
        it = 0
        while remaining and it < safety:
            it += 1
            found = False
            for jc in join_cols:
                for rtbl in list(remaining):
                    if rtbl in jc["tabels"]:
                        for jtbl in jc["tabels"]:
                            if jtbl in joined and jtbl != rtbl:
                                parts.append(f"INNER JOIN {ft(rtbl)}")
                                ol = f"{aliases[rtbl]}.{jc['kolom']}" if use_alias else f"{rtbl}.{jc['kolom']}"
                                orr = f"{aliases[jtbl]}.{jc['kolom']}" if use_alias else f"{jtbl}.{jc['kolom']}"
                                parts.append(f"  ON {ol} = {orr}")
                                joined.add(rtbl)
                                remaining.remove(rtbl)
                                found = True
                                break
                        if found:
                            break
                if found:
                    break
            if not found and remaining:
                for rtbl in remaining:
                    parts.append(f"CROSS JOIN {ft(rtbl)}")
                remaining.clear()

    # WHERE
    if wheres:
        wp = []
        for i, w in enumerate(wheres):
            col, op, val = fr(w["column"]), w["operator"], w["value"]
            if op in ("IS NULL", "IS NOT NULL"):
                cl = f"{col} {op}"
            elif op in ("IN", "NOT IN"):
                cl = f"{col} {op} ({val})"
            elif op in ("LIKE", "NOT LIKE"):
                cl = f"{col} {op} '{val}'"
            else:
                cl = f"{col} {op} {format_where_value(val, op)}"
            if i > 0:
                cl = f"{w.get('logic', 'AND')} {cl}"
            wp.append(cl)
        parts.append("WHERE " + "\n      ".join(wp))

    # ORDER BY
    if order_bys:
        parts.append("ORDER BY " + ", ".join(f"{fr(o['column'])} {o['direction']}" for o in order_bys))

    # LIMIT
    if limit_val and str(limit_val).strip().isdigit():
        parts.append(f"LIMIT {int(limit_val)}")

    return "\n".join(parts)


def copy_button(text):
    components.html(
        f"""<button onclick="navigator.clipboard.writeText({json.dumps(text)}).then(()=>{{
            this.textContent='✅ Tersalin!';setTimeout(()=>{{this.textContent='📋 Copy ke Clipboard'}},2000)
        }})" style="padding:10px 20px;background:#0d6efd;color:white;border:none;border-radius:6px;
        cursor:pointer;font-size:14px;width:100%;transition:background .2s"
        onmouseover="this.style.background='#0b5ed7'" onmouseout="this.style.background='#0d6efd'">
        📋 Copy ke Clipboard</button>""", height=48)


# ============================================================
# RENDER SATU TAB
# ============================================================

def render_tab(prefix, csv_path, tables):
    # --- Jika file tidak ditemukan ---
    if tables is None:
        st.warning(f"⚠️ File `{csv_path}` tidak ditemukan atau format tidak sesuai.")
        st.info("Pastikan CSV memiliki kolom: **tabel**, **kolom**, **keterangan** (opsional: **tipe**)")
        sample = """tabel,kolom,keterangan,tipe
pelanggan,id_pelanggan,ID Pelanggan (PK),INT
pelanggan,nama,Nama Lengkap,VARCHAR(100)
pesanan,id_pesanan,ID Pesanan (PK),INT
pesanan,id_pelanggan,FK ke pelanggan,INT
pesanan,total,Total Nilai,DECIMAL(15,2)"""
        st.code(sample, language="csv")
        st.download_button(f"⬇ Download contoh {csv_path}", sample, csv_path, "text/csv", use_container_width=True)
        return

    table_names = sorted(tables.keys())
    if not table_names:
        st.warning("CSV tidak berisi data tabel.")
        return

    # ================================================================
    # PREVIEW DATAFRAME CSV
    # ================================================================
    with st.expander("👁️ Lihat Data Metadata CSV", expanded=False):
        # Rekonstruksi dataframe dari dict tables untuk ditampilkan
        rows = []
        for tbl, kolom_list in tables.items():
            for k in kolom_list:
                rows.append({"tabel": tbl, "kolom": k["kolom"],
                             "label": k["label"], "keterangan": k["keterangan"], "tipe": k["tipe"]})
        df_preview = pd.DataFrame(rows).fillna("").replace("nan", "")
        st.dataframe(df_preview, width="stretch", hide_index=True)
        st.caption(f"Total: **{len(table_names)}** tabel, **{len(rows)}** kolom")

    # ================================================================
    # 1. PILIH TABEL
    # ================================================================
    st.markdown("### 1️⃣ Pilih Tabel")
    selected_tables = st.multiselect("Pilih satu atau lebih tabel:", table_names, key=f"{prefix}_tables")

    if not selected_tables:
        st.info("👆 Pilih minimal satu tabel untuk melanjutkan.")
        return

    # Kolom tersedia
    all_cols = get_all_columns(tables, selected_tables)
    col_refs = [c["ref"] for c in all_cols]
    col_disp = {c["ref"]: c["display"] for c in all_cols}

    # Cleanup session jika tabel berubah
    if f"{prefix}_cols" in st.session_state:
        st.session_state[f"{prefix}_cols"] = [c for c in st.session_state[f"{prefix}_cols"] if c in col_disp]

    # ================================================================
    # 2. PILIH KOLOM
    # ================================================================
    st.markdown("### 2️⃣ Pilih Kolom")
    selected_columns = st.multiselect(
        "Kolom yang ditampilkan  (kosongkan = SELECT *):",
        col_refs, format_func=lambda x: col_disp.get(x, x),
        key=f"{prefix}_cols")

    # ================================================================
    # 3. JOIN (opsional)
    # ================================================================
    join_columns = []
    if len(selected_tables) >= 2:
        st.markdown("### 3️⃣ JOIN — Kolom Penghubung  *(Opsional)*")
        candidates = find_join_candidates(tables, selected_tables)

        if candidates:
            valid_jc = [f"{prefix}_jc_{i}" for i in range(len(candidates))]
            if f"{prefix}_jc" in st.session_state:
                st.session_state[f"{prefix}_jc"] = [k for k in st.session_state[f"{prefix}_jc"] if k in valid_jc]

            cmap = {f"{prefix}_jc_{i}": c for i, c in enumerate(candidates)}
            chosen = st.multiselect(
                f"Kolom bernama sama di beberapa tabel  ({len(candidates)} ditemukan):",
                list(cmap.keys()), format_func=lambda x: cmap[x]["display"], key=f"{prefix}_jc")
            join_columns = [cmap[k] for k in chosen if k in cmap]

            if join_columns:
                for jc in join_columns:
                    st.success(f"✅ `{jc['kolom']}`  menghubungkan:  {', '.join(jc['tabels'])}")
        else:
            st.warning("⚠️ Tidak ditemukan kolom bernama sama di beberapa tabel. "
                       "Tambahkan kondisi hubungan manual di WHERE jika perlu.")

    # Warning CROSS JOIN
    if len(selected_tables) >= 2 and not join_columns:
        st.warning("⚠️ Beberapa tabel dipilih tanpa kolom JOIN → akan menghasilkan CROSS JOIN (perkalian cartesian).")

    # ================================================================
    # 4. WHERE
    # ================================================================
    st.markdown("### 4️⃣ Kondisi WHERE")

    # Cleanup
    if f"{prefix}_wheres" in st.session_state:
        vr = set(col_refs)
        st.session_state[f"{prefix}_wheres"] = [w for w in st.session_state[f"{prefix}_wheres"] if w["column"] in vr]

    with st.form(f"{prefix}_wf"):
        w1, w2, w3, w4, w5 = st.columns([3, 1.5, 3, 1, 1])
        with w1:
            wcol = st.selectbox("Kolom", col_refs, format_func=lambda x: col_disp.get(x, x), key=f"{prefix}_wcol")
        with w2:
            wop = st.selectbox("Operator",
                               ["=", "!=", ">", "<", ">=", "<=", "LIKE", "NOT LIKE",
                                "IN", "NOT IN", "BETWEEN", "IS NULL", "IS NOT NULL"],
                               key=f"{prefix}_wop")
        with w3:
            wval = st.text_input("Nilai", key=f"{prefix}_wval",
                                 placeholder="teks / angka / 1,2,3 / val1 AND val2",
                                 disabled=(wop in ("IS NULL", "IS NOT NULL")))
        with w4:
            wlogic = st.selectbox("Logic", ["AND", "OR"], key=f"{prefix}_wlogic")
        with w5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("➕"):
                st.session_state.setdefault(f"{prefix}_wheres", []).append(
                    {"column": wcol, "operator": wop, "value": wval, "logic": wlogic})
                st.session_state[f"{prefix}_wval"] = ""
                st.rerun()

    if st.session_state.get(f"{prefix}_wheres"):
        for i, w in enumerate(st.session_state[f"{prefix}_wheres"]):
            c1, c2 = st.columns([5, 1])
            with c1:
                lg = f"**{w['logic']}**  " if i > 0 else ""
                if w["operator"] in ("IS NULL", "IS NOT NULL"):
                    st.markdown(f"{lg}`{w['column']} {w['operator']}`")
                else:
                    st.markdown(f"{lg}`{w['column']} {w['operator']} {w['value']}`")
            with c2:
                if st.button("✕", key=f"{prefix}_dw_{i}"):
                    st.session_state[f"{prefix}_wheres"].pop(i)
                    st.rerun()

    # ORDER BY & LIMIT
    with st.expander("📌 ORDER BY  &  LIMIT  *(Opsional)*"):
        if f"{prefix}_obs" in st.session_state:
            vr = set(col_refs)
            st.session_state[f"{prefix}_obs"] = [o for o in st.session_state[f"{prefix}_obs"] if o["column"] in vr]

        o1, o2, o3 = st.columns([3, 2, 2])
        with o1:
            obc = st.selectbox("Kolom", [""] + col_refs,
                               format_func=lambda x: col_disp.get(x, x) if x else "— Pilih —",
                               key=f"{prefix}_obc")
        with o2:
            obd = st.selectbox("Arah", ["ASC", "DESC"], key=f"{prefix}_obd")
        with o3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕", key=f"{prefix}_aob") and obc:
                st.session_state.setdefault(f"{prefix}_obs", []).append({"column": obc, "direction": obd})
                st.rerun()

        for i, ob in enumerate(st.session_state.get(f"{prefix}_obs", [])):
            oa, obb = st.columns([4, 1])
            with oa:
                st.caption(f"• {ob['column']}  {ob['direction']}")
            with obb:
                if st.button("✕", key=f"{prefix}_dob_{i}"):
                    st.session_state[f"{prefix}_obs"].pop(i)
                    st.rerun()

        # ✅ FIX: baca langsung dari widget, JANGAN tulis ulang ke session_state
        st.text_input("LIMIT", placeholder="Kosongkan = tanpa limit", key=f"{prefix}_lim")

    # ================================================================
    # 5. TOMBOL BUAT QUERY
    # ================================================================
    st.markdown("---")
    use_alias = st.checkbox("🏷️ Gunakan alias tabel  (misal: pelanggan → p)", key=f"{prefix}_alias")

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("🔨 Buat Query", type="primary", use_container_width=True, key=f"{prefix}_build"):
            st.session_state[f"{prefix}_query"] = build_query(
                tables, selected_tables, selected_columns, join_columns,
                st.session_state.get(f"{prefix}_wheres", []),
                st.session_state.get(f"{prefix}_obs", []),
                st.session_state.get(f"{prefix}_lim", ""),   # ✅ baca dari sini
                use_alias)
    with b2:
        if st.button("🗑 Reset Semua Kondisi", type="secondary", use_container_width=True, key=f"{prefix}_reset"):
            for k in (f"{prefix}_wheres", f"{prefix}_obs", f"{prefix}_query", f"{prefix}_jc"):
                st.session_state.pop(k, None)
            st.rerun()

    # ================================================================
    # 6. HASIL QUERY
    # ================================================================
    if st.session_state.get(f"{prefix}_query"):
        st.markdown("---")
        st.markdown("### 6️⃣ Hasil Query SQL")
        q = st.session_state[f"{prefix}_query"]
        st.code(q, language="sql")

        cb1, cb2 = st.columns([1, 1])
        with cb1:
            copy_button(q)
        with cb2:
            st.download_button("💾 Download .sql", q, f"query_{prefix}.sql",
                               "text/plain", use_container_width=True)
# ============================================================
# MAIN APP
# ============================================================

st.set_page_config(page_title="SQL Query Builder", page_icon="🔧", layout="wide")
st.title("🔧 SQL Query Builder")
st.caption("Generate query SQL dari file metadata CSV — 2 tab terpisah untuk UMK & UB")

st.markdown("""<style>
    div[data-testid="stTabsTablist"] { gap: 8px; }
    .stTabs [data-baseweb="tab-list"] [data-baseweb="tab"] { font-size: 16px; padding: 10px 28px; }
</style>""", unsafe_allow_html=True)

# Load kedua file
tables_umk = load_metadata("metadata_umk.csv")
tables_ub = load_metadata("metadata_ub.csv")

tab_umk, tab_ub = st.tabs(["📄 UMK", "📄 UB"])

with tab_umk:
    st.markdown(f"**Data:** `metadata_umk.csv`  —  "
                f"{'✅ ' + str(len(tables_umk)) + ' tabel' if tables_umk else '❌ file tidak ditemukan'}")
    render_tab("umk", "metadata_umk.csv", tables_umk)

with tab_ub:
    st.markdown(f"**Data:** `metadata_ub.csv`  —  "
                f"{'✅ ' + str(len(tables_ub)) + ' tabel' if tables_ub else '❌ file tidak ditemukan'}")
    render_tab("ub", "metadata_ub.csv", tables_ub)