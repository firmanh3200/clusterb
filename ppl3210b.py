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

df_ppl2['target'] = df_ppl2['target'].astype('Int64')
df_ppl2['open_val'] = df_ppl2['open_val'].astype('Int64')
df_ppl2['draft'] = df_ppl2['draft'].astype('Int64')
df_ppl2['submit'] = df_ppl2['submit'].astype('Int64')
df_ppl2['pendataan'] = df_ppl2['pendataan'].astype('Int64')

#TERTINGGI
target_tertinggi = df_ppl2.loc[df_ppl2['target'].idxmax(), ['target', 'nama_petugas', 'kec_petugas']]
open_tertinggi = df_ppl2.loc[df_ppl2['open_val'].idxmax(), ['open_val', 'nama_petugas', 'kec_petugas']]
draft_tertinggi = df_ppl2.loc[df_ppl2['draft'].idxmax(), ['draft', 'nama_petugas', 'kec_petugas']]
submit_tertinggi = df_ppl2.loc[df_ppl2['submit'].idxmax(), ['submit', 'nama_petugas', 'kec_petugas']]
mendata_tertinggi = df_ppl2.loc[df_ppl2['pendataan'].idxmax(), ['pendataan', 'nama_petugas', 'kec_petugas']]

#TERENDAH
target_terendah = df_ppl2.loc[df_ppl2['target'].idxmin(), ['target', 'nama_petugas', 'kec_petugas']]
open_terendah = df_ppl2.loc[df_ppl2['open_val'].idxmin(), ['open_val', 'nama_petugas', 'kec_petugas']]
draft_terendah = df_ppl2.loc[df_ppl2['draft'].idxmin(), ['draft', 'nama_petugas', 'kec_petugas']]
submit_terendah = df_ppl2.loc[df_ppl2['submit'].idxmin(), ['submit', 'nama_petugas', 'kec_petugas']]
mendata_terendah = df_ppl2.loc[df_ppl2['pendataan'].idxmin(), ['pendataan', 'nama_petugas', 'kec_petugas']]

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

df_sls2['sls2'] = df_sls2['sls'].str.replace(r'\s*\([^)]*\)\s*$', '', regex=True)

sls_didata = df_sls2[df_sls2['pendataan'] != 0].copy()
sls_belum = df_sls2[df_sls2['pendataan'] == 0].copy()

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
df_art["kab"]  = "KAB. MAJALENGKA"

rekap_art_kab = df_art.groupby(by='kab')[['art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']].sum().reset_index()

df_kk = df_qk[['kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
       'k_khusus', 'k_meninggal', 'k_menolak',
       'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']]
df_kk = df_kk.sort_values(by=['kec', 'desa', 'sls'])
df_kk["kab"]  = "KAB. MAJALENGKA"

rekap_kk_kab = df_kk.groupby(by='kab')[['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
       'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']].sum().reset_index()

# Samakan tipe data menjadi string terlebih dahulu
df_bku['kec'] = df_bku['kec'].astype(str)
df_bku['desa'] = df_bku['desa'].astype(str)
df_bku['sls'] = df_bku['sls'].astype(str)

df_sls2['nama_kec'] = df_sls2['nama_kec'].astype(str).str.strip()
df_sls2['nama_kel'] = df_sls2['nama_kel'].astype(str).str.strip()
df_sls2['sls2'] = df_sls2['sls2'].astype(str)

# Langkah 1: Merge berdasarkan 3 kolom kunci
kolom_yang_diperlukan = ['nama_kec', 'nama_kel', 'sls2', 'nama_lengkap', 'email', 'no_telp']
df_sls2_subset = df_sls2[kolom_yang_diperlukan]

# 2. Lakukan merge dengan menyesuaikan nama kolom kuncinya
df_bku = df_bku.merge(
    df_sls2_subset,
    how='left', 
    left_on=['kec', 'desa', 'sls'],           # Nama kolom di df_bku
    right_on=['nama_kec', 'nama_kel', 'sls2'] # Nama kolom di df_sls2
)

# 3. Buang kolom kunci bawaan df_sls2 yang sudah tidak diperlukan lagi
# Karena nama kolomnya berbeda, merge akan menghasilkan 6 kolom kunci.
# Kita hapus 3 kolom milik df_sls2 ('nama_kec', 'nama_kel', 'sls2') karena sudah diwakili oleh 'kec', 'desa', 'sls'
df_bku = df_bku.drop(columns=['nama_kec', 'nama_kel', 'sls2'])

