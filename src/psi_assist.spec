# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# Diretório do projeto
project_dir = Path(SPECPATH)

# Coletar todos os arquivos do Django
django_files = []
for root, dirs, files in os.walk(project_dir):
    # Ignorar diretórios desnecessários
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules']]
    
    for file in files:
        if file.endswith(('.py', '.html', '.css', '.js', '.json', '.txt', '.md')):
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, project_dir)
            dest_dir = os.path.dirname(rel_path) or "."
            django_files.append((file_path, dest_dir))

# Coletar templates do crispy-tailwind
crispy_tailwind_data = collect_data_files('crispy_tailwind', includes=['templates/**/*'])

# Coletar templates do crispy_forms (caso necessário)
crispy_forms_data = collect_data_files('crispy_forms', includes=['templates/**/*'])

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=django_files + crispy_tailwind_data + crispy_forms_data + [
        # Adicionar arquivos estáticos do Django
        (str(project_dir / 'staticfiles'), 'static'),
        # Adicionar arquivos de cada app
        (str(project_dir / 'user' / 'templates'), 'user/templates'),
        (str(project_dir / 'patients' / 'templates'), 'patients/templates'),
        (str(project_dir / 'psy_records' / 'templates'), 'psy_records/templates'),
    ],
    hiddenimports=[
        'django',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'user',
        'patients',
        'psy_records',
        'psi_assist_backend',
        'psi_assist_backend.settings',
        'psi_assist_backend.urls',
        'psi_assist_backend.wsgi',
        'google',
        'crispy_forms',
        'crispy_tailwind',
        'pydub'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    # NÃO incluir a.binaries, a.zipfiles, a.datas aqui para modo não-onefile
    [],
    name='psi_assist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

# COLLECT é necessário para distribuição em pasta (não-onefile)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    name='PSI_Assist_Backend'
)