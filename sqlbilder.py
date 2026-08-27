import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# ============================================================
# HELPER: BACA CSV
# ============================================================

def load_metadata(filepath):
    def _clean(val):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        s = str(val).strip()
        return "" if s.lower() == "nan" else s

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
    col_ket   = next((c for c in df.columns if c in ("keterangan", "deskripsi", "description", "info", "ket")), None)
    col_tipe  = next((c for c in df.columns if c in ("tipe", "type", "tipe_data", "data_type")), None)

    if not col_tabel or not col_kolom:
        return None

    tables = {}
    for _, row in df.iterrows():
        tbl  = _clean(row[col_tabel])
        kol  = _clean(row[col_kolom])
        ket  = _clean(row[col_ket]) if col_ket else ""
        tipe = _clean(row[col_tipe]) if col_tipe else ""
        if tbl and kol:
            tables.setdefault(tbl, []).append({"kolom": kol, "keterangan": ket, "tipe": tipe})
    return tables


# ============================================================
# HELPER: KOLOM & JOIN
# ============================================================

def get_all_columns(tables, selected_tables):
    cols = []
    for tbl in selected_tables:
        if tbl in tables:
            for c in tables[tbl]:
                ref = f"{tbl}.{c['kolom']}"
                disp = f"{ref}  —  {c['keterangan']}" if c["keterangan"] else ref
                cols.append({"tabel": tbl, "kolom": c["kolom"], "ref": ref,
                             "keterangan": c["keterangan"], "tipe": c["tipe"], "display": disp})
    return cols


def find_join_candidates(tables, selected_tables):
    if len(selected_tables) < 2:
        return []
    col_map = {}
    for tbl in selected_tables:
        if tbl in tables:
            for c in tables[tbl]:
                col_map.setdefault(c["kolom"], []).append(tbl)
    return [{"kolom": n, "tabels": t, "display": f"{n}  →  {', '.join(t)}"}
            for n, t in sorted(col_map.items()) if len(t) >= 2]


# ============================================================
# HELPER: FORMAT NILAI WHERE
# ============================================================

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


# ============================================================
# HELPER: BUILD QUERY
# ============================================================

def build_query(tables, sel_tables, sel_cols, join_columns, wheres,
                order_bys, limit_val, use_alias,
                extra_select=None, custom_from=None, custom_order_by=None):
    if not sel_tables:
        return "-- Pilih minimal satu tabel"

    expr_map = {e["key"]: e["sql"] for e in (extra_select or [])}

    # ---- SELECT ----
    sel_items = []
    for c in sel_cols:
        if c.startswith("__EXPR__"):
            key = c[7:]
            if key in expr_map:
                sel_items.append(expr_map[key])
        else:
            sel_items.append(c)
    if not sel_items:
        sel_items = ["*"]
    parts = ["SELECT " + ",\n       ".join(sel_items)]

    # ---- FROM + JOIN ----
    if custom_from:
        parts.append(custom_from)
    else:
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
                for jc in join_columns:
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

    # ---- WHERE ----
    if wheres:
        wp = []
        for i, w in enumerate(wheres):
            col, op, val = w["column"], w["operator"], w["value"]
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

    # ---- ORDER BY ----
    if custom_order_by:
        parts.append(custom_order_by)
    elif order_bys:
        parts.append("ORDER BY " + ", ".join(f"{o['column']} {o['direction']}" for o in order_bys))

    # ---- LIMIT ----
    if limit_val and str(limit_val).strip().isdigit():
        parts.append(f"LIMIT {int(limit_val)}")

    return "\n".join(parts)


# ============================================================
# HELPER: COPY BUTTON
# ============================================================

def copy_button(text):
    components.html(
        f"""<button onclick="navigator.clipboard.writeText({json.dumps(text)}).then(()=>{{
            this.textContent='✅ Tersalin!';setTimeout(()=>{{this.textContent='📋 Copy ke Clipboard'}},2000)
        }})" style="padding:10px 20px;background:#0d6efd;color:white;border:none;border-radius:6px;
        cursor:pointer;font-size:14px;width:100%;transition:background .2s"
        onmouseover="this.style.background='#0b5ed7'" onmouseout="this.style.background='#0d6efd'">
        📋 Copy ke Clipboard</button>""", height=48)


# ============================================================
# DEFAULTS PER TAB
# ============================================================

