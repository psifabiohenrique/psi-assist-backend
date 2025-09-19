from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from patients.views import PatientListView

def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("patients:list")
    else:
        form = CustomUserCreationForm()
    return render(request, "user/signup.html", {"form": form})

class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "user/login.html"

@login_required
def logout_view(request):
    logout(request)
    return redirect("user:login")