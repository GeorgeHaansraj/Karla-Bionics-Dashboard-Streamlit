import streamlit as st
import firebase_admin
import ast
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
import json
import html
import plotly.express as px
import plotly.graph_objects as go
from openai import OpenAI
from fpdf import FPDF
import os

from api import COLLECTION_NAME


def render_soft_metric_cards(metrics):
    palette = ["#f1f5f9"]
    cards = []
    for index, (label, value, help_text) in enumerate(metrics):
        cards.append(f"""
            <div title="{html.escape(help_text)}"
                 style="background:{palette[index % len(palette)]};
                        border:1px solid #d9e2e8; border-radius:12px;
                        padding:1rem 1.1rem; min-height:92px;
                        box-shadow:0 1px 3px rgba(15, 23, 42, 0.06);">
                <div style="color:#52606d; font-size:0.82rem; font-weight:600;
                            line-height:1.3;">{html.escape(label)}</div>
                <div style="color:#1f2937; font-size:1.45rem; font-weight:700;
                            margin-top:0.45rem;">{html.escape(str(value))}</div>
            </div>
            """)
    st.html(f"""
        <div style="display:grid; grid-template-columns:repeat({len(metrics)}, minmax(0, 1fr));
                    gap:0.8rem; margin:0.4rem 0 0.8rem;">
            {"".join(cards)}
        </div>
        """)


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

