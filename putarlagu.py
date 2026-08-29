import streamlit as st
import os

# ---------------- Konfigurasi Halaman ----------------
st.set_page_config(
    page_title="Music & Video Player",
    page_icon="🎵",
    layout="centered"
)

# ---------------- Fungsi Utama ----------------
def main():
    st.title("🎵 Local MP3/MP4 Player")
    st.caption("Memutar file langsung dari folder 'lagu'")

    # Nama folder tempat menyimpan lagu
    folder_name = "lagu"

    # Cek apakah folder ada
    if not os.path.exists(folder_name):
        st.error(f"❌ Folder **{folder_name}** tidak ditemukan! Silakan buat folder tersebut.")
        return

    # Ambil semua file dalam folder
    all_files = os.listdir(folder_name)
    
    # Filter hanya file audio dan video
    allowed_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mkv', '.webm')
    media_files = [f for f in all_files if f.lower().endswith(allowed_extensions)]

    # Cek apakah ada file media di dalam folder
    if not media_files:
        st.warning(f"⚠️ Tidak ada file MP3/MP4 di dalam folder **{folder_name}**.")
        return

    # Urutkan file secara alfabet
    media_files.sort()

    # ---------------- UI Pemilihan Lagu ----------------
    st.subheader("Pilih Media")
    selected_file = st.selectbox(
        "Daftar Lagu/Video:",
        media_files,
        index=0
    )

    if selected_file:
        # Buat path lengkap menuju file
        file_path = os.path.join(folder_name, selected_file)
        
        # Hitung ukuran file dalam MB
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Tampilkan info file
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📂 **Sedang Diputar:** `{selected_file}`")
        with col2:
            st.metric("Ukuran", f"{file_size_mb:.2f} MB")

        # ---------------- Logika Pemutar ----------------
        # Cek apakah itu video atau audio
        is_video = selected_file.lower().endswith(('.mp4', '.mkv', '.webm'))

        # Gunakan parameter 'key' yang unik (nama file) agar player 
        # langsung berubah saat user ganti pilihan lagu di selectbox
        if is_video:
            st.video(file_path, format="video/mp4", key=selected_file)
        else:
            st.audio(file_path, format="audio/mpeg", key=selected_file)

if __name__ == "__main__":
    main()
