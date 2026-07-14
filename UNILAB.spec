# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = [
    ('assets', 'assets'),
    ('static', 'static'),
    ('templates', 'templates'),
    ('database', 'database'),
    ('bulk_reports', 'bulk_reports')
]
binaries = []
hiddenimports = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.template.backends.django',
    'django.template.backends.jinja2',
    'jinja2',
    'pymysql',
    'mysql.connector',
    'waitress',
    'webview',
    
    # Project core and routing modules
    'unilab_project',
    'unilab_project.settings',
    'unilab_project.urls',
    'unilab_project.jinja2',
    
    # Local application modules
    'core',
    'core.views',
    'core.urls',
    'core.models',
    'core.middleware',
    'core.apps',
    
    'accounts',
    'accounts.views',
    'accounts.urls',
    'accounts.models',
    'accounts.backends',
    'accounts.hashers',
    'accounts.apps',
    
    'patients',
    'patients.views',
    'patients.urls',
    'patients.models',
    'patients.apps',
    
    'tests',
    'tests.views',
    'tests.urls',
    'tests.models',
    'tests.apps',
    
    'reports',
    'reports.views',
    'reports.urls',
    'reports.models',
    'reports.apps',
]

# Gather database driver hooks and pywebview environment parameters recursively
tmp_ret_mysql = collect_all('mysql.connector')
datas += tmp_ret_mysql[0]; binaries += tmp_ret_mysql[1]; hiddenimports += tmp_ret_mysql[2]

tmp_ret_webview = collect_all('webview')
datas += tmp_ret_webview[0]; binaries += tmp_ret_webview[1]; hiddenimports += tmp_ret_webview[2]

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UNILAB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Temporarily show console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/logo.ico',
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UNILAB',
)