DEFAULTS = {
    "umk": {
        "tables": ["tgr_fd68e454.se2026_nested", "tgr_fd68e454.base_table_assignment"],
        "cols": [],
        "extra_select": [
            {"key": "umk_1",  "display": "n.assignment_id", "sql": "n.assignment_id"},
            {"key": "umk_2",  "display": "COALESCE(kab_l, CONCAT('[',n.level_2_code,'] ',n.level_2_name)) AS kab", "sql": "COALESCE(kab_l, CONCAT('[', n.level_2_code,'] ',n.level_2_name)) AS kab"},
            {"key": "umk_3",  "display": "COALESCE(kec_l, CONCAT('[',n.level_3_code,'] ',n.level_3_name)) AS kec", "sql": "COALESCE(kec_l, CONCAT('[', n.level_3_code,'] ',n.level_3_name)) AS kec"},
            {"key": "umk_4",  "display": "COALESCE(desa_l, CONCAT('[',n.level_4_code,'] ',n.level_4_name)) AS desakel", "sql": "COALESCE(desa_l, CONCAT('[', n.level_4_code,'] ',n.level_4_name)) AS desakel"},
            {"key": "umk_5",  "display": "COALESCE(CONCAT('[',sls_l,'] ',kodesls_l), CONCAT('[',n.level_5_code,'] ',n.level_5_name)) AS sls", "sql": "COALESCE(CONCAT('[',sls_l,'] ', kodesls_l), CONCAT('[', n.level_5_code,'] ',n.level_5_name)) AS sls"},
            {"key": "umk_6",  "display": "nama_usaha", "sql": "nama_usaha"},
            {"key": "umk_7",  "display": "nama_komersial", "sql": "nama_komersial"},
            {"key": "umk_8",  "display": "keg_utama", "sql": "keg_utama"},
            {"key": "umk_9",  "display": "COALESCE(kbli_akhir, kbli_prelist) AS kbli", "sql": "COALESCE(kbli_akhir, kbli_prelist) AS kbli"},
            {"key": "umk_10", "display": "kategori", "sql": "kategori"},
            {"key": "umk_11", "display": "COALESCE(total_pendapatan, total_pendapatan_bln*12) AS total_pendapatan", "sql": "COALESCE(total_pendapatan, total_pendapatan_bln*12) AS total_pendapatan"},
            {"key": "umk_12", "display": "COALESCE(keberadaan_usaha_label) AS keberadaan", "sql": "COALESCE(keberadaan_usaha_label) AS keberadaan"},
            {"key": "umk_13", "display": "COALESCE(jaringan_label) AS jaringan", "sql": "COALESCE(jaringan_label) AS jaringan"},
            {"key": "umk_14", "display": "CONCAT('https://fasih-sm.bps.go.id/app/assignment-detail/', n.assignment_id) AS link_fasih", "sql": "CONCAT('https://fasih-sm.bps.go.id/app/assignment-detail/', n.assignment_id) AS link_fasih"},
        ],
        "default_extra_select": ["umk_1","umk_2","umk_3","umk_4","umk_5","umk_6","umk_7","umk_8","umk_9","umk_10","umk_11","umk_12","umk_13","umk_14"],
        "custom_from": """FROM tgr_fd68e454.se2026_nested n
LEFT JOIN tgr_fd68e454.base_table_assignment bta
  ON bta.assignment_id = n.assignment_id
  AND bta.date_modified = n.assignment_date_modified""",
        "custom_order_by": """ORDER BY
  COALESCE(kab_l, CONCAT('[', n.level_2_code,'] ',n.level_2_name)),
  COALESCE(kec_l, CONCAT('[', n.level_3_code,'] ',n.level_3_name)),
  COALESCE(desa_l, CONCAT('[', n.level_4_code,'] ',n.level_4_name)),
  COALESCE(CONCAT('[',sls_l,'] ', kodesls_l), CONCAT('[', n.level_5_code,'] ',n.level_5_name))""",
    },
    "ub": {
        "tables": ["tcz_37526b20.root_table", "tcz_37526b20.base_table_assignment"],
        "cols": [],
        "extra_select": [
            {"key": "ub_1",  "display": "n.assignment_id", "sql": "n.assignment_id"},
            {"key": "ub_2",  "display": "COALESCE(kab_l_label, CONCAT('[',n.level_2_code,'] ',n.level_2_name)) AS kab", "sql": "COALESCE(kab_l_label, CONCAT('[', n.level_2_code,'] ',n.level_2_name)) AS kab"},
            {"key": "ub_3",  "display": "COALESCE(kec_l_label, CONCAT('[',n.level_3_code,'] ',n.level_3_name)) AS kec", "sql": "COALESCE(kec_l_label, CONCAT('[', n.level_3_code,'] ',n.level_3_name)) AS kec"},
            {"key": "ub_4",  "display": "COALESCE(desa_l_label, CONCAT('[',n.level_4_code,'] ',n.level_4_name)) AS desakel", "sql": "COALESCE(desa_l_label, CONCAT('[', n.level_4_code,'] ',n.level_4_name)) AS desakel"},
            {"key": "ub_5",  "display": "COALESCE(CONCAT('[',idsls,'] '), CONCAT('[',n.level_5_code,'] ',n.level_5_name)) AS sls", "sql": "COALESCE(CONCAT('[',idsls,'] '), CONCAT('[', n.level_5_code,'] ',n.level_5_name)) AS sls"},
            {"key": "ub_6",  "display": "nama_usaha", "sql": "nama_usaha"},
            {"key": "ub_7",  "display": "nama_komersial", "sql": "nama_komersial"},
            {"key": "ub_8",  "display": "keg_utama", "sql": "keg_utama"},
            {"key": "ub_9",  "display": "COALESCE(kbli_akhir, kbli_prelist) AS kbli", "sql": "COALESCE(kbli_akhir, kbli_prelist) AS kbli"},
            {"key": "ub_10", "display": "kategori", "sql": "kategori"},
            {"key": "ub_11", "display": "COALESCE(total_pendapatan) AS total_pendapatan", "sql": "COALESCE(total_pendapatan) AS total_pendapatan"},
            {"key": "ub_12", "display": "COALESCE(keberadaan_label) AS keberadaan", "sql": "COALESCE(keberadaan_label) AS keberadaan"},
            {"key": "ub_13", "display": "COALESCE(jaringan_label) AS jaringan", "sql": "COALESCE(jaringan_label) AS jaringan"},
            {"key": "ub_14", "display": "CONCAT('https://fasih-sm.bps.go.id/app/assignment-detail/', n.assignment_id) AS link_fasih", "sql": "CONCAT('https://fasih-sm.bps.go.id/app/assignment-detail/', n.assignment_id) AS link_fasih"},
        ],
        "default_extra_select": ["ub_1","ub_2","ub_3","ub_4","ub_5","ub_6","ub_7","ub_8","ub_9","ub_10","ub_11","ub_12","ub_13","ub_14"],
        "custom_from": """FROM tcz_37526b20.root_table n
LEFT JOIN tcz_37526b20.base_table_assignment bta
  ON bta.assignment_id = n.assignment_id""",
        "custom_order_by": """ORDER BY
  COALESCE(kab_l_label, CONCAT('[', n.level_2_code,'] ',n.level_2_name)),
  COALESCE(kec_l_label, CONCAT('[', n.level_3_code,'] ',n.level_3_name)),
  COALESCE(desa_l_label, CONCAT('[', n.level_4_code,'] ',n.level_4_name)),
  COALESCE(CONCAT('[',idsls,'] '), CONCAT('[', n.level_5_code,'] ',n.level_5_name))""",
    },
    "kel": {
        "tables": [],
        "cols": []
    },
}


