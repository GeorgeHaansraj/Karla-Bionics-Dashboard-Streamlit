import streamlit as st
import firebase_admin
import ast
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import json
import plotly.express as px
from openai import OpenAI
from fpdf import FPDF
import os

from api import COLLECTION_NAME


# ==========================================
# 1. SETUP & KONEKSI FIRESTORE (CACHED)
# ==========================================
# st.cache_resource memastikan Firebase tidak login berulang-ulang setiap kali tombol ditekan
@st.cache_resource
def init_connection():
    if not firebase_admin._apps:
        # GANTI NAMA FILE JSON INI DENGAN MILIKMU YANG ADA DI FOLDER LOKAL
        cred = credentials.Certificate(
            "karla-bionics-firebase-adminsdk-fbsvc-da0c821b20.json"
        )
        firebase_admin.initialize_app(cred)
    return firestore.client()


db = init_connection()


# Fungsi menarik data dari Firestore ke Pandas DataFrame
@st.cache_data(ttl=600)  # Data di-cache selama 10 menit
def load_data():
    docs = db.collection(COLLECTION_NAME).stream()
    data = [doc.to_dict() for doc in docs]
    return pd.DataFrame(data)


# Memuat data
df = load_data()

# ==========================================
# 2. PENGATURAN HALAMAN (PAGE CONFIG)
# ==========================================
st.set_page_config(
    page_title="Karla Bionics Impact Engine",
    page_icon="🦾",
    layout="wide",  # Agar dasbor melebar memenuhi layar
)

# ==========================================
# 3. SISTEM ROUTING (SIDEBAR)
# ==========================================
# st.sidebar.title("🦾 Karla Bionics")
# st.sidebar.markdown("### Navigasi Sistem")

# Membuat radio button untuk navigasi halaman
# halaman = st.sidebar.radio(
#    "Pilih Tampilan Dasbor:", ["Publik / CSR Showcase", "Internal R&D (Raw Data)"]
# )

# st.sidebar.markdown("---")
# st.sidebar.info(
#    f"Status Koneksi: Terhubung ke Firestore\nTotal Data: {len(df)} Laporan"
# )

st.sidebar.title("🦾 Karla Bionics")
st.sidebar.markdown("---")
st.sidebar.info(
    f"Status Koneksi: Terhubung ke Firestore\nTotal Data: {len(df)} Laporan"
)
# (Bagian st.sidebar.radio sudah dihapus sepenuhnya)

# ==========================================
# 4. LOGIKA TAMPILAN & ROUTING (MENGGUNAKAN TABS)
# ==========================================

tab_publik, tab_internal = st.tabs(
    ["📊 Dashboard CSR (Publik)", "🔐 Raw Data & AI (Internal)"]
)

