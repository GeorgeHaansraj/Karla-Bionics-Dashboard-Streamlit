# 📊 Karla Bionics — AI-Powered Analytics Dashboard

Aplikasi ini adalah sistem dasbor berbasis kecerdasan buatan (_Artificial Intelligence_) yang dirancang khusus untuk membantu **Karla Bionics** dalam mengolah data mentah (baik berupa teks maupun rekaman suara), menganalisisnya secara otomatis menggunakan teknologi _Large Language Model_ (LLM), menyimpannya secara terpusat di _cloud_, dan menampilkannya dalam bentuk visualisasi grafik untuk mempermudah pengambilan keputusan.

> \[!NOTE\]
> **Catatan Latar Belakang Proyek:**
>
> Proyek ini dikembangkan sebagai bagian dari program **Kuliah Praktik (Kerja Praktik)** oleh mahasiswa/developer untuk **Karla Bionics**. Panduan di bawah ini ditulis dengan bahasa yang sederhana agar dapat dioperasikan oleh siapa saja, meskipun tidak memiliki latar belakang di bidang IT maupun pemrograman.

## ⚠️ Peringatan Penting Sebelum Memulai

Mohon perhatikan tiga poin krusial berikut sebelum Anda mencoba menjalankan aplikasi ini:

1. **Kredensial Rahasia Disembunyikan (`.gitignore`)**

   Demi keamanan data dan privasi sistem, seluruh kunci rahasia (_API Keys_, kredensial akun Firebase, dan file konfigurasi sensitif) **tidak diunggah** ke repositori GitHub ini. Repositori ini dilengkapi file `.gitignore` yang secara otomatis memblokir file-file rahasia agar tidak bocor ke publik.

   👉 **Tindakan yang diperlukan:** Anda **wajib menghubungi developer atau pemilik repositori** terlebih dahulu untuk meminta **paket file kredensial** beserta **Dokumen Teknis** lengkap agar aplikasi dapat terhubung ke _database_ dan AI.

2. **Masa Berlaku API Groq AI Hanya 10 Hari**

   Fitur analisis AI pada sistem ini menggunakan layanan **Groq AI API** yang saat ini masih terhubung ke akun pribadi milik developer/pemilik repositori. Kunci API sementara ini **hanya berlaku selama 10 hari terhitung sejak 25 November 2026 (berakhir sekitar 5 Desember 2026)**. Setelah melewati batas waktu tersebut, fitur AI tidak akan merespons hingga Anda memasukkan _API Key_ baru milik Karla Bionics sendiri.

3. **Database Saat Ini Menggunakan Data Sintetis (Simulasi)**

   Database Firebase pada sistem ini memiliki **2 Collection** utama. Untuk keperluan demonstrasi, pengujian fitur, dan menjaga kerahasiaan data perusahaan selama masa pengembangan, isi database saat ini merupakan **data sintetis (data buatan/simulasi)**, bukan data operasional asli Karla Bionics.

## 🛠️ Teknologi yang Digunakan (_Tech Stack_)

Sistem ini dibangun menggunakan kombinasi teknologi:

- **Python** — Bahasa pemrograman utama yang menjalankan seluruh logika pemrosesan data di balik layar.

- **Streamlit** — Kerangka kerja (_framework_) untuk membangun antarmuka website/dasbor interaktif.

- **Firebase (Cloud Firestore)** — Layanan _database cloud_ dari Google untuk menyimpan data dengan terstruktur.

- **Groq AI API (LLM)** — Mesin kecerdasan buatan (_Large Language Model_) yang bertugas membaca, memahami, mengekstrak informasi penting, dan merangkum data teks secara otomatis.

## 📋 Persyaratan Sistem (_Requirements_)

Sebelum menjalankan aplikasi di komputer/laptop Anda, pastikan hal-hal berikut sudah tersedia:

1. **Komputer / Laptop** (Windows, macOS, atau Linux) dengan koneksi internet yang stabil.

