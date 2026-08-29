import streamlit as st
import os
import mimetypes

# ---------------- Konfigurasi Halaman ----------------
st.set_page_config(
    page_title="Music & Video Player",
    page_icon="🎵",
    layout="centered"
)

# ---------------- Fungsi Cache untuk Membaca File ----------------
@st.cache_data
def load_media_bytes(file_path):
    with open(file_path, "rb") as f:
        return f.read()

# ---------------- Fungsi Utama ----------------
def main():
    st.title("🎵 MP3/MP4 Player")
    
    folder_name = "lagu"

    if not os.path.exists(folder_name):
        st.error(f"❌ Folder **{folder_name}** tidak ditemukan! Silakan buat folder tersebut.")
        return

    all_files = os.listdir(folder_name)
    allowed_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mkv', '.webm')
    media_files = [f for f in all_files if f.lower().endswith(allowed_extensions)]

    if not media_files:
        st.warning(f"⚠️ Tidak ada file MP3/MP4 di dalam folder **{folder_name}**.")
        return

    media_files.sort()

    st.subheader("Pilih Lagu")
    selected_file = st.selectbox(
        "Daftar Lagu/Video:",
        media_files,
        index=0
    )

    if selected_file:
        file_path = os.path.join(folder_name, selected_file)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📂 **Sedang Diputar:** `{selected_file}`")
        with col2:
            st.metric("Ukuran", f"{file_size_mb:.2f} MB")

        is_video = selected_file.lower().endswith(('.mp4', '.mkv', '.webm'))

        try:
            # Ambil file dalam bentuk bytes
            media_bytes = load_media_bytes(file_path)
            
            # Deteksi MIME type secara otomatis
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if is_video:
                if not mime_type or not mime_type.startswith('video'):
                    mime_type = "video/mp4"
                # Parameter 'key' dihapus di sini
                st.video(media_bytes, format=mime_type)
            else:
                if not mime_type or not mime_type.startswith('audio'):
                    mime_type = "audio/mpeg"
                # Parameter 'key' dihapus di sini
                st.audio(media_bytes, format=mime_type)
                
        except Exception as e:
            st.error(f"Gagal memuat pemutar. Detail: {e}")

if __name__ == "__main__":
    main()
