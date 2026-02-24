import sys
from cx_Freeze import setup, Executable

# Definições básicas do instalador
build_exe_options = {
    "packages": ["os", "requests", "fpdf", "customtkinter", "tkcalendar", "matplotlib", "babel"],
    "includes": ["babel.numbers"],
    "include_files": [], # Adicione pastas de assets/imagens aqui se houver
}

base = None
if sys.platform == "win32":
    base = "Win32GUI" # Garante que não abra um console preto ao iniciar

setup(
    name="Sistema Hotel Santos",
    version="1.0",
    description="Sistema de Gestão Hoteleira - Developed with Gemini AI",
    author="Seu Nome",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "sistemahotelsantos/app_gui.py", # Caminho para seu script principal
            base=base,
            target_name="SistemaHotel.exe",
            shortcut_name="Sistema Hotel Santos",
            shortcut_dir="ProgramMenuFolder",
        )
    ],
)
