from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("register/", views.signup_page, name="register"),
    path("profile/", views.profile_page, name="profile"),
    path("api/auth/signup/", views.api_signup, name="api_signup"),
    path("api/auth/login/", views.api_login, name="api_login"),
    path("api/auth/google/", views.api_google_auth, name="api_google_auth"),
    path("api/profile/profile/", views.api_profile, name="api_profile"),
]
