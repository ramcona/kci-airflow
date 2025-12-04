# Checklist Monitoring Proyek

Gunakan checklist ini untuk memantau fitur yang telah diimplementasikan oleh Gemini CLI.

## 1. Setup Infrastruktur
- [x] Konfigurasi `docker-compose.yml` dengan semua service (webapp, 3x postgres, 2x airflow).
- [x] Membuat `Dockerfile.webapp` untuk aplikasi Node.js.
- [x] Menyiapkan file `.env.example` untuk variabel lingkungan.
- [x] Menyediakan `package.json` dengan semua dependensi yang dibutuhkan.

## 2. Fitur Web App (Node.js/Express)
- [x] Implementasi Autentikasi Admin (Login/Logout) dengan session.
- [x] Halaman Dashboard dengan statistik ringkas.
- [x] Fitur CRUD (Create, Read, Update, Delete) untuk Manajemen Konfigurasi.
- [x] Seeder untuk import data awal dari `data_table_need_to_archive.csv`.
- [x] Seeder untuk membuat user admin default.
- [x] Halaman Activity Logs untuk menampilkan riwayat aktivitas.
- [x] Desain UI/UX menggunakan Bootstrap 5 yang profesional.
- [x] Proteksi halaman admin menggunakan middleware.

## 3. Fitur Airflow DAG (Python)
- [x] DAG dijadwalkan untuk berjalan setiap hari (`@daily`).
- [x] DAG membaca konfigurasi aktif dari database aplikasi.
- [x] DAG melakukan pengecekan koneksi ke semua database.
- [x] Logika untuk sinkronisasi skema (membuat tabel jika tidak ada di tujuan).
- [x] Proses pemindahan data dari DB Main ke DB Archive.
- [x] Implementasi validasi data dengan membandingkan jumlah baris.
- [x] Logika penghapusan data (Purging) yang aman (hanya jika validasi sukses).
- [x] Pelaporan status (Success/Failed) ke tabel `activity_logs` di database aplikasi.
- [x] Penanganan error (Error Handling) yang robust.

## 4. Dokumentasi & Testing
- [x] Membuat file `README.md` yang komprehensif.
- [x] `README.md` berisi cara instalasi, setup Docker, dan menjalankan migrasi/seeder.
- [x] `README.md` menjelaskan arsitektur sistem.
- [ ] Aturan untuk backup database (disarankan untuk ditambahkan).
- [ ] Skenario testing untuk validasi end-to-end (manual/otomatis).

## 5. Lain-lain
- [x] Semua kode, UI, dan dokumentasi menggunakan Bahasa Indonesia.
