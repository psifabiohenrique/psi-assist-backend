import os
import sys
from pathlib import Path

# Ajuste estes caminhos:
project_home = '/home/fabiohenriquedev/psi_assist_backend/src'  # caminho onde está manage.py
python_path = project_home

if python_path not in sys.path:
    sys.path.insert(0, python_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Se usar virtualenv, o PA já conecta o virtualenv no painel; nao precisa aqui.

from django.core.wsgi import get_wsgi_application  # noqa: E402
application = get_wsgi_application()