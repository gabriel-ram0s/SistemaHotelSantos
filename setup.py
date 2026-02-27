import sys
import os
from cx_Freeze import setup, Executable

# --- LÓGICA DE DETECÇÃO DE ASSETS (CustomTkinter) ---
def get_customtkinter_path():
    try:
        import customtkinter
        return os.path.dirname(customtkinter.__file__)
    except ImportError:
        return None

tk_path = get_customtkinter_path()
include_files = []
if tk_path:
    include_files.append((tk_path, "customtkinter"))

# --- BUSCA DINÂMICA PELO SCRIPT PRINCIPAL ---
# Tenta encontrar o app_gui.py em diferentes locais comuns
posiveis_caminhos = [
    "sistemahotelsantos/app_gui.py",
    "app_gui.py",
    "src/app_gui.py"
]

target_script = None
for caminho in posiveis_caminhos:
    if os.path.exists(caminho):
        target_script = caminho
        break

if not target_script:
    # Lista arquivos para debug caso falhe
    print(f"Arquivos no diretório atual: {os.listdir('.')}")
    raise FileNotFoundError("ERRO CRÍTICO: app_gui.py não encontrado no repositório.")

# --- CONFIGURAÇÕES DE BUILD ---
build_exe_options = {
    "packages": ["os", "requests", "fpdf", "customtkinter", "tkcalendar", "matplotlib", "babel"],
    "includes": ["babel.numbers", "tkinter"],
    "include_files": include_files,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sistema Hotel Santos",
    version="1.0",
    description="Sistema de Gestão Hoteleira - Ref 2026",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script=target_script,
            base=base,
            target_name="SistemaHotel.exe",
            shortcut_name="Sistema Hotel Santos",
            shortcut_dir="ProgramMenuFolder",
        )
    ],
)
