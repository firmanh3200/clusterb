import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import lxml

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard SE2026 Majalengka",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


## PPL
url_ppl = "https://simpul-jabar.32net.id/api/um-rekap?kdkab=3210%20-%20KAB.%20MAJALENGKA&kdkec=&kdkel=&level_view=PETUGAS"

response_ppl = requests.get(url_ppl)
response_ppl.raise_for_status()  # raise error jika gagal

json_data_ppl = response_ppl.json()

# Ambil key "data" yang berisi list of dict
df_ppl = pd.DataFrame(json_data_ppl["data"])

df_ppl = df_ppl.sort_values(by=['kec_petugas', 'kel_petugas', 'nama_petugas'])

df_ppl2 = df_ppl.groupby(by=['kec_petugas', 'kel_petugas', 'nama_petugas'])[['target', 'open_val', 'draft', 'submit', 'pendataan']].sum().reset_index()


## SLS
url_sls = "https://simpul-jabar.32net.id/api/um-rekap?kdkab=3210%20-%20KAB.%20MAJALENGKA&kdkec=&kdkel=&level_view=SLS"

response_sls = requests.get(url_sls)
response_sls.raise_for_status()  # raise error jika gagal

json_data_sls = response_sls.json()

# Ambil key "data" yang berisi list of dict
df_sls = pd.DataFrame(json_data_sls["data"])

df_sls["sls"]  = df_sls["kdkab"]
df_sls = df_sls.sort_values(by=['nama_kab', 'nama_kec', 'nama_kel', 'sls'])

df_sls2 = df_sls[['nama_kec', 'nama_kel', 'sls', 'nama_lengkap', 'email', 'no_telp', 'target', 'open_val', 'submit', 'pendataan', 'percentage', 'percentage_pendataan', 'progress_difference', 'rerata_per_24_jam', 'selisih_jam']]
df_sls2 = df_sls2.sort_values(by=['nama_kec', 'nama_kel', 'sls'])


## USAHA
url_usaha = "https://simpul-jabar.32net.id/api/usaha-data-rekap?kdkab=3210%20-%20KAB.%20MAJALENGKA&kdkec=&kdkel=&level=sls"

response_usaha = requests.get(url_usaha)
response_usaha.raise_for_status()  # raise error jika gagal

json_data_usaha = response_usaha.json()

# Ambil key "data" yang berisi list of dict
df_usaha = pd.DataFrame(json_data_usaha["data"])

df_usaha["desa"] = df_usaha["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[0]
df_usaha["kec"]  = df_usaha["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[1]
df_usaha["sls"]  = df_usaha["wilayah"]
df_usaha = df_usaha.sort_values(by=['kec', 'desa', 'sls'])

df_bku = df_usaha[['kec', 'desa', 'sls', 'target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']]


## KUALITAS
url_q = "https://simpul-jabar.32net.id/api/kualitas-data-rekap?kdkab=3210%20-%20KAB.%20MAJALENGKA&kdkec=&kdkel=&level=sls"

response_q = requests.get(url_q)
response_q.raise_for_status()  # raise error jika gagal

json_data_q = response_q.json()

# Ambil key "data" yang berisi list of dict
df_q = pd.DataFrame(json_data_q["data"])

df_q["desa"] = df_q["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[0]
df_q["kec"]  = df_q["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[1]
df_q["sls"]  = df_q["wilayah"]

df_art = df_q[['kec', 'desa', 'sls', 'art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']]
df_art = df_art.sort_values(by=['kec', 'desa', 'sls'])

df_kk = df_q[['kec', 'desa', 'sls', 'target_keluarga', 'usaha_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
       'k_khusus', 'k_memiliki_usaha', 'k_meninggal', 'k_menolak',
       'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']]
df_kk = df_kk.sort_values(by=['kec', 'desa', 'sls'])

df_qusaha = df_q[['kec', 'desa', 'sls', 'target_usaha', 'target_ub', 'ub_didata', 'target_um', 'um_didata', 'target_umk', 'umk_didata', 'bku_baru', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_tutup']]
df_qusaha = df_qusaha.sort_values(by=['kec', 'desa', 'sls'])


with st.container(border=True):
       st.header("Progress Sensus Ekonomi 2026 Kabupaten Majalengka")
       st.caption("Sumber: simpul-jabar.32net.id")

tab_ppl, tab_sls, tab_usaha, tab_qc = st.tabs(['PPL', 'SLS', 'USAHA', 'KUALITAS'])

with tab_ppl:
    st.subheader("Progress PPL")
    st.dataframe(df_ppl2, width='stretch', hide_index=True)

with tab_sls:
    st.subheader("Progress SLS")
    st.dataframe(df_sls2, width='stretch', hide_index=True)

with tab_usaha:
    st.subheader("Progress Usaha")
    st.dataframe(df_bku, width='stretch', hide_index=True)

with tab_qc:
    st.subheader("Kualitas Data")
    
    with st.expander("KUALITAS DATA USAHA"):
       st.dataframe(df_qusaha, width='stretch', hide_index=True)

    with st.expander("KUALITAS DATA KELUARGA"):
       st.dataframe(df_kk, width='stretch', hide_index=True)

    with st.expander("KUALITAS DATA ANGGOTA KELUARGA"):
       st.dataframe(df_art, width='stretch', hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)