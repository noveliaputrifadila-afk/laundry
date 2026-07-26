from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path(
        "",
        views.profile_view,
        name="profile",
    ),
    path(
        "edit/",
        views.profile_edit,
        name="profile_edit",
    ),
    path(
        "ubah-password/",
        views.password_change,
        name="password_change",
    ),
    
]