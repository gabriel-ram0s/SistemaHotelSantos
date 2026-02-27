[Setup]
AppName=Sistema Hotel Santos
AppVersion=1.0
DefaultDirName={autopf}\SistemaHotelSantos
DefaultGroupName=Sistema Hotel Santos
UninstallDisplayIcon={app}\SistemaHotel.exe
Compression=lzma2
SolidCompression=yes
OutputDir=./dist_installer
OutputBaseFilename=SistemaHotel_Setup
; Aqui incluímos sua assinatura digital nos metadados do instalador
AppPublisher=Developed with Gemini AI assistance
AppCopyright=© 2026

[Files]
; Origem: o executável gerado pelo PyInstaller na pasta dist
Source: "dist\SistemaHotel.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Sistema Hotel Santos"; Filename: "{app}\SistemaHotel.exe"
Name: "{autodesktop}\Sistema Hotel Santos"; Filename: "{app}\SistemaHotel.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\SistemaHotel.exe"; Description: "{cm:LaunchProgram,Sistema Hotel Santos}"; Flags: nowait postinstall skipifsilent
