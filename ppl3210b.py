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


## PENDATAAN KELUARGA
url_qk = "https://simpul-jabar.32net.id/api/kualitas-data-rekap?kdkab=3210%20-%20KAB.%20MAJALENGKA&kdkec=&kdkel=&level=sls"

response_qk = requests.get(url_qk)
response_qk.raise_for_status()  # raise error jika gagal

json_data_qk = response_qk.json()

# Ambil key "data" yang berisi list of dict
df_qk = pd.DataFrame(json_data_qk["data"])

df_qk["desa"] = df_qk["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[0]
df_qk["kec"]  = df_qk["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[1]
df_qk["sls"]  = df_qk["wilayah"]

df_art = df_qk[['kec', 'desa', 'sls', 'art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']]
df_art = df_art.sort_values(by=['kec', 'desa', 'sls'])

df_kk = df_qk[['kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
       'k_khusus', 'k_meninggal', 'k_menolak',
       'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']]
df_kk = df_kk.sort_values(by=['kec', 'desa', 'sls'])


with st.container(border=True):
       st.header("Progress Sensus Ekonomi 2026 Kabupaten Majalengka")
       st.caption("Sumber: simpul-jabar.32net.id")

tab_ppl, tab_sls, tab_usaha, tab_qc = st.tabs(['PPL', 'SLS', 'PENDATAAN USAHA', 'PENDATAAN KELUARGA'])

with tab_ppl:
    st.subheader("Progress PPL")
    st.dataframe(df_ppl2, width='stretch', hide_index=True)

with tab_sls:
    st.subheader("Progress SLS")
    st.dataframe(df_sls2, width='stretch', hide_index=True)

with tab_usaha:
    st.subheader("Progress Pendataan Usaha")
    df_bku['kab'] = 'KAB. MAJALENGKA'
    df_bku_kab = df_bku.groupby(by=['kab'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
    
    grafik_bku_kab = px.bar(df_bku_kab, x='kab', y=['target_usaha', 'bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Capaian Pendataan BKU", labels={'value':'Jumlah', 'variable':'Status'})
    
    with st.container(border=True):    
        st.plotly_chart(grafik_bku_kab, width="content")
    
    with st.expander("PER SLS"):
        st.dataframe(df_bku, width='stretch', hide_index=True)
    with st.expander("REKAP DESA"):
        df_bku_desa = df_bku.groupby(by=['kec', 'desa'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
        st.dataframe(df_bku_desa, width='stretch', hide_index=True)
    with st.expander("REKAP KECAMATAN"):
        df_bku_kec = df_bku.groupby(by=['kec'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
        st.dataframe(df_bku_kec, width='stretch', hide_index=True)
        
        grafik_bku_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Rekap Pendataan BKU per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})
        
        with st.container(border=True):
            st.plotly_chart(grafik_bku_kec, width="content")
    

with tab_qc:
    st.subheader("Pendataan Keluarga")
    
    with st.expander("KUALITAS DATA KELUARGA"):
       st.dataframe(df_kk, width='stretch', hide_index=True)

    with st.expander("KUALITAS DATA ANGGOTA KELUARGA"):
       st.dataframe(df_art, width='stretch', hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)
