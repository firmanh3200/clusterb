import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import lxml
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard SE2026 Jabar",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

tanggal_mulai = datetime(2026, 6, 14)
tanggal_target = datetime(2026, 8, 31)
hari_ini = datetime.now()

hari_ke = (hari_ini - tanggal_mulai).days
menuju = (tanggal_target - hari_ini).days

data_wilayah = [
    {"kode": 3201, "tipe": "-", "nama": "KAB. BOGOR"},
    {"kode": 3202, "tipe": "-", "nama": "KAB. SUKABUMI"},
    {"kode": 3203, "tipe": "-", "nama": "KAB. CIANJUR"},
    {"kode": 3204, "tipe": "-", "nama": "KAB. BANDUNG"},
    {"kode": 3205, "tipe": "-", "nama": "KAB. GARUT"},
    {"kode": 3206, "tipe": "-", "nama": "KAB. TASIKMALAYA"},
    {"kode": 3207, "tipe": "-", "nama": "KAB. CIAMIS"},
    {"kode": 3208, "tipe": "-", "nama": "KAB. KUNINGAN"},
    {"kode": 3209, "tipe": "-", "nama": "KAB. CIREBON"},
    {"kode": 3210, "tipe": "-", "nama": "KAB. MAJALENGKA"},
    {"kode": 3211, "tipe": "-", "nama": "KAB. SUMEDANG"},
    {"kode": 3212, "tipe": "-", "nama": "KAB. INDRAMAYU"},
    {"kode": 3213, "tipe": "-", "nama": "KAB. SUBANG"},
    {"kode": 3214, "tipe": "-", "nama": "KAB. PURWAKARTA"},
    {"kode": 3215, "tipe": "-", "nama": "KAB. KARAWANG"},
    {"kode": 3216, "tipe": "-", "nama": "KAB. BEKASI"},
    {"kode": 3217, "tipe": "-", "nama": "KAB. BANDUNG BARAT"},
    {"kode": 3218, "tipe": "-", "nama": "KAB. PANGANDARAN"},
    {"kode": 3271, "tipe": "-", "nama": "BOGOR"},
    {"kode": 3272, "tipe": "-", "nama": "SUKABUMI"},
    {"kode": 3273, "tipe": "-", "nama": "BANDUNG"},
    {"kode": 3274, "tipe": "-", "nama": "CIREBON"},
    {"kode": 3275, "tipe": "-", "nama": "BEKASI"},
    {"kode": 3276, "tipe": "-", "nama": "DEPOK"},
    {"kode": 3277, "tipe": "-", "nama": "CIMAHI"},
    {"kode": 3278, "tipe": "-", "nama": "TASIKMALAYA"},
    {"kode": 3279, "tipe": "-", "nama": "BANJAR"},
]

# Buat label
labels = [f"{d['kode']} {d['tipe']} {d['nama']}" for d in data_wilayah]

with st.container(border=True):
    pilihan = st.selectbox("Pilih Wilayah:", options=labels, key="pilihan1")

# Cari index yang dipilih
idx = labels.index(pilihan)

v1 = data_wilayah[idx]["kode"]
v2 = data_wilayah[idx]["tipe"]
v3 = data_wilayah[idx]["nama"]

