# hook-PyQt6.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

hiddenimports = [
    'PyQt6.sip',
    'sip',
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
]

# Добавляем все подмодули
hiddenimports += collect_submodules('PyQt6')

# Добавляем все DLL
binaries = collect_dynamic_libs('PyQt6')
datas = collect_data_files('PyQt6')
