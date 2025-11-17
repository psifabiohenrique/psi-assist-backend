from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User  # Importe seu modelo de usuário

class CustomUserAdmin(BaseUserAdmin):
    # Campos que aparecem na lista de usuários (list_display)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'is_active', 'gemini_model', # Adicione os campos que deseja ver na lista
    )

    # Campos que aparecem na página de edição do usuário (fieldsets)
    # Você pode reorganizar ou adicionar campos conforme necessário
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
        ('Configurações da API Gemini', {'fields': ('api_key', 'system_prompt', 'gemini_model')}), # Seu novo fieldset
    )

    # Campos que aparecem na página de adição de usuário (add_fieldsets)
    # Geralmente é mais simples, pois não há senha ou últimas datas
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password', 'password2')
        }),
        ('Configurações da API Gemini', {'fields': ('api_key', 'system_prompt', 'gemini_model')}),
    )

    # Campos que podem ser pesquisados na lista de usuários
    search_fields = ('username', 'email', 'first_name', 'last_name', 'gemini_model')

    # Filtros na barra lateral
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'gemini_model')


# Desregistre o UserAdmin padrão se ele já estiver registrado
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass # Não faça nada se não estiver registrado

# Registre seu modelo de usuário com sua classe CustomUserAdmin
admin.site.register(User, CustomUserAdmin)