2. **Python (Versi 3.9 atau lebih baru)** sudah terinstal di komputer Anda.

   _(Jika belum, unduh gratis di [python.org](https://www.python.org/downloads/). Saat instalasi di Windows, pastikan mencentang kotak **"Add Python to PATH"**)._

3. **File Kredensial Rahasia & Dokumen Teknis** yang sudah Anda dapatkan dari developer/pemilik repositori.

4. **Daftar Pustaka Python (`requirements.txt`)** — Berisi seluruh komponen pendukung (seperti Streamlit, Firebase Admin, Groq SDK, Pandas, dll.) yang akan diinstal secara otomatis pada panduan di bawah.

## 🚀 Panduan Menjalankan Proyek (Untuk Pemula / Non-IT)

Ikuti langkah-langkah berikut secara berurutan untuk menjalankan dasbor di komputer Anda:

### Langkah 1: Unduh Kode Proyek ke Komputer Anda

Anda tidak perlu mengerti Git untuk mengunduh proyek ini:

1. Pada halaman utama repositori GitHub ini, klik tombol berwarna hijau bertuliskan **`<> Code`**.

2. Pilih menu **`Download ZIP`**.

3. Setelah file ZIP selesai diunduh, klik kanan pada file tersebut lalu pilih **`Extract All...`** (ekstrak ke folder yang mudah ditemukan, misalnya di `Desktop` atau `Documents`).

### Langkah 2: Masukkan File Kredensial dari Developer

1. Hubungi developer/pemilik repositori untuk meminta file kredensial rahasia (biasanya berupa file `.env`, folder`data/`, dan/atau file kunci `.json` Firebase).

2. Tambahkan file dan folder tersebut ke dalam folder utama hasil ekstrak tadi (sejajar dengan file `app.py`), sesuai arahan pada Dokumen Teknis.

### Langkah 3: Buka Terminal / Command Prompt di Dalam Folder Proyek

1. Buka folder proyek hasil ekstrak menggunakan _File Explorer_ (Windows) atau _Finder_ (Mac).

2. **Untuk pengguna Windows:** Klik pada bilah alamat folder di bagian atas (address bar), ketik `cmd`, lalu tekan **Enter**. Jendela layar hitam (_Command Prompt_) akan langsung terbuka di lokasi folder tersebut.

   **Untuk pengguna Mac:** Klik kanan pada folder proyek, lalu pilih **`New Terminal at Folder`**.

### Langkah 4: Instal Komponen Pendukung (_Dependencies_)

Ketik perintah berikut di jendela Terminal/Command Prompt, lalu tekan **Enter**:

```
pip install -r requirements.txt

```

_(Tunggu beberapa saat hingga proses pengunduhan dan pemasangan komponen selesai 100% tanpa pesan error)._

### Langkah 5: Jalankan Dasbor Utama

Setelah instalasi selesai, jalankan aplikasi dasbor dengan mengetik perintah berikut lalu tekan **Enter**:

```
streamlit run app.py

```

Secara otomatis, browser (Google Chrome/Edge/Safari) akan terbuka dan menampilkan **Karla Bionics Dashboard** di alamat lokal `http://localhost:8501`.

_(Catatan: Jika Anda juga perlu menjalankan layanan API penerima data di latar belakang, buka satu jendela Terminal baru di folder yang sama dan jalankan perintah `python api.py` atau `uvicorn api:app --reload` sesuai petunjuk di Dokumen Teknis)._

## 🔄 Alur Kerja & Pipeline Sistem

Secara sederhana, data di dalam proyek ini mengalir melalui tahapan (_pipeline_) berikut:

```
[1. Input Data]           -->  Rekaman suara atau data teks mentah masuk ke sistem
       │
       ▼
[2. Speech-to-Text]       -->  (Opsional) Audio diubah menjadi tulisan oleh stt_script.py
       │
       ▼
[3. Analisis AI (Groq)]   -->  Teks dibaca, dipahami, & dirangkum oleh LLM (llm_prompting.py)
       │
       ▼
[4. Pembersihan (ETL)]    -->  Data dirapikan & diformat ulang oleh etl_script.py
       │
       ▼
[5. Penyimpanan Cloud]    -->  Data masuk ke 2 Collection di Firebase Firestore
       │
       ▼
[6. Visualisasi Dasbor]   -->  Grafik & laporan tampil interaktif di website (app.py)

```

### Penjelasan Struktur Database (2 Collection Firebase)

Database **Cloud Firestore** pada proyek ini dibagi menjadi **2 Collection** utama:

1. **Collection Pertama (Data Mentah / Log Interaksi):** Menyimpan catatan mentah hasil transkripsi atau input awal beserta waktu pencatatannya.

2. **Collection Kedua (Data Terstruktur / Hasil Analisis AI):** Menyimpan hasil ekstraksi informasi yang sudah dirapikan oleh Groq AI LLM sehingga siap dihitung dan ditampilkan sebagai grafik pada dasbor.

_(Detail nama field dan skema lengkap kedua collection dapat dilihat pada Dokumen Teknis yang diberikan oleh developer)._

## 📁 Struktur Kode & Cara Mengoperasikan Setiap File

Berikut adalah daftar seluruh file di dalam repositori ini beserta fungsi dan cara mengoperasikannya:

| Nama File / Folder                                                              | Fungsi Utama                                                                                                                       | Cara Mengoperasikan                                                                                                       |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **`app.py`**                                                                    | **File Utama Dasbor.** Mengatur seluruh tampilan visual, grafik, filter data, dan interaksi pengguna di browser.                   | Jalankan dengan perintah: `streamlit run app.py`                                                                          |
| **`api.py`**                                                                    | **Antarmuka API / Webhook.** Bertugas menerima kiriman data dari sistem eksternal dan meneruskannya ke pipeline pemrosesan.        | Jalankan di terminal terpisah jika ingin menerima data otomatis dari luar (`python api.py`).                              |
| **`scripts/stt_script.py`**                                                     | **Pengubah Suara ke Teks (_Speech-to-Text_).** Mengonversi file rekaman suara menjadi teks tertulis.                               | Dipanggil otomatis oleh sistem, atau dapat diuji langsung melalui terminal: `python scripts/stt_script.py`                |
| **`scripts/llm_prompting.py`**                                                  | **Otak Analisis AI (Groq LLM).** Mengirim teks ke Groq AI beserta instruksi (_prompt_) khusus untuk mengekstrak poin-poin penting. | Dipanggil otomatis saat pemrosesan data berlangsung.                                                                      |
| **`scripts/etl_script.py`**                                                     | **Pemroses Data (_Extract, Transform, Load_).** Membersihkan data hasil AI dan mengunggahnya ke 2 collection di Firebase.          | Jalankan manual jika ingin memproses ulang tumpukan data: `python scripts/etl_script.py`                                  |
| **`scripts/synthetic_dataset_generator.py`**                                    | **Pembuat Data Simulasi.** Membuat data buatan/sintetis secara acak untuk mengisi database saat demo atau pengujian.               | **Jangan dijalankan pada database asli!** Hanya digunakan saat pengujian: `python scripts/synthetic_dataset_generator.py` |
| **`requirements.txt`**                                                          | **Daftar Pustaka.** Berisi daftar paket Python yang wajib diinstal agar kode berjalan.                                             | Dijalankan sekali di awal dengan perintah: `pip install -r requirements.txt`                                              |
| **`.streamlit/config.toml`**                                                    | **Pengaturan Tema Dasbor.** Mengatur warna, font, dan tampilan bawaan Streamlit.                                                   | Berjalan otomatis saat `app.py` dibuka (tidak perlu dijalankan manual).                                                   |
| **`.firebaserc`, `firebase.json`, `firestore.rules`, `firestore.indexes.json`** | **Konfigurasi Database Firebase.** Mengatur koneksi proyek Firebase dan aturan izin baca/tulis database.                           | Digunakan oleh administrator saat melakukan pengaturan atau pembaruan aturan di Firebase Console.                         |
| **`.gitignore`**                                                                | **Pelindung Keamanan.** Mencegah file rahasia (kunci API & kredensial) ikut terunggah ke GitHub.                                   | Bekerja otomatis di latar belakang saat menggunakan Git.                                                                  |

## 🎯 Saran Implementasi Nyata (_Production_) untuk Karla Bionics

Agar sistem ini dapat digunakan secara resmi, aman, dan berkelanjutan untuk kebutuhan operasional nyata perusahaan **Karla Bionics**, berikut adalah langkah-langkah transisi yang sangat disarankan:

1. **Buat Repositori Baru (Clone & Re-upload)**

   Jika tim internal atau developer penerus di Karla Bionics ingin melanjutkan pengembangan kode ini, **sangat disarankan untuk melakukan _clone_ proyek ini lalu mengunggahnya ke repositori GitHub baru milik akun organisasi Karla Bionics**. Hal ini penting agar kendali penuh kode, pengaturan keamanan, dan riwayat pembaruan sepenuhnya menjadi hak milik perusahaan.

2. **Buat Akun Mandiri untuk Firebase & Groq AI**
   - **Groq AI:** Segera daftarkan akun perusahaan di [console.groq.com](https://console.groq.com), buat **API Key baru**, dan gantikan API Key sementara milik developer (mengingat masa aktifnya hanya 10 hari).

   - **Firebase:** Buat proyek Firebase baru menggunakan email resmi Karla Bionics, aktifkan **Cloud Firestore**, lalu unduh file kredensial _Service Account_ yang baru.

3. **Bersihkan Data Sintetis Sebelum Penggunaan Asli**

   Pastikan seluruh dokumen simulasi di dalam **2 Collection Firestore** sudah dihapus bersih, dan jangan menjalankan ulang file `synthetic_dataset_generator.py` pada database _production_ agar data perusahaan tidak tercampur dengan data palsu.

4. **Perketat Aturan Keamanan Database (`firestore.rules`)**

   Pada tahap demonstrasi, aturan akses database biasanya dibuat longgar untuk memudahkan pengujian. Sebelum digunakan secara luas, pastikan aturan pada `firestore.rules` diperbarui agar hanya aplikasi atau pengguna terautentikasi yang diizinkan membaca dan menulis data.

5. **Publikasikan ke Server Cloud (_Deployment_)**

   Agar dasbor dapat diakses oleh tim manajemen Karla Bionics kapan saja melalui tautan website tanpa harus menyalakan komputer lokal terus-menerus, unggah proyek ini ke layanan _cloud_ seperti **Streamlit Community Cloud** (gratis/mudah terhubung dengan GitHub), **Google Cloud Run**, atau **VPS internal perusahaan**.

## 📞 Kontak & Bantuan Teknis

Untuk mendapatkan **Dokumen Teknis lengkap**, **paket file kredensial sementara**, atau panduan serah terima sistem, silakan hubungi developer / pemilik repositori ini secara langsung.
