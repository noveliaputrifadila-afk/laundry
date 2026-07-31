# APLIKASI PENGELOLAAN JASA LAUNDRY
## Laundry Management System

Aplikasi Pengelolaan Jasa Laundry adalah aplikasi berbasis web yang digunakan untuk membantu pengelolaan kegiatan operasional usaha laundry secara terintegrasi.

Aplikasi mencakup proses registrasi pelanggan, pembuatan pesanan, penerimaan dan pemeriksaan barang, perhitungan biaya, penugasan Petugas Laundry, pengerjaan laundry, pembayaran, invoice, monitoring status, notifikasi, rating dan ulasan, serta laporan pesanan dan pendapatan.

Aplikasi ini dikembangkan menggunakan framework **Django** untuk memenuhi tugas **Ujian Akhir Semester Mata Kuliah Web Programming Kelas A Tahun Akademik 2025/2026**.

---

## 1. Informasi Proyek

| Keterangan | Isi |
|---|---|
| Nama aplikasi | Aplikasi Pengelolaan Jasa Laundry |
| Nama lain | Laundry Management System |
| Mata kuliah | Web Programming |
| Kelas | A |
| Kelompok | 2 |
| Tahun akademik | 2025/2026 |
| Framework | Django |
| Database | SQLite |
| Status repository | Public |

---

## 2. Anggota Kelompok

| No. | Nama | NIM | Username GitHub |
|---:|---|---|---|
| 1 | Novelia Putri Fadila | 2421400028 | noveliaputrifadila-afk |
| 2 | Ifatul Hasanah | 2421400067 | ifatul252 |
| 3 | Amanda Puspita Sari | 2421400029 | amanda933 |
| 4 | Salma Fatih Risqiah | 2421400119 | salmafatihriskiah-rgb |

---

## 3. Pembagian Tugas Anggota

Pembagian tugas harus sesuai dengan pekerjaan yang benar-benar dilakukan dan dapat dibuktikan melalui riwayat commit GitHub.

| Nama | Pembagian Tugas |
|---|---|
| Novelia Putri Fadila | Menganalisis kebutuhan dan alur aplikasi; merancang database; mengembangkan dan mengintegrasikan sebagian besar modul Administrator, Kasir, Petugas Laundry, dan Pelanggan; memperbaiki error; mengembangkan proses pesanan, pemeriksaan, pembayaran, notifikasi, invoice, dan laporan; mengelola repository GitHub; melakukan pengujian; serta menyusun laporan. |
| Ifatul Hasanah | Mengembangkan dan menguji modul Pelanggan, meliputi registrasi, dashboard pelanggan, pembuatan pesanan, tracking, pembayaran, invoice, notifikasi, rating, dan ulasan; membantu memperbaiki tampilan halaman pelanggan; aktif membantu mencari penyebab dan solusi ketika terjadi error, ikut berdiskusi dalam menentukan alur dan perbaikan fitur; memberikan tanggapan, masukan, dan pertimbangan terhadap pendapat anggota utama; serta membantu penyuntingan dan pemeriksaan laporan. |
| Amanda Puspita Sari| Mengikuti diskusi kelompok, memahami gambaran umum aplikasi, memberikan masukan umum terhadap tampilan dan alur penggunaan, serta membantu meninjau hasil akhir aplikasi sebelum demonstrasi. |
| Salma Fatih Risqiah | Mengikuti diskusi kelompok, memahami alur utama aplikasi, membantu memeriksa kelengkapan dokumentasi dan tampilan laporan, serta mengikuti persiapan demonstrasi. |


---

## 4. Repository GitHub

Repository aplikasi:

```[Repository aplikasi](https://github.com/noveliaputrifadila-afk/laundry)

```

Riwayat commit:

```
[Riwayat Commit Repository](https://github.com/noveliaputrifadila-afk/laundry/commits/main/)
```


Ketentuan repository:

- Repository wajib bersifat **Public**.
- Repository harus dapat dibuka tanpa permintaan izin.
- Repository berisi seluruh source code aplikasi yang dipresentasikan.
- Source code di GitHub harus sama dengan aplikasi yang didemonstrasikan.
- Setiap anggota harus memiliki commit yang bermakna.
- Repository wajib memiliki `README.md` dan `requirements.txt`.
- Repository harus tetap Public sampai proses penilaian selesai.

