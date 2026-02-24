import sys
import os
from cx_Freeze import setup, Executable

# Função para encontrar o caminho do customtkinter automaticamente
def get_customtkinter_path():
    import customtkinter
    return os.path.dirname(customtkinter.__file__)

build_exe_options = {
    "packages": ["os", "requests", "fpdf", "customtkinter", "tkcalendar", "matplotlib", "babel"],
    "includes": ["babel.numbers"],
    "include_files": [
        # Inclui os arquivos de tema e assets do customtkinter
        (get_customtkinter_path(), "customtkinter")
    ],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sistema Hotel Santos",
    version="1.0",
    description="Sistema de Gestão Hoteleira - Ref 2025-12-17",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "sistemahotelsantos/app_gui.py", # AJUSTE AQUI SE O ARQUIVO NÃO ESTIVER NESTA PASTA
            base=base,
            target_name="SistemaHotel.exe",
            shortcut_name="Sistema Hotel Santos",
            shortcut_dir="ProgramMenuFolder",
        )
    ],
)
