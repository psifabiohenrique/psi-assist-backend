from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # Inclua os campos customizados aqui para que apareçam no formulário.
        # Como eles são blank=True e null=True no modelo, serão opcionais no formulário.
        fields = ("username", "email", "first_name", "last_name", "api_key", "system_prompt")

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ("username", "password")