---

## 5. Latar Belakang

Usaha laundry memiliki berbagai proses yang harus dikelola, seperti pencatatan pelanggan, layanan, barang, pesanan, pemeriksaan berat, pembayaran, proses pencucian, penyerahan barang, dan pembuatan laporan.

Jika seluruh proses masih dilakukan secara manual menggunakan buku atau spreadsheet sederhana, dapat terjadi kesalahan pencatatan, kehilangan data, perhitungan biaya yang tidak sesuai, keterlambatan pelayanan, serta kesulitan mengetahui perkembangan pesanan.

Aplikasi Pengelolaan Jasa Laundry dikembangkan untuk membantu seluruh proses tersebut agar lebih terstruktur, cepat, mudah dipantau, dan tersimpan dalam satu sistem.

---

## 6. Permasalahan yang Diselesaikan

Aplikasi ini membantu menyelesaikan beberapa permasalahan berikut:

- Kesalahan pencatatan data pelanggan dan pesanan.
- Kesulitan mengelola layanan, jenis barang, tarif, promo, dan area layanan.
- Kesulitan menentukan berat aktual dan total biaya pesanan.
- Kesulitan membagi pekerjaan kepada Petugas Laundry.
- Pelanggan kesulitan mengetahui perkembangan proses laundry.
- Pemeriksaan pembayaran dan bukti pembayaran belum terstruktur.
- Riwayat perubahan status pesanan sulit ditelusuri.
- Pembuatan invoice masih dilakukan secara manual.
- Pembuatan laporan pesanan dan pendapatan memerlukan waktu lama.
- Informasi penting belum dapat disampaikan dengan cepat kepada pengguna.

---

## 7. Sasaran Pengguna

Aplikasi memiliki empat jenis pengguna:

1. **Administrator**
2. **Kasir**
3. **Petugas Laundry**
4. **Pelanggan**

Setiap pengguna hanya dapat mengakses menu dan fitur sesuai hak aksesnya.

---

## 8. Fitur Administrator

Administrator dapat:

- Login dan logout.
- Melihat dashboard Administrator.
- Melihat ringkasan operasional.
- Mengelola akun Administrator.
- Mengelola akun Kasir.
- Mengelola akun Petugas Laundry.
- Mengelola akun Pelanggan.
- Mengaktifkan atau menonaktifkan akun pengguna.
- Mengelola kategori layanan.
- Mengelola layanan laundry.
- Mengelola jenis barang.
- Mengelola tarif.
- Mengelola promo.
- Mengelola metode pembayaran.
- Mengelola area layanan antar-jemput.
- Melihat seluruh pesanan.
- Melihat data pembayaran.
- Melihat invoice.
- Memantau proses laundry.
- Melihat kendala laundry.
- Melihat rating dan ulasan pelanggan.
- Melihat laporan pesanan.
- Melihat laporan pendapatan.
- Memfilter laporan.
- Mengekspor laporan dalam format CSV.
- Melihat log aktivitas.
- Mengelola pengaturan sistem.
- Melihat notifikasi Administrator.

---

## 9. Fitur Kasir

Kasir dapat:

- Login dan logout.
- Melihat dashboard Kasir.
- Melihat daftar pesanan pelanggan.
- Membuat pesanan melalui Kasir.
- Menerima barang pelanggan.
- Melakukan pemeriksaan barang.
- Memeriksa jenis, jumlah, dan kondisi barang.
- Memasukkan berat aktual untuk layanan kiloan.
- Memeriksa jumlah barang untuk layanan satuan.
- Menentukan harga dan total biaya akhir.
- Menambahkan biaya tambahan jika diperlukan.
- Menambahkan catatan hasil pemeriksaan.
- Menerima atau menolak pesanan.
- Menentukan Petugas Laundry.
- Memeriksa pembayaran.
- Memverifikasi bukti pembayaran.
- Memperbarui status pembayaran.
- Melihat dan mencetak invoice.
- Mencatat barang telah diterima pelanggan.
- Menyelesaikan pesanan setelah pembayaran lunas.
- Menerima notifikasi pesanan baru dan aktivitas penting.

---

## 10. Fitur Petugas Laundry

Petugas Laundry dapat:

- Login dan logout.
- Melihat dashboard Petugas Laundry.
- Melihat daftar tugas.
- Menerima notifikasi tugas baru.
- Melihat detail layanan dan barang.
- Melihat hasil pemeriksaan Kasir.
- Memperbarui status proses laundry.
- Melihat riwayat pengerjaan.
- Melaporkan kendala selama proses laundry.
- Mengubah status menjadi siap diambil.
- Mengubah status menjadi siap diantar.
- Memantau tugas yang belum dikerjakan, sedang diproses, dan selesai.

---

## 11. Fitur Pelanggan

Pelanggan dapat:

- Melakukan registrasi akun.
- Login langsung setelah registrasi berhasil.
- Logout.
- Melihat dashboard Pelanggan.
- Melihat daftar layanan laundry.
- Membuat pesanan.
- Memilih cara barang masuk.
- Memilih cara barang dikembalikan.
- Memilih area layanan.
- Memilih layanan dan jenis barang.
- Memasukkan jumlah barang.
- Menggunakan promo.
- Memilih metode pembayaran.
- Menambahkan catatan pesanan.
- Melihat daftar pesanan.
- Melihat detail pesanan.
- Melacak perkembangan proses laundry.
- Melihat hasil pemeriksaan Kasir.
- Melihat total biaya akhir.
- Melakukan pembayaran.
- Mengunggah bukti pembayaran.
- Melihat status pembayaran.
- Melihat dan mencetak invoice.
- Melihat notifikasi.
- Melihat badge jumlah notifikasi yang belum dibaca.
- Memberikan rating dan ulasan setelah pesanan selesai.

---

## 12. Alur Utama Aplikasi

1. Pelanggan melakukan registrasi.
2. Sistem memvalidasi data registrasi.
3. Akun pelanggan langsung aktif setelah registrasi berhasil.
4. Pelanggan login menggunakan username dan password.
5. Pelanggan membuat pesanan laundry.
6. Pelanggan memilih cara barang masuk, yaitu diantar ke outlet atau dijemput.
7. Pelanggan memilih cara barang dikembalikan, yaitu diambil sendiri atau diantar.
8. Pelanggan memilih layanan, jenis barang, jumlah barang, promo, dan metode pembayaran.
9. Sistem membuat kode pesanan dan menyimpan data.
10. Status awal menjadi **Menunggu Barang Diantar** atau **Menunggu Penjemputan**.
11. Setelah barang sampai di outlet, status berubah menjadi **Menunggu Pemeriksaan**.
12. Kasir memeriksa jenis, jumlah, kondisi, dan berat barang.
13. Kasir memasukkan berat aktual atau jumlah barang.
14. Sistem menghitung total biaya berdasarkan tarif, promo, biaya antar-jemput, dan biaya tambahan.
15. Kasir memilih Petugas Laundry.
16. Petugas Laundry menerima tugas.
17. Petugas memperbarui status pengerjaan secara bertahap.
18. Pelanggan memantau perkembangan melalui menu **Lacak Laundry**.
19. Pelanggan melakukan pembayaran.
20. Kasir memeriksa dan memverifikasi pembayaran.
21. Setelah proses selesai, status menjadi **Siap Diambil** atau **Siap Diantar**.
22. Jika barang diantar, status dapat berubah menjadi **Dalam Pengantaran**.
23. Barang diserahkan atau diantar kepada pelanggan.
24. Pesanan dinyatakan **Selesai** setelah pembayaran lunas dan barang diterima pelanggan.
25. Pelanggan dapat memberikan rating dan ulasan.
26. Administrator dapat melihat laporan pesanan dan pendapatan.

---

## 13. Status Pesanan

Status pesanan yang digunakan:

- Menunggu Barang Diantar
- Menunggu Penjemputan
- Menunggu Pemeriksaan
- Menunggu Petugas Tersedia
- Menunggu Antrian
- Dicuci
- Dikeringkan
- Disetrika
- Dilipat
- Dikemas
- Siap Diambil
- Siap Diantar
- Dalam Pengantaran
- Selesai
- Ditolak
- Dibatalkan

---

## 14. Status Pembayaran

Status pembayaran yang digunakan:

- Belum Dibayar
- Menunggu Verifikasi
- Dibayar Sebagian atau DP
- Lunas
- Gagal
- Dikembalikan

Pesanan hanya dapat dinyatakan selesai apabila pembayaran telah lunas dan barang telah diterima pelanggan.

---

## 15. Sistem Notifikasi

Notifikasi diberikan pada aktivitas penting, seperti:

- Pesanan baru untuk Kasir.
- Tugas baru untuk Petugas Laundry.
- Pesanan berhasil dibuat.
- Pemeriksaan barang selesai.
- Total biaya telah ditentukan.
- Pembayaran menunggu verifikasi.
- Pembayaran berhasil atau ditolak.
- Pesanan siap diambil.
- Pesanan siap diantar.
- Pesanan sedang dalam pengantaran.
- Pesanan selesai.
- Pesanan ditolak.
- Pesanan mengalami kendala.

Jumlah notifikasi yang belum dibaca ditampilkan dalam bentuk badge pada menu **Notifikasi**.

Status seperti Dicuci, Dikeringkan, Disetrika, dan Dilipat tetap dapat dipantau melalui halaman **Lacak Laundry** tanpa harus menghasilkan notifikasi pada setiap tahap.

---

## 16. Validasi Sistem

### Validasi Akun

- Username tidak boleh sama dengan pengguna lain.
- Email harus menggunakan format yang benar.
- Nomor HP harus menggunakan format yang sesuai.
- Password dan konfirmasi password harus sama.
- Pengguna yang tidak aktif tidak dapat login.
- Pengguna diarahkan ke dashboard sesuai role.

### Validasi Data Master

- Nama data tidak boleh kosong.
- Harga dan biaya tidak boleh bernilai negatif.
- Tanggal akhir tidak boleh lebih awal dari tanggal mulai.
- Promo hanya dapat digunakan selama periode aktif.
- Nilai diskon harus sesuai ketentuan.
- Metode pembayaran harus aktif agar dapat digunakan.

### Validasi Pesanan

- Pelanggan harus login sebelum membuat pesanan.
- Pesanan harus memiliki minimal satu detail barang.
- Jumlah barang harus lebih dari nol.
- Layanan harus berstatus aktif.
- Cara barang masuk dan keluar wajib dipilih.
- Area dan alamat wajib diisi jika menggunakan layanan antar-jemput.
- Pelanggan tidak memasukkan berat aktual.
- Berat aktual ditentukan oleh Kasir setelah pemeriksaan.

### Validasi Pemeriksaan

- Pesanan harus berada pada status yang dapat diperiksa.
- Berat aktual harus lebih dari nol untuk layanan kiloan.
- Jumlah barang harus lebih dari nol untuk layanan satuan.
- Harga dan biaya tambahan tidak boleh negatif.
- Pesanan harus memiliki Petugas Laundry sebelum diproses.
- Alasan penolakan wajib dicatat jika pesanan ditolak.

### Validasi Pembayaran

- Jumlah pembayaran harus lebih dari nol.
- Jumlah pembayaran tidak boleh melebihi sisa tagihan.
- Bukti pembayaran dapat diwajibkan untuk pembayaran non-tunai.
- Status lunas diberikan setelah pembayaran memenuhi total tagihan.
- Pesanan tidak dapat diselesaikan jika pembayaran belum lunas.

### Validasi Hak Akses

- Administrator hanya dapat mengakses menu Administrator.
- Kasir hanya dapat mengakses menu Kasir.
- Petugas Laundry hanya dapat mengakses menu Petugas.
- Pelanggan hanya dapat mengakses menu Pelanggan.
- Akses di luar role ditolak atau dialihkan oleh sistem.

---

## 17. Teknologi yang Digunakan

| Teknologi | Kegunaan |
|---|---|
| Python 3.14.3 | Bahasa pemrograman utama |
| Django 6.0.7 | Framework aplikasi web |
| HTML | Struktur halaman |
| CSS | Pengaturan tampilan |
| Bootstrap 5.3.3 | Antarmuka dan responsivitas |
| Bootstrap Icons 1.11.3 | Ikon antarmuka |
| JavaScript | Interaksi halaman |
| SQLite | Database pengembangan |
| Git | Version control |
| GitHub | Repository dan kolaborasi |

Daftar dependency lengkap tersedia pada file `requirements.txt`.

---

## 18. Struktur Utama Proyek

```text
laundry/
├── administrator/
├── kasir/
├── pelanggan/
├── petugaslaundry/
├── laundry/
├── static/
├── templates/
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

Keterangan:

- `administrator/` berisi model utama dan fitur Administrator.
- `kasir/` berisi fitur pemeriksaan, pembayaran, invoice, dan transaksi.
- `pelanggan/` berisi fitur registrasi, pesanan, tracking, pembayaran, notifikasi, dan rating.
- `petugaslaundry/` berisi fitur tugas dan pembaruan status laundry.
- `laundry/` berisi konfigurasi utama project Django.
- `templates/` berisi seluruh file tampilan HTML.
- `static/` berisi CSS, JavaScript, gambar, dan aset.
- `requirements.txt` berisi daftar dependency.
- `.gitignore` berisi daftar file yang tidak disimpan ke repository.
- `manage.py` digunakan untuk menjalankan perintah Django.

---

## 19. Persyaratan Sistem

Sebelum menjalankan aplikasi, pastikan perangkat memiliki:

- Python.
- Git.
- Web browser.
- Visual Studio Code atau code editor lainnya.
- Koneksi internet saat instalasi dependency.

---

## 20. Cara Instalasi

### 20.1 Clone Repository

```bash
git clone https://github.com/noveliaputrifadila-afk/laundry.git
```

### 20.2 Masuk ke Folder Proyek

```bash
cd laundry
```

### 20.3 Membuat Virtual Environment

```bash
python -m venv env
```

### 20.4 Mengaktifkan Virtual Environment

#### PowerShell

```powershell
.\env\Scripts\Activate.ps1
```

Jika PowerShell menolak eksekusi script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\env\Scripts\Activate.ps1
```

#### Git Bash

```bash
source env/Scripts/activate
```

#### Command Prompt

```cmd
env\Scripts\activate
```

### 20.5 Menginstal Dependency

```bash
pip install -r requirements.txt
```

### 20.6 Menjalankan Migration

```bash
python manage.py migrate
```

### 20.7 Membuat Superuser Jika Diperlukan

```bash
python manage.py createsuperuser
```

### 20.8 Memeriksa Konfigurasi

```bash
python manage.py check
```

Hasil yang diharapkan:

```text
System check identified no issues (0 silenced).
```

### 20.9 Menjalankan Server

```bash
python manage.py runserver
```

Aplikasi dapat dibuka melalui:

```http://localhost:8000/
```
---

## 21. Cara Menjalankan Aplikasi

Jalankan server:

```bash
python manage.py runserver
```

Buka aplikasi melalui browser:

```text
http://127.0.0.1:8000/
```

Untuk menghentikan server:

```text
Ctrl + C
```

---

## 22. Data Awal yang Perlu Disiapkan

Sebelum aplikasi didemonstrasikan, siapkan data:

- Akun Administrator.
- Akun Kasir.
- Akun Petugas Laundry.
- Akun Pelanggan.
- Kategori layanan.
- Layanan laundry.
- Jenis barang.
- Tarif layanan.
- Promo.
- Metode pembayaran.
- Area layanan.
- Pesanan contoh.
- Pembayaran contoh.
- Invoice.
- Riwayat status.
- Rating dan ulasan.

Data contoh harus logis dan mendekati kondisi nyata usaha laundry.

---

## 23. Akun Pengujian

Gunakan akun khusus pengujian yang benar-benar tersedia pada database demonstrasi.

| Role | Username | Password |
|---|---|---|
| Administrator | admin | admin123 |
| Kasir | hasanahmaula | kasir123 |
| Petugas Laundry | dianasinta | petugasdiana123 |
| Pelanggan | melastianggraeni | mawarmelati12 |


---

## 24. Pengujian Aplikasi

| No. | Fitur | Skenario | Hasil yang Diharapkan | Status |
|---:|---|---|---|---|
| 1 | Login | Username dan password benar | Masuk ke dashboard sesuai role | Berhasil |
| 2 | Login | Password salah | Pesan kesalahan tampil | Berhasil |
| 3 | Registrasi | Data pelanggan valid | Akun dibuat dan langsung aktif | Berhasil |
| 4 | Tambah Layanan | Data layanan valid | Data tersimpan | Berhasil |
| 5 | Tambah Tarif | Harga negatif | Validasi ditampilkan | Berhasil |
| 6 | Tambah Promo | Periode tidak valid | Data ditolak | Berhasil |
| 7 | Pemesanan | Data pesanan lengkap | Pesanan dibuat | Berhasil |
| 8 | Penerimaan Barang | Barang diterima outlet | Status menjadi Menunggu Pemeriksaan | Berhasil |
| 9 | Pemeriksaan | Kasir mengisi berat dan harga | Total biaya dihitung | Berhasil |
| 10 | Penugasan | Kasir menentukan Petugas | Tugas masuk ke akun Petugas | Berhasil |
| 11 | Status Laundry | Petugas mengubah status | Status dan riwayat berubah | Berhasil |
| 12 | Pembayaran | Jumlah sesuai tagihan | Status menjadi lunas | Berhasil |
| 13 | Invoice | Cetak invoice | Invoice berhasil dibuat | Berhasil |
| 14 | Notifikasi | Ada aktivitas penting | Notifikasi dan badge tampil | Berhasil |
| 15 | Penyelesaian | Lunas dan barang diterima | Pesanan menjadi selesai | Berhasil |
| 16 | Hak Akses | Pelanggan membuka halaman Admin | Akses ditolak | Berhasil |
| 17 | Rating | Pelanggan memberi ulasan | Rating tersimpan | Berhasil |
| 18 | Laporan | Filter tanggal dipilih | Data laporan tampil | Berhasil |
| 19 | Export CSV | Tombol export dipilih | File CSV dibuat | Berhasil |

---

## 25. Sumber dan Referensi

Sumber yang digunakan:

- Dokumentasi Django: `https://docs.djangoproject.com/`
- Dokumentasi Python: `https://docs.python.org/`
- Dokumentasi Bootstrap: `https://getbootstrap.com/docs/`
- Bootstrap Icons: `https://icons.getbootstrap.com/`
- Materi perkuliahan Web Programming.
- Referensi atau tutorial lain yang benar-benar digunakan kelompok.

Tambahkan sumber lain jika digunakan dalam pengembangan aplikasi.

---

## 26. Kelebihan Aplikasi

- Memiliki empat hak akses pengguna.
- Mengelola proses laundry dari awal sampai akhir.
- Mendukung pemeriksaan berat dan harga akhir oleh Kasir.
- Memiliki pembagian tugas kepada Petugas Laundry.
- Memiliki tracking status pesanan.
- Memiliki notifikasi dan badge belum dibaca.
- Mendukung pembayaran dan verifikasi bukti pembayaran.
- Menyediakan invoice.
- Menyediakan rating dan ulasan.
- Menyediakan laporan dan export CSV.
- Memiliki validasi dan pembatasan hak akses.
- Menggunakan tampilan responsif berbasis Bootstrap.

---

## 27. Keterbatasan Aplikasi

- Pembayaran masih diverifikasi secara manual.
- Belum terhubung dengan payment gateway.
- Notifikasi belum terintegrasi dengan WhatsApp atau email.
- Database pengembangan masih menggunakan SQLite.
- Belum tersedia aplikasi Android atau iOS.
- Penjemputan dan pengantaran belum menggunakan GPS.
- Backup database belum dilakukan otomatis.

---

## 28. Saran Pengembangan

- Menambahkan payment gateway.
- Menambahkan notifikasi WhatsApp dan email.
- Mengembangkan aplikasi versi mobile.
- Menggunakan PostgreSQL atau MySQL untuk produksi.
- Menambahkan backup database otomatis.
- Menambahkan dashboard statistik dan grafik.
- Menambahkan pelacakan petugas antar-jemput.
- Menambahkan fitur komplain pelanggan.
- Menambahkan pengelolaan stok bahan laundry.
- Menambahkan sistem poin dan loyalitas pelanggan.

---

## 29. Catatan Penting

- Akun pelanggan langsung aktif setelah registrasi berhasil.
- Pelanggan tidak perlu menunggu verifikasi Administrator.
- Pelanggan tidak memasukkan berat aktual saat membuat pesanan.
- Berat aktual dan total biaya akhir ditentukan oleh Kasir.
- Status proses dapat dipantau melalui menu Lacak Laundry.
- Notifikasi diberikan pada aktivitas penting.
- Pesanan hanya selesai setelah pembayaran lunas dan barang diterima pelanggan.
- Pembayaran masih dilakukan secara manual.
- Repository GitHub wajib bersifat Public.
- Source code di repository harus sama dengan aplikasi yang dipresentasikan.
- Seluruh anggota wajib memahami alur dan source code aplikasi.