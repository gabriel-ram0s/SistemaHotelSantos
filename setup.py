import sys
from cx_Freeze import setup, Executable

# Configurações do build
build_exe_options = {
    "packages": ["os", "requests", "fpdf", "customtkinter", "tkcalendar", "matplotlib", "babel"],
    "includes": ["babel.numbers"],
}

# Define que é uma aplicação GUI (para não abrir o prompt de comando atrás)
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Sistema Hotel Santos",
    version="1.0",
    description="Sistema de Gestão - Developed with Gemini AI",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "sistemahotelsantos/app_gui.py", # Verifique se este caminho está correto
            base=base,
            target_name="SistemaHotel.exe",
            shortcut_name="Sistema Hotel Santos",
            shortcut_dir="ProgramMenuFolder", # Cria atalho no Menu Iniciar
        )
    ],
)