if pilihan:
    ## PPL
    url_ppl = f"https://simpul-jabar.32net.id/api/um-rekap?kdkab={v1}%20{v2}%20{v3}&kdkec=&kdkel=&level_view=PETUGAS"


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
    url_sls = f"https://simpul-jabar.32net.id/api/um-rekap?kdkab={v1}%20{v2}%20{v3}&kdkec=&kdkel=&level_view=SLS"

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
    url_usaha = f"https://simpul-jabar.32net.id/api/usaha-data-rekap?kdkab={v1}%20{v2}%20{v3}&kdkec=&kdkel=&level=sls"

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
    url_qk = f"https://simpul-jabar.32net.id/api/kualitas-data-rekap?kdkab={v1}%20{v2}%20{v3}&kdkec=&kdkel=&level=sls"

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
    df_art["kab"]  = f"{v1}"

    rekap_art_kab = df_art.groupby(by='kab')[['art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']].sum().reset_index()

    df_kk = df_qk[['kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
        'k_khusus', 'k_meninggal', 'k_menolak',
        'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']]
    df_kk = df_kk.sort_values(by=['kec', 'desa', 'sls'])
    df_kk["kab"]  = f"{v1}"

    rekap_kk_kab = df_kk.groupby(by='kab')[['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
        'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']].sum().reset_index()

    # Samakan tipe data menjadi string terlebih dahulu
    df_kk['sls'] = df_kk['sls'].astype(str)
    
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

    df_kk2 = df_kk.merge(
        df_sls2_subset,
        how='left', 
        left_on=['kec', 'desa', 'sls'],           # Nama kolom di df_bku
        right_on=['nama_kec', 'nama_kel', 'sls2'] # Nama kolom di df_sls2
    )

    df_lk = df_kk2.merge(
        df_bku,
        how='left', 
        left_on=['kec', 'desa', 'sls'],           # Nama kolom di df_bku
        right_on=['kec', 'desa', 'sls'] # Nama kolom di df_sls2
    )

    df_kk2 = df_kk2.sort_values(by=['kec', 'nama_lengkap', 'desa', 'sls'])

    # 3. Buang kolom kunci bawaan df_sls2 yang sudah tidak diperlukan lagi
    # Karena nama kolomnya berbeda, merge akan menghasilkan 6 kolom kunci.
    # Kita hapus 3 kolom milik df_sls2 ('nama_kec', 'nama_kel', 'sls2') karena sudah diwakili oleh 'kec', 'desa', 'sls'
    df_bku = df_bku.drop(columns=['nama_kec', 'nama_kel', 'sls2'])
    df_kk2 = df_kk2.drop(columns=['nama_kec', 'nama_kel', 'sls2'])

    kk_ppl = df_kk2.groupby(by=['kec', 'nama_lengkap', 'email'])[['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan', 'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']].sum().reset_index()

    kk_ppl['k_baru'] = kk_ppl['k_baru'].astype('Int64')
    kk_ppl['k_ditemukan'] = kk_ppl['k_ditemukan'].astype('Int64')
    kk_ppl['k_meninggal'] = kk_ppl['k_meninggal'].astype('Int64')
    kk_ppl['k_menolak'] = kk_ppl['k_menolak'].astype('Int64')
    kk_ppl['k_tidak_ditemukan'] = kk_ppl['k_tidak_ditemukan'].astype('Int64')


    #TERTINGGI
    maks_kk_baru = kk_ppl.loc[kk_ppl['k_baru'].idxmax(), ['k_baru', 'nama_lengkap', 'kec']]
    maks_kk_ketemu = kk_ppl.loc[kk_ppl['k_ditemukan'].idxmax(), ['k_ditemukan', 'nama_lengkap', 'kec']]
    maks_kk_meninggal = kk_ppl.loc[kk_ppl['k_meninggal'].idxmax(), ['k_meninggal', 'nama_lengkap', 'kec']]
    maks_kk_menolak = kk_ppl.loc[kk_ppl['k_menolak'].idxmax(), ['k_menolak', 'nama_lengkap', 'kec']]
    maks_kk_gaketemu = kk_ppl.loc[kk_ppl['k_tidak_ditemukan'].idxmax(), ['k_tidak_ditemukan', 'nama_lengkap', 'kec']]


    #TERENDAH
    min_kk_baru = kk_ppl.loc[kk_ppl['k_baru'].idxmin(), ['k_baru', 'nama_lengkap', 'kec']]
    min_kk_ketemu = kk_ppl.loc[kk_ppl['k_ditemukan'].idxmin(), ['k_ditemukan', 'nama_lengkap', 'kec']]
    min_kk_meninggal = kk_ppl.loc[kk_ppl['k_meninggal'].idxmin(), ['k_meninggal', 'nama_lengkap', 'kec']]
    min_kk_menolak = kk_ppl.loc[kk_ppl['k_menolak'].idxmin(), ['k_menolak', 'nama_lengkap', 'kec']]
    min_kk_gaketemu = kk_ppl.loc[kk_ppl['k_tidak_ditemukan'].idxmin(), ['k_tidak_ditemukan', 'nama_lengkap', 'kec']]

    
    ## B K U
    usaha_ppl = df_bku.groupby(by=['kec', 'nama_lengkap', 'email'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()

    usaha_ppl['bku_baru'] = usaha_ppl['bku_baru'].astype('Int64')
    usaha_ppl['bku_ganda'] = usaha_ppl['bku_ganda'].astype('Int64')
    usaha_ppl['bku_tutup'] = usaha_ppl['bku_tutup'].astype('Int64')
    usaha_ppl['bku_tdk_ditemukan'] = usaha_ppl['bku_tdk_ditemukan'].astype('Int64')
    usaha_ppl['bku_ditemukan'] = usaha_ppl['bku_ditemukan'].astype('Int64')


    #TERTINGGI
    maks_bku_baru = usaha_ppl.loc[usaha_ppl['bku_baru'].idxmax(), ['bku_baru', 'nama_lengkap', 'kec']]
    maks_bku_ganda = usaha_ppl.loc[usaha_ppl['bku_ganda'].idxmax(), ['bku_ganda', 'nama_lengkap', 'kec']]
    maks_bku_tutup = usaha_ppl.loc[usaha_ppl['bku_tutup'].idxmax(), ['bku_tutup', 'nama_lengkap', 'kec']]
    maks_bku_tdketemu = usaha_ppl.loc[usaha_ppl['bku_tdk_ditemukan'].idxmax(), ['bku_tdk_ditemukan', 'nama_lengkap', 'kec']]
    maks_bku_ketemu = usaha_ppl.loc[usaha_ppl['bku_ditemukan'].idxmax(), ['bku_ditemukan', 'nama_lengkap', 'kec']]


    #TERENDAH
    min_bku_baru = usaha_ppl.loc[usaha_ppl['bku_baru'].idxmin(), ['bku_baru', 'nama_lengkap', 'kec']]
    min_bku_ganda = usaha_ppl.loc[usaha_ppl['bku_ganda'].idxmin(), ['bku_ganda', 'nama_lengkap', 'kec']]
    min_bku_tutup = usaha_ppl.loc[usaha_ppl['bku_tutup'].idxmin(), ['bku_tutup', 'nama_lengkap', 'kec']]
    min_bku_tdketemu = usaha_ppl.loc[usaha_ppl['bku_tdk_ditemukan'].idxmin(), ['bku_tdk_ditemukan', 'nama_lengkap', 'kec']]
    min_bku_ketemu = usaha_ppl.loc[usaha_ppl['bku_ditemukan'].idxmin(), ['bku_ditemukan', 'nama_lengkap', 'kec']]

    ## USAHA KELUARGA
    usaha_ppl['uk_baru'] = usaha_ppl['uk_baru'].astype('Int64')
    usaha_ppl['uk_ganda'] = usaha_ppl['uk_ganda'].astype('Int64')
    usaha_ppl['uk_tutup'] = usaha_ppl['uk_tutup'].astype('Int64')
    usaha_ppl['uk_tdk_ditemukan'] = usaha_ppl['uk_tdk_ditemukan'].astype('Int64')
    usaha_ppl['uk_ditemukan'] = usaha_ppl['uk_ditemukan'].astype('Int64')


    #TERTINGGI
    maks_uk_baru = usaha_ppl.loc[usaha_ppl['uk_baru'].idxmax(), ['uk_baru', 'nama_lengkap', 'kec']]
    maks_uk_ganda = usaha_ppl.loc[usaha_ppl['uk_ganda'].idxmax(), ['uk_ganda', 'nama_lengkap', 'kec']]
    maks_uk_tutup = usaha_ppl.loc[usaha_ppl['uk_tutup'].idxmax(), ['uk_tutup', 'nama_lengkap', 'kec']]
    maks_uk_tdketemu = usaha_ppl.loc[usaha_ppl['uk_tdk_ditemukan'].idxmax(), ['uk_tdk_ditemukan', 'nama_lengkap', 'kec']]
    maks_uk_ketemu = usaha_ppl.loc[usaha_ppl['uk_ditemukan'].idxmax(), ['uk_ditemukan', 'nama_lengkap', 'kec']]


    #TERENDAH
    min_uk_baru = usaha_ppl.loc[usaha_ppl['uk_baru'].idxmin(), ['uk_baru', 'nama_lengkap', 'kec']]
    min_uk_ganda = usaha_ppl.loc[usaha_ppl['uk_ganda'].idxmin(), ['uk_ganda', 'nama_lengkap', 'kec']]
    min_uk_tutup = usaha_ppl.loc[usaha_ppl['uk_tutup'].idxmin(), ['uk_tutup', 'nama_lengkap', 'kec']]
    min_uk_tdketemu = usaha_ppl.loc[usaha_ppl['uk_tdk_ditemukan'].idxmin(), ['uk_tdk_ditemukan', 'nama_lengkap', 'kec']]
    min_uk_ketemu = usaha_ppl.loc[usaha_ppl['uk_ditemukan'].idxmin(), ['uk_ditemukan', 'nama_lengkap', 'kec']]


    df_bku['kab'] = f'{v1}'
    df_bku_kab = df_bku.groupby(by=['kab'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
    
    grafik_bku_kab = px.bar(df_bku_kab, x='kab', y=['bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Capaian Pendataan BKU", labels={'value':'Jumlah', 'variable':'Status'})
    grafik_bku_kab.update_yaxes(
        range=[0, df_bku_kab['target_usaha'].max()],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )
    
    df_uk_kab = df_bku.groupby(by=['kab'])[['target_usaha', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
    
    grafik_uk_kab = px.bar(df_uk_kab, x='kab', y=['uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_baru'], barmode='group', title="Capaian Pendataan Usaha Keluarga", labels={'value':'Jumlah', 'variable':'Status'})
    grafik_uk_kab.update_yaxes(
        range=[0, df_uk_kab['target_usaha'].max()],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )

    grafik_target_usaha = px.bar(df_bku_kab, x='kab', y='target_usaha', title="Target Usaha")
    grafik_target_usaha.update_yaxes(
        range=[0, df_bku_kab['target_usaha'].max()],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )

    grafik_kk_kab = px.bar(rekap_kk_kab, x='kab', y=['target_keluarga', 'k_ditemukan', 'k_tidak_ditemukan', 'k_menolak', 'k_meninggal', 'k_baru', 'k_tidak_eligible'], barmode='group', title="Capaian Pendataan Keluarga", labels={'value':'Jumlah', 'variable':'Status'})
    grafik_kk_kab.update_yaxes(
        range=[0, rekap_kk_kab['target_keluarga'].max()],
        tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
    )


    df_bku_kec = df_bku.groupby(by=['kec'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
    #st.dataframe(df_bku_kec, width='stretch', hide_index=True)
    
    grafik_bku_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Rekap Pendataan BKU per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})

    grafik_uk_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_tutup', 'uk_baru'], barmode='group', title="Rekap Pendataan Usaha Keluarga per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})
    
    df_bku_desa = df_bku.groupby(by=['kec', 'desa'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
            

    with st.container(border=True):
        with st.container(border=True):
            st.header(f"MONITORING KINERJA PPL: {v1} {v2} {v3}")
            kol1, kol2 = st.columns(2)
            with kol1:
                st.success(f"Hari ke: {hari_ke}")
            with kol2:
                st.warning(f"Sisa Waktu: {menuju} Hari")
            st.caption("Sumber: simpul-jabar.32net.id")

    dashboard, tab_ppl = st.tabs(['DASHBOARD', 'KINERJA PPL'])

    with dashboard:
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

        st.divider()
        with st.expander("PENDATAAN BKU"):
            kol4aa, kol4bb = st.columns(2)
            with kol4aa:
                with st.container(border=True):
                    st.subheader("Pendataan BKU Tertinggi")
                    st.success(f"Baru: {' | '.join(maks_bku_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(maks_bku_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(maks_bku_tutup.astype(str).values)}")
                    st.text(f"Tidak Ditemukan: {' | '.join(maks_bku_tdketemu.astype(str).values)}")
                    st.caption(f"Ditemukan: {' | '.join(maks_bku_ketemu.astype(str).values)}")
        
            with kol4bb:
                with st.container(border=True):
                    st.subheader("Pendataan BKU Terendah")
                    st.success(f"Baru: {' | '.join(min_bku_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(min_bku_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(min_bku_tutup.astype(str).values)}")
                    st.caption(f"Tidak Ditemukan: {' | '.join(min_bku_tdketemu.astype(str).values)}")
                    st.text(f"Ditemukan: {' | '.join(min_bku_ketemu.astype(str).values)}")

        st.divider()
        with st.expander("PENDATAAN USAHA KELUARGA"):
            kol4cc, kol4dd = st.columns(2)
            with kol4cc:
                with st.container(border=True):
                    st.subheader("Pendataan Usaha Keluarga Tertinggi")
                    st.success(f"Baru: {' | '.join(maks_uk_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(maks_uk_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(maks_uk_tutup.astype(str).values)}")
                    st.text(f"Tidak Ditemukan: {' | '.join(maks_uk_tdketemu.astype(str).values)}")
                    st.caption(f"Ditemukan: {' | '.join(maks_uk_ketemu.astype(str).values)}")
        
            with kol4dd:
                with st.container(border=True):
                    st.subheader("Pendataan Usaha Keluarga Terendah")
                    st.success(f"Baru: {' | '.join(min_uk_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(min_uk_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(min_uk_tutup.astype(str).values)}")
                    st.caption(f"Tidak Ditemukan: {' | '.join(min_uk_tdketemu.astype(str).values)}")
                    st.text(f"Ditemukan: {' | '.join(min_uk_ketemu.astype(str).values)}")

        st.divider()
        with st.expander("PENDATAAN KELUARGA"):
            kolom1, kolom2, kolom3 = st.columns(3)
            with kolom1:
                with st.container(border=True):
                    st.subheader("Pendataan Keluarga Tertinggi")
                    st.success(f"Baru: {' | '.join(maks_kk_baru.astype(str).values)}")
                    st.info(f"Ditemukan: {' | '.join(maks_kk_ketemu.astype(str).values)}")
                    st.warning(f"Meninggal: {' | '.join(maks_kk_meninggal.astype(str).values)}")
                    st.text(f"Tidak Ditemukan: {' | '.join(maks_kk_gaketemu.astype(str).values)}")
                    st.caption(f"Menolak: {' | '.join(maks_kk_menolak.astype(str).values)}")
        
            with kolom2:
                with st.container(border=True):    
                    st.plotly_chart(grafik_kk_kab, width="content")
            
            with kolom3:
                with st.container(border=True):
                    st.subheader("Pendataan Keluarga Terendah")
                    st.success(f"Baru: {' | '.join(min_kk_baru.astype(str).values)}")
                    st.info(f"Ditemukan: {' | '.join(min_kk_ketemu.astype(str).values)}")
                    st.warning(f"Meninggal: {' | '.join(min_kk_meninggal.astype(str).values)}")
                    st.text(f"Tidak Ditemukan: {' | '.join(min_kk_gaketemu.astype(str).values)}")
                    st.caption(f"Menolak: {' | '.join(min_kk_menolak.astype(str).values)}")


        st.divider()
        with st.expander("TOTAL ASSIGNMENT"):
            kol1a, kol1b = st.columns(2)
            with kol1a:
                with st.container(border=True):
                    st.subheader("Pendataan Tertinggi")
                    st.success(f"Pendataan: {' | '.join(mendata_tertinggi.astype(str).values)}")
                    st.info(f"Submit: {' | '.join(submit_tertinggi.astype(str).values)}")
                    st.warning(f"Draft: {' | '.join(draft_tertinggi.astype(str).values)}")
                    st.caption(f"Target: {' | '.join(target_tertinggi.astype(str).values)}")
                    st.caption(f"Open: {' | '.join(open_tertinggi.astype(str).values)}")

            with kol1b:
                with st.container(border=True):
                    st.subheader("Pendataan Terendah")
                    st.success(f"Pendataan: {' | '.join(mendata_terendah.astype(str).values)}")
                    st.info(f"Submit: {' | '.join(submit_terendah.astype(str).values)}")
                    st.warning(f"Draft: {' | '.join(draft_terendah.astype(str).values)}")
                    st.caption(f"Target: {' | '.join(target_terendah.astype(str).values)}")
                    st.caption(f"Open: {' | '.join(open_terendah.astype(str).values)}")

        st.divider()
        with st.expander("SLS Belum Didata"):
            st.subheader("SLS Belum Didata")
            st.dataframe(sls_belum, width='stretch', hide_index=True)
            st.caption(f"Jumlah SLS: {len(sls_belum)}")
            st.divider()
            pilihankec2 = sls_belum['nama_kec'].unique()
            kec_terpilih2 = st.selectbox("Pilih Kecamatan", pilihankec2, key="pilihan3")

            if kec_terpilih2:
                sls_belum2 = sls_belum[sls_belum['nama_kec'] == kec_terpilih2]
                st.dataframe(sls_belum2, width='stretch', hide_index=True)
                st.caption(f"Jumlah SLS: {len(sls_belum2)}")
        
        

    with tab_ppl:
        st.subheader("Monitoring Kinerja PPL")
        st.dataframe(df_ppl2, width='stretch', hide_index=True)
        st.caption(f"PPL: {len(df_ppl2)}")
        
        pilihankec = df_ppl2['kec_petugas'].unique()

        with st.expander("Filter per Kecamatan"):
            kec_terpilih = st.selectbox("Filter Kecamatan", pilihankec, key="pilihan2")
            if kec_terpilih:
                df_ppl3 = df_ppl2[df_ppl2['kec_petugas'] == kec_terpilih]
                df_ppl3['%_capaian'] = round(df_ppl3['pendataan'] / df_ppl3['target'] * 100, 2)
                df_ppl3 = df_ppl3.sort_values(by=['kec_petugas', 'kel_petugas', 'pendataan'])
                
                st.dataframe(df_ppl3, width='stretch', hide_index=True)
                st.caption(f"PPL: {len(df_ppl3)}")
        
        st.divider()

        st.subheader('CAPAIAN PENDATAAN')
        
        df_lk2 = df_lk.drop(columns=['no_telp_y', 'email_y', 'nama_lengkap_y', 'sls2_y', 'nama_kel_y', 'nama_kec_y', 'no_telp_x', 'sls2_x', 'nama_kel_x', 'nama_kec_x', 'kab'])

        df_lk2['realisasi_keluarga'] = df_lk2['k_baru'] + df_lk2['k_ditemukan'] + df_lk2['k_khusus'] + df_lk2['k_meninggal'] + df_lk2['k_menolak'] + df_lk2['k_tidak_ditemukan'] + df_lk2['k_tidak_eligible']

        df_lk2['realisasi_usaha'] = df_lk2['bku_baru'] + df_lk2['bku_ditemukan'] + df_lk2['bku_ganda'] + df_lk2['bku_tdk_ditemukan'] + df_lk2['bku_tutup'] + df_lk2['uk_baru'] + df_lk2['uk_ditemukan'] + df_lk2['uk_ganda'] + df_lk2['uk_tdk_ditemukan'] + df_lk2['uk_tutup']

        df_lk2['total_target'] = df_lk2['target_keluarga'] + df_lk2['target_usaha']

        df_lk2['total_realisasi'] = df_lk2['realisasi_keluarga'] + df_lk2['realisasi_usaha']

        df_lk2['persentase'] = round(df_lk2['total_realisasi'] / df_lk2['total_target'] * 100, 2)

        susunan_lk = ['nama_lengkap_x', 'email_x', 'kec', 'desa', 'sls', 'target_keluarga', 'target_usaha', 'total_target', 'realisasi_keluarga', 'realisasi_usaha', 'total_realisasi', 'persentase']

        df_lk_final = df_lk2[susunan_lk]
        df_lk_final = df_lk_final.rename(columns={'nama_lengkap_x':'nama_lengkap', 'email_x':'email'})

        df_lk_final = df_lk_final.sort_values(by=['kec', 'nama_lengkap', 'desa', 'sls'])

        st.dataframe(df_lk_final, width='stretch', hide_index=True)

        st.divider()

        rekap_lk = df_lk_final.groupby(['kec', 'nama_lengkap'])[['target_keluarga', 'target_usaha', 'total_target', 'realisasi_keluarga', 'realisasi_usaha', 'total_realisasi']].sum().reset_index()
        rekap_lk['persentase'] = round(rekap_lk['total_realisasi'] / rekap_lk['total_target'] * 100, 2)
        st.info("REKAP CAPAIAN PPL")
        st.dataframe(rekap_lk, width='stretch', hide_index=True)

        st.divider()
        st.subheader("CATATAN PETUGAS")
        
        with st.expander("CATATAN PADA PENDATAAN KELUARGA"):
            st.warning("PADA PENDATAAN KELUARGA")
            df_lk2 = df_lk2.rename(columns={'nama_lengkap_x':'nama_lengkap', 'email_x':'email'})
            df_lk2 = df_lk2.sort_values(by=['kec', 'nama_lengkap', 'desa', 'sls'])

            kolom_catatan1 = ['nama_lengkap', 'email', 'kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan', 'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']

            df_catatan1 = df_lk2[kolom_catatan1]
            st.dataframe(df_catatan1, width='stretch', hide_index=True)

        st.divider()
        kolom_catatan2 = ['nama_lengkap', 'email', 'kec', 'desa', 'sls', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup']

        df_catatan2 = df_lk2[kolom_catatan2]
        
        with st.expander("CATATAN PADA PENDATAAN BKU"):
            st.warning("PADA PENDATAAN BKU")
            st.dataframe(df_catatan2, width='stretch', hide_index=True)

        st.divider()
        kolom_catatan3 = ['nama_lengkap', 'email', 'kec', 'desa', 'sls', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']

        df_catatan3 = df_lk2[kolom_catatan3]

        with st.expander("CATATAN PADA PENDATAAN USAHA KELUARGA"):
            st.warning("PADA PENDATAAN USAHA KELUARGA")
            st.dataframe(df_catatan3, width='stretch', hide_index=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)