with tab_publik:
    st.header("Laporan Dampak Sosial")
    st.write(
        "Selamat datang di Dasbor Publik Karla Bionics. Di sini kami menyoroti narasi positif, kemandirian pasien, dan dampak sosial yang terukur (SDG 4)."
    )

    st.markdown("---")

    df_public = df.copy()
    for column in [
        "ID_Pasien",
        "Domisili",
        "Status_Utilitas",
        "Sentimen_Laporan",
        "Kutipan_Asli",
        "Kategori_Tuna_Daksa",
        "Kategori_Aktivitas_ADL",
    ]:
        if column not in df_public:
            df_public[column] = ""
        df_public[column] = df_public[column].fillna("").astype(str).str.strip()
    df_public["Durasi_Pakai_Jam"] = pd.to_numeric(
        df_public.get("Durasi_Pakai_Jam", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    df_public["Usia"] = pd.to_numeric(
        df_public.get("Usia", pd.Series(dtype=float)), errors="coerce"
    )
    df_public["Tanggal_Lapor"] = pd.to_datetime(
        df_public.get("Tanggal_Lapor", pd.Series(dtype="datetime64[ns]")),
        errors="coerce",
    )

    st.subheader("Opsi A - Metrik Utama (KPI)")
    col1, col2, col3 = st.columns(3)
    total_pasien = df_public.loc[df_public["ID_Pasien"].ne(""), "ID_Pasien"].nunique()
    total_jam_produktif = int(df_public["Durasi_Pakai_Jam"].sum())
    utilitas_positif = (
        df_public["Status_Utilitas"].isin(["Sangat Berguna", "Cukup Berguna"]).sum()
    )
    tingkat_kepuasan = (
        (utilitas_positif / len(df_public) * 100) if len(df_public) else 0
    )

    col1.metric(label="Total Penerima Manfaat", value=f"{total_pasien} Jiwa")
    col2.metric(
        label="Total Jam Produktif (Akumulasi)", value=f"{total_jam_produktif} Jam"
    )
    col3.metric(label="Tingkat Kepuasan Pengguna", value=f"{tingkat_kepuasan:.0f}%")

    st.markdown("---")

    st.subheader("Opsi B - Visualisasi Persebaran & Demografi")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Peta Sebaran Wilayah")
        df_domisili = (
            df_public.loc[df_public["Domisili"].ne(""), "Domisili"]
            .value_counts()
            .reset_index()
        )
        df_domisili.columns = ["Provinsi", "Jumlah Pasien"]

        fig_sebaran = px.bar(
            df_domisili,
            x="Provinsi",
            y="Jumlah Pasien",
            color="Provinsi",
            text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_sebaran.update_layout(showlegend=False)
        st.plotly_chart(fig_sebaran, use_container_width=True)

    with chart_col2:
        st.subheader("Distribusi Usia")
        fig_usia = px.histogram(
            df_public.dropna(subset=["Usia"]),
            x="Usia",
            nbins=10,
            labels={"Usia": "Usia (tahun)", "count": "Jumlah Penerima"},
            color_discrete_sequence=["#2a9d8f"],
        )
        fig_usia.update_layout(bargap=0.12)
        st.plotly_chart(fig_usia, use_container_width=True)

    st.subheader("Sebaran Kategori Tuna Daksa")
    df_kategori = (
        df_public.loc[df_public["Kategori_Tuna_Daksa"].ne(""), "Kategori_Tuna_Daksa"]
        .value_counts()
        .reset_index()
    )
    df_kategori.columns = ["Kategori", "Jumlah"]
    fig_kategori = px.pie(
        df_kategori,
        names="Kategori",
        values="Jumlah",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_kategori, use_container_width=True)

    st.markdown("---")

    st.subheader("Opsi C - Metrik Dampak Sosial (SDGs)")
    st.markdown("**Tingkat Kebermanfaatan Alat**")
    st.progress(
        round(tingkat_kepuasan),
        text=f"{tingkat_kepuasan:.0f}% laporan menyatakan alat sangat atau cukup berguna",
    )
    st.caption("Gabungan status Sangat Berguna dan Cukup Berguna")

    aktivitas = []
    for raw_value in df_public["Kategori_Aktivitas_ADL"]:
        try:
            parsed_value = ast.literal_eval(raw_value)
            aktivitas.extend(
                parsed_value if isinstance(parsed_value, list) else [parsed_value]
            )
        except (ValueError, SyntaxError):
            if raw_value:
                aktivitas.append(raw_value)
    df_aktivitas = pd.Series(aktivitas, dtype="string").str.strip()
    df_aktivitas = df_aktivitas[df_aktivitas.ne("Pasif/Hanya Dipakai")]
    df_aktivitas = df_aktivitas.value_counts().head(5).sort_values().reset_index()
    df_aktivitas.columns = ["Aktivitas", "Jumlah"]
    fig_aktivitas = px.bar(
        df_aktivitas,
        x="Jumlah",
        y="Aktivitas",
        orientation="h",
        text_auto=True,
        color_discrete_sequence=["#e76f51"],
    )
    fig_aktivitas.update_layout(showlegend=False)
    st.plotly_chart(fig_aktivitas, use_container_width=True)

    st.markdown("---")

    st.subheader("Opsi D - Jejak Historis / Tren Pertumbuhan")
    df_tren = df_public.dropna(subset=["Tanggal_Lapor"]).copy()
    if not df_tren.empty:
        df_tren["Bulan"] = df_tren["Tanggal_Lapor"].dt.to_period("M").astype(str)
        df_tren = (
            df_tren.groupby("Bulan")["ID_Pasien"]
            .nunique()
            .rename("Penerima Manfaat Unik")
            .reset_index()
        )
        fig_tren = px.line(
            df_tren,
            x="Bulan",
            y="Penerima Manfaat Unik",
            markers=True,
            labels={"Bulan": "Bulan", "Penerima Manfaat Unik": "Penerima Manfaat"},
        )
        st.plotly_chart(fig_tren, use_container_width=True)
    else:
        st.info("Belum ada data tanggal laporan untuk ditampilkan.")

    st.markdown("---")

    st.subheader("Opsi E - Cerita Kebaikan (NLP Sentimen)")
    df_positif = df_public[
        (
            (df_public["Sentimen_Laporan"] == "Positif")
            | (df_public["Status_Utilitas"] == "Sangat Berguna")
        )
        & df_public["Kutipan_Asli"].ne("")
    ].reset_index(drop=True)

    if not df_positif.empty:
        pilihan_testimoni = st.radio(
            "Testimoni kurasi",
            range(len(df_positif)),
            format_func=lambda index: f"Testimoni {index + 1} dari {len(df_positif)}",
            horizontal=True,
            label_visibility="collapsed",
        )
        row = df_positif.iloc[pilihan_testimoni]
        usia = f"{row['Usia']:.0f}" if pd.notna(row["Usia"]) else "-"
        st.success(
            f"*\"{row['Kutipan_Asli']}\"*\n\n"
            f"**P-{row['ID_Pasien']}** | Usia: {usia}, {row['Domisili']} | {row['Kategori_Tuna_Daksa']}"
        )
    else:
        st.info("Belum ada testimoni positif yang dapat ditampilkan.")

    teks_positif = " ".join(
        df_public.loc[
            (df_public["Sentimen_Laporan"] == "Positif")
            & df_public["Kutipan_Asli"].ne(""),
            "Kutipan_Asli",
        ]
    )
    if teks_positif:
        try:
            import matplotlib.pyplot as plt
            from wordcloud import WordCloud

            wordcloud = WordCloud(
                width=1200, height=500, background_color="white", colormap="viridis"
            ).generate(teks_positif)
            fig_wordcloud, ax = plt.subplots(figsize=(12, 5))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig_wordcloud)
            plt.close(fig_wordcloud)
        except ImportError:
            st.caption("Word cloud tersedia setelah library wordcloud terpasang.")

    st.markdown("---")

    # 4. GENERATIVE STORYTELLING & EXPORT PDF
    st.subheader("🤖 Generative AI: Laporan Eksekutif Otomatis")
    st.write(
        "Sistem AI akan menganalisis metrik saat ini dan merangkai narasi laporan CSR bulanan secara otomatis."
    )

    # Input API Key secara aman di antarmuka
    # api_key_input = st.text_input(
    #    "Masukkan OpenAI API Key (sk-...) untuk men-generate laporan:", type="password"
    # )

    if st.button("✨ Generate Narasi CSR & Siapkan PDF"):
        with st.spinner("AI sedang menganalisis data dan merangkai narasi..."):
            try:
                rahasia_api_key = os.getenv("GROQ_API_KEY")

                if not rahasia_api_key:
                    st.error(
                        "⚠️ Sistem gagal menemukan API Key di dalam environment (.env). Hubungi tim teknis."
                    )
                    st.stop()

                # 1. ARAHKAN KE SERVER GROQ
                client = OpenAI(
                    base_url="https://api.groq.com/openai/v1", api_key=rahasia_api_key
                )

                # Prompting dinamis dengan metrik real-time
                prompt_laporan = f"""
                    Tuliskan 2 paragraf narasi eksekutif yang profesional dan inspiratif untuk laporan donatur CSR Karla Bionics.
                    Gunakan data live berikut:
                    - Total Penerima Manfaat: {total_pasien} jiwa
                    - Total Jam Produktif (Akumulasi): {total_jam_produktif} jam
                    - Jumlah Pengguna Aktif & Terbantu: {utilitas_positif} pasien
                    
                    Instruksi Khusus:
                    - Fokus pada pencapaian Tujuan Pembangunan Berkelanjutan (SDG 4 & 10).
                    - Jelaskan bagaimana angka-angka ini mencerminkan peningkatan kemandirian penyandang disabilitas (tuna daksa).
                    - Gunakan bahasa Indonesia yang formal, elegan, dan apresiatif. Tanpa awalan sapaan surat.
                    """

                # Pemanggilan LLM (gpt-oss-120b) untuk menghasilkan narasi
                chat_completion = client.chat.completions.create(
                    model="openai/gpt-oss-120b",  # Harus persis dengan teks di menu dropdown
                    messages=[
                        {
                            "role": "system",
                            "content": "Anda adalah spesialis komunikasi CSR dan analis dampak sosial.",
                        },
                        {"role": "user", "content": prompt_laporan},
                    ],
                    temperature=0.7,
                )

                narasi_ai = chat_completion.choices[0].message.content

                st.success("✅ Narasi berhasil dibuat!")
                st.info(narasi_ai)

                # Logika Pembuatan File PDF menggunakan FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(
                    0,
                    10,
                    "Laporan Eksekutif Dampak CSR - Karla Bionics",
                    ln=True,
                    align="C",
                )
                pdf.ln(10)

                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "Ringkasan Metrik Utama:", ln=True)
                pdf.set_font("Arial", "", 12)
                pdf.cell(
                    0, 8, f"- Total Penerima Manfaat: {total_pasien} Jiwa", ln=True
                )
                pdf.cell(
                    0,
                    8,
                    f"- Total Jam Produktif: {total_jam_produktif} Jam",
                    ln=True,
                )
                pdf.cell(
                    0,
                    8,
                    f"- Pengguna Aktif & Terbantu: {utilitas_positif} Pasien",
                    ln=True,
                )
                pdf.ln(10)

                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "Narasi Dampak Berkelanjutan:", ln=True)
                pdf.set_font("Arial", "", 12)

                # FPDF memerlukan encoding khusus (latin-1) agar tidak error saat membaca teks AI
                narasi_bersih = narasi_ai.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 7, txt=narasi_bersih)

                # Output PDF ke dalam format byte string agar bisa diunduh oleh Streamlit
                pdf_output = pdf.output(dest="S").encode("latin-1")

                # Tombol Unduh
                st.download_button(
                    label="📄 Unduh Laporan PDF Eksekutif",
                    data=pdf_output,
                    file_name="Laporan_Eksekutif_Karla_Bionics.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"Terjadi kesalahan pada sistem AI: {str(e)}")

with tab_internal:
    # Pindahkan SEMUA baris kode dasbor internalmu ke sini
    # (Tabel pandas raw data, tombol Generate Narasi AI)
    st.header("Manajemen Data Mentah")

    st.title("🔧 Intelijen Pemeliharaan & Audit Hardware")
    st.write(
        "Peringatan: Tampilan ini tidak disensor. Berisi raw data operasional, Red Flag Matrix, dan log keluhan spesifik dari setiap ID Pasien."
    )

    st.markdown("---")

    # 1. RED FLAG MATRIX (Prioritas Servis)
    st.subheader("🚨 Red Flag Matrix (Tindakan Mendesak)")
    st.info(
        "Tabel ini secara otomatis memfilter pasien dengan Tingkat Urgensi Pemeliharaan 'Tinggi'. Teknisi harap segera menindaklanjuti."
    )

    # Memfilter data dengan urgensi tinggi
    df_red_flag = df[df["Tingkat_Urgensi_Pemeliharaan"] == "Tinggi"].copy()

    # Menampilkan tabel khusus untuk teknisi (hanya kolom yang relevan)
    if not df_red_flag.empty:
        kolom_teknisi = [
            "ID_Pasien",
            "Tanggal_Lapor",
            "Keluhan_Hardware",
            "Domisili",
            "Status_Utilitas",
        ]
        st.dataframe(df_red_flag[kolom_teknisi], use_container_width=True)
    else:
        st.success("Tidak ada pasien dengan tingkat urgensi tinggi saat ini.")

    st.markdown("---")

    # 2. ANALISIS KELUHAN HARDWARE (Grafik Batang)
    st.subheader("📊 Distribusi Kendala Fisik Alat")

    try:
        # Karena Keluhan_Hardware berbentuk list/array di Firestore, kita pisahkan (explode) agar bisa dihitung
        # Pastikan data di-convert ke tipe string terlebih dahulu agar aman
        df_keluhan = df.copy()
        df_keluhan["Keluhan_Hardware"] = df_keluhan["Keluhan_Hardware"].astype(str)

        # Membersihkan karakter kurung siku dari format string array
        df_keluhan["Keluhan_Hardware"] = df_keluhan["Keluhan_Hardware"].str.replace(
            r"\[|\]|'", "", regex=True
        )

        # Memisahkan string berdasarkan koma jika ada lebih dari 1 keluhan
        df_keluhan["Keluhan_Hardware"] = df_keluhan["Keluhan_Hardware"].str.split(", ")

        # Melakukan explode (meratakan list menjadi baris)
        df_exploded = df_keluhan.explode("Keluhan_Hardware")

        # Menghitung frekuensi setiap keluhan
        df_count = df_exploded["Keluhan_Hardware"].value_counts().reset_index()
        df_count.columns = ["Jenis Kerusakan", "Jumlah Kasus"]

        # Memisahkan keluhan "Tidak Ada Keluhan" agar fokus pada kerusakan saja
        df_kerusakan = df_count[df_count["Jenis Kerusakan"] != "Tidak Ada Keluhan"]

        fig_keluhan = px.bar(
            df_kerusakan,
            x="Jenis Kerusakan",
            y="Jumlah Kasus",
            color="Jenis Kerusakan",
            text_auto=True,
            color_discrete_sequence=px.colors.sequential.Reds_r,
        )
        fig_keluhan.update_layout(showlegend=False)
        st.plotly_chart(fig_keluhan, use_container_width=True)
    except Exception as e:
        st.warning(
            f"Sistem sedang memproses format data keluhan hardware... (Error log: {e})"
        )

    st.markdown("---")

    # 3. AUDIT DATA MENTAH (FULL DATAMART)
    st.subheader("🗄️ Audit Data Mentah (Datamart Penuh)")
    st.write(
        "Fasilitas pencarian dan pencocokan data asli untuk keperluan investigasi lanjutan."
    )
    st.dataframe(df, use_container_width=True)
