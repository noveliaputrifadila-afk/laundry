from django import forms
from django.contrib.auth.forms import UserCreationForm

from administrator.models import User


class PelangganKasirRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nama depan",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan nama depan",
            }
        ),
    )

    last_name = forms.CharField(
        label="Nama belakang",
        max_length=150,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan nama belakang",
            }
        ),
    )

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan username",
            }
        ),
    )

    nomor_hp = forms.CharField(
        label="Nomor HP",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contoh: 081234567890",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "nama@email.com",
            }
        ),
    )

    alamat = forms.CharField(
        label="Alamat",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Masukkan alamat pelanggan",
            }
        ),
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan password",
            }
        ),
    )

    password2 = forms.CharField(
        label="Konfirmasi password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ulangi password",
            }
        ),
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "nomor_hp",
            "email",
            "alamat",
            "password1",
            "password2",
        ]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "Username tersebut sudah digunakan."
            )

        return username

    def clean_nomor_hp(self):
        nomor_hp = self.cleaned_data["nomor_hp"].strip()

        if User.objects.filter(nomor_hp=nomor_hp).exists():
            raise forms.ValidationError(
                "Nomor HP tersebut sudah terdaftar."
            )

        return nomor_hp

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Email tersebut sudah terdaftar."
            )

        return email

    def save(self, commit=True):
        pelanggan = super().save(commit=False)

        pelanggan.role = User.Role.PELANGGAN
        pelanggan.is_active = True
        pelanggan.is_verified = True

        if commit:
            pelanggan.save()

        return pelanggan