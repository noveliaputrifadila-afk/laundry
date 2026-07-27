# Laundry Management System

Laundry Management System adalah aplikasi berbasis web yang digunakan untuk mengelola kegiatan operasional jasa laundry, mulai dari registrasi pelanggan, pemesanan layanan, proses pencucian, pembayaran, hingga pembuatan laporan.

Aplikasi ini dikembangkan untuk memenuhi tugas mata kuliah **Web Programming**.

## Teknologi yang Digunakan

- Python
- Django
- HTML
- CSS
- Bootstrap
- JavaScript
- SQLite

## Hak Akses Pengguna

Aplikasi memiliki empat jenis pengguna:

1. Administrator
2. Kasir
3. Petugas Laundry
4. Pelanggan

## Fitur Administrator

Administrator memiliki akses untuk:

- Melihat dashboard dan ringkasan data
- Mengelola akun pengguna
- Memverifikasi akun pelanggan
- Mengelola kategori layanan
- Mengelola layanan laundry
- Mengelola tarif
- Mengelola promo
- Mengelola metode pembayaran
- Mengelola area layanan antar-jemput
- Melihat dan mengelola seluruh pesanan
- Melihat data pembayaran
- Melakukan monitoring proses laundry
- Melihat invoice
- Melihat laporan pesanan dan pendapatan
- Melihat log aktivitas
- Mengatur sistem

## Fitur Kasir

Kasir memiliki akses untuk:

- Melihat dashboard kasir
- Menginput pesanan pelanggan
- Mengelola data pelanggan
- Memeriksa pembayaran
- Memverifikasi pembayaran
- Melihat dan mencetak invoice
- Memantau transaksi pesanan

## Fitur Petugas Laundry

Petugas Laundry memiliki akses untuk:

- Melihat dashboard petugas
- Melihat pesanan yang ditugaskan
- Memperbarui status proses laundry
- Mencatat proses pengerjaan
- Menyelesaikan proses laundry
- Melakukan monitoring pesanan

## Fitur Pelanggan

Pelanggan memiliki akses untuk:

- Melakukan registrasi akun
- Login setelah diverifikasi administrator
- Melihat daftar layanan laundry
- Membuat pesanan
- Memilih layanan dan metode pembayaran
- Melihat daftar pesanan
- Melacak status pesanan
- Melakukan pembayaran
- Melihat invoice
- Melihat notifikasi

## Alur Aplikasi

1. Pelanggan melakukan registrasi menggunakan nomor HP dan email.
2. Administrator memeriksa dan memverifikasi akun pelanggan.
3. Pelanggan login setelah akun berhasil diverifikasi.
4. Pelanggan memilih layanan dan membuat pesanan laundry.
5. Kasir memeriksa data pesanan dan pembayaran.
6. Administrator atau kasir menentukan petugas laundry.
7. Petugas laundry memproses pesanan dan memperbarui status pengerjaan.
8. Pelanggan dapat melacak perkembangan pesanan.
9. Setelah proses selesai, pelanggan menerima informasi penyelesaian pesanan.
10. Administrator dapat melihat laporan pesanan dan pendapatan.

## Status Pesanan

Status pesanan yang digunakan dalam aplikasi antara lain:

- Menunggu konfirmasi
- Dikonfirmasi
- Dijemput
- Diterima
- Diproses
- Selesai
- Siap diambil atau dikirim
- Telah diterima pelanggan
- Dibatalkan

## Cara Menjalankan Aplikasi

### 1. Buka folder proyek

```bash
cd laundry
```

### 2. Aktifkan virtual environment

Untuk Windows:

```bash
env\Scripts\activate
```

### 3. Install Django

```bash
pip install django
```

### 4. Jalankan migrasi database

```bash
python manage.py migrate
```

### 5. Jalankan server

```bash
python manage.py runserver
```

### 6. Buka aplikasi

Buka alamat berikut melalui browser:

```text
http://127.0.0.1:8000/
```

## Struktur Utama Proyek

```text
laundry/
├── administrator/
├── kasir/
├── pelanggan/
├── petugaslaundry/
├── static/
├── templates/
├── laundry/
├── db.sqlite3
└── manage.py
```

Keterangan:

- `administrator` berisi fitur untuk pengguna Administrator.
- `kasir` berisi fitur untuk pengguna Kasir.
- `pelanggan` berisi fitur untuk pengguna Pelanggan.
- `petugaslaundry` berisi fitur untuk Petugas Laundry.
- `templates` berisi tampilan HTML.
- `static` berisi file CSS, JavaScript, dan aset aplikasi.
- `db.sqlite3` merupakan database aplikasi.
- `manage.py` digunakan untuk menjalankan perintah Django.

## Anggota Kelompok

| Nama | NIM | Pembagian Tugas |
|---|---|---|
| Novelia Putri Fadila | 2421400028| Tuliskan tugas yang dikerjakan |
| Ifatul Hasanah| 2421400067| Tuliskan tugas yang dikerjakan |
| Amanda Puspita | NIM Anggota 3 | Tuliskan tugas yang dikerjakan |

## Mata Kuliah

**Web Programming – Kelas A**

## Catatan

Akun Administrator, Kasir, dan Petugas Laundry dibuat oleh Administrator. Akun Pelanggan harus melalui proses verifikasi sebelum dapat digunakan untuk login.