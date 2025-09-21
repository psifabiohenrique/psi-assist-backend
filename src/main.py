#!/usr/bin/env python
"""
Main de inicialização: aplica migrações, cria superusuário padrão,
e inicia o Django `runserver` no console.
"""

import os
import sys
from pathlib import Path

# Apontar para as configurações do Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Adicionar diretório do projeto no path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Importar Django
import django
from django.core.management import call_command
from django.contrib.auth import get_user_model

def setup_database():
    """Executa migrações e cria superusuário padrão se não existir."""
    django.setup()

    print(">> Aplicando migrações...")
    call_command("migrate", interactive=False, verbosity=1)

    # Criar superusuário padrão
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        print(">> Criando superusuário padrão (admin/admin123)")
        User.objects.create_superuser(
            username="admin",
            email="admin@psiassist.local",
            password="admin123",
            api_key="",
            system_prompt="Você é um assistente especializado em psicologia."
        )
    else:
        print(">> Superusuário já existe")

def run_server():
    """Inicia o servidor Django (executa como se fosse manage.py runserver)."""
    print(">> Iniciando servidor Django em http://127.0.0.1:8000 ...")
    call_command("runserver", "127.0.0.1:8000", use_reloader=False)

def main():
    setup_database()
    run_server()

if __name__ == "__main__":
    main()