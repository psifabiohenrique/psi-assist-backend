from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserUpdateForm


User = get_user_model()

def signup_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        # form = CustomUserCreationForm(request.POST)
        # if form.is_valid():
        #     user = form.save()
        #     login(request, user)
        #     return redirect("patients:list")
        return redirect('user:login')
    else:
        form = CustomUserCreationForm()
    return render(request, "user/signup.html", {"form": form, "title": "Cadastrar - Psi Assist"})


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "user/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login - Psi Assist'
        return context


@login_required
def logout_view(request):
    logout(request)
    return redirect("user:login")


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "user/user_update.html"
    success_url = reverse_lazy("patients:list")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Seus dados foram atualizados com sucesso!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Ocorreu um erro ao atualizar seus dados. Verifique os campos abaixo.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Atualizar Conta"
        context["user"] = self.request.user

        # Verifica se o usuário tem API key configurada
        context["has_api_key"] = bool(self.request.user.api_key)

        return context

class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "user/password_change.html"
    success_url = reverse_lazy("patients:list")

    def form_valid(self, form):
        messages.success(self.request, "Sua senha foi alterada com sucesso.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ocorreu um erro ao alterar sua senha.")
        return super().form_invalid(form)