st.sidebar.title("Karla Bionics Streamlit Dashboard")
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

    total_pasien = df_public.loc[df_public["ID_Pasien"].ne(""), "ID_Pasien"].nunique()
    total_jam_produktif = int(df_public["Durasi_Pakai_Jam"].sum())
    utilitas_positif = (
        df_public["Status_Utilitas"].isin(["Sangat Berguna", "Cukup Berguna"]).sum()
    )
    tingkat_kepuasan = (
        (utilitas_positif / len(df_public) * 100) if len(df_public) else 0
    )

    total_wilayah = df_public.loc[df_public["Domisili"].ne(""), "Domisili"].nunique()
    kategori_aktivitas = set()
    for raw_value in df_public["Kategori_Aktivitas_ADL"]:
        try:
            parsed_value = ast.literal_eval(raw_value)
            values = parsed_value if isinstance(parsed_value, list) else [parsed_value]
        except (ValueError, SyntaxError):
            values = [raw_value] if raw_value else []
        kategori_aktivitas.update(
            str(value).strip() for value in values if str(value).strip()
        )

    tahun_laporan = df_public["Tanggal_Lapor"].dropna().dt.year
    periode_laporan = (
        str(int(tahun_laporan.mode().iloc[0])) if not tahun_laporan.empty else "-"
    )

    with st.container(border=True):
        st.subheader("Ringkasan dampak Karla Bionics")
        render_soft_metric_cards(
            [
                (
                    "Penerima Manfaat",
                    f"{total_pasien} Jiwa",
                    "Jumlah seluruh penerima manfaat.",
                ),
                (
                    "Wilayah Jangkauan",
                    f"{total_wilayah} Wilayah",
                    "Sebaran daerah penerima manfaat.",
                ),
                (
                    "Kategori Aktivitas",
                    f"{len(kategori_aktivitas)} Kategori",
                    "Aktivitas yang dapat dilakukan para penerima manfaat karena penggunaan lengan prostetik Karla Bionics.",
                ),
                (
                    "Periode Laporan",
                    periode_laporan,
                    "Tahun data laporan dikumpulkan.",
                ),
            ]
        )

    st.markdown("---")

    st.subheader("Sebaran penerima manfaat")
    st.subheader("Peta Sebaran Wilayah")
    koordinat_provinsi = {
        "Aceh": (4.6951, 96.7494),
        "Sumatera Utara": (2.1154, 99.5451),
        "Sumatera Barat": (-0.7399, 100.8000),
        "Riau": (0.2933, 101.7068),
        "Jambi": (-1.4852, 102.4381),
        "Sumatera Selatan": (-3.3194, 104.9146),
        "Bengkulu": (-3.7928, 102.2608),
        "Lampung": (-4.5586, 105.4068),
        "Kepulauan Bangka Belitung": (-2.7411, 106.4406),
        "Kepulauan Riau": (3.9457, 108.1429),
        "DKI Jakarta": (-6.2088, 106.8456),
        "Jawa Barat": (-6.9175, 107.6191),
        "Jawa Tengah": (-7.1509, 110.1403),
        "DI Yogyakarta": (-7.7956, 110.3695),
        "Jawa Timur": (-7.5361, 112.2384),
        "Banten": (-6.4058, 106.0640),
        "Bali": (-8.4095, 115.1889),
        "Nusa Tenggara Barat": (-8.6529, 117.3616),
        "Nusa Tenggara Timur": (-8.6574, 121.0794),
        "Kalimantan Barat": (-0.2788, 111.4753),
        "Kalimantan Tengah": (-1.6815, 113.3824),
        "Kalimantan Selatan": (-3.0926, 115.2838),
        "Kalimantan Timur": (0.5387, 116.4194),
        "Kalimantan Utara": (3.0731, 116.0414),
        "Sulawesi Utara": (0.6247, 123.9750),
        "Sulawesi Tengah": (-1.4300, 121.4456),
        "Sulawesi Selatan": (-3.6688, 119.9741),
        "Sulawesi Tenggara": (-4.1449, 122.1746),
        "Gorontalo": (0.6999, 122.4467),
        "Sulawesi Barat": (-2.8441, 119.2321),
        "Maluku": (-3.2385, 130.1453),
        "Maluku Utara": (1.5709, 127.8088),
        "Papua Barat": (-1.3361, 133.1747),
        "Papua Barat Daya": (-1.3842, 130.5167),
        "Papua": (-4.2699, 138.0804),
        "Papua Selatan": (-7.7735, 139.0193),
        "Papua Tengah": (-3.5931, 136.5275),
        "Papua Pegunungan": (-4.0833, 138.9500),
    }
    jumlah_per_wilayah = (
        df_public.loc[df_public["Domisili"].ne(""), "Domisili"].value_counts().to_dict()
    )

    provinsi_terjangkau = [
        provinsi for provinsi in koordinat_provinsi if provinsi in jumlah_per_wilayah
    ]
    jumlah_tertinggi = max(
        (jumlah_per_wilayah[provinsi] for provinsi in provinsi_terjangkau),
        default=0,
    )
    provinsi_tertinggi = {
        provinsi
        for provinsi in provinsi_terjangkau
        if jumlah_per_wilayah[provinsi] == jumlah_tertinggi
    }
    provinsi_biasa = [
        provinsi
        for provinsi in provinsi_terjangkau
        if provinsi not in provinsi_tertinggi
    ]
    provinsi_belum_terjangkau = [
        provinsi
        for provinsi in koordinat_provinsi
        if provinsi not in jumlah_per_wilayah
    ]

    def buat_trace_peta(provinsi, warna, ukuran, teks, teks_font):
        return go.Scattergeo(
            lat=[koordinat_provinsi[nama][0] for nama in provinsi],
            lon=[koordinat_provinsi[nama][1] for nama in provinsi],
            text=teks,
            textposition="top center",
            textfont=teks_font,
            mode="markers+text",
            marker=dict(
                size=ukuran,
                color=warna,
                line=dict(color="white", width=1),
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=[
                f"{nama}: {jumlah_per_wilayah.get(nama, 0)} penerima manfaat"
                for nama in provinsi
            ],
            showlegend=False,
        )

    fig_sebaran = go.Figure()
    if provinsi_belum_terjangkau:
        fig_sebaran.add_trace(
            buat_trace_peta(
                provinsi_belum_terjangkau,
                "#cbd5e1",
                9,
                [""] * len(provinsi_belum_terjangkau),
                dict(size=10, color="#64748b"),
            )
        )
    if provinsi_biasa:
        fig_sebaran.add_trace(
            buat_trace_peta(
                provinsi_biasa,
                px.colors.qualitative.Pastel,
                12,
                [str(jumlah_per_wilayah[nama]) for nama in provinsi_biasa],
                dict(size=11, color="#334155"),
            )
        )
    if provinsi_tertinggi:
        fig_sebaran.add_trace(
            buat_trace_peta(
                sorted(provinsi_tertinggi),
                "#ef4444",
                18,
                [str(jumlah_tertinggi)] * len(provinsi_tertinggi),
                dict(size=16, color="#991b1b", family="Arial Black"),
            )
        )
    fig_sebaran.update_geos(
        scope="asia",
        projection_type="natural earth",
        center=dict(lat=-2, lon=118),
        lataxis_range=[-11, 6],
        lonaxis_range=[94, 142],
        showland=True,
        landcolor="#f1f5f9",
        showcountries=True,
        countrycolor="#94a3b8",
        showcoastlines=True,
        coastlinecolor="#94a3b8",
    )
    fig_sebaran.update_layout(height=440, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_sebaran, use_container_width=True)

    trend_col, historical_col = st.columns(2)
    with trend_col:
        st.subheader("Perkembangan Jangkauan Wilayah")
        df_jangkauan = df_public.loc[
            df_public["Domisili"].ne("") & df_public["Tanggal_Lapor"].notna(),
            ["Domisili", "Tanggal_Lapor"],
        ].copy()
        tahun_periode = int(periode_laporan) if periode_laporan != "-" else None
        if tahun_periode is not None:
            df_jangkauan = df_jangkauan.loc[
                df_jangkauan["Tanggal_Lapor"].dt.year == tahun_periode
            ]

        if not df_jangkauan.empty:
            wilayah_pertama = (
                df_jangkauan.groupby("Domisili")["Tanggal_Lapor"].min().reset_index()
            )
            wilayah_pertama["Periode"] = wilayah_pertama["Tanggal_Lapor"].dt.to_period(
                "M"
            )
            df_tren_jangkauan = (
                wilayah_pertama.groupby("Periode")
                .size()
                .cumsum()
                .rename("Wilayah Terjangkau")
                .rename_axis("Bulan")
                .reset_index()
            )
            df_tren_jangkauan["Bulan"] = df_tren_jangkauan["Bulan"].astype(str)
            fig_tren_jangkauan = px.line(
                df_tren_jangkauan,
                x="Bulan",
                y="Wilayah Terjangkau",
                markers=True,
                text="Wilayah Terjangkau",
                color_discrete_sequence=["#2a9d8f"],
            )
            fig_tren_jangkauan.update_traces(textposition="top center")
            fig_tren_jangkauan.update_layout(
                height=440,
                yaxis_title="Jumlah Wilayah Kumulatif",
                xaxis_title=(
                    f"Bulan ({tahun_periode})" if tahun_periode is not None else "Bulan"
                ),
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig_tren_jangkauan, use_container_width=True)
        else:
            st.info("Belum ada data tanggal dan wilayah untuk menampilkan tren.")

    with historical_col:
        st.subheader("Jejak Historis / Tren Pertumbuhan")
        df_tren = df_public.loc[
            df_public["ID_Pasien"].ne("") & df_public["Tanggal_Lapor"].notna(),
            ["ID_Pasien", "Tanggal_Lapor"],
        ].copy()
        if not df_tren.empty:
            penerima_pertama = (
                df_tren.groupby("ID_Pasien")["Tanggal_Lapor"].min().reset_index()
            )
            penerima_pertama["Bulan"] = penerima_pertama["Tanggal_Lapor"].dt.to_period(
                "M"
            )
            df_tren = (
                penerima_pertama.groupby("Bulan")
                .size()
                .cumsum()
                .rename("Penerima Manfaat Kumulatif")
                .reset_index()
            )
            df_tren["Bulan"] = df_tren["Bulan"].astype(str)
            fig_tren = px.line(
                df_tren,
                x="Bulan",
                y="Penerima Manfaat Kumulatif",
                markers=True,
                labels={
                    "Bulan": "Bulan",
                    "Penerima Manfaat Kumulatif": "Penerima Manfaat",
                },
            )
            st.plotly_chart(fig_tren, use_container_width=True)
        else:
            st.info("Belum ada data tanggal laporan untuk ditampilkan.")

    age_col, category_col = st.columns(2)
    with age_col:
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

    with category_col:
        st.subheader("Sebaran Kategori Tuna Daksa")
        df_kategori = (
            df_public.loc[
                df_public["Kategori_Tuna_Daksa"].ne(""), "Kategori_Tuna_Daksa"
            ]
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

    st.subheader("Aktivitas sehari-hari yang didukung")

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

    st.subheader("Cerita dan pengalaman penerima manfaat")

    def parse_aktivitas(raw_value):
        try:
            parsed_value = ast.literal_eval(raw_value)
            values = parsed_value if isinstance(parsed_value, list) else [parsed_value]
        except (ValueError, SyntaxError):
            values = [raw_value] if raw_value else []
        return [
            str(value).strip()
            for value in values
            if str(value).strip() and str(value).strip() != "Pasif/Hanya Dipakai"
        ]

    df_cerita = df_public.copy()
    df_cerita["Aktivitas_Terbantu"] = df_cerita["Kategori_Aktivitas_ADL"].apply(
        lambda value: ", ".join(parse_aktivitas(value))
    )
    df_cerita = df_cerita[
        (df_cerita["Sentimen_Laporan"] == "Positif")
        & df_cerita["Kutipan_Asli"].str.len().ge(30)
        & df_cerita["Aktivitas_Terbantu"].ne("")
    ].copy()

    if not df_cerita.empty:
        # Kurasi kutipan tetap menggunakan filter kualitas yang sama; hanya tabel
        # dan filter interaktif berdasarkan karakteristik penerima yang disembunyikan.
        df_terfilter = df_cerita

        for _, row in df_terfilter.head(10).iterrows():
            kutipan = html.escape(row["Kutipan_Asli"])
            aktivitas = html.escape(row["Aktivitas_Terbantu"])
            wilayah = html.escape(row["Domisili"])
            st.markdown(
                f"""
                <div style="border-left: 4px solid #2a9d8f; background-color: #f0fdfa;
                            padding: 1rem 1.25rem; margin: 0.75rem 0; border-radius: 0 8px 8px 0;">
                    <div style="font-size: 1.05rem; font-style: italic;">
                        “{kutipan}”
                    </div>
                    <div style="color: #475569; margin-top: 0.6rem; font-size: 0.9rem;">
                        Aktivitas: {aktivitas} · {wilayah}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("Belum ada kutipan positif yang memenuhi kriteria kurasi.")

    st.markdown("---")

    # 4. GENERATIVE STORYTELLING & EXPORT PDF
    st.subheader("🤖 Generative AI: Laporan Eksekutif Otomatis")
    st.write(
        "Sistem AI akan menganalisis metrik saat ini dan merangkai narasi laporan CSR bulanan secara otomatis."
    )

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
    st.header("Manajemen Data Mentah")
    st.markdown("---")

    df_internal = df.copy()
    for column in [
        "ID_Laporan",
        "ID_Pasien",
        "Tanggal_Lapor",
        "Domisili",
        "Kategori_Tuna_Daksa",
        "Kategori_Aktivitas_ADL",
        "Status_Utilitas",
        "Sentimen_Laporan",
        "Tingkat_Urgensi_Pemeliharaan",
        "Kutipan_Asli",
    ]:
        if column not in df_internal:
            df_internal[column] = ""
        df_internal[column] = df_internal[column].fillna("").astype(str).str.strip()

    if "Keluhan_Hardware" not in df_internal:
        df_internal["Keluhan_Hardware"] = [[] for _ in range(len(df_internal))]

    def parse_hardware_categories(raw_value):
        if isinstance(raw_value, (list, tuple, set)):
            values = raw_value
        elif pd.isna(raw_value):
            values = []
        else:
            text_value = str(raw_value).strip()
            try:
                parsed_value = ast.literal_eval(text_value)
                values = (
                    parsed_value
                    if isinstance(parsed_value, (list, tuple, set))
                    else [parsed_value]
                )
            except (ValueError, SyntaxError):
                values = [text_value]

        return [
            str(value).strip()
            for value in values
            if str(value).strip() and str(value).strip() != "Tidak Ada Keluhan"
        ]

    df_internal["Durasi_Pakai_Jam"] = pd.to_numeric(
        df_internal.get("Durasi_Pakai_Jam", pd.Series(dtype=float)), errors="coerce"
    )
    df_internal["Usia"] = pd.to_numeric(
        df_internal.get("Usia", pd.Series(dtype=float)), errors="coerce"
    )
    df_internal["Tanggal_Lapor"] = pd.to_datetime(
        df_internal["Tanggal_Lapor"], errors="coerce"
    )
    df_internal["Kategori_Keluhan_Hardware"] = df_internal["Keluhan_Hardware"].apply(
        parse_hardware_categories
    )

    total_penerima = df_internal.loc[
        df_internal["ID_Pasien"].ne(""), "ID_Pasien"
    ].nunique()
    penerima_terkendala = df_internal.loc[
        df_internal["Status_Utilitas"].eq("Terkendala")
        & df_internal["ID_Pasien"].ne(""),
        "ID_Pasien",
    ].nunique()
    kasus_urgensi_tinggi = (
        df_internal["Tingkat_Urgensi_Pemeliharaan"].eq("Tinggi").sum()
    )
    total_laporan = len(df_internal)
    laporan_negatif = df_internal["Sentimen_Laporan"].eq("Negatif").sum()
    laporan_keluhan_hardware = (
        df_internal["Kategori_Keluhan_Hardware"].apply(bool).sum()
    )
    durasi_valid = df_internal["Durasi_Pakai_Jam"].dropna()
    durasi_valid = durasi_valid[durasi_valid.gt(0)]
    durasi_penggunaan = (
        f"{durasi_valid.mean():.1f} jam / {durasi_valid.median():.1f} jam"
        if not durasi_valid.empty
        else "-"
    )

    metric_rows = [
        (
            "Total penerima manfaat",
            total_penerima,
            "Jumlah penerima manfaat unik berdasarkan ID pasien.",
        ),
        (
            "Penerima manfaat terkendala",
            penerima_terkendala,
            "Penerima manfaat dengan status utilitas Terkendala.",
        ),
        (
            "Kasus urgensi tinggi",
            kasus_urgensi_tinggi,
            "Laporan dengan tingkat urgensi pemeliharaan Tinggi.",
        ),
        ("Total laporan", total_laporan, "Jumlah seluruh laporan yang tersedia."),
        (
            "Laporan sentimen negatif",
            laporan_negatif,
            "Laporan yang perlu diperiksa lebih lanjut.",
        ),
        (
            "Laporan dengan keluhan hardware",
            laporan_keluhan_hardware,
            "Laporan yang memuat setidaknya satu keluhan hardware.",
        ),
        (
            "Rata-rata / median durasi penggunaan",
            durasi_penggunaan,
            "Durasi valid dalam jam; format nilai adalah rata-rata / median.",
        ),
    ]

    with st.container(border=True):
        st.subheader("Overview")
        st.write(
            "Ringkasan kondisi keseluruhan penerima manfaat, penggunaan alat, dan laporan pemeliharaan."
        )
        render_soft_metric_cards(metric_rows[:4])
        render_soft_metric_cards(metric_rows[4:])

    st.markdown("#### Distribusi kondisi dan laporan")
    chart_columns = st.columns(2)

    with chart_columns[0]:
        df_status_utilitas = (
            df_internal.loc[df_internal["Status_Utilitas"].ne(""), "Status_Utilitas"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Jumlah")
        )
        if df_status_utilitas.empty:
            st.info("Belum ada data status utilitas.")
        else:
            fig_status_utilitas = px.pie(
                df_status_utilitas,
                names="Status",
                values="Jumlah",
                title="Distribusi status utilitas",
                hole=0.35,
            )
            st.plotly_chart(fig_status_utilitas, use_container_width=True)

    with chart_columns[1]:
        df_urgensi = (
            df_internal.loc[
                df_internal["Tingkat_Urgensi_Pemeliharaan"].ne(""),
                "Tingkat_Urgensi_Pemeliharaan",
            ]
            .value_counts()
            .rename_axis("Tingkat urgensi")
            .reset_index(name="Jumlah")
        )
        if df_urgensi.empty:
            st.info("Belum ada data tingkat urgensi pemeliharaan.")
        else:
            fig_urgensi = px.pie(
                df_urgensi,
                names="Tingkat urgensi",
                values="Jumlah",
                title="Distribusi tingkat urgensi pemeliharaan",
                hole=0.35,
            )
            st.plotly_chart(fig_urgensi, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        df_sentimen = (
            df_internal.loc[df_internal["Sentimen_Laporan"].ne(""), "Sentimen_Laporan"]
            .value_counts()
            .rename_axis("Sentimen")
            .reset_index(name="Jumlah")
        )
        if df_sentimen.empty:
            st.info("Belum ada data sentimen laporan.")
        else:
            fig_sentimen = px.pie(
                df_sentimen,
                names="Sentimen",
                values="Jumlah",
                title="Distribusi sentimen laporan",
                hole=0.35,
            )
            st.plotly_chart(fig_sentimen, use_container_width=True)

    with chart_columns[1]:
        df_keluhan_overview = (
            df_internal["Kategori_Keluhan_Hardware"]
            .explode()
            .dropna()
            .value_counts()
            .rename_axis("Kategori keluhan")
            .reset_index(name="Jumlah kasus")
        )
        if df_keluhan_overview.empty:
            st.info("Belum ada keluhan hardware.")
        else:
            fig_keluhan_overview = px.bar(
                df_keluhan_overview.head(10),
                x="Jumlah kasus",
                y="Kategori keluhan",
                orientation="h",
                title="Kategori keluhan hardware terbanyak",
                text_auto=True,
                color="Jumlah kasus",
                color_continuous_scale="Reds",
            )
            fig_keluhan_overview.update_layout(showlegend=False)
            st.plotly_chart(fig_keluhan_overview, use_container_width=True)

    st.markdown("---")

    st.subheader("Beneficiary Management")
    st.write(
        "Pahami kondisi setiap penerima manfaat secara individual melalui daftar, filter, "
        "dan riwayat laporan yang tersedia."
    )

    def parse_list_values(raw_value):
        if isinstance(raw_value, (list, tuple, set)):
            values = raw_value
        elif pd.isna(raw_value):
            values = []
        else:
            text_value = str(raw_value).strip()
            try:
                parsed_value = ast.literal_eval(text_value)
                values = (
                    parsed_value
                    if isinstance(parsed_value, (list, tuple, set))
                    else [parsed_value]
                )
            except (ValueError, SyntaxError):
                values = [text_value]
        return [str(value).strip() for value in values if str(value).strip()]

    df_beneficiary = df_internal.copy()
    df_beneficiary["Aktivitas_ADL"] = df_beneficiary["Kategori_Aktivitas_ADL"].apply(
        lambda value: ", ".join(parse_list_values(value))
    )
    df_beneficiary["Keluhan"] = df_beneficiary["Kategori_Keluhan_Hardware"].apply(
        lambda values: ", ".join(values) if values else "Tidak ada keluhan"
    )
    df_beneficiary["Tanggal"] = (
        df_beneficiary["Tanggal_Lapor"].dt.strftime("%Y-%m-%d").fillna("-")
    )

    filter_columns = st.columns(5)
    with filter_columns[0]:
        pencarian = (
            st.text_input(
                "Cari ID atau identitas internal",
                placeholder="Contoh: P-001 atau nama internal",
                key="beneficiary_search",
            )
            .strip()
            .lower()
        )
    with filter_columns[1]:
        domisili_options = sorted(
            value for value in df_beneficiary["Domisili"].unique() if value
        )
        domisili_filter = st.selectbox(
            "Domisili", ["Semua"] + domisili_options, key="beneficiary_domicile"
        )
    with filter_columns[2]:
        kategori_options = sorted(
            value for value in df_beneficiary["Kategori_Tuna_Daksa"].unique() if value
        )
        kategori_filter = st.selectbox(
            "Kategori tuna daksa",
            ["Semua"] + kategori_options,
            key="beneficiary_category",
        )
    with filter_columns[3]:
        utilitas_options = sorted(
            value for value in df_beneficiary["Status_Utilitas"].unique() if value
        )
        utilitas_filter = st.selectbox(
            "Status utilitas",
            ["Semua"] + utilitas_options,
            key="beneficiary_utility",
        )
    with filter_columns[4]:
        urgensi_options = sorted(
            value
            for value in df_beneficiary["Tingkat_Urgensi_Pemeliharaan"].unique()
            if value
        )
        urgensi_filter = st.selectbox(
            "Tingkat urgensi",
            ["Semua"] + urgensi_options,
            key="beneficiary_urgency",
        )

    df_beneficiary_filtered = df_beneficiary.copy()
    if pencarian:
        searchable_columns = [
            column
            for column in ["ID_Pasien", "ID_Laporan", "Nama", "Identitas_Internal"]
            if column in df_beneficiary_filtered
        ]
        search_mask = pd.Series(False, index=df_beneficiary_filtered.index)
        for column in searchable_columns:
            search_mask |= (
                df_beneficiary_filtered[column]
                .astype(str)
                .str.lower()
                .str.startswith(pencarian, na=False)
            )
        df_beneficiary_filtered = df_beneficiary_filtered[search_mask]
    if domisili_filter != "Semua":
        df_beneficiary_filtered = df_beneficiary_filtered[
            df_beneficiary_filtered["Domisili"] == domisili_filter
        ]
    if kategori_filter != "Semua":
        df_beneficiary_filtered = df_beneficiary_filtered[
            df_beneficiary_filtered["Kategori_Tuna_Daksa"] == kategori_filter
        ]
    if utilitas_filter != "Semua":
        df_beneficiary_filtered = df_beneficiary_filtered[
            df_beneficiary_filtered["Status_Utilitas"] == utilitas_filter
        ]
    if urgensi_filter != "Semua":
        df_beneficiary_filtered = df_beneficiary_filtered[
            df_beneficiary_filtered["Tingkat_Urgensi_Pemeliharaan"] == urgensi_filter
        ]

    daftar_columns = [
        "ID_Pasien",
        "ID_Laporan",
        "Tanggal",
        "Domisili",
        "Kategori_Tuna_Daksa",
        "Status_Utilitas",
        "Tingkat_Urgensi_Pemeliharaan",
    ]
    st.caption(
        f"Menampilkan {len(df_beneficiary_filtered)} dari {len(df_beneficiary)} laporan penerima manfaat."
    )
    previous_search = st.session_state.get("_beneficiary_previous_search")
    if previous_search != pencarian:
        st.session_state.pop("beneficiary_table", None)
        st.session_state["_beneficiary_previous_search"] = pencarian
    beneficiary_table = (
        df_beneficiary_filtered[daftar_columns]
        .rename(
            columns={
                "ID_Pasien": "ID penerima manfaat",
                "ID_Laporan": "ID laporan",
                "Tanggal": "Tanggal laporan",
                "Domisili": "Domisili",
                "Kategori_Tuna_Daksa": "Kategori tuna daksa",
                "Status_Utilitas": "Status utilitas",
                "Tingkat_Urgensi_Pemeliharaan": "Tingkat urgensi",
            }
        )
        .reset_index(drop=True)
    )
    table_event = st.dataframe(
        beneficiary_table,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="beneficiary_table",
    )

    selected_rows = table_event.selection.rows
    if selected_rows:
        selected_row = beneficiary_table.iloc[selected_rows[0]]
        selected_beneficiary = selected_row["ID penerima manfaat"]
        df_detail = df_beneficiary[
            df_beneficiary["ID_Pasien"] == selected_beneficiary
        ].sort_values("Tanggal_Lapor", ascending=False)
        detail_summary = df_detail.iloc[0]

        detail_columns = st.columns(4)
        detail_columns[0].metric("ID penerima manfaat", selected_beneficiary)
        detail_columns[1].metric("Domisili", detail_summary["Domisili"] or "-")
        detail_columns[2].metric(
            "Kategori tuna daksa", detail_summary["Kategori_Tuna_Daksa"] or "-"
        )
        detail_columns[3].metric(
            "Status utilitas", detail_summary["Status_Utilitas"] or "-"
        )

        st.markdown("##### Detail aktivitas ADL")
        aktivitas_detail = sorted(
            {
                aktivitas
                for values in df_detail["Kategori_Aktivitas_ADL"].apply(
                    parse_list_values
                )
                for aktivitas in values
            }
        )
        st.write(
            ", ".join(aktivitas_detail)
            if aktivitas_detail
            else "Belum ada data aktivitas ADL."
        )

        st.markdown("##### Riwayat keluhan dan penanganan")
        handling_columns = [
            column
            for column in [
                "Penanganan",
                "Status_Penanganan",
                "Tindak_Lanjut",
                "Catatan_Penanganan",
            ]
            if column in df_detail
        ]
        complaint_columns = [
            "Tanggal",
            "ID_Laporan",
            "Keluhan",
            "Status_Utilitas",
            "Tingkat_Urgensi_Pemeliharaan",
            "Sentimen_Laporan",
            "Kutipan_Asli",
        ] + handling_columns
        st.dataframe(
            df_detail[complaint_columns].rename(
                columns={
                    "Tanggal": "Tanggal laporan",
                    "ID_Laporan": "ID laporan",
                    "Keluhan": "Keluhan hardware",
                    "Status_Utilitas": "Status utilitas",
                    "Tingkat_Urgensi_Pemeliharaan": "Tingkat urgensi",
                    "Sentimen_Laporan": "Sentimen",
                    "Kutipan_Asli": "Laporan/kutipan",
                    "Status_Penanganan": "Status penanganan",
                    "Catatan_Penanganan": "Catatan penanganan",
                    "Tindak_Lanjut": "Tindak lanjut",
                    "Penanganan": "Penanganan",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        if not handling_columns:
            st.caption(
                "Kolom penanganan belum tersedia pada data saat ini; status utilitas, urgensi, dan laporan digunakan sebagai indikator tindak lanjut."
            )

        st.markdown("##### Riwayat durasi penggunaan")
        duration_history = df_detail[
            ["Tanggal", "ID_Laporan", "Durasi_Pakai_Jam"]
        ].copy()
        duration_history["Durasi_Pakai_Jam"] = duration_history[
            "Durasi_Pakai_Jam"
        ].apply(lambda value: f"{value:.1f} jam" if pd.notna(value) else "-")
        st.dataframe(
            duration_history.rename(
                columns={
                    "Tanggal": "Tanggal laporan",
                    "ID_Laporan": "ID laporan",
                    "Durasi_Pakai_Jam": "Durasi penggunaan",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    elif pencarian and df_beneficiary_filtered.empty:
        st.info("Tidak ada penerima manfaat yang sesuai dengan filter.")

    st.markdown("---")

    st.subheader("Utilization & User Experience")
    st.write(
        "Analisis ini menggambarkan bagaimana penerima manfaat menggunakan lengan "
        "prostetik dalam aktivitas sehari-hari, termasuk durasi, utilitas, aktivitas "
        "ADL, sentimen laporan, dan perubahan status pemakaian."
    )

    ux_columns = st.columns(4)
    ux_columns[0].metric(
        "Laporan dengan durasi valid",
        int(durasi_valid.size),
        help="Jumlah laporan dengan durasi penggunaan lebih dari nol jam.",
    )
    ux_columns[1].metric(
        "Rata-rata durasi penggunaan",
        f"{durasi_valid.mean():.1f} jam" if not durasi_valid.empty else "-",
        help="Rata-rata durasi penggunaan dari laporan dengan durasi valid.",
    )
    ux_columns[2].metric(
        "Kategori aktivitas ADL",
        int(
            len(
                {
                    aktivitas
                    for values in df_internal["Kategori_Aktivitas_ADL"].apply(
                        parse_list_values
                    )
                    for aktivitas in values
                }
            )
        ),
        help="Jumlah kategori aktivitas ADL unik yang tercatat.",
    )
    ux_columns[3].metric(
        "Laporan sentimen positif",
        int(df_internal["Sentimen_Laporan"].eq("Positif").sum()),
        help="Jumlah laporan yang memiliki sentimen positif.",
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        df_duration = df_internal.loc[
            df_internal["Durasi_Pakai_Jam"].gt(0), ["Durasi_Pakai_Jam"]
        ]
        if df_duration.empty:
            st.info("Belum ada data durasi penggunaan yang valid.")
        else:
            fig_duration = px.histogram(
                df_duration,
                x="Durasi_Pakai_Jam",
                nbins=10,
                title="Distribusi durasi pemakaian",
                labels={
                    "Durasi_Pakai_Jam": "Durasi penggunaan (jam)",
                    "count": "Jumlah laporan",
                },
                text_auto=True,
            )
            st.plotly_chart(fig_duration, use_container_width=True)

    with chart_columns[1]:
        df_adl = (
            df_internal["Kategori_Aktivitas_ADL"]
            .apply(parse_list_values)
            .explode()
            .dropna()
            .value_counts()
            .rename_axis("Aktivitas ADL")
            .reset_index(name="Jumlah laporan")
        )
        if df_adl.empty:
            st.info("Belum ada data aktivitas ADL.")
        else:
            fig_adl = px.bar(
                df_adl,
                x="Jumlah laporan",
                y="Aktivitas ADL",
                orientation="h",
                title="Aktivitas ADL yang paling sering dilaporkan",
                text_auto=True,
                color="Jumlah laporan",
                color_continuous_scale="Blues",
            )
            fig_adl.update_layout(showlegend=False)
            st.plotly_chart(fig_adl, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        df_utility_by_category = df_internal.loc[
            df_internal["Kategori_Tuna_Daksa"].ne("")
            & df_internal["Status_Utilitas"].ne(""),
            ["Kategori_Tuna_Daksa", "Status_Utilitas"],
        ]
        if df_utility_by_category.empty:
            st.info("Belum ada data kategori pengguna dan status utilitas.")
        else:
            df_utility_by_category = (
                df_utility_by_category.value_counts()
                .rename("Jumlah laporan")
                .reset_index()
            )
            fig_utility_stack = px.bar(
                df_utility_by_category,
                x="Kategori_Tuna_Daksa",
                y="Jumlah laporan",
                color="Status_Utilitas",
                title="Distribusi status utilitas per kategori pengguna",
                labels={
                    "Kategori_Tuna_Daksa": "Kategori pengguna",
                    "Status_Utilitas": "Status utilitas",
                },
                text_auto=True,
            )
            fig_utility_stack.update_layout(barmode="stack")
            st.plotly_chart(fig_utility_stack, use_container_width=True)

    with chart_columns[1]:
        df_status_history = df_internal.loc[
            df_internal["ID_Pasien"].ne("")
            & df_internal["Tanggal_Lapor"].notna()
            & df_internal["Status_Utilitas"].ne(""),
            ["ID_Pasien", "Tanggal_Lapor", "Status_Utilitas"],
        ].sort_values(["ID_Pasien", "Tanggal_Lapor"])
        if df_status_history.empty:
            st.info("Belum ada data riwayat status pemakaian.")
        else:
            df_status_history["Status_sebelumnya"] = df_status_history.groupby(
                "ID_Pasien"
            )["Status_Utilitas"].shift()
            df_status_changes = df_status_history.loc[
                df_status_history["Status_sebelumnya"].notna()
                & df_status_history["Status_sebelumnya"].ne(
                    df_status_history["Status_Utilitas"]
                )
            ].copy()
            if df_status_changes.empty:
                st.info("Belum ada perubahan status pemakaian yang tercatat.")
            else:
                df_status_changes["Periode"] = (
                    df_status_changes["Tanggal_Lapor"]
                    .dt.to_period("M")
                    .dt.to_timestamp()
                )
                df_status_changes = (
                    df_status_changes.groupby(
                        ["Periode", "Status_Utilitas"], as_index=False
                    )
                    .size()
                    .rename(columns={"size": "Jumlah perubahan"})
                )
                fig_status_trend = px.line(
                    df_status_changes,
                    x="Periode",
                    y="Jumlah perubahan",
                    color="Status_Utilitas",
                    markers=True,
                    title="Tren perubahan status pemakaian",
                    labels={
                        "Periode": "Periode laporan",
                        "Status_Utilitas": "Status baru",
                    },
                )
                st.plotly_chart(fig_status_trend, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        df_adl_utility = df_internal.loc[
            df_internal["Status_Utilitas"].ne(""),
            ["Kategori_Aktivitas_ADL", "Status_Utilitas"],
        ].copy()
        df_adl_utility["Aktivitas ADL"] = df_adl_utility[
            "Kategori_Aktivitas_ADL"
        ].apply(parse_list_values)
        df_adl_utility = df_adl_utility.explode("Aktivitas ADL")
        df_adl_utility = df_adl_utility.loc[df_adl_utility["Aktivitas ADL"].ne("")]
        if df_adl_utility.empty:
            st.info("Belum ada data hubungan aktivitas ADL dan status utilitas.")
        else:
            df_adl_utility = (
                df_adl_utility[["Aktivitas ADL", "Status_Utilitas"]]
                .value_counts()
                .rename("Jumlah laporan")
                .reset_index()
                .pivot(
                    index="Aktivitas ADL",
                    columns="Status_Utilitas",
                    values="Jumlah laporan",
                )
                .fillna(0)
            )
            fig_adl_heatmap = px.imshow(
                df_adl_utility,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                title="Hubungan aktivitas ADL dengan status utilitas",
                labels={
                    "x": "Status utilitas",
                    "y": "Aktivitas ADL",
                    "color": "Jumlah laporan",
                },
            )
            st.plotly_chart(fig_adl_heatmap, use_container_width=True)

    with chart_columns[1]:
        df_duration_category = df_internal.loc[
            df_internal["Kategori_Tuna_Daksa"].ne("")
            & df_internal["Durasi_Pakai_Jam"].gt(0),
            ["Kategori_Tuna_Daksa", "Durasi_Pakai_Jam"],
        ]
        if df_duration_category.empty:
            st.info("Belum ada data durasi per kategori pengguna.")
        else:
            df_duration_category = (
                df_duration_category.groupby("Kategori_Tuna_Daksa", as_index=False)[
                    "Durasi_Pakai_Jam"
                ]
                .mean()
                .sort_values("Durasi_Pakai_Jam", ascending=False)
            )
            fig_duration_category = px.bar(
                df_duration_category,
                x="Kategori_Tuna_Daksa",
                y="Durasi_Pakai_Jam",
                title="Durasi penggunaan per kategori pengguna",
                labels={
                    "Kategori_Tuna_Daksa": "Kategori pengguna",
                    "Durasi_Pakai_Jam": "Rata-rata durasi (jam)",
                },
                text_auto=".1f",
                color="Durasi_Pakai_Jam",
                color_continuous_scale="Teal",
            )
            fig_duration_category.update_layout(showlegend=False)
            st.plotly_chart(fig_duration_category, use_container_width=True)

    st.markdown("---")

    st.subheader("Hardware & Maintenance")
    st.write(
        "Analisis ini membantu mengidentifikasi komponen yang paling sering dikeluhkan, "
        "tingkat keseriusan masalah, pola keluhan berulang, dan hasil tindakan pemeliharaan."
    )

    df_complaints = df_internal[["Kategori_Keluhan_Hardware"]].explode(
        "Kategori_Keluhan_Hardware"
    )
    df_complaints = df_complaints.rename(
        columns={"Kategori_Keluhan_Hardware": "Keluhan"}
    )
    df_complaints = df_complaints.loc[
        df_complaints["Keluhan"].notna() & df_complaints["Keluhan"].ne("")
    ]

    complaint_counts = (
        df_complaints["Keluhan"]
        .value_counts()
        .rename_axis("Keluhan")
        .reset_index(name="Jumlah laporan")
    )
    total_complaints = int(complaint_counts["Jumlah laporan"].sum())
    repeated_complaints = int(
        complaint_counts.loc[
            complaint_counts["Jumlah laporan"].gt(1), "Jumlah laporan"
        ].sum()
    )
    urgent_complaints = int(
        df_internal["Tingkat_Urgensi_Pemeliharaan"].eq("Tinggi").sum()
    )

    hardware_metrics = st.columns(4)
    hardware_metrics[0].metric(
        "Total laporan keluhan",
        total_complaints,
        help="Jumlah kemunculan kategori keluhan hardware pada seluruh laporan.",
    )
    hardware_metrics[1].metric(
        "Jenis keluhan",
        int(len(complaint_counts)),
        help="Jumlah kategori keluhan hardware yang unik.",
    )
    hardware_metrics[2].metric(
        "Keluhan berulang",
        repeated_complaints,
        help="Total laporan yang termasuk kategori keluhan dengan lebih dari satu kemunculan.",
    )
    hardware_metrics[3].metric(
        "Kasus urgensi tinggi",
        urgent_complaints,
        help="Jumlah laporan dengan tingkat urgensi pemeliharaan Tinggi.",
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        if complaint_counts.empty:
            st.info("Belum ada data keluhan hardware.")
        else:
            fig_complaints = px.bar(
                complaint_counts,
                x="Jumlah laporan",
                y="Keluhan",
                orientation="h",
                title="Distribusi keluhan hardware",
                text_auto=True,
                color="Jumlah laporan",
                color_continuous_scale="Reds",
            )
            fig_complaints.update_layout(showlegend=False)
            st.plotly_chart(fig_complaints, use_container_width=True)

    with chart_columns[1]:
        if complaint_counts.empty:
            st.info("Belum ada data untuk Pareto chart.")
        else:
            df_pareto = complaint_counts.copy()
            df_pareto["Persentase kumulatif"] = (
                df_pareto["Jumlah laporan"].cumsum() / total_complaints * 100
            )
            fig_pareto = go.Figure()
            fig_pareto.add_trace(
                go.Bar(
                    x=df_pareto["Keluhan"],
                    y=df_pareto["Jumlah laporan"],
                    name="Jumlah laporan",
                    marker_color="#d95f59",
                )
            )
            fig_pareto.add_trace(
                go.Scatter(
                    x=df_pareto["Keluhan"],
                    y=df_pareto["Persentase kumulatif"],
                    name="Persentase kumulatif",
                    mode="lines+markers",
                    line={"color": "#2f5597"},
                    yaxis="y2",
                )
            )
            fig_pareto.update_layout(
                title="Pareto chart keluhan hardware",
                xaxis_title="Jenis keluhan",
                yaxis={"title": "Jumlah laporan"},
                yaxis2={
                    "title": "Persentase kumulatif",
                    "overlaying": "y",
                    "side": "right",
                    "range": [0, 100],
                    "ticksuffix": "%",
                },
                legend={"orientation": "h"},
            )
            st.plotly_chart(fig_pareto, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        df_complaints_category = df_internal[
            ["Kategori_Tuna_Daksa", "Kategori_Keluhan_Hardware"]
        ].explode("Kategori_Keluhan_Hardware")
        df_complaints_category = df_complaints_category.rename(
            columns={"Kategori_Keluhan_Hardware": "Keluhan"}
        )
        df_complaints_category = df_complaints_category.loc[
            df_complaints_category["Kategori_Tuna_Daksa"].ne("")
            & df_complaints_category["Keluhan"].notna()
            & df_complaints_category["Keluhan"].ne("")
        ]
        if df_complaints_category.empty:
            st.info("Belum ada data keluhan berdasarkan kategori tuna daksa.")
        else:
            df_complaints_category = (
                df_complaints_category.value_counts()
                .rename("Jumlah laporan")
                .reset_index()
            )
            fig_category_complaints = px.bar(
                df_complaints_category,
                x="Kategori_Tuna_Daksa",
                y="Jumlah laporan",
                color="Keluhan",
                title="Keluhan berdasarkan kategori tuna daksa",
                labels={
                    "Kategori_Tuna_Daksa": "Kategori tuna daksa",
                    "Keluhan": "Keluhan hardware",
                },
                text_auto=True,
            )
            fig_category_complaints.update_layout(barmode="stack")
            st.plotly_chart(fig_category_complaints, use_container_width=True)

    with chart_columns[1]:
        urgency_order = ["Rendah", "Sedang", "Tinggi"]
        df_urgency_hardware = (
            df_internal.loc[
                df_internal["Tingkat_Urgensi_Pemeliharaan"].ne(""),
                "Tingkat_Urgensi_Pemeliharaan",
            ]
            .value_counts()
            .rename_axis("Tingkat urgensi")
            .reset_index(name="Jumlah kasus")
        )
        if df_urgency_hardware.empty:
            st.info("Belum ada data tingkat urgensi pemeliharaan.")
        else:
            df_urgency_hardware["Tingkat urgensi"] = pd.Categorical(
                df_urgency_hardware["Tingkat urgensi"],
                categories=urgency_order,
                ordered=True,
            )
            df_urgency_hardware = df_urgency_hardware.sort_values("Tingkat urgensi")
            fig_urgency_hardware = px.bar(
                df_urgency_hardware,
                x="Tingkat urgensi",
                y="Jumlah kasus",
                title="Tingkat urgensi pemeliharaan",
                text_auto=True,
                color="Tingkat urgensi",
                category_orders={"Tingkat urgensi": urgency_order},
                color_discrete_map={
                    "Rendah": "#70ad47",
                    "Sedang": "#ffc000",
                    "Tinggi": "#c00000",
                },
            )
            fig_urgency_hardware.update_layout(showlegend=False)
            st.plotly_chart(fig_urgency_hardware, use_container_width=True)

    st.markdown("---")
    st.subheader("Geographic & Demographic Analysis")
    st.write(
        "Analisis ini membantu memahami karakteristik penerima manfaat berdasarkan "
        "domisili, usia, kategori tuna daksa, serta pola penggunaan dan keluhan. "
        "Temuan digunakan sebagai dasar hipotesis pengembangan produk dan pendampingan, "
        "bukan sebagai kesimpulan desain langsung."
    )

    geo_demo_columns = st.columns(4)
    geo_demo_columns[0].metric(
        "Domisili terwakili",
        int(df_internal.loc[df_internal["Domisili"].ne(""), "Domisili"].nunique()),
    )
    geo_demo_columns[1].metric("Usia valid", int(df_internal["Usia"].notna().sum()))
    geo_demo_columns[2].metric(
        "Kategori tuna daksa",
        int(
            df_internal.loc[
                df_internal["Kategori_Tuna_Daksa"].ne(""), "Kategori_Tuna_Daksa"
            ].nunique()
        ),
    )
    geo_demo_columns[3].metric(
        "Penerima manfaat",
        int(df_internal.loc[df_internal["ID_Pasien"].ne(""), "ID_Pasien"].nunique()),
    )
    df_profiles = (
        df_internal.loc[df_internal["ID_Pasien"].ne("")]
        .sort_values("Tanggal_Lapor")
        .drop_duplicates("ID_Pasien", keep="last")
    )

    chart_columns = st.columns(2)
    with chart_columns[0]:
        domicile_counts = (
            df_profiles.loc[df_profiles["Domisili"].ne(""), "Domisili"]
            .value_counts()
            .rename_axis("Domisili")
            .reset_index(name="Jumlah laporan")
        )
        if domicile_counts.empty:
            st.info("Belum ada data domisili penerima manfaat.")
        else:
            fig_domicile = px.bar(
                domicile_counts,
                x="Jumlah laporan",
                y="Domisili",
                orientation="h",
                title="Distribusi penerima manfaat berdasarkan domisili",
                text_auto=True,
                color="Jumlah laporan",
                color_continuous_scale="Blues",
            )
            fig_domicile.update_layout(showlegend=False)
            st.plotly_chart(fig_domicile, use_container_width=True)

    with chart_columns[1]:
        age_data = df_profiles.loc[df_profiles["Usia"].notna(), ["Usia"]]
        if age_data.empty:
            st.info("Belum ada data usia penerima manfaat.")
        else:
            fig_age = px.histogram(
                age_data,
                x="Usia",
                nbins=10,
                title="Distribusi usia penerima manfaat",
                labels={"Usia": "Usia (tahun)", "count": "Jumlah laporan"},
                text_auto=True,
            )
            st.plotly_chart(fig_age, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        disability_counts = (
            df_profiles.loc[
                df_profiles["Kategori_Tuna_Daksa"].ne(""), "Kategori_Tuna_Daksa"
            ]
            .value_counts()
            .rename_axis("Kategori tuna daksa")
            .reset_index(name="Jumlah laporan")
        )
        if disability_counts.empty:
            st.info("Belum ada data kategori tuna daksa.")
        else:
            fig_disability = px.bar(
                disability_counts,
                x="Kategori tuna daksa",
                y="Jumlah laporan",
                title="Distribusi kategori tuna daksa",
                text_auto=True,
                color="Jumlah laporan",
                color_continuous_scale="Teal",
            )
            fig_disability.update_layout(showlegend=False)
            st.plotly_chart(fig_disability, use_container_width=True)

    with chart_columns[1]:
        duration_by_disability = df_internal.loc[
            df_internal["Kategori_Tuna_Daksa"].ne("")
            & df_internal["Durasi_Pakai_Jam"].gt(0),
            ["Kategori_Tuna_Daksa", "Durasi_Pakai_Jam"],
        ]
        if duration_by_disability.empty:
            st.info("Belum ada data durasi berdasarkan kategori tuna daksa.")
        else:
            duration_by_disability = (
                duration_by_disability.groupby("Kategori_Tuna_Daksa")[
                    "Durasi_Pakai_Jam"
                ]
                .agg(["mean", "median"])
                .reset_index()
                .melt(
                    id_vars="Kategori_Tuna_Daksa",
                    var_name="Statistik",
                    value_name="Durasi (jam)",
                )
            )
            duration_by_disability["Statistik"] = duration_by_disability[
                "Statistik"
            ].map({"mean": "Rata-rata", "median": "Median"})
            fig_duration_disability = px.bar(
                duration_by_disability,
                x="Kategori_Tuna_Daksa",
                y="Durasi (jam)",
                color="Statistik",
                barmode="group",
                title="Durasi penggunaan berdasarkan kategori tuna daksa",
                labels={"Kategori_Tuna_Daksa": "Kategori tuna daksa"},
                text_auto=".1f",
            )
            st.plotly_chart(fig_duration_disability, use_container_width=True)

    chart_columns = st.columns(2)
    with chart_columns[0]:
        domicile_complaints = df_internal[
            ["Domisili", "Kategori_Keluhan_Hardware"]
        ].explode("Kategori_Keluhan_Hardware")
        domicile_complaints = domicile_complaints.rename(
            columns={"Kategori_Keluhan_Hardware": "Keluhan"}
        )
        domicile_complaints = domicile_complaints.loc[
            domicile_complaints["Domisili"].ne("")
            & domicile_complaints["Keluhan"].notna()
            & domicile_complaints["Keluhan"].ne("")
        ]
        if domicile_complaints.empty:
            st.info("Belum ada data hubungan domisili dan keluhan hardware.")
        else:
            domicile_complaints = (
                domicile_complaints.value_counts()
                .rename("Jumlah laporan")
                .reset_index()
            )
            fig_domicile_complaints = px.bar(
                domicile_complaints,
                x="Domisili",
                y="Jumlah laporan",
                color="Keluhan",
                title="Keluhan hardware berdasarkan domisili",
                text_auto=True,
            )
            fig_domicile_complaints.update_layout(barmode="stack")
            st.plotly_chart(fig_domicile_complaints, use_container_width=True)

    with chart_columns[1]:
        adl_by_age = df_internal.loc[
            df_internal["Usia"].notna(), ["Usia", "Kategori_Aktivitas_ADL"]
        ].copy()
        adl_by_age["Kelompok usia"] = pd.cut(
            adl_by_age["Usia"],
            bins=[0, 17, 30, 45, 60, float("inf")],
            labels=["0-17", "18-30", "31-45", "46-60", "61+"],
            include_lowest=True,
        )
        adl_by_age["Aktivitas ADL"] = adl_by_age["Kategori_Aktivitas_ADL"].apply(
            parse_list_values
        )
        adl_by_age = adl_by_age.explode("Aktivitas ADL")
        adl_by_age = adl_by_age.loc[
            adl_by_age["Kelompok usia"].notna() & adl_by_age["Aktivitas ADL"].ne("")
        ]
        if adl_by_age.empty:
            st.info("Belum ada data aktivitas ADL berdasarkan kelompok usia.")
        else:
            adl_by_age = (
                adl_by_age[["Kelompok usia", "Aktivitas ADL"]]
                .value_counts()
                .rename("Jumlah laporan")
                .reset_index()
            )
            fig_adl_age = px.bar(
                adl_by_age,
                x="Kelompok usia",
                y="Jumlah laporan",
                color="Aktivitas ADL",
                title="Distribusi aktivitas ADL berdasarkan kelompok usia",
                text_auto=True,
            )
            fig_adl_age.update_layout(barmode="stack")
            st.plotly_chart(fig_adl_age, use_container_width=True)

    st.markdown("---")
    st.subheader("Data Quality")
    st.write(
        "Pemeriksaan ini memantau kelengkapan, duplikasi, format, konsistensi kategori, "
        "serta hasil klasifikasi dan ekstraksi data. Temuan perlu ditinjau sebelum "
        "digunakan untuk analisis lanjutan."
    )

    df_quality = df.copy()
    quality_fields = [
        "ID_Laporan",
        "ID_Pasien",
        "Tanggal_Lapor",
        "Usia",
        "Durasi_Pakai_Jam",
        "Domisili",
        "Kategori_Tuna_Daksa",
        "Status_Utilitas",
        "Sentimen_Laporan",
        "Kategori_Aktivitas_ADL",
        "Keluhan_Hardware",
    ]
    for column in quality_fields:
        if column not in df_quality:
            df_quality[column] = pd.NA

    def quality_is_empty(series):
        return series.isna() | series.astype("string").str.strip().eq("")

    empty_counts = (
        pd.DataFrame(
            {
                "Kolom": quality_fields,
                "Jumlah kosong": [
                    int(quality_is_empty(df_quality[column]).sum())
                    for column in quality_fields
                ],
            }
        )
        .sort_values("Jumlah kosong", ascending=False)
        .reset_index(drop=True)
    )
    duplicate_report_count = int(
        df_quality.loc[~quality_is_empty(df_quality["ID_Laporan"]), "ID_Laporan"]
        .duplicated(keep=False)
        .sum()
    )
    duplicate_row_count = int(df_quality.duplicated(keep=False).sum())

    quality_metrics = st.columns(4)
    quality_metrics[0].metric("Total baris", len(df_quality))
    quality_metrics[1].metric(
        "Nilai kosong",
        int(empty_counts["Jumlah kosong"].sum()),
    )
    quality_metrics[2].metric("Baris duplikat", duplicate_row_count)
    quality_metrics[3].metric("ID laporan duplikat", duplicate_report_count)

    quality_columns = st.columns(2)
    with quality_columns[0]:
        st.markdown("#### Kelengkapan data")
        st.dataframe(
            empty_counts.rename(columns={"Kolom": "Kolom data"}),
            use_container_width=True,
            hide_index=True,
        )

    with quality_columns[1]:
        st.markdown("#### Duplikasi laporan")
        duplicate_ids = (
            df_quality.loc[
                ~quality_is_empty(df_quality["ID_Laporan"]),
                ["ID_Laporan"],
            ]
            .loc[lambda frame: frame["ID_Laporan"].duplicated(keep=False)]
            .value_counts()
            .rename("Jumlah kemunculan")
            .reset_index()
        )
        if duplicate_ids.empty and duplicate_row_count == 0:
            st.success("Tidak ditemukan laporan atau baris duplikat.")
        else:
            if not duplicate_ids.empty:
                st.dataframe(
                    duplicate_ids,
                    use_container_width=True,
                    hide_index=True,
                )
            st.caption(
                f"Total baris yang merupakan duplikat penuh: {duplicate_row_count}."
            )

    invalid_date_count = int(
        (
            ~quality_is_empty(df_quality["Tanggal_Lapor"])
            & pd.to_datetime(df_quality["Tanggal_Lapor"], errors="coerce").isna()
        ).sum()
    )
    invalid_duration_count = int(
        (
            ~quality_is_empty(df_quality["Durasi_Pakai_Jam"])
            & pd.to_numeric(df_quality["Durasi_Pakai_Jam"], errors="coerce").isna()
        ).sum()
    )
    invalid_age_count = int(
        (
            ~quality_is_empty(df_quality["Usia"])
            & (
                pd.to_numeric(df_quality["Usia"], errors="coerce").isna()
                | ~pd.to_numeric(df_quality["Usia"], errors="coerce").between(0, 120)
            )
        ).sum()
    )
    format_counts = pd.DataFrame(
        {
            "Pemeriksaan format": [
                "Tanggal laporan tidak valid",
                "Durasi penggunaan tidak numerik",
                "Usia di luar rentang 0-120 atau tidak numerik",
            ],
            "Jumlah masalah": [
                invalid_date_count,
                invalid_duration_count,
                invalid_age_count,
            ],
        }
    )
    st.markdown("#### Format data")
    st.dataframe(format_counts, use_container_width=True, hide_index=True)

    expected_categories = {
        "Status utilitas": (
            "Status_Utilitas",
            {"Sangat Berguna", "Cukup Berguna", "Terkendala"},
        ),
        "Sentimen laporan": (
            "Sentimen_Laporan",
            {"Positif", "Netral", "Negatif"},
        ),
        "Tingkat urgensi": (
            "Tingkat_Urgensi_Pemeliharaan",
            {"Rendah", "Sedang", "Tinggi"},
        ),
        "Kategori tuna daksa": (
            "Kategori_Tuna_Daksa",
            {"Above Elbow", "Below Elbow", "Bilateral (Keduanya)"},
        ),
    }
    consistency_rows = []
    for label, (column, allowed_values) in expected_categories.items():
        if column not in df_quality:
            df_quality[column] = pd.NA
        observed_values = {
            str(value).strip()
            for value in df_quality[column].dropna()
            if str(value).strip()
        }
        unexpected_values = sorted(observed_values - allowed_values)
        consistency_rows.append(
            {
                "Kategori": label,
                "Nilai unik": len(observed_values),
                "Nilai tidak konsisten": ", ".join(unexpected_values) or "-",
                "Jumlah masalah": int(
                    df_quality[column].astype("string").isin(unexpected_values).sum()
                ),
            }
        )
    st.markdown("#### Konsistensi kategori")
    st.dataframe(
        pd.DataFrame(consistency_rows),
        use_container_width=True,
        hide_index=True,
    )

    def extraction_quality(raw_value, parser):
        if pd.isna(raw_value) or str(raw_value).strip() == "":
            return "Kosong"
        if isinstance(raw_value, (list, tuple, set)):
            return "Valid"
        try:
            parsed_value = ast.literal_eval(str(raw_value).strip())
        except (ValueError, SyntaxError):
            return "Format tidak terstruktur"
        return (
            "Valid"
            if isinstance(parsed_value, (list, tuple, set))
            else "Format tidak terstruktur"
        )

    extraction_rows = []
    for label, column, parser in [
        ("Keluhan hardware", "Keluhan_Hardware", parse_hardware_categories),
        ("Kategori aktivitas ADL", "Kategori_Aktivitas_ADL", parse_list_values),
    ]:
        extraction_status = df_quality[column].apply(
            lambda value: extraction_quality(value, parser)
        )
        extraction_rows.extend(
            {
                "Pemeriksaan": label,
                "Status": status,
                "Jumlah": int((extraction_status == status).sum()),
            }
            for status in ["Valid", "Kosong", "Format tidak terstruktur"]
        )
    st.markdown("#### Hasil ekstraksi kategori")
    st.dataframe(
        pd.DataFrame(extraction_rows),
        use_container_width=True,
        hide_index=True,
    )

    sentiment_values = df_quality["Sentimen_Laporan"].astype("string").str.strip()
    sentiment_summary = (
        sentiment_values.loc[sentiment_values.ne("")]
        .value_counts()
        .rename_axis("Sentimen")
        .reset_index(name="Jumlah laporan")
    )
    st.markdown("#### Hasil klasifikasi sentimen")
    if sentiment_summary.empty:
        st.info("Belum ada hasil klasifikasi sentimen.")
    else:
        fig_quality_sentiment = px.bar(
            sentiment_summary,
            x="Sentimen",
            y="Jumlah laporan",
            title="Ringkasan hasil klasifikasi sentimen",
            text_auto=True,
            color="Sentimen",
            color_discrete_map={
                "Positif": "#70ad47",
                "Netral": "#a5a5a5",
                "Negatif": "#c00000",
            },
        )
        fig_quality_sentiment.update_layout(showlegend=False)
        st.plotly_chart(fig_quality_sentiment, use_container_width=True)
