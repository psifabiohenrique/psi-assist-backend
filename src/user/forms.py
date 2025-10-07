from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "api_key",
            "system_prompt",
        )


class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ("username", "password")


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "system_prompt", "api_key"]
        widgets = {
            "api_key": forms.PasswordInput(
                render_value=True,
                attrs={
                    "placeholder": "Digite sua chave de API do Google Gemini",
                    "class": "form-control",
                },
            ),
            "system_prompt": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Digite o prompt de sistema para o Gemini (opcional)",
                    "class": "form-control",
                }
            ),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "system_prompt": "Prompt de Sistema",
            "api_key": "Chave de API do Gemini",
        }
        help_texts = {
            "api_key": "Sua chave pessoal de API do Google Gemini para geração automática de prontuários.",
            "system_prompt": "Instruções personalizadas para o modelo de IA (opcional).",
        }

    def clean_email(self):
        """
        Valida se o email não está sendo usado por outro usuário
        """
        email = self.cleaned_data.get("email")
        if email:
            existing_user = User.objects.filter(email=email).exclude(
                pk=self.instance.pk
            )
            if existing_user.exists():
                raise forms.ValidationError(
                    "Este e-mail já está sendo usado por outro usuário."
                )
        return email

    def clean_api_key(self):
        """
        Validação básica da API Key
        """
        api_key = self.cleaned_data.get("api_key")
        if api_key:
            # Validação básica do formato da chave (Google API keys geralmente começam com AIza)
            if not api_key.startswith("AIza") or len(api_key) < 30:
                raise forms.ValidationError(
                    "Formato de chave de API inválido. Verifique se você copiou a chave corretamente."
                )
        return api_key
