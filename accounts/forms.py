from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm


User = get_user_model()


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan nama depan",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan nama belakang",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masukkan email",
                }
            ),
        }

        labels = {
            "first_name": "Nama Depan",
            "last_name": "Nama Belakang",
            "email": "Email",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model_field_names = {
            field.name
            for field in User._meta.get_fields()
        }

        if "nomor_hp" in model_field_names:
            self.fields["nomor_hp"] = forms.CharField(
                required=False,
                label="Nomor HP",
                initial=getattr(
                    self.instance,
                    "nomor_hp",
                    "",
                ),
                widget=forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "placeholder": "Contoh: 081234567890",
                    }
                ),
            )

        if "alamat" in model_field_names:
            self.fields["alamat"] = forms.CharField(
                required=False,
                label="Alamat",
                initial=getattr(
                    self.instance,
                    "alamat",
                    "",
                ),
                widget=forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder": "Masukkan alamat lengkap",
                    }
                ),
            )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()

        if not email:
            return email

        email_exists = User.objects.filter(
            email__iexact=email,
        ).exclude(
            pk=self.instance.pk,
        ).exists()

        if email_exists:
            raise forms.ValidationError(
                "Email sudah digunakan oleh pengguna lain."
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        if "nomor_hp" in self.cleaned_data:
            user.nomor_hp = self.cleaned_data[
                "nomor_hp"
            ]

        if "alamat" in self.cleaned_data:
            user.alamat = self.cleaned_data[
                "alamat"
            ]

        if commit:
            user.save()

        return user


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

        self.fields["old_password"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Masukkan password lama",
            }
        )

        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Masukkan password baru",
            }
        )

        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Ulangi password baru",
            }
        )