usaha_ppl = df_bku.groupby(by=['kec', 'nama_lengkap', 'email'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()

with st.container(border=True):
       st.header("Progress SE2026 Kabupaten Majalengka")
       st.caption("Sumber: simpul-jabar.32net.id")

tab_ppl, tab_sls, tab_usaha, tab_qc = st.tabs(['PPL', 'SLS', 'PENDATAAN USAHA', 'PENDATAAN KELUARGA'])

with tab_ppl:
    st.subheader("Progress PPL")
    kol1a, kol1b = st.columns(2)
    with kol1a:
        with st.container(border=True):
            st.subheader("Tertinggi")
            st.success(f"Pendataan: {' | '.join(mendata_tertinggi.astype(str).values)}")
            st.info(f"Submit: {' | '.join(submit_tertinggi.astype(str).values)}")
            st.warning(f"Draft: {' | '.join(draft_tertinggi.astype(str).values)}")
            st.caption(f"Target: {' | '.join(target_tertinggi.astype(str).values)}")
            st.caption(f"Open: {' | '.join(open_tertinggi.astype(str).values)}")

    with kol1b:
        with st.container(border=True):
            st.subheader("Terendah")
            st.success(f"Pendataan: {' | '.join(mendata_terendah.astype(str).values)}")
            st.info(f"Submit: {' | '.join(submit_terendah.astype(str).values)}")
            st.warning(f"Draft: {' | '.join(draft_terendah.astype(str).values)}")
            st.caption(f"Target: {' | '.join(target_terendah.astype(str).values)}")
            st.caption(f"Open: {' | '.join(open_terendah.astype(str).values)}")
    
    st.dataframe(df_ppl2, width='stretch', hide_index=True)

with tab_sls:
    st.subheader("Progress SLS")
    st.dataframe(sls_didata, width='stretch', hide_index=True)
    st.divider()
    st.subheader("SLS Belum Didata")
    st.dataframe(sls_belum, width='stretch', hide_index=True)
    
with tab_usaha:
    st.subheader("Progress Pendataan Usaha")
    df_bku['kab'] = 'KAB. MAJALENGKA'
    df_bku_kab = df_bku.groupby(by=['kab'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
    
    grafik_bku_kab = px.bar(df_bku_kab, x='kab', y=['bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Capaian Pendataan BKU", labels={'value':'Jumlah', 'variable':'Status'})
    grafik_bku_kab.update_yaxes(
        range=[0, 210000],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )
    
    grafik_uk_kab = px.bar(df_bku_kab, x='kab', y=['uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_baru'], barmode='group', title="Capaian Pendataan Usaha Keluarga", labels={'value':'Jumlah', 'variable':'Status'})
    grafik_uk_kab.update_yaxes(
        range=[0, 210000],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )

    grafik_target_usaha = px.bar(df_bku_kab, x='kab', y='target_usaha', title="Target Usaha")
    grafik_target_usaha.update_yaxes(
        range=[0, 210000],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )

    kol1c, kol2c, kol3c = st.columns([3, 2, 3])
    
    with kol1c:
        with st.container(border=True):    
            st.plotly_chart(grafik_bku_kab, width="content")
    
    with kol2c:
        with st.container(border=True):
            st.plotly_chart(grafik_target_usaha, width="stretch")
    
    with kol3c:
        with st.container(border=True):
            st.plotly_chart(grafik_uk_kab, width="content")

    with st.expander("REKAP KECAMATAN"):
        df_bku_kec = df_bku.groupby(by=['kec'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
        st.dataframe(df_bku_kec, width='stretch', hide_index=True)
        
        grafik_bku_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Rekap Pendataan BKU per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})

        grafik_uk_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_tutup', 'uk_baru'], barmode='group', title="Rekap Pendataan Usaha Keluarga per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})
        
        with st.container(border=True):
            st.plotly_chart(grafik_bku_kec, width="stretch")

        with st.container(border=True):
            st.plotly_chart(grafik_uk_kec, width="stretch")
    
    with st.expander("REKAP DESA"):
        df_bku_desa = df_bku.groupby(by=['kec', 'desa'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
        st.dataframe(df_bku_desa, width='stretch', hide_index=True)
    
    with st.expander("PER SLS"):
        st.dataframe(df_bku, width='stretch', hide_index=True)
    
    with st.expander("REKAP PPL"):
        st.dataframe(usaha_ppl, width='stretch', hide_index=True)

with tab_qc:
    st.subheader("Pendataan Keluarga")
    
    with st.expander("HASIL PENDATAAN KELUARGA"):
       grafik_kk = px.bar(rekap_kk_kab, x='kab', y=['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan', 'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible'], barmode='group')
       st.plotly_chart(grafik_kk, width='stretch') 
       st.dataframe(df_kk, width='stretch', hide_index=True)

    with st.expander("HASIL PENDATAAN ANGGOTA KELUARGA"):
       st.dataframe(df_art, width='stretch', hide_index=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)
