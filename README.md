# Sistem Otomasi Pengarsipan Data Enterprise

Sistem ini adalah aplikasi web yang dibangun dengan Node.js (Express.js) untuk memonitor dan mengonfigurasi aturan pengarsipan data dari database utama ke database arsip. Proses pengarsipan dieksekusi secara otomatis oleh Apache Airflow.

## Arsitektur

Sistem ini terdiri dari beberapa komponen yang berjalan di dalam kontainer Docker:

1.  **`webapp`**: Aplikasi Node.js/Express untuk antarmuka pengguna (UI).
2.  **`postgres_app`**: Database PostgreSQL untuk menyimpan konfigurasi, user, dan log aktivitas.
3.  **`postgres_main`**: Simulasi database utama (sumber data) yang akan diarsipkan.
4.  **`postgres_archive`**: Simulasi database arsip (tujuan data).
5.  **`airflow-webserver`**: Antarmuka web Apache Airflow untuk memonitor DAG.
6.  **`airflow-scheduler`**: Komponen Airflow yang bertanggung jawab menjadwalkan dan menjalankan DAG.

## Prasyarat

-   Docker & Docker Compose
-   Sistem Operasi: macOS (diuji pada macOS)

## Instalasi & Setup (macOS)

### 1. Clone Repository

(Asumsikan kode ini ada di dalam sebuah git repository)
```bash
git clone <url_repository>
cd app-maintenace
```

### 2. Konfigurasi Environment

Salin file `.env.example` menjadi `.env`.
```bash
cp .env.example .env
```
Tidak ada perubahan yang diperlukan pada file `.env` untuk menjalankan secara lokal dengan Docker, tetapi Anda bisa mengubah `SESSION_SECRET` untuk keamanan.

### 3. Jalankan Semua Services dengan Docker Compose

Buka terminal di root folder proyek dan jalankan perintah berikut:
```bash
docker-compose up --build -d
```
Perintah ini akan membangun image untuk `webapp` dan menjalankan semua kontainer di background. Proses ini mungkin memakan waktu beberapa menit saat pertama kali dijalankan.

### 4. Jalankan Migrasi & Seeder Database

Setelah kontainer berjalan, kita perlu membuat tabel dan mengisi data awal (admin user dan konfigurasi dari CSV).

Eksekusi perintah ini dari terminal Anda:
```bash
# Masuk ke dalam kontainer webapp
docker-compose exec webapp bash

# Setelah masuk ke shell di dalam kontainer, jalankan perintah berikut:
npm run db:migrate
npm run db:seed:all
exit
```

### 5. Setup Koneksi di Apache Airflow

Agar DAG Airflow bisa terhubung ke database, Anda perlu menambahkan koneksi melalui UI Airflow.

1.  Buka UI Airflow di browser: `http://localhost:8080`
2.  Login dengan username `airflow` dan password `airflow`.
3.  Navigasi ke **Admin -> Connections**.
4.  Buat 3 koneksi baru dengan tipe **Postgres**:
    -   **Koneksi untuk App DB:**
        -   **Conn Id:** `postgres_app`
        -   **Host:** `postgres_app`
        -   **Schema:** `app_db`
        -   **Login:** `admin`
        -   **Password:** `admin`
        -   **Port:** `5432`
    -   **Koneksi untuk Main DB:**
        -   **Conn Id:** `postgres_main`
        -   **Host:** `postgres_main`
        -   **Schema:** `main_db`
        -   **Login:** `admin`
        -   **Password:** `admin`
        -   **Port:** `5432`
    -   **Koneaksi untuk Archive DB:**
        -   **Conn Id:** `postgres_archive`
        -   **Host:** `postgres_archive`
        -   **Schema:** `archive_db`
        -   **Login:** `admin`
        -   **Password:** `admin`
        -   **Port:** `5432`

### 6. Aktifkan DAG di Airflow

1.  Di UI Airflow, navigasi ke halaman **DAGs**.
2.  Cari DAG dengan nama `archive_automation_dag`.
3.  Aktifkan DAG tersebut dengan mengklik tombol toggle di sebelah kiri namanya.
4.  DAG akan berjalan sesuai jadwal (`@daily`) atau Anda bisa memicunya secara manual.

## Akses Aplikasi

-   **Web App (Sistem Arsip)**: `http://localhost:3000`
    -   **Email:** `admin@example.com`
    -   **Password:** `admin123`
-   **Apache Airflow UI**: `http://localhost:8080`
    -   **Username:** `airflow`
    -   **Password:** `airflow`

### 7. Konfigurasi SMTP untuk Notifikasi Email Kustom

Untuk mengaktifkan notifikasi email kustom pada keberhasilan atau kegagalan DAG, Anda perlu mengonfigurasi kredensial SMTP sebagai **Airflow Variables** di UI Airflow.

1.  **Akses Airflow UI:** Buka Airflow web UI Anda (`http://localhost:8080`).
2.  **Navigasi ke Admin -> Variables:** Di menu atas, pilih `Admin` lalu `Variables`.
3.  **Buat Variabel Baru:** Klik tombol `+` untuk setiap variabel berikut dan masukkan nilai yang sesuai dengan server SMTP Anda:

    *   **`SMTP_HOST`**:
        *   Key: `SMTP_HOST`
        *   Val: `host_smtp_anda.com` (contoh: `smtp.gmail.com`)
    *   **`SMTP_PORT`**:
        *   Key: `SMTP_PORT`
        *   Val: `587` (atau port server SMTP Anda, contoh: `465`)
    *   **`SMTP_USER`**:
        *   Key: `SMTP_USER`
        *   Val: `username_smtp_anda` (contoh: `email_anda@gmail.com`)
    *   **`SMTP_PASSWORD`**:
        *   Key: `SMTP_PASSWORD`
        *   Val: `password_smtp_anda` (gunakan "App Password" jika menggunakan Gmail dengan 2FA)
    *   **`SMTP_SENDER`**:
        *   Key: `SMTP_SENDER`
        *   Val: `airflow@domain_anda.com` (alamat email pengirim)
    *   **`SMTP_RECIPIENT`**:
        *   Key: `SMTP_RECIPIENT`
        *   Val: `email_penerima_notifikasi@domain.com` (alamat email penerima notifikasi)

    **Penting:** Pastikan untuk mengganti nilai placeholder dengan detail server SMTP Anda yang sebenarnya dan alamat email penerima yang diinginkan.