# ============================================================
# RENDER SATU TAB
# ============================================================

def render_tab(prefix, csv_path, tables):

    # ---- File tidak ditemukan ----
    if tables is None:
        st.warning(f"⚠️ File `{csv_path}` tidak ditemukan atau format tidak sesuai.")
        st.info("Pastikan CSV memiliki kolom: **tabel**, **kolom**, **keterangan** (opsional: **tipe**)")
        sample = "tabel,kolom,keterangan,tipe\npelanggan,id_pelanggan,ID Pelanggan,INT\npelanggan,nama,Nama Lengkap,VARCHAR(100)"
        st.code(sample, language="csv")
        st.download_button(f"⬇ Download contoh {csv_path}", sample, csv_path, "text/csv", use_container_width=True)
        return

    table_names = sorted(tables.keys())
    if not table_names:
        st.warning("CSV tidak berisi data tabel.")
        return

    # ---- Preview CSV ----
    with st.expander("👁️ Lihat Data Metadata CSV", expanded=False):
        rows = []
        for tbl, kl in tables.items():
            for k in kl:
                rows.append({"tabel": tbl, "kolom": k["kolom"], "keterangan": k["keterangan"], "tipe": k["tipe"]})
        st.dataframe(pd.DataFrame(rows).fillna("").replace("nan", ""), use_container_width=True, hide_index=True)
        st.caption(f"Total: **{len(table_names)}** tabel, **{len(rows)}** kolom")

    # ---- Konfigurasi tab ----
    cfg = DEFAULTS.get(prefix, {})
    has_custom = bool(cfg.get("custom_from"))
    extra_select = cfg.get("extra_select", [])
    default_extra_keys = cfg.get("default_extra_select", [])

    # ============================================================
    # 1. PILIH TABEL
    # ============================================================
    st.markdown("### 1️⃣ Pilih Tabel")

    if f"{prefix}_tables" not in st.session_state:
        st.session_state[f"{prefix}_tables"] = [t for t in cfg.get("tables", []) if t in table_names]

    selected_tables = st.multiselect("Pilih satu atau lebih tabel:", table_names, key=f"{prefix}_tables")

    if not selected_tables:
        st.info("👆 Pilih minimal satu tabel untuk melanjutkan.")
        return

    # ---- Kolom reguler dari CSV ----
    all_cols = get_all_columns(tables, selected_tables)
    col_refs = [c["ref"] for c in all_cols]
    col_disp = {c["ref"]: c["display"] for c in all_cols}

    # ============================================================
    # 2. PILIH KOLOM (ekspresi ⚡ + reguler 📋)
    # ============================================================
    st.markdown("### 2️⃣ Pilih Kolom")

    merged = {}
    for e in extra_select:
        merged[f"__EXPR__{e['key']}"] = f"⚡ {e['display']}"
    for ref, disp in col_disp.items():
        merged[ref] = f"📋 {disp}"

    if f"{prefix}_cols" in st.session_state:
        st.session_state[f"{prefix}_cols"] = [c for c in st.session_state[f"{prefix}_cols"] if c in merged]

    if f"{prefix}_cols" not in st.session_state:
        defs = [f"__EXPR__{k}" for k in default_extra_keys if f"__EXPR__{k}" in merged]
        defs += [c for c in cfg.get("cols", []) if c in merged]
        st.session_state[f"{prefix}_cols"] = defs

    selected_columns = st.multiselect(
        "Kolom / ekspresi yang ditampilkan  (kosongkan = SELECT *):",
        list(merged.keys()), format_func=lambda x: merged.get(x, x), key=f"{prefix}_cols")

    # ============================================================
    # 3. FROM + JOIN
    # ============================================================
    join_columns = []

    if has_custom:
        st.markdown("### 3️⃣ FROM + JOIN")
        st.info("JOIN sudah didefinisikan di bawah. Edit langsung di text area jika perlu.")
        if f"{prefix}_custom_from" not in st.session_state:
            st.session_state[f"{prefix}_custom_from"] = cfg["custom_from"]
        st.text_area("FROM + JOIN:", key=f"{prefix}_custom_from", height=110)
    else:
        if len(selected_tables) >= 2:
            st.markdown("### 3️⃣ JOIN — Kolom Penghubung  *(Opsional)*")
            candidates = find_join_candidates(tables, selected_tables)

            if candidates:
                valid_jc = [f"{prefix}_jc_{i}" for i in range(len(candidates))]
                if f"{prefix}_jc" in st.session_state:
                    st.session_state[f"{prefix}_jc"] = [k for k in st.session_state[f"{prefix}_jc"] if k in valid_jc]

                cmap = {f"{prefix}_jc_{i}": c for i, c in enumerate(candidates)}
                chosen = st.multiselect(
                    f"Kolom bernama sama di {len(selected_tables)} tabel  ({len(candidates)} ditemukan):",
                    list(cmap.keys()), format_func=lambda x: cmap[x]["display"], key=f"{prefix}_jc")
                join_columns = [cmap[k] for k in chosen if k in cmap]

                if join_columns:
                    for jc in join_columns:
                        st.success(f"✅ `{jc['kolom']}`  →  {', '.join(jc['tabels'])}")
            else:
                st.warning("⚠️ Tidak ada kolom bernama sama di beberapa tabel. Tambahkan kondisi di WHERE jika perlu.")

        if len(selected_tables) >= 2 and not join_columns:
            st.warning("⚠️ Beberapa tabel tanpa kolom JOIN → akan menghasilkan CROSS JOIN.")

    # ============================================================
    # 4. WHERE
    # ============================================================
    st.markdown("### 4️⃣ Kondisi WHERE")

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
                                "IN", "NOT IN", "BETWEEN", "IS NULL", "IS NOT NULL"], key=f"{prefix}_wop")
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

    # ============================================================
    # ORDER BY & LIMIT
    # ============================================================
    with st.expander("📌 ORDER BY  &  LIMIT  *(Opsional)*"):

        if has_custom:
            if f"{prefix}_custom_ob" not in st.session_state:
                st.session_state[f"{prefix}_custom_ob"] = cfg.get("custom_order_by", "")
            st.text_area("ORDER BY:", key=f"{prefix}_custom_ob", height=100)
        else:
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

        st.text_input("LIMIT", placeholder="Kosongkan = tanpa limit", key=f"{prefix}_lim")

    # ============================================================
    # 5. TOMBOL
    # ============================================================
    st.markdown("---")

    if not has_custom:
        use_alias = st.checkbox("🏷️ Gunakan alias tabel", key=f"{prefix}_alias")
    else:
        use_alias = False

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("🔨 Buat Query", type="primary", use_container_width=True, key=f"{prefix}_build"):
            cf = st.session_state.get(f"{prefix}_custom_from", "") if has_custom else None
            cob = st.session_state.get(f"{prefix}_custom_ob", "") if has_custom else None
            if has_custom and not cob.strip():
                cob = None

            st.session_state[f"{prefix}_query"] = build_query(
                tables, selected_tables, selected_columns, join_columns,
                st.session_state.get(f"{prefix}_wheres", []),
                st.session_state.get(f"{prefix}_obs", []),
                st.session_state.get(f"{prefix}_lim", ""),
                use_alias,
                extra_select=extra_select or None,
                custom_from=cf,
                custom_order_by=cob)
    with b2:
        if st.button("🗑 Reset Semua Kondisi", type="secondary", use_container_width=True, key=f"{prefix}_reset"):
            for k in (f"{prefix}_wheres", f"{prefix}_obs", f"{prefix}_query", f"{prefix}_jc"):
                st.session_state.pop(k, None)
            st.rerun()

    # ============================================================
    # 6. HASIL QUERY
    # ============================================================
    if st.session_state.get(f"{prefix}_query"):
        st.markdown("---")
        st.markdown("### 6️⃣ Hasil Query SQL")
        q = st.session_state[f"{prefix}_query"]
        st.code(q, language="sql")
        cb1, cb2 = st.columns([1, 1])
        with cb1:
            copy_button(q)
        with cb2:
            st.download_button("💾 Download .sql", q, f"query_{prefix}.sql", "text/plain", use_container_width=True)


