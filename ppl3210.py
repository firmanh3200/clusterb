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
    page_title="Dashboard",
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
    {"kode": 3210, "tipe": "-", "nama": "KAB. MAJALENGKA"},
    ]

data_petugas = pd.read_csv('db_petugas3210.csv')

df_petugas = pd.DataFrame(data_petugas)

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
    ## SLS
    url_sls = f"https://simpul-jabar.32net.id/api/usaha-data-rekap?kdkab={v1}%20{v2}%20{v3}&kdkec=&kdkel=&level=sls"

    response_sls = requests.get(url_sls)
    response_sls.raise_for_status()  # raise error jika gagal

    json_data_sls = response_sls.json()

    # Ambil key "data" yang berisi list of dict
    df_sls = pd.DataFrame(json_data_sls["data"])

    df_sls["sls"]  = df_sls["wilayah"]
    df_sls["desa"] = df_sls["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[0]
    df_sls["kec"]  = df_sls["parent_wilayah"].str.extract(r"^(.+?)\s*\|\s*(.+)$")[1]
    df_sls["kab"]  = f"{v1}"

    df_sls_ppl = pd.merge(
        df_sls, 
        df_petugas[['kec', 'desa', 'sls', 'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl']], 
        on=['kec', 'desa', 'sls'], 
        how='left'
    )

    df_sls_ppl = df_sls_ppl.rename(columns={'email_pml_y':'email_pml'})

    df_sls_ppl = df_sls_ppl.sort_values(by=['kec', 'desa', 'sls'])

    kolomsls_bku = ['kec', 'desa', 'sls', 'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup']

    kolomsls_uk = ['kec', 'desa', 'sls', 'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']

    kolomsls_progres = ['kec', 'desa', 'sls',  'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl', 'draft_pendataan', 'progres_pendataan', 'target_awal_total', 'target_st', 'target_usaha']

    #st.dataframe(df_sls_ppl)
    usaha_ppl = df_sls_ppl.groupby(by=['kec', 'desa', 'sls',  'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl'])[['target_usaha', 'progres_pendataan', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()

    sls_didata = usaha_ppl[usaha_ppl['progres_pendataan'] != 0].copy()
    sls_belum = usaha_ppl[usaha_ppl['progres_pendataan'] == 0].copy()
         
    usaha_ppl['bku_baru'] = usaha_ppl['bku_baru'].astype('Int64')
    usaha_ppl['bku_ganda'] = usaha_ppl['bku_ganda'].astype('Int64')
    usaha_ppl['bku_tutup'] = usaha_ppl['bku_tutup'].astype('Int64')
    usaha_ppl['bku_tdk_ditemukan'] = usaha_ppl['bku_tdk_ditemukan'].astype('Int64')
    usaha_ppl['bku_ditemukan'] = usaha_ppl['bku_ditemukan'].astype('Int64')


    #TERTINGGI
    maks_bku_baru = usaha_ppl.loc[usaha_ppl['bku_baru'].idxmax(), ['bku_baru', 'nama_ppl', 'kec']]
    maks_bku_ganda = usaha_ppl.loc[usaha_ppl['bku_ganda'].idxmax(), ['bku_ganda', 'nama_ppl', 'kec']]
    maks_bku_tutup = usaha_ppl.loc[usaha_ppl['bku_tutup'].idxmax(), ['bku_tutup', 'nama_ppl', 'kec']]
    maks_bku_tdketemu = usaha_ppl.loc[usaha_ppl['bku_tdk_ditemukan'].idxmax(), ['bku_tdk_ditemukan', 'nama_ppl', 'kec']]
    maks_bku_ketemu = usaha_ppl.loc[usaha_ppl['bku_ditemukan'].idxmax(), ['bku_ditemukan', 'nama_ppl', 'kec']]


    #TERENDAH
    min_bku_baru = usaha_ppl.loc[usaha_ppl['bku_baru'].idxmin(), ['bku_baru', 'nama_ppl', 'kec']]
    min_bku_ganda = usaha_ppl.loc[usaha_ppl['bku_ganda'].idxmin(), ['bku_ganda', 'nama_ppl', 'kec']]
    min_bku_tutup = usaha_ppl.loc[usaha_ppl['bku_tutup'].idxmin(), ['bku_tutup', 'nama_ppl', 'kec']]
    min_bku_tdketemu = usaha_ppl.loc[usaha_ppl['bku_tdk_ditemukan'].idxmin(), ['bku_tdk_ditemukan', 'nama_ppl', 'kec']]
    min_bku_ketemu = usaha_ppl.loc[usaha_ppl['bku_ditemukan'].idxmin(), ['bku_ditemukan', 'nama_ppl', 'kec']]

    

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
    df_qk["nmkab"]  = f"{v1}"

    df_qk = pd.merge(
            df_qk, 
            df_petugas[['kab', 'kec', 'desa', 'sls', 'nama_pml', 'email_pml', 'nama_ppl', 'email_ppl']], 
            on=['kec', 'desa', 'sls'], 
            how='left'
        )

    df_art = df_qk[['kab', 'kec', 'desa', 'sls', 'art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']]
    df_art = df_art.sort_values(by=['kec', 'desa', 'sls'])
    
    rekap_art_kab = df_art.groupby(by='kab')[['art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama']].sum().reset_index()

    df_kk = df_qk[['kab', 'kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
        'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']]
    df_kk = df_kk.sort_values(by=['kec', 'desa', 'sls'])
    
    rekap_kk_kab = df_kk.groupby(by='kab')[['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan',
        'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']].sum().reset_index()


    df_lk = df_sls_ppl.merge(
        df_kk,
        how='left', 
        left_on=['kec', 'desa', 'sls'], # Nama kolom di df_bku
        right_on=['kec', 'desa', 'sls'] # Nama kolom di df_sls2
    )
    
    df_lk['realisasi_keluarga'] = df_lk['k_baru'] + df_lk['k_ditemukan'] + df_lk['k_khusus'] + df_lk['k_meninggal'] + df_lk['k_menolak'] + df_lk['k_tidak_ditemukan'] + df_lk['k_tidak_eligible']

    df_lk['realisasi_usaha'] = df_lk['bku_baru'] + df_lk['bku_ditemukan'] + df_lk['bku_ganda'] + df_lk['bku_tdk_ditemukan'] + df_lk['bku_tutup'] + df_lk['uk_baru'] + df_lk['uk_ditemukan'] + df_lk['uk_ganda'] + df_lk['uk_tdk_ditemukan'] + df_lk['uk_tutup']

    df_lk['total_target'] = df_lk['target_keluarga'] + df_lk['target_usaha']

    df_lk['total_realisasi'] = df_lk['realisasi_keluarga'] + df_lk['realisasi_usaha']

    df_lk['persentase'] = round(df_lk['total_realisasi'] / df_lk['total_target'] * 100, 2)

    susunan_lk = ['nama_pml', 'email_pml', 'nama_ppl', 'email', 'kec', 'desa', 'sls', 'target_keluarga', 'target_usaha', 'total_target', 'realisasi_keluarga', 'realisasi_usaha', 'total_realisasi', 'persentase']

    df_lk_final = df_lk[susunan_lk]
    
    df_lk_final = df_lk_final.sort_values(by=['kec', 'nama_ppl', 'desa', 'sls'])


    with st.container(border=True):
        with st.container(border=True):
            st.header(f"Progress SE2026 {v1} {v2} {v3}")
            kol1, kol2 = st.columns(2)
            with kol1:
                st.success(f"Hari ke: {hari_ke}")
            with kol2:
                st.warning(f"Sisa Waktu: {menuju} Hari")
            st.caption("Sumber: simpul-jabar.32net.id")

    with st.expander("DAFTAR PETUGAS"):
        st.subheader("DAFTAR PETUGAS")
        st.dataframe(data_petugas, hide_index=True)

    tab_usaha, tab_qc, tab_sls, tab_lk = st.tabs(['PENDATAAN USAHA', 'PENDATAAN KELUARGA', 'PROGRESS SLS', 'LEMBAR KERJA'])

    ## PENDATAAN USAHA
    with tab_usaha:
        st.subheader("Progress Pendataan Usaha")
        df_bku_kab = df_sls_ppl.groupby(by=['kab'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
        
        grafik_bku_kab = px.bar(df_bku_kab, x='kab', y=['bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Capaian Pendataan BKU", labels={'value':'Jumlah', 'variable':'Status'})
        grafik_bku_kab.update_yaxes(
            range=[0, df_bku_kab['target_usaha'].max()],
            tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
        )
        
        grafik_uk_kab = px.bar(df_bku_kab, x='kab', y=['uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_baru'], barmode='group', title="Capaian Pendataan Usaha Keluarga", labels={'value':'Jumlah', 'variable':'Status'})
        grafik_uk_kab.update_yaxes(
            range=[0, df_bku_kab['target_usaha'].max()],
            tickformat=",.0f" # Menambahkan koma sebagai pemisah ribuan
        )

        grafik_target_usaha = px.bar(df_bku_kab, x='kab', y='target_usaha', title="Target Usaha")
        grafik_target_usaha.update_yaxes(
            range=[0, df_bku_kab['target_usaha'].max()],
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
            df_bku_kec = df_sls_ppl.groupby(by=['kec'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
            st.dataframe(df_bku_kec, width='stretch', hide_index=True)
            
            grafik_bku_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'bku_ditemukan', 'bku_tdk_ditemukan', 'bku_ganda', 'bku_tutup', 'bku_baru'], barmode='group', title="Rekap Pendataan BKU per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})

            grafik_uk_kec = px.bar(df_bku_kec, x='kec', y=['target_usaha', 'uk_ditemukan', 'uk_tdk_ditemukan', 'uk_ganda', 'uk_tutup', 'uk_tutup', 'uk_baru'], barmode='group', title="Rekap Pendataan Usaha Keluarga per Kecamatan", labels={'value':'Jumlah', 'variable':'Status'})
            
            with st.container(border=True):
                st.plotly_chart(grafik_bku_kec, width="stretch")

            with st.container(border=True):
                st.plotly_chart(grafik_uk_kec, width="stretch")
        
        with st.expander("REKAP DESA"):
            df_bku_desa = df_sls_ppl.groupby(by=['kec', 'desa'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index()
            st.dataframe(df_bku_desa, width='stretch', hide_index=True)
        
        with st.expander("PER SLS"):
            df_usaha_sls = df_sls_ppl.groupby(by=['kec', 'desa', 'sls'])[['target_usaha', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']].sum().reset_index() 
            st.dataframe(df_usaha_sls, width='stretch', hide_index=True)
        
        with st.expander("REKAP PPL"):
            st.dataframe(usaha_ppl, width='stretch', hide_index=True)
            kol4aa, kol4bb = st.columns(2)
            with kol4aa:
                with st.container(border=True):
                    st.subheader("BKU Tertinggi")
                    st.success(f"Baru: {' | '.join(maks_bku_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(maks_bku_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(maks_bku_tutup.astype(str).values)}")
                    st.caption(f"Tidak Ditemukan: {' | '.join(maks_bku_tdketemu.astype(str).values)}")
                    st.caption(f"Ditemukan: {' | '.join(maks_bku_ketemu.astype(str).values)}")
        
            with kol4bb:
                with st.container(border=True):
                    st.subheader("BKU Terendah")
                    st.success(f"Baru: {' | '.join(min_bku_baru.astype(str).values)}")
                    st.info(f"Ganda: {' | '.join(min_bku_ganda.astype(str).values)}")
                    st.warning(f"Tutup: {' | '.join(min_bku_tutup.astype(str).values)}")
                    st.caption(f"Tidak Ditemukan: {' | '.join(min_bku_tdketemu.astype(str).values)}")
                    st.caption(f"Ditemukan: {' | '.join(min_bku_ketemu.astype(str).values)}")

            st.divider()
            pilihankec3 = usaha_ppl['kec'].unique()
            kec_terpilih3 = st.selectbox("Filter Kecamatan", pilihankec3, key="pilihan4")
            if kec_terpilih3:
                usaha_ppl2 = usaha_ppl[usaha_ppl['kec'] == kec_terpilih3]

                usaha_ppl2_bku = usaha_ppl2[['kec', 'nama_ppl', 'email_ppl', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup']]

                usaha_ppl2_uk = usaha_ppl2[['kec', 'nama_ppl', 'email_ppl', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']]
                
                st.dataframe(usaha_ppl2, width='stretch', hide_index=True)
                st.divider()
                st.warning("B K U")
                st.dataframe(usaha_ppl2_bku, width='stretch', hide_index=True)
                st.divider()
                st.warning("USAHA KELUARGA")
                st.dataframe(usaha_ppl2_uk, width='stretch', hide_index=True)
                
    

    ## PROGRESS SLS
    with tab_sls:
        with st.container(border=True):
            st.subheader("CAPAIAN PENDATAAN SLS")
            st.dataframe(sls_didata, width='stretch', hide_index=True)
            st.divider()
            with st.expander("SLS Belum Didata"):
                st.subheader("SLS Belum Didata")
                st.dataframe(sls_belum, width='stretch', hide_index=True)
                st.caption(f"Jumlah SLS: {len(sls_belum)}")
                st.divider()
                pilihankec2 = sls_belum['kec'].unique()
                kec_terpilih2 = st.selectbox("Pilih Kecamatan", pilihankec2, key="pilihan3")

                if kec_terpilih2:
                    sls_belum2 = sls_belum[sls_belum['kec'] == kec_terpilih2]
                    st.dataframe(sls_belum2, width='stretch', hide_index=True)
                    st.caption(f"Jumlah SLS: {len(sls_belum2)}")
            
    ## PENDATAAN KELUARGA
    with tab_qc:
        st.subheader("Pendataan Keluarga")
        
        with st.expander("HASIL PENDATAAN KELUARGA"):
            grafik_kk = px.bar(rekap_kk_kab, x='kab', y=['target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan', 'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible'], barmode='group')
            with st.container(border=True):
                st.plotly_chart(grafik_kk, width='stretch') 
            st.dataframe(df_kk, width='stretch', hide_index=True)
            st.divider()
            #st.dataframe(df_kk2, width='stretch', hide_index=True)
            
    
        with st.expander("HASIL PENDATAAN ANGGOTA KELUARGA"):
            grafik_art = px.bar(rekap_art_kab, x='kab', y=['art_baru', 'art_khusus', 'art_meninggal', 'art_pindah_dn', 'art_pindah_ln', 'art_prelist', 'art_tidak_ditemukan', 'art_tinggal_bersama'], barmode='group')
            with st.container(border=True):
                st.plotly_chart(grafik_art, width='stretch')
            st.dataframe(df_art, width='stretch', hide_index=True)
            st.divider()

    ## LEMBAR KERJA    
    with tab_lk:
        st.subheader('LEMBAR KERJA')
        
        st.dataframe(df_lk_final, width='stretch', hide_index=True)

        st.divider()

        rekap_lk = df_lk_final.groupby(['kec', 'nama_ppl'])[['target_keluarga', 'target_usaha', 'total_target', 'realisasi_keluarga', 'realisasi_usaha', 'total_realisasi']].sum().reset_index()
        rekap_lk['persentase'] = round(rekap_lk['total_realisasi'] / rekap_lk['total_target'] * 100, 2)

        with st.expander("REKAP CAPAIAN PPL"):
            st.info("REKAP CAPAIAN PPL")
            st.dataframe(rekap_lk, width='stretch', hide_index=True)
            st.caption(f"{len(rekap_lk)} PPL")

            termin1, termin2, termin3 = st.tabs(['TERMIN 1', ' TERMIN 2', 'TERMIN 3'])

            with termin1:
                df_termin1 = rekap_lk[rekap_lk['persentase'] > 40]
                st.success("DAFTAR PETUGAS DENGAN CAPAIAN > 40 PERSEN")
                st.dataframe(df_termin1, hide_index=True, width='stretch')
                st.caption(f"{len(df_termin1)} PPL")

            with termin2:
                df_termin2 = rekap_lk[rekap_lk['persentase'] > 80]
                st.success("DAFTAR PETUGAS DENGAN CAPAIAN > 80 PERSEN")
                st.dataframe(df_termin2, hide_index=True, width='stretch')
                st.caption(f"{len(df_termin2)} PPL")

            with termin3:
                df_termin3 = rekap_lk[rekap_lk['persentase'] > 100]
                st.success("DAFTAR PETUGAS DENGAN CAPAIAN > 100 PERSEN")
                st.dataframe(df_termin3, hide_index=True, width='stretch')
                st.caption(f"{len(df_termin3)} PPL")

        st.divider()
        st.subheader("CATATAN PETUGAS")

        with st.expander("PADA PENDATAAN KELUARGA"):
            st.warning("PADA PENDATAAN KELUARGA")
            df_lk = df_lk.rename(columns={'nama_ppl_x':'nama_ppl', 'email_x':'email'})
            df_lk = df_lk.sort_values(by=['kec', 'nama_ppl', 'desa', 'sls'])

            kolom_catatan1 = ['nama_ppl', 'email', 'kec', 'desa', 'sls', 'target_keluarga', 'k_baru', 'k_bersedia', 'k_ditemukan', 'k_khusus', 'k_meninggal', 'k_menolak', 'k_tidak_ditemui', 'k_tidak_ditemukan', 'k_tidak_eligible']

            df_catatan1 = df_lk[kolom_catatan1]
            st.dataframe(df_catatan1, width='stretch', hide_index=True)

        kolom_catatan2 = ['nama_ppl', 'email', 'kec', 'desa', 'sls', 'bku_baru', 'bku_baru_non', 'bku_baru_pertanian', 'bku_ditemukan', 'bku_ganda', 'bku_tdk_ditemukan', 'bku_temu_non', 'bku_temu_pertanian', 'bku_tutup']

        df_catatan2 = df_lk[kolom_catatan2]

        with st.expander("PADA PENDATAAN BKU"):
            st.warning("PADA PENDATAAN BKU")
            st.dataframe(df_catatan2, width='stretch', hide_index=True)

        kolom_catatan3 = ['nama_ppl', 'email', 'kec', 'desa', 'sls', 'uk_baru', 'uk_baru_non', 'uk_baru_pertanian', 'uk_ditemukan', 'uk_ganda', 'uk_tdk_ditemukan', 'uk_temu_non', 'uk_temu_pertanian', 'uk_tutup']

        df_catatan3 = df_lk[kolom_catatan3]
        with st.expander("PADA PENDATAAN USAHA KELUARGA"):
            st.warning("PADA PENDATAAN USAHA KELUARGA")
            st.dataframe(df_catatan3, width='stretch', hide_index=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown(f"""<div style="text-align:center; padding:1rem 0;"><p style="font-size:0.78rem; color:#94a3b8; margin:0;">🏗️ | Sumber: simpul-jabar.32net.id</p><p style="font-size:0.7rem; color:#cbd5e1; margin:0.25rem 0 0 0;">Data di-cache selama 5 menit. Klik <b>Rerun</b> di menu untuk memperbarui.</p></div>""", unsafe_allow_html=True)
