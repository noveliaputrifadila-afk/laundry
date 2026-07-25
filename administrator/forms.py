from decimal import Decimal
from django import forms
from django.utils import timezone
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from .models import KategoriLayanan, User, Layanan, Tarif, Promo, MetodePembayaran, AreaLayanan, PengaturanSistem, Pesanan


class BootstrapFormMixin:
    """
    Menambahkan class Bootstrap ke semua field form.
    """

    def apply_bootstrap_classes(self):
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.RadioSelect,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                if isinstance(widget, forms.CheckboxInput):
                    widget.attrs["class"] = "form-check-input"

                continue

            if isinstance(widget, forms.Select):
                widget.attrs["class"] = "form-select"
            else:
                widget.attrs["class"] = "form-control"

            widget.attrs.setdefault(
                "placeholder",
                field.label,
            )


class PelangganRegistrationForm(
    BootstrapFormMixin,
    UserCreationForm,
):
    """
    Form registrasi khusus pelanggan.

    Pelanggan hanya dapat memilih username, nama, nomor HP,
    email, alamat, dan password. Role ditentukan otomatis
    sebagai pelanggan.
    """

    first_name = forms.CharField(
        label="Nama depan",
        max_length=150,
        required=True,
    )
    last_name = forms.CharField(
        label="Nama belakang",
        max_length=150,
        required=False,
    )
    nomor_hp = forms.CharField(
        label="Nomor HP",
        max_length=20,
        required=True,
    )
    email = forms.EmailField(
        label="Email",
        required=True,
    )
    alamat = forms.CharField(
        label="Alamat",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "nomor_hp",
            "email",
            "alamat",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["username"].help_text = (
            "Username digunakan untuk login."
        )
        self.fields["password1"].help_text = (
            "Gunakan password yang kuat dan tidak mudah ditebak."
        )
        self.fields["password2"].help_text = (
            "Masukkan kembali password yang sama."
        )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()

        if not username:
            raise forms.ValidationError(
                "Username wajib diisi."
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():
            raise forms.ValidationError(
                "Username sudah digunakan."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Email sudah digunakan."
            )

        return email

    def clean_nomor_hp(self):
        nomor_hp = self.cleaned_data.get(
            "nomor_hp",
            "",
        ).strip()

        # Normalisasi awalan nomor Indonesia.
        if nomor_hp.startswith("+62"):
            nomor_hp = "0" + nomor_hp[3:]
        elif nomor_hp.startswith("62"):
            nomor_hp = "0" + nomor_hp[2:]

        nomor_hp = nomor_hp.replace(" ", "")
        nomor_hp = nomor_hp.replace("-", "")

        if not nomor_hp.isdigit():
            raise forms.ValidationError(
                "Nomor HP hanya boleh berisi angka."
            )

        if len(nomor_hp) < 10 or len(nomor_hp) > 15:
            raise forms.ValidationError(
                "Nomor HP harus terdiri dari 10 sampai 15 digit."
            )

        if not nomor_hp.startswith("08"):
            raise forms.ValidationError(
                "Nomor HP harus diawali dengan 08."
            )

        if User.objects.filter(
            nomor_hp=nomor_hp
        ).exists():
            raise forms.ValidationError(
                "Nomor HP sudah digunakan."
            )

        return nomor_hp

    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = User.Role.PELANGGAN
        user.is_verified = False
        user.is_staff = False
        user.is_superuser = False
        user.email = self.cleaned_data["email"].lower()

        if commit:
            user.save()

        return user


class RoleAuthenticationForm(
    BootstrapFormMixin,
    AuthenticationForm,
):
    """
    Form login yang memeriksa status verifikasi pelanggan.
    """

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label="Ingat saya",
        required=False,
    )

    error_messages = {
        "invalid_login": (
            "Username atau password yang Anda masukkan salah."
        ),
        "inactive": (
            "Akun Anda sedang tidak aktif."
        ),
        "unverified": (
            "Akun pelanggan belum diverifikasi oleh administrator."
        ),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(
            request=request,
            *args,
            **kwargs,
        )
        self.apply_bootstrap_classes()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        if (
            user.role == User.Role.PELANGGAN
            and not user.is_verified
        ):
            raise forms.ValidationError(
                self.error_messages["unverified"],
                code="unverified",
            )


class UserInternalCreationForm(
    BootstrapFormMixin,
    UserCreationForm,
):
    """
    Form yang digunakan administrator untuk membuat akun:
    - Administrator
    - Kasir
    - Petugas Laundry

    Pelanggan tidak dibuat melalui form ini.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "nomor_hp",
            "alamat",
            "role",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["role"].choices = [
            (
                User.Role.ADMINISTRATOR,
                User.Role.ADMINISTRATOR.label,
            ),
            (
                User.Role.KASIR,
                User.Role.KASIR.label,
            ),
            (
                User.Role.PETUGAS_LAUNDRY,
                User.Role.PETUGAS_LAUNDRY.label,
            ),
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "Email sudah digunakan."
            )

        return email

    def clean_nomor_hp(self):
        nomor_hp = self.cleaned_data.get(
            "nomor_hp",
            "",
        ).strip()

        nomor_hp = nomor_hp.replace(" ", "")
        nomor_hp = nomor_hp.replace("-", "")

        if User.objects.filter(
            nomor_hp=nomor_hp
        ).exists():
            raise forms.ValidationError(
                "Nomor HP sudah digunakan."
            )

        return nomor_hp

    def clean_role(self):
        role = self.cleaned_data.get("role")

        allowed_roles = {
            User.Role.ADMINISTRATOR,
            User.Role.KASIR,
            User.Role.PETUGAS_LAUNDRY,
        }

        if role not in allowed_roles:
            raise forms.ValidationError(
                "Hak akses yang dipilih tidak valid."
            )

        return role

    def save(self, commit=True):
        user = super().save(commit=False)

        user.is_verified = True
        user.is_active = True

        if user.role == User.Role.ADMINISTRATOR:
            user.is_staff = True
        else:
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

        return user

class UserCreateForm(UserInternalCreationForm):
    """
    Form administrator untuk membuat akun internal:
    Administrator, Kasir, dan Petugas Laundry.
    """

    foto = forms.ImageField(
        label="Foto profil",
        required=False,
    )

    class Meta(UserInternalCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "nomor_hp",
            "alamat",
            "role",
            "foto",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()


class UserUpdateForm(BootstrapFormMixin, forms.ModelForm):
    """
    Form administrator untuk mengubah data pengguna.

    Password tidak diubah melalui form ini.
    """

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "nomor_hp",
            "alamat",
            "role",
            "foto",
            "is_active",
            "is_verified",
        )
        widgets = {
            "alamat": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop(
            "request_user",
            None,
        )

        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

        self.fields["is_verified"].widget.attrs[
            "class"
        ] = "form-check-input"

    def clean_username(self):
        username = self.cleaned_data.get(
            "username",
            "",
        ).strip()

        if not username:
            raise forms.ValidationError(
                "Username wajib diisi."
            )

        queryset = User.objects.filter(
            username__iexact=username
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "Username sudah digunakan."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get(
            "email",
            "",
        ).strip().lower()

        if not email:
            raise forms.ValidationError(
                "Email wajib diisi."
            )

        queryset = User.objects.filter(
            email__iexact=email
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "Email sudah digunakan."
            )

        return email

    def clean_nomor_hp(self):
        nomor_hp = self.cleaned_data.get(
            "nomor_hp",
            "",
        ).strip()

        if nomor_hp.startswith("+62"):
            nomor_hp = "0" + nomor_hp[3:]
        elif nomor_hp.startswith("62"):
            nomor_hp = "0" + nomor_hp[2:]

        nomor_hp = nomor_hp.replace(" ", "")
        nomor_hp = nomor_hp.replace("-", "")

        if nomor_hp:
            if not nomor_hp.isdigit():
                raise forms.ValidationError(
                    "Nomor HP hanya boleh berisi angka."
                )

            if len(nomor_hp) < 10 or len(nomor_hp) > 15:
                raise forms.ValidationError(
                    "Nomor HP harus terdiri dari 10 sampai 15 digit."
                )

            if not nomor_hp.startswith("08"):
                raise forms.ValidationError(
                    "Nomor HP harus diawali dengan 08."
                )

            queryset = User.objects.filter(
                nomor_hp=nomor_hp
            )

            if self.instance.pk:
                queryset = queryset.exclude(
                    pk=self.instance.pk
                )

            if queryset.exists():
                raise forms.ValidationError(
                    "Nomor HP sudah digunakan."
                )

        return nomor_hp

    def clean_role(self):
        role = self.cleaned_data.get("role")

        if self.instance.is_superuser:
            return User.Role.ADMINISTRATOR

        return role

    def clean_is_active(self):
        is_active = self.cleaned_data.get(
            "is_active"
        )

        if (
            self.request_user
            and self.instance.pk
            and self.request_user.pk == self.instance.pk
            and not is_active
        ):
            raise forms.ValidationError(
                "Anda tidak dapat menonaktifkan akun sendiri."
            )

        return is_active

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data[
            "email"
        ].lower()

        if user.role == User.Role.ADMINISTRATOR:
            user.is_staff = True
        else:
            user.is_staff = False

            if not user.is_superuser:
                user.is_superuser = False

        if user.role in {
            User.Role.ADMINISTRATOR,
            User.Role.KASIR,
            User.Role.PETUGAS_LAUNDRY,
        }:
            user.is_verified = True

        if commit:
            user.save()

        return user

class KategoriLayananForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    """
    Form tambah dan edit kategori layanan.
    """

    class Meta:
        model = KategoriLayanan
        fields = (
            "nama",
            "deskripsi",
            "is_active",
        )
        widgets = {
            "deskripsi": forms.Textarea(
                attrs={
                    "rows": 4,
                }
            ),
        }
        labels = {
            "nama": "Nama kategori",
            "deskripsi": "Deskripsi",
            "is_active": "Kategori aktif",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

    def clean_nama(self):
        nama = self.cleaned_data.get(
            "nama",
            "",
        ).strip()

        if not nama:
            raise forms.ValidationError(
                "Nama kategori wajib diisi."
            )

        queryset = KategoriLayanan.objects.filter(
            nama__iexact=nama
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "Nama kategori sudah digunakan."
            )

        return nama

class LayananForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    """
    Form tambah dan edit layanan laundry.
    """

    class Meta:
        model = Layanan
        fields = (
            "kategori",
            "nama",
            "deskripsi",
            "satuan",
            "estimasi_hari",
            "is_active",
        )
        widgets = {
            "deskripsi": forms.Textarea(
                attrs={
                    "rows": 4,
                }
            ),
            "estimasi_hari": forms.NumberInput(
                attrs={
                    "min": 1,
                }
            ),
        }
        labels = {
            "kategori": "Kategori layanan",
            "nama": "Nama layanan",
            "deskripsi": "Deskripsi",
            "satuan": "Satuan",
            "estimasi_hari": "Estimasi selesai",
            "is_active": "Layanan aktif",
        }
        help_texts = {
            "estimasi_hari": (
                "Masukkan estimasi waktu pengerjaan dalam hari."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

        self.fields["kategori"].queryset = (
            KategoriLayanan.objects.filter(
                is_active=True
            ).order_by("nama")
        )

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

    def clean_nama(self):
        nama = self.cleaned_data.get(
            "nama",
            "",
        ).strip()

        if not nama:
            raise forms.ValidationError(
                "Nama layanan wajib diisi."
            )

        queryset = Layanan.objects.filter(
            nama__iexact=nama
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "Nama layanan sudah digunakan."
            )

        return nama

    def clean_estimasi_hari(self):
        estimasi_hari = self.cleaned_data.get(
            "estimasi_hari"
        )

        if estimasi_hari is not None and estimasi_hari < 1:
            raise forms.ValidationError(
                "Estimasi pengerjaan minimal 1 hari."
            )

        return estimasi_hari

from django.utils import timezone


class TarifForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    """
    Form untuk menambah dan mengubah tarif layanan.
    """

    class Meta:
        model = Tarif
        fields = (
            "layanan",
            "harga",
            "tanggal_mulai",
            "tanggal_selesai",
            "is_active",
        )
        labels = {
            "layanan": "Layanan",
            "harga": "Harga",
            "tanggal_mulai": "Tanggal mulai berlaku",
            "tanggal_selesai": "Tanggal selesai",
            "is_active": "Tarif aktif",
        }
        widgets = {
            "harga": forms.NumberInput(
                attrs={
                    "min": 0,
                    "step": 500,
                    "placeholder": "Contoh: 10000",
                }
            ),
            "tanggal_mulai": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "tanggal_selesai": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }
        help_texts = {
            "harga": (
                "Masukkan harga sesuai satuan layanan."
            ),
            "tanggal_selesai": (
                "Kosongkan jika tarif belum memiliki "
                "tanggal berakhir."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["layanan"].queryset = (
            Layanan.objects
            .select_related("kategori")
            .filter(is_active=True)
            .order_by(
                "kategori__nama",
                "nama",
            )
        )

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

        if not self.instance.pk:
            self.fields[
                "tanggal_mulai"
            ].initial = timezone.localdate()

    def clean_harga(self):
        harga = self.cleaned_data.get("harga")

        if harga is None:
            raise forms.ValidationError(
                "Harga wajib diisi."
            )

        if harga <= 0:
            raise forms.ValidationError(
                "Harga harus lebih besar dari nol."
            )

        return harga

    def clean(self):
        cleaned_data = super().clean()

        layanan = cleaned_data.get("layanan")
        tanggal_mulai = cleaned_data.get(
            "tanggal_mulai"
        )
        tanggal_selesai = cleaned_data.get(
            "tanggal_selesai"
        )
        is_active = cleaned_data.get("is_active")

        if (
            tanggal_mulai
            and tanggal_selesai
            and tanggal_selesai < tanggal_mulai
        ):
            self.add_error(
                "tanggal_selesai",
                (
                    "Tanggal selesai tidak boleh "
                    "lebih awal dari tanggal mulai."
                ),
            )

        if layanan and tanggal_mulai:
            tarif_sama = Tarif.objects.filter(
                layanan=layanan,
                tanggal_mulai=tanggal_mulai,
            )

            if self.instance.pk:
                tarif_sama = tarif_sama.exclude(
                    pk=self.instance.pk
                )

            if tarif_sama.exists():
                self.add_error(
                    "tanggal_mulai",
                    (
                        "Layanan ini sudah memiliki "
                        "tarif pada tanggal tersebut."
                    ),
                )

        if layanan and is_active:
            tarif_aktif = Tarif.objects.filter(
                layanan=layanan,
                is_active=True,
            )

            if self.instance.pk:
                tarif_aktif = tarif_aktif.exclude(
                    pk=self.instance.pk
                )

            if tarif_aktif.exists():
                self.add_error(
                    "is_active",
                    (
                        "Layanan ini sudah mempunyai "
                        "tarif aktif. Nonaktifkan tarif "
                        "lama terlebih dahulu."
                    ),
                )

        return cleaned_data

from decimal import Decimal

from django import forms
from django.utils import timezone


class PromoForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Promo
        fields = (
            "kode",
            "nama",
            "jenis_diskon",
            "nilai_diskon",
            "maksimal_diskon",
            "minimal_transaksi",
            "layanan",
            "tanggal_mulai",
            "tanggal_selesai",
            "kuota",
            "is_active",
        )
        labels = {
            "kode": "Kode Promo",
            "nama": "Nama Promo",
            "jenis_diskon": "Jenis Diskon",
            "nilai_diskon": "Nilai Diskon",
            "maksimal_diskon": "Maksimal Diskon",
            "minimal_transaksi": "Minimal Transaksi",
            "layanan": "Berlaku untuk Layanan",
            "tanggal_mulai": "Tanggal Mulai",
            "tanggal_selesai": "Tanggal Selesai",
            "kuota": "Kuota Promo",
            "is_active": "Promo Aktif",
        }
        widgets = {
            "kode": forms.TextInput(
                attrs={
                    "placeholder": "Contoh: HEMAT20",
                }
            ),
            "nama": forms.TextInput(
                attrs={
                    "placeholder": "Contoh: Promo Hemat 20%",
                }
            ),
            "jenis_diskon": forms.Select(),
            "nilai_diskon": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Contoh: 20 atau 10000",
                }
            ),
            "maksimal_diskon": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                    "placeholder": "Kosongkan jika tidak dibatasi",
                }
            ),
            "minimal_transaksi": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                    "placeholder": "Contoh: 50000",
                }
            ),
            "layanan": forms.CheckboxSelectMultiple(),
            "tanggal_mulai": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "tanggal_selesai": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "kuota": forms.NumberInput(
                attrs={
                    "min": "1",
                    "placeholder": (
                        "Kosongkan jika tidak dibatasi"
                    ),
                }
            ),
        }
        help_texts = {
            "kode": (
                "Gunakan kode singkat tanpa spasi, "
                "misalnya HEMAT20."
            ),
            "nilai_diskon": (
                "Isi angka persentase atau nominal "
                "sesuai jenis diskon."
            ),
            "maksimal_diskon": (
                "Biasanya digunakan untuk promo persentase."
            ),
            "minimal_transaksi": (
                "Nilai minimum transaksi agar promo dapat digunakan."
            ),
            "layanan": (
                "Kosongkan pilihan jika promo berlaku "
                "untuk seluruh layanan."
            ),
            "kuota": (
                "Kosongkan jika jumlah penggunaan "
                "tidak dibatasi."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["layanan"].queryset = (
            Layanan.objects
            .select_related("kategori")
            .filter(is_active=True)
            .order_by(
                "kategori__nama",
                "nama",
            )
        )

        self.fields["tanggal_mulai"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]
        self.fields["tanggal_selesai"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

        # CheckboxSelectMultiple jangan diberi form-control.
        self.fields["layanan"].widget.attrs.pop(
            "class",
            None,
        )

        if not self.instance.pk:
            sekarang = timezone.localtime().replace(
                second=0,
                microsecond=0,
            )
            self.fields[
                "tanggal_mulai"
            ].initial = sekarang

        elif self.instance.pk:
            if self.instance.tanggal_mulai:
                self.initial["tanggal_mulai"] = (
                    timezone.localtime(
                        self.instance.tanggal_mulai
                    ).strftime("%Y-%m-%dT%H:%M")
                )

            if self.instance.tanggal_selesai:
                self.initial["tanggal_selesai"] = (
                    timezone.localtime(
                        self.instance.tanggal_selesai
                    ).strftime("%Y-%m-%dT%H:%M")
                )

    def clean_kode(self):
        kode = self.cleaned_data.get(
            "kode",
            "",
        ).strip().upper()

        if not kode:
            raise forms.ValidationError(
                "Kode promo wajib diisi."
            )

        if " " in kode:
            raise forms.ValidationError(
                "Kode promo tidak boleh mengandung spasi."
            )

        promo_sama = Promo.objects.filter(
            kode__iexact=kode
        )

        if self.instance.pk:
            promo_sama = promo_sama.exclude(
                pk=self.instance.pk
            )

        if promo_sama.exists():
            raise forms.ValidationError(
                "Kode promo sudah digunakan."
            )

        return kode

    def clean_nilai_diskon(self):
        nilai_diskon = self.cleaned_data.get(
            "nilai_diskon"
        )

        if nilai_diskon is None:
            raise forms.ValidationError(
                "Nilai diskon wajib diisi."
            )

        if nilai_diskon <= Decimal("0.00"):
            raise forms.ValidationError(
                "Nilai diskon harus lebih besar dari nol."
            )

        return nilai_diskon

    def clean_kuota(self):
        kuota = self.cleaned_data.get("kuota")

        if kuota is not None and kuota < 1:
            raise forms.ValidationError(
                "Kuota minimal adalah 1."
            )

        return kuota

    def clean(self):
        cleaned_data = super().clean()

        jenis_diskon = cleaned_data.get(
            "jenis_diskon"
        )
        nilai_diskon = cleaned_data.get(
            "nilai_diskon"
        )
        maksimal_diskon = cleaned_data.get(
            "maksimal_diskon"
        )
        minimal_transaksi = cleaned_data.get(
            "minimal_transaksi"
        )
        tanggal_mulai = cleaned_data.get(
            "tanggal_mulai"
        )
        tanggal_selesai = cleaned_data.get(
            "tanggal_selesai"
        )

        if (
            jenis_diskon
            == Promo.JenisDiskon.PERSENTASE
            and nilai_diskon is not None
            and nilai_diskon > Decimal("100.00")
        ):
            self.add_error(
                "nilai_diskon",
                (
                    "Diskon persentase tidak boleh "
                    "lebih dari 100%."
                ),
            )

        if (
            maksimal_diskon is not None
            and maksimal_diskon < Decimal("0.00")
        ):
            self.add_error(
                "maksimal_diskon",
                "Maksimal diskon tidak boleh negatif.",
            )

        if (
            minimal_transaksi is not None
            and minimal_transaksi < Decimal("0.00")
        ):
            self.add_error(
                "minimal_transaksi",
                "Minimal transaksi tidak boleh negatif.",
            )

        if (
            tanggal_mulai
            and tanggal_selesai
            and tanggal_selesai <= tanggal_mulai
        ):
            self.add_error(
                "tanggal_selesai",
                (
                    "Tanggal selesai harus lebih akhir "
                    "dari tanggal mulai."
                ),
            )

        return cleaned_data

class MetodePembayaranForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = MetodePembayaran
        fields = (
            "nama",
            "nomor_rekening",
            "atas_nama",
            "instruksi",
            "is_active",
        )
        labels = {
            "nama": "Nama Metode Pembayaran",
            "nomor_rekening": "Nomor Rekening/Akun",
            "atas_nama": "Atas Nama",
            "instruksi": "Instruksi Pembayaran",
            "is_active": "Metode Aktif",
        }
        widgets = {
            "nama": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Contoh: Transfer Bank BCA, Tunai, QRIS"
                    ),
                }
            ),
            "nomor_rekening": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Contoh: 1234567890 atau nomor akun"
                    ),
                }
            ),
            "atas_nama": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Contoh: Laundry Bersih Sejahtera"
                    ),
                }
            ),
            "instruksi": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Tuliskan petunjuk pembayaran"
                    ),
                }
            ),
        }
        help_texts = {
            "nomor_rekening": (
                "Kosongkan untuk metode seperti tunai."
            ),
            "atas_nama": (
                "Kosongkan jika tidak diperlukan."
            ),
            "instruksi": (
                "Berikan petunjuk yang mudah dipahami pelanggan."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

    def clean_nama(self):
        nama = self.cleaned_data.get(
            "nama",
            "",
        ).strip()

        if not nama:
            raise forms.ValidationError(
                "Nama metode pembayaran wajib diisi."
            )

        metode_sama = MetodePembayaran.objects.filter(
            nama__iexact=nama
        )

        if self.instance.pk:
            metode_sama = metode_sama.exclude(
                pk=self.instance.pk
            )

        if metode_sama.exists():
            raise forms.ValidationError(
                "Nama metode pembayaran sudah digunakan."
            )

        return nama

    def clean_nomor_rekening(self):
        nomor_rekening = self.cleaned_data.get(
            "nomor_rekening",
            "",
        ).strip()

        return nomor_rekening

    def clean_atas_nama(self):
        atas_nama = self.cleaned_data.get(
            "atas_nama",
            "",
        ).strip()

        return atas_nama

from decimal import Decimal

from django import forms


class AreaLayananForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = AreaLayanan
        fields = (
            "nama_area",
            "kode_pos",
            "biaya_antar",
            "biaya_jemput",
            "estimasi_menit",
            "is_active",
        )
        labels = {
            "nama_area": "Nama Area",
            "kode_pos": "Kode Pos",
            "biaya_antar": "Biaya Antar",
            "biaya_jemput": "Biaya Jemput",
            "estimasi_menit": "Estimasi Perjalanan",
            "is_active": "Area Aktif",
        }
        widgets = {
            "nama_area": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Contoh: Kecamatan Sukarame"
                    ),
                }
            ),
            "kode_pos": forms.TextInput(
                attrs={
                    "placeholder": "Contoh: 35131",
                    "maxlength": "10",
                }
            ),
            "biaya_antar": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                    "placeholder": "Contoh: 10000",
                }
            ),
            "biaya_jemput": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                    "placeholder": "Contoh: 10000",
                }
            ),
            "estimasi_menit": forms.NumberInput(
                attrs={
                    "min": "1",
                    "placeholder": "Contoh: 30",
                }
            ),
        }
        help_texts = {
            "nama_area": (
                "Masukkan kecamatan, kelurahan, "
                "atau nama wilayah layanan."
            ),
            "kode_pos": (
                "Kode pos bersifat opsional."
            ),
            "biaya_antar": (
                "Isi 0 jika layanan antar gratis."
            ),
            "biaya_jemput": (
                "Isi 0 jika layanan jemput gratis."
            ),
            "estimasi_menit": (
                "Perkiraan waktu perjalanan dalam menit."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["is_active"].widget.attrs[
            "class"
        ] = "form-check-input"

    def clean_nama_area(self):
        nama_area = self.cleaned_data.get(
            "nama_area",
            "",
        ).strip()

        if not nama_area:
            raise forms.ValidationError(
                "Nama area wajib diisi."
            )

        area_sama = AreaLayanan.objects.filter(
            nama_area__iexact=nama_area
        )

        if self.instance.pk:
            area_sama = area_sama.exclude(
                pk=self.instance.pk
            )

        if area_sama.exists():
            raise forms.ValidationError(
                "Nama area tersebut sudah terdaftar."
            )

        return nama_area

    def clean_kode_pos(self):
        kode_pos = self.cleaned_data.get(
            "kode_pos",
            "",
        ).strip()

        if kode_pos and not kode_pos.isdigit():
            raise forms.ValidationError(
                "Kode pos hanya boleh berisi angka."
            )

        if kode_pos and len(kode_pos) < 5:
            raise forms.ValidationError(
                "Kode pos minimal terdiri dari 5 angka."
            )

        return kode_pos

    def clean_biaya_antar(self):
        biaya_antar = self.cleaned_data.get(
            "biaya_antar"
        )

        if biaya_antar is None:
            return Decimal("0.00")

        if biaya_antar < Decimal("0.00"):
            raise forms.ValidationError(
                "Biaya antar tidak boleh negatif."
            )

        return biaya_antar

    def clean_biaya_jemput(self):
        biaya_jemput = self.cleaned_data.get(
            "biaya_jemput"
        )

        if biaya_jemput is None:
            return Decimal("0.00")

        if biaya_jemput < Decimal("0.00"):
            raise forms.ValidationError(
                "Biaya jemput tidak boleh negatif."
            )

        return biaya_jemput

    def clean_estimasi_menit(self):
        estimasi_menit = self.cleaned_data.get(
            "estimasi_menit"
        )

        if (
            estimasi_menit is not None
            and estimasi_menit < 1
        ):
            raise forms.ValidationError(
                "Estimasi perjalanan minimal 1 menit."
            )

        return estimasi_menit

from decimal import Decimal

from django import forms


class PengaturanSistemForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = PengaturanSistem
        fields = (
            "nama_laundry",
            "nomor_hp",
            "email",
            "alamat",
            "jam_buka",
            "jam_tutup",
            "minimum_pesanan",
            "menerima_pesanan",
        )
        labels = {
            "nama_laundry": "Nama Laundry",
            "nomor_hp": "Nomor HP",
            "email": "Email",
            "alamat": "Alamat Laundry",
            "jam_buka": "Jam Buka",
            "jam_tutup": "Jam Tutup",
            "minimum_pesanan": "Minimum Pesanan",
            "menerima_pesanan": "Menerima Pesanan",
        }
        widgets = {
            "nama_laundry": forms.TextInput(
                attrs={
                    "placeholder": "Contoh: Laundry Bersih Sejahtera",
                }
            ),
            "nomor_hp": forms.TextInput(
                attrs={
                    "placeholder": "Contoh: 081234567890",
                    "inputmode": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Contoh: laundry@email.com",
                }
            ),
            "alamat": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Masukkan alamat lengkap laundry",
                }
            ),
            "jam_buka": forms.TimeInput(
                attrs={
                    "type": "time",
                },
                format="%H:%M",
            ),
            "jam_tutup": forms.TimeInput(
                attrs={
                    "type": "time",
                },
                format="%H:%M",
            ),
            "minimum_pesanan": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                    "placeholder": "Contoh: 20000",
                }
            ),
        }
        help_texts = {
            "nomor_hp": (
                "Nomor yang dapat dihubungi pelanggan."
            ),
            "jam_buka": (
                "Kosongkan jika jam operasional belum ditentukan."
            ),
            "jam_tutup": (
                "Kosongkan jika jam operasional belum ditentukan."
            ),
            "minimum_pesanan": (
                "Isi 0 jika tidak ada minimum transaksi."
            ),
            "menerima_pesanan": (
                "Nonaktifkan sementara jika laundry sedang tutup "
                "atau tidak menerima pesanan."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["jam_buka"].input_formats = [
            "%H:%M",
        ]
        self.fields["jam_tutup"].input_formats = [
            "%H:%M",
        ]

        self.fields[
            "menerima_pesanan"
        ].widget.attrs["class"] = "form-check-input"

    def clean_nama_laundry(self):
        nama_laundry = self.cleaned_data.get(
            "nama_laundry",
            "",
        ).strip()

        if not nama_laundry:
            raise forms.ValidationError(
                "Nama laundry wajib diisi."
            )

        return nama_laundry

    def clean_nomor_hp(self):
        nomor_hp = self.cleaned_data.get(
            "nomor_hp",
            "",
        ).strip()

        if not nomor_hp:
            return nomor_hp

        karakter_diizinkan = set(
            "0123456789+-() "
        )

        if any(
            karakter not in karakter_diizinkan
            for karakter in nomor_hp
        ):
            raise forms.ValidationError(
                "Nomor HP mengandung karakter yang tidak valid."
            )

        jumlah_digit = sum(
            karakter.isdigit()
            for karakter in nomor_hp
        )

        if jumlah_digit < 9:
            raise forms.ValidationError(
                "Nomor HP minimal terdiri dari 9 angka."
            )

        return nomor_hp

    def clean_minimum_pesanan(self):
        minimum_pesanan = self.cleaned_data.get(
            "minimum_pesanan"
        )

        if minimum_pesanan is None:
            return Decimal("0.00")

        if minimum_pesanan < Decimal("0.00"):
            raise forms.ValidationError(
                "Minimum pesanan tidak boleh negatif."
            )

        return minimum_pesanan

    def clean(self):
        cleaned_data = super().clean()

        jam_buka = cleaned_data.get(
            "jam_buka"
        )
        jam_tutup = cleaned_data.get(
            "jam_tutup"
        )

        if (
            jam_buka
            and jam_tutup
            and jam_buka == jam_tutup
        ):
            self.add_error(
                "jam_tutup",
                (
                    "Jam tutup tidak boleh sama "
                    "dengan jam buka."
                ),
            )

        return cleaned_data

class KonfirmasiPesananForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Pesanan
        fields = (
            "kasir",
            "petugas_laundry",
            "estimasi_selesai",
            "biaya_tambahan",
            "catatan_kasir",
        )
        labels = {
            "kasir": "Kasir Penanggung Jawab",
            "petugas_laundry": "Petugas Laundry",
            "estimasi_selesai": "Estimasi Selesai",
            "biaya_tambahan": "Biaya Tambahan",
            "catatan_kasir": "Catatan Kasir",
        }
        widgets = {
            "estimasi_selesai": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "biaya_tambahan": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "500",
                }
            ),
            "catatan_kasir": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Catatan untuk pelanggan "
                        "atau petugas laundry"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["kasir"].queryset = (
            User.objects.filter(
                role=User.Role.KASIR,
                is_active=True,
                is_verified=True,
            )
            .order_by("first_name", "username")
        )

        self.fields["petugas_laundry"].queryset = (
            User.objects.filter(
                role=User.Role.PETUGAS_LAUNDRY,
                is_active=True,
                is_verified=True,
            )
            .order_by("first_name", "username")
        )

        self.fields["estimasi_selesai"].input_formats = [
            "%Y-%m-%dT%H:%M",
        ]

        if (
            user
            and user.role == User.Role.KASIR
            and not self.instance.kasir_id
        ):
            self.fields["kasir"].initial = user

        if (
            self.instance.pk
            and self.instance.estimasi_selesai
        ):
            self.initial["estimasi_selesai"] = (
                timezone.localtime(
                    self.instance.estimasi_selesai
                ).strftime("%Y-%m-%dT%H:%M")
            )

    def clean_biaya_tambahan(self):
        biaya = self.cleaned_data.get(
            "biaya_tambahan"
        )

        if biaya is None:
            return Decimal("0.00")

        if biaya < Decimal("0.00"):
            raise forms.ValidationError(
                "Biaya tambahan tidak boleh negatif."
            )

        return biaya

class TolakPesananForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Pesanan
        fields = (
            "alasan_penolakan",
        )
        labels = {
            "alasan_penolakan": "Alasan Penolakan",
        }
        widgets = {
            "alasan_penolakan": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Jelaskan alasan pesanan ditolak"
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def clean_alasan_penolakan(self):
        alasan = self.cleaned_data.get(
            "alasan_penolakan",
            "",
        ).strip()

        if not alasan:
            raise forms.ValidationError(
                "Alasan penolakan wajib diisi."
            )

        return alasan

class PenugasanPetugasForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Pesanan
        fields = (
            "petugas_laundry",
        )
        labels = {
            "petugas_laundry": "Petugas Laundry",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.apply_bootstrap_classes()

        self.fields["petugas_laundry"].queryset = (
            User.objects.filter(
                role=User.Role.PETUGAS_LAUNDRY,
                is_active=True,
                is_verified=True,
            )
            .order_by("first_name", "username")
        )

    def clean_petugas_laundry(self):
        petugas = self.cleaned_data.get(
            "petugas_laundry"
        )

        if petugas is None:
            raise forms.ValidationError(
                "Petugas laundry wajib dipilih."
            )

        return petugas

class UbahStatusPesananForm(
    BootstrapFormMixin,
    forms.Form,
):
    status = forms.ChoiceField(
        label="Status Baru",
        choices=Pesanan.StatusPesanan.choices,
    )
    catatan = forms.CharField(
        label="Catatan",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": (
                    "Catatan perubahan status"
                ),
            }
        ),
    )

    def __init__(
        self,
        *args,
        pesanan=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.pesanan = pesanan
        self.apply_bootstrap_classes()

        if pesanan:
            self.fields["status"].choices = (
                self.get_status_choices(pesanan)
            )

    @staticmethod
    def get_status_choices(pesanan):
        alur_status = {
            Pesanan.StatusPesanan.MENUNGGU_KONFIRMASI: [
                Pesanan.StatusPesanan.DITERIMA,
                Pesanan.StatusPesanan.DITOLAK,
                Pesanan.StatusPesanan.DIBATALKAN,
            ],
            Pesanan.StatusPesanan.DITERIMA: [
                Pesanan.StatusPesanan.MENUNGGU_ANTRIAN,
                Pesanan.StatusPesanan.DIBATALKAN,
            ],
            Pesanan.StatusPesanan.MENUNGGU_ANTRIAN: [
                Pesanan.StatusPesanan.DICUCI,
                Pesanan.StatusPesanan.DIBATALKAN,
            ],
            Pesanan.StatusPesanan.DICUCI: [
                Pesanan.StatusPesanan.DIKERINGKAN,
            ],
            Pesanan.StatusPesanan.DIKERINGKAN: [
                Pesanan.StatusPesanan.DISETRIKA,
                Pesanan.StatusPesanan.DILIPAT,
                Pesanan.StatusPesanan.DIKEMAS,
            ],
            Pesanan.StatusPesanan.DISETRIKA: [
                Pesanan.StatusPesanan.DILIPAT,
            ],
            Pesanan.StatusPesanan.DILIPAT: [
                Pesanan.StatusPesanan.DIKEMAS,
            ],
            Pesanan.StatusPesanan.DIKEMAS: [
                Pesanan.StatusPesanan.SIAP_DIAMBIL,
                Pesanan.StatusPesanan.SIAP_DIANTAR,
            ],
            Pesanan.StatusPesanan.SIAP_DIAMBIL: [
                Pesanan.StatusPesanan.SELESAI,
            ],
            Pesanan.StatusPesanan.SIAP_DIANTAR: [
                Pesanan.StatusPesanan.DALAM_PENGANTARAN,
            ],
            Pesanan.StatusPesanan.DALAM_PENGANTARAN: [
                Pesanan.StatusPesanan.SELESAI,
            ],
        }

        status_diizinkan = alur_status.get(
            pesanan.status,
            [],
        )

        label_status = dict(
            Pesanan.StatusPesanan.choices
        )

        return [
            (
                status,
                label_status[status],
            )
            for status in status_diizinkan
        ]

    def clean_status(self):
        status_baru = self.cleaned_data.get(
            "status"
        )

        if not self.pesanan:
            return status_baru

        status_diizinkan = {
            value
            for value, label in self.get_status_choices(
                self.pesanan
            )
        }

        if status_baru not in status_diizinkan:
            raise forms.ValidationError(
                "Perubahan status tersebut tidak diizinkan."
            )

        return status_baru

class UbahStatusPembayaranForm(
    BootstrapFormMixin,
    forms.ModelForm,
):
    class Meta:
        model = Pesanan
        fields = (
            "status_pembayaran",
        )
        labels = {
            "status_pembayaran": (
                "Status Pembayaran"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()