; Script gerado para Inno Setup

#define MyAppName "Sistema Hotel Santos"
#define MyAppVersion "4.2.9"
#define MyAppPublisher "Gabriel Ramos"
#define MyAppURL "https://github.com/gabriel-ram0s/sistemahotelsantos"
#define MyAppExeName "SistemaHotel.exe"

[Setup]
; ID único do aplicativo
AppId={{A8F9D8E2-3B4C-4D5E-9F0G-1H2I3J4K5L6M}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; INSTALAÇÃO NA PASTA DO USUÁRIO (AppData/Local) para permitir escrita no DB e Auto-Update
DefaultDirName={autolocalappdata}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=Instalador_SistemaHotel
; Aponta para o ícone na subpasta
SetupIconFile=sistemahotelsantos\app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Não exige admin para instalar (pois é na pasta do usuário)
PrivilegesRequired=lowest

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Copia o ícone para a pasta de instalação
Source: "sistemahotelsantos\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent