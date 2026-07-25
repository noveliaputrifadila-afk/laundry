from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Model abstrak untuk mencatat waktu pembuatan dan perubahan data.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Dibuat pada",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Diubah pada",
    )

    class Meta:
        abstract = True


class User(AbstractUser):
    """
    Custom user untuk:
    1. Administrator
    2. Kasir
    3. Petugas Laundry
    4. Pelanggan
    """

    class Role(models.TextChoices):
        ADMINISTRATOR = "administrator", "Administrator"
        KASIR = "kasir", "Kasir"
        PETUGAS_LAUNDRY = "petugaslaundry", "Petugas Laundry"
        PELANGGAN = "pelanggan", "Pelanggan"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.PELANGGAN,
        db_index=True,
        verbose_name="Hak akses",
    )
    nomor_hp = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Nomor HP",
    )
    alamat = models.TextField(
        blank=True,
        verbose_name="Alamat",
    )
    foto = models.ImageField(
        upload_to="pengguna/foto/",
        blank=True,
        null=True,
        verbose_name="Foto",
    )
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Terverifikasi",
        help_text="Pelanggan harus diverifikasi administrator sebelum dapat login.",
    )
    verified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Waktu verifikasi",
    )
    verified_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pengguna_diverifikasi",
        verbose_name="Diverifikasi oleh",
    )

    # AbstractUser sudah memiliki field email, tetapi default-nya tidak unik.
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )

    class Meta:
        verbose_name = "Pengguna"
        verbose_name_plural = "Data Pengguna"
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} - {self.get_role_display()}"

    def save(self, *args, **kwargs):
        """
        Administrator, kasir, dan petugas laundry yang dibuat administrator
        langsung dianggap terverifikasi.

        Pelanggan tetap harus melalui proses verifikasi.
        """
        if self.role != self.Role.PELANGGAN and not self.is_verified:
            self.is_verified = True

            if self.verified_at is None:
                self.verified_at = timezone.now()

        # Sinkronkan role administrator dengan atribut Django admin.
        if self.role == self.Role.ADMINISTRATOR:
            self.is_staff = True

        super().save(*args, **kwargs)

    def verifikasi(self, administrator):
        """
        Memverifikasi akun pelanggan.
        """
        self.is_verified = True
        self.is_active = True
        self.verified_at = timezone.now()
        self.verified_by = administrator
        self.save(
            update_fields=[
                "is_verified",
                "is_active",
                "verified_at",
                "verified_by",
                "updated_at",
            ]
        )

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR

    @property
    def is_kasir(self):
        return self.role == self.Role.KASIR

    @property
    def is_petugas_laundry(self):
        return self.role == self.Role.PETUGAS_LAUNDRY

    @property
    def is_pelanggan(self):
        return self.role == self.Role.PELANGGAN


class KategoriLayanan(TimeStampedModel):
    nama = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nama kategori",
    )
    deskripsi = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    class Meta:
        verbose_name = "Kategori Layanan"
        verbose_name_plural = "Kategori Layanan"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class Layanan(TimeStampedModel):
    class Satuan(models.TextChoices):
        KILOGRAM = "kg", "Kilogram"
        ITEM = "item", "Item"
        PASANG = "pasang", "Pasang"
        METER = "meter", "Meter"
        TRANSAKSI = "transaksi", "Per Transaksi"

    kategori = models.ForeignKey(
        KategoriLayanan,
        on_delete=models.PROTECT,
        related_name="layanan",
        verbose_name="Kategori",
    )
    nama = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nama layanan",
    )
    kode = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Kode layanan",
    )
    satuan = models.CharField(
        max_length=20,
        choices=Satuan.choices,
        verbose_name="Satuan",
    )
    estimasi_hari = models.PositiveIntegerField(
        default=3,
        verbose_name="Estimasi pengerjaan",
        help_text="Estimasi pengerjaan dalam satuan hari.",
    )
    deskripsi = models.TextField(
        blank=True,
        verbose_name="Deskripsi",
    )
    is_express = models.BooleanField(
        default=False,
        verbose_name="Layanan express",
    )
    is_antar_jemput = models.BooleanField(
        default=False,
        verbose_name="Mendukung antar-jemput",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    class Meta:
        verbose_name = "Layanan"
        verbose_name_plural = "Data Layanan"
        ordering = ["kategori__nama", "nama"]

    def __str__(self):
        return f"{self.nama} ({self.get_satuan_display()})"

    @property
    def tarif_aktif(self):
        return self.tarif_set.filter(is_active=True).order_by("-tanggal_mulai").first()


class Tarif(models.Model):
    layanan = models.ForeignKey(
        Layanan,
        on_delete=models.PROTECT,
        related_name="tarif_set",
        verbose_name="Layanan",
    )

    harga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
        verbose_name="Harga",
    )

    tanggal_mulai = models.DateField(
        default=timezone.localdate,
        verbose_name="Tanggal mulai berlaku",
    )

    tanggal_selesai = models.DateField(
        blank=True,
        null=True,
        verbose_name="Tanggal selesai",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-tanggal_mulai",
            "-created_at",
        ]
        verbose_name = "Tarif"
        verbose_name_plural = "Tarif"

    def __str__(self):
        return (
            f"{self.layanan.nama} - "
            f"Rp{self.harga:,.0f}"
        )
    
class Promo(TimeStampedModel):
    class JenisDiskon(models.TextChoices):
        PERSENTASE = "persentase", "Persentase"
        NOMINAL = "nominal", "Nominal"

    kode = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Kode promo",
    )
    nama = models.CharField(
        max_length=150,
        verbose_name="Nama promo",
    )
    jenis_diskon = models.CharField(
        max_length=20,
        choices=JenisDiskon.choices,
        verbose_name="Jenis diskon",
    )
    nilai_diskon = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Nilai diskon",
    )
    maksimal_diskon = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Maksimal diskon",
    )
    minimal_transaksi = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Minimal transaksi",
    )
    layanan = models.ManyToManyField(
        Layanan,
        blank=True,
        related_name="promo",
        verbose_name="Berlaku untuk layanan",
        help_text="Kosongkan jika promo berlaku untuk semua layanan.",
    )
    tanggal_mulai = models.DateTimeField(
        verbose_name="Tanggal mulai",
    )
    tanggal_selesai = models.DateTimeField(
        verbose_name="Tanggal selesai",
    )
    kuota = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Kuota",
    )
    jumlah_digunakan = models.PositiveIntegerField(
        default=0,
        verbose_name="Jumlah digunakan",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    class Meta:
        verbose_name = "Promo"
        verbose_name_plural = "Data Promo"
        ordering = ["-tanggal_mulai"]

    def __str__(self):
        return f"{self.kode} - {self.nama}"

    def masih_berlaku(self):
        sekarang = timezone.now()

        if not self.is_active:
            return False

        if not self.tanggal_mulai <= sekarang <= self.tanggal_selesai:
            return False

        if self.kuota is not None and self.jumlah_digunakan >= self.kuota:
            return False

        return True

    def hitung_diskon(self, subtotal):
        subtotal = Decimal(subtotal)

        if not self.masih_berlaku():
            return Decimal("0.00")

        if subtotal < self.minimal_transaksi:
            return Decimal("0.00")

        if self.jenis_diskon == self.JenisDiskon.PERSENTASE:
            diskon = subtotal * self.nilai_diskon / Decimal("100")
        else:
            diskon = self.nilai_diskon

        if self.maksimal_diskon is not None:
            diskon = min(diskon, self.maksimal_diskon)

        return min(diskon, subtotal)


class MetodePembayaran(TimeStampedModel):
    nama = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nama metode",
    )
    nomor_rekening = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nomor rekening/akun",
    )
    atas_nama = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Atas nama",
    )
    instruksi = models.TextField(
        blank=True,
        verbose_name="Instruksi pembayaran",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    class Meta:
        verbose_name = "Metode Pembayaran"
        verbose_name_plural = "Metode Pembayaran"
        ordering = ["nama"]

    def __str__(self):
        return self.nama


class AreaLayanan(TimeStampedModel):
    nama_area = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nama area",
    )
    kode_pos = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Kode pos",
    )
    biaya_antar = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Biaya antar",
    )
    biaya_jemput = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Biaya jemput",
    )
    estimasi_menit = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Estimasi perjalanan",
        help_text="Estimasi perjalanan dalam menit.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif",
    )

    class Meta:
        verbose_name = "Area Layanan"
        verbose_name_plural = "Area Layanan Antar-Jemput"
        ordering = ["nama_area"]

    def __str__(self):
        return self.nama_area

    @property
    def total_biaya_antar_jemput(self):
        return self.biaya_antar + self.biaya_jemput


class Pesanan(TimeStampedModel):
    class JenisPengantaran(models.TextChoices):
        DATANG_SENDIRI = "datang_sendiri", "Datang Sendiri"
        JEMPUT = "jemput", "Dijemput"
        ANTAR = "antar", "Diantar"
        ANTAR_JEMPUT = "antar_jemput", "Antar dan Jemput"

    class StatusPesanan(models.TextChoices):
        MENUNGGU_KONFIRMASI = (
            "menunggu_konfirmasi",
            "Menunggu Konfirmasi Kasir",
        )
        DITERIMA = "diterima", "Diterima"
        DITOLAK = "ditolak", "Ditolak"
        MENUNGGU_ANTRIAN = "menunggu_antrian", "Menunggu Antrian"
        DICUCI = "dicuci", "Dicuci"
        DIKERINGKAN = "dikeringkan", "Dikeringkan"
        DISETRIKA = "disetrika", "Disetrika"
        DILIPAT = "dilipat", "Dilipat"
        DIKEMAS = "dikemas", "Dikemas"
        SIAP_DIAMBIL = "siap_diambil", "Siap Diambil"
        SIAP_DIANTAR = "siap_diantar", "Siap Diantar"
        DALAM_PENGANTARAN = "dalam_pengantaran", "Dalam Pengantaran"
        SELESAI = "selesai", "Selesai"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    class StatusPembayaran(models.TextChoices):
        BELUM_DIBAYAR = "belum_dibayar", "Belum Dibayar"
        MENUNGGU_VERIFIKASI = (
            "menunggu_verifikasi",
            "Menunggu Verifikasi",
        )
        DP = "dp", "Dibayar Sebagian"
        LUNAS = "lunas", "Lunas"
        GAGAL = "gagal", "Gagal"
        DIKEMBALIKAN = "dikembalikan", "Dikembalikan"

    kode_pesanan = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Kode pesanan",
    )
    pelanggan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pesanan_pelanggan",
        limit_choices_to={"role": User.Role.PELANGGAN},
        verbose_name="Pelanggan",
    )
    kasir = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pesanan_ditangani_kasir",
        limit_choices_to={"role": User.Role.KASIR},
        verbose_name="Kasir",
    )
    petugas_laundry = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pesanan_dikerjakan",
        limit_choices_to={"role": User.Role.PETUGAS_LAUNDRY},
        verbose_name="Petugas laundry",
    )
    promo = models.ForeignKey(
        Promo,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pesanan",
        verbose_name="Promo",
    )
    metode_pembayaran = models.ForeignKey(
        MetodePembayaran,
        on_delete=models.PROTECT,
        related_name="pesanan",
        verbose_name="Metode pembayaran",
    )
    area_layanan = models.ForeignKey(
        AreaLayanan,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pesanan",
        verbose_name="Area antar-jemput",
    )
    jenis_pengantaran = models.CharField(
        max_length=30,
        choices=JenisPengantaran.choices,
        default=JenisPengantaran.DATANG_SENDIRI,
        verbose_name="Metode penerimaan",
    )
    alamat_penjemputan = models.TextField(
        blank=True,
        verbose_name="Alamat penjemputan",
    )
    alamat_pengantaran = models.TextField(
        blank=True,
        verbose_name="Alamat pengantaran",
    )
    tanggal_penjemputan = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Tanggal penjemputan",
    )
    tanggal_pengambilan = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Tanggal pengambilan",
    )
    estimasi_selesai = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Estimasi selesai",
    )
    tanggal_selesai = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Tanggal selesai",
    )
    catatan_pelanggan = models.TextField(
        blank=True,
        verbose_name="Catatan pelanggan",
    )
    catatan_kasir = models.TextField(
        blank=True,
        verbose_name="Catatan kasir",
    )
    alasan_penolakan = models.TextField(
        blank=True,
        verbose_name="Alasan penolakan",
    )
    status = models.CharField(
        max_length=30,
        choices=StatusPesanan.choices,
        default=StatusPesanan.MENUNGGU_KONFIRMASI,
        db_index=True,
        verbose_name="Status pesanan",
    )
    status_pembayaran = models.CharField(
        max_length=30,
        choices=StatusPembayaran.choices,
        default=StatusPembayaran.BELUM_DIBAYAR,
        db_index=True,
        verbose_name="Status pembayaran",
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Subtotal",
    )
    diskon = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Diskon",
    )
    biaya_antar_jemput = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Biaya antar-jemput",
    )
    biaya_tambahan = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Biaya tambahan",
    )
    total_biaya = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Total biaya",
    )
    diterima_pelanggan = models.BooleanField(
        default=False,
        verbose_name="Sudah diterima pelanggan",
    )

    class Meta:
        verbose_name = "Pesanan"
        verbose_name_plural = "Data Pesanan"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["pelanggan", "status"]),
            models.Index(fields=["kasir", "status"]),
            models.Index(fields=["petugas_laundry", "status"]),
        ]

    def __str__(self):
        return f"{self.kode_pesanan} - {self.pelanggan.username}"

    def save(self, *args, **kwargs):
        if not self.kode_pesanan:
            self.kode_pesanan = self.generate_kode_pesanan()

        self.total_biaya = max(
            Decimal("0.00"),
            self.subtotal
            - self.diskon
            + self.biaya_antar_jemput
            + self.biaya_tambahan,
        )

        if (
            self.status == self.StatusPesanan.SELESAI
            and self.tanggal_selesai is None
        ):
            self.tanggal_selesai = timezone.now()

        super().save(*args, **kwargs)

    @staticmethod
    def generate_kode_pesanan():
        """
        Contoh hasil: LDR-20260724-00001
        """
        tanggal = timezone.localdate()
        prefix = f"LDR-{tanggal:%Y%m%d}"

        pesanan_terakhir = (
            Pesanan.objects.filter(kode_pesanan__startswith=prefix)
            .order_by("-kode_pesanan")
            .first()
        )

        if pesanan_terakhir:
            nomor_terakhir = int(pesanan_terakhir.kode_pesanan.split("-")[-1])
            nomor_baru = nomor_terakhir + 1
        else:
            nomor_baru = 1

        return f"{prefix}-{nomor_baru:05d}"

    def hitung_total(self, simpan=True):
        subtotal = sum(
            (detail.subtotal for detail in self.detail.all()),
            Decimal("0.00"),
        )

        self.subtotal = subtotal

        if self.promo:
            self.diskon = self.promo.hitung_diskon(subtotal)
        else:
            self.diskon = Decimal("0.00")

        total = (
            self.subtotal
            - self.diskon
            + self.biaya_antar_jemput
            + self.biaya_tambahan
        )

        self.total_biaya = max(total, Decimal("0.00"))

        if simpan:
            self.save(
                update_fields=[
                    "subtotal",
                    "diskon",
                    "total_biaya",
                    "updated_at",
                ]
            )

        return self.total_biaya

    @property
    def dapat_diselesaikan(self):
        return (
            self.status_pembayaran == self.StatusPembayaran.LUNAS
            and self.diterima_pelanggan
        )


class DetailPesanan(TimeStampedModel):
    pesanan = models.ForeignKey(
        Pesanan,
        on_delete=models.CASCADE,
        related_name="detail",
        verbose_name="Pesanan",
    )
    layanan = models.ForeignKey(
        Layanan,
        on_delete=models.PROTECT,
        related_name="detail_pesanan",
        verbose_name="Layanan",
    )
    nama_barang = models.CharField(
        max_length=150,
        verbose_name="Nama/detail barang",
    )
    jumlah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Berat/jumlah",
    )
    satuan = models.CharField(
        max_length=20,
        choices=Layanan.Satuan.choices,
        verbose_name="Satuan",
    )
    harga_satuan = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Harga satuan",
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Subtotal",
    )
    catatan = models.TextField(
        blank=True,
        verbose_name="Catatan khusus",
    )

    class Meta:
        verbose_name = "Detail Pesanan"
        verbose_name_plural = "Detail Pesanan"
        ordering = ["id"]

    def __str__(self):
        return f"{self.pesanan.kode_pesanan} - {self.nama_barang}"

    def save(self, *args, **kwargs):
        self.subtotal = self.jumlah * self.harga_satuan
        super().save(*args, **kwargs)


class RiwayatStatus(TimeStampedModel):
    pesanan = models.ForeignKey(
        Pesanan,
        on_delete=models.CASCADE,
        related_name="riwayat_status",
        verbose_name="Pesanan",
    )
    status_sebelumnya = models.CharField(
        max_length=30,
        choices=Pesanan.StatusPesanan.choices,
        blank=True,
        verbose_name="Status sebelumnya",
    )
    status_baru = models.CharField(
        max_length=30,
        choices=Pesanan.StatusPesanan.choices,
        verbose_name="Status baru",
    )
    diubah_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="perubahan_status_pesanan",
        verbose_name="Diubah oleh",
    )
    catatan = models.TextField(
        blank=True,
        verbose_name="Catatan",
    )

    class Meta:
        verbose_name = "Riwayat Status"
        verbose_name_plural = "Riwayat Status Pesanan"
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.pesanan.kode_pesanan} - "
            f"{self.get_status_baru_display()}"
        )


class Invoice(TimeStampedModel):
    class StatusInvoice(models.TextChoices):
        DRAFT = "draft", "Draft"
        DITERBITKAN = "diterbitkan", "Diterbitkan"
        LUNAS = "lunas", "Lunas"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    pesanan = models.OneToOneField(
        Pesanan,
        on_delete=models.CASCADE,
        related_name="invoice",
        verbose_name="Pesanan",
    )
    nomor_invoice = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        verbose_name="Nomor invoice",
    )
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="invoice_dibuat",
        limit_choices_to={"role": User.Role.KASIR},
        verbose_name="Dibuat oleh",
    )
    tanggal_terbit = models.DateTimeField(
        default=timezone.now,
        verbose_name="Tanggal terbit",
    )
    tanggal_jatuh_tempo = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Tanggal jatuh tempo",
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Total invoice",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusInvoice.choices,
        default=StatusInvoice.DRAFT,
        verbose_name="Status invoice",
    )
    catatan = models.TextField(
        blank=True,
        verbose_name="Catatan",
    )

    class Meta:
        verbose_name = "Invoice"
        verbose_name_plural = "Data Invoice"
        ordering = ["-tanggal_terbit"]

    def __str__(self):
        return self.nomor_invoice

    def save(self, *args, **kwargs):
        if not self.nomor_invoice:
            self.nomor_invoice = f"INV-{self.pesanan.kode_pesanan}"

        self.total = self.pesanan.total_biaya
        super().save(*args, **kwargs)


class Pembayaran(TimeStampedModel):
    class StatusPembayaran(models.TextChoices):
        MENUNGGU = "menunggu", "Menunggu Verifikasi"
        BERHASIL = "berhasil", "Berhasil"
        GAGAL = "gagal", "Gagal"
        DITOLAK = "ditolak", "Ditolak"
        DIKEMBALIKAN = "dikembalikan", "Dikembalikan"

    pesanan = models.ForeignKey(
        Pesanan,
        on_delete=models.PROTECT,
        related_name="pembayaran",
        verbose_name="Pesanan",
    )
    metode_pembayaran = models.ForeignKey(
        MetodePembayaran,
        on_delete=models.PROTECT,
        related_name="pembayaran",
        verbose_name="Metode pembayaran",
    )
    kode_pembayaran = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="Kode pembayaran",
    )
    jumlah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Jumlah pembayaran",
    )
    tanggal_pembayaran = models.DateTimeField(
        default=timezone.now,
        verbose_name="Tanggal pembayaran",
    )
    bukti_pembayaran = models.ImageField(
        upload_to="pembayaran/bukti/",
        blank=True,
        null=True,
        verbose_name="Bukti pembayaran",
    )
    status = models.CharField(
        max_length=20,
        choices=StatusPembayaran.choices,
        default=StatusPembayaran.MENUNGGU,
        verbose_name="Status",
    )
    diverifikasi_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pembayaran_diverifikasi",
        limit_choices_to={
            "role__in": [
                User.Role.ADMINISTRATOR,
                User.Role.KASIR,
            ]
        },
        verbose_name="Diverifikasi oleh",
    )
    diverifikasi_pada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Diverifikasi pada",
    )
    catatan = models.TextField(
        blank=True,
        verbose_name="Catatan",
    )

    class Meta:
        verbose_name = "Pembayaran"
        verbose_name_plural = "Data Pembayaran"
        ordering = ["-tanggal_pembayaran"]

    def __str__(self):
        return self.kode_pembayaran

    def save(self, *args, **kwargs):
        if not self.kode_pembayaran:
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S%f")
            self.kode_pembayaran = f"PAY-{timestamp}"

        super().save(*args, **kwargs)


