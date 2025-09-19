from django.urls import path
from .views import (
    signup_view,
    CustomLoginView,
    logout_view,
    UserUpdateView,
    UserPasswordChangeView,
)

app_name = "user"

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("update/", UserUpdateView.as_view(), name="update"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
]
