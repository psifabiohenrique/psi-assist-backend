from django.urls import path
from .views import signup_view, CustomLoginView, logout_view

app_name = "user"

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout')
]