# ============================================================
# MAIN APP
# ============================================================

st.set_page_config(page_title="SQL Query Builder", page_icon="🔧", layout="wide")
st.title("🔧 SQL Query Builder")
st.caption("Generate query SQL dari file metadata CSV")

st.markdown("""<style>
    .stTabs [data-baseweb="tab-list"] [data-baseweb="tab"] { font-size: 16px; padding: 10px 28px; }
</style>""", unsafe_allow_html=True)

tables_umk      = load_metadata("metadata_umk.csv")
tables_ub       = load_metadata("metadata_ub.csv")
tables_keluarga = load_metadata("metadata_keluarga.csv")

tab_umk, tab_ub, tab_kel = st.tabs(["📄 UMK", "📄 UB", "📄 KELUARGA"])

with tab_umk:
    st.markdown(f"**Data:** `metadata_umk.csv`  —  "
                f"{'✅ ' + str(len(tables_umk)) + ' tabel' if tables_umk else '❌ file tidak ditemukan'}")
    render_tab("umk", "metadata_umk.csv", tables_umk)

with tab_ub:
    st.markdown(f"**Data:** `metadata_ub.csv`  —  "
                f"{'✅ ' + str(len(tables_ub)) + ' tabel' if tables_ub else '❌ file tidak ditemukan'}")
    render_tab("ub", "metadata_ub.csv", tables_ub)

with tab_kel:
    st.markdown(f"**Data:** `metadata_keluarga.csv`  —  "
                f"{'✅ ' + str(len(tables_keluarga)) + ' tabel' if tables_keluarga else '❌ file tidak ditemukan'}")
    render_tab("kel", "metadata_keluarga.csv", tables_keluarga)
