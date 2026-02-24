import sys
import os
from cx_Freeze import setup, Executable

# --- LÓGICA PARA INCLUSÃO DE ASSETS DO CUSTOMTKINTER ---
# Isso evita o erro comum de "theme not found"
def get_customtkinter_path():
    try:
        import customtkinter
        return os.path.dirname(customtkinter.__file__)
    except ImportError:
        return None

tk_path = get_customtkinter_path()
include_files = []
if tk_path:
    # Adiciona a pasta do customtkinter inteira para garantir temas e imagens
    include_files.append((tk_path, "customtkinter"))

# --- CONFIGURAÇÕES DE BUILD ---
build_exe_options = {
    "packages": [
        "os", 
        "requests", 
        "fpdf", 
        "customtkinter", 
        "tkcalendar", 
        "matplotlib", 
        "babel"
    ],
    "includes": [
        "babel.numbers",
        "tkinter"
    ],
    "include_files": include_files,
}

# --- DEFINIÇÃO DO EXECUTÁVEL ---
# "Win32GUI" impede que uma janela de terminal (CMD) abra junto com seu app
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sistema Hotel Santos",
    version="1.0",
    description="Sistema de Gestão Hoteleira - Assistência Gemini AI",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="sistemahotelsantos/app_gui.py", # Caminho relativo no GitHub
            base=base,
            target_name="SistemaHotel.exe",
            shortcut_name="Sistema Hotel Santos",
            shortcut_dir="ProgramMenuFolder", # Cria atalho no Menu Iniciar
        )
    ],
)