class KendalaLaundry(TimeStampedModel):
    class StatusKendala(models.TextChoices):
        DILAPORKAN = "dilaporkan", "Dilaporkan"
        DITINDAKLANJUTI = "ditindaklanjuti", "Ditindaklanjuti"
        SELESAI = "selesai", "Selesai"

    pesanan = models.ForeignKey(
        Pesanan,
        on_delete=models.CASCADE,
        related_name="kendala",
        verbose_name="Pesanan",
    )
    dilaporkan_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kendala_dilaporkan",
        limit_choices_to={"role": User.Role.PETUGAS_LAUNDRY},
        verbose_name="Dilaporkan oleh",
    )
    judul = models.CharField(
        max_length=150,
        verbose_name="Judul kendala",
    )
    deskripsi = models.TextField(
        verbose_name="Deskripsi kendala",
    )
    status = models.CharField(
        max_length=30,
        choices=StatusKendala.choices,
        default=StatusKendala.DILAPORKAN,
        verbose_name="Status",
    )
    tanggapan_kasir = models.TextField(
        blank=True,
        verbose_name="Tanggapan kasir",
    )
    ditangani_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="kendala_ditangani",
        limit_choices_to={
            "role__in": [
                User.Role.ADMINISTRATOR,
                User.Role.KASIR,
            ]
        },
        verbose_name="Ditangani oleh",
    )

    class Meta:
        verbose_name = "Kendala Laundry"
        verbose_name_plural = "Kendala Laundry"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pesanan.kode_pesanan} - {self.judul}"


class Notifikasi(TimeStampedModel):
    class JenisNotifikasi(models.TextChoices):
        PESANAN = "pesanan", "Pesanan"
        STATUS = "status", "Perubahan Status"
        PEMBAYARAN = "pembayaran", "Pembayaran"
        KENDALA = "kendala", "Kendala"
        SISTEM = "sistem", "Sistem"

    penerima = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifikasi",
        verbose_name="Penerima",
    )
    pesanan = models.ForeignKey(
        Pesanan,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="notifikasi",
        verbose_name="Pesanan",
    )
    jenis = models.CharField(
        max_length=20,
        choices=JenisNotifikasi.choices,
        default=JenisNotifikasi.SISTEM,
        verbose_name="Jenis",
    )
    judul = models.CharField(
        max_length=150,
        verbose_name="Judul",
    )
    pesan = models.TextField(
        verbose_name="Pesan",
    )
    url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="URL tujuan",
    )
    sudah_dibaca = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Sudah dibaca",
    )
    dibaca_pada = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Dibaca pada",
    )

    class Meta:
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["penerima", "sudah_dibaca"]),
        ]

    def __str__(self):
        return f"{self.penerima.username} - {self.judul}"

    def tandai_dibaca(self):
        if not self.sudah_dibaca:
            self.sudah_dibaca = True
            self.dibaca_pada = timezone.now()
            self.save(
                update_fields=[
                    "sudah_dibaca",
                    "dibaca_pada",
                    "updated_at",
                ]
            )


class PengaturanSistem(TimeStampedModel):
    nama_laundry = models.CharField(
        max_length=150,
        default="Laundry Management System",
        verbose_name="Nama laundry",
    )
    nomor_hp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Nomor HP",
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Email",
    )
    alamat = models.TextField(
        blank=True,
        verbose_name="Alamat",
    )
    jam_buka = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Jam buka",
    )
    jam_tutup = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Jam tutup",
    )
    minimum_pesanan = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Minimum pesanan",
    )
    menerima_pesanan = models.BooleanField(
        default=True,
        verbose_name="Menerima pesanan",
    )

    class Meta:
        verbose_name = "Pengaturan Sistem"
        verbose_name_plural = "Pengaturan Sistem"

    def __str__(self):
        return self.nama_laundry