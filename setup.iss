; Script gerado para Inno Setup
; Salve este arquivo como "setup.iss" na raiz do projeto

#define MyAppName "Sistema Hotel Santos"
#define MyAppVersion "4.2.8"
#define MyAppPublisher "Gabriel Ramos"
#define MyAppURL "https://github.com/gabriel-ram0s/sistemahotelsantos"
#define MyAppExeName "SistemaHotel.exe"

[Setup]
; ID único do aplicativo (Gere um novo GUID no Inno Setup se quiser, mas este funciona)
AppId={{A8F9D8E2-3B4C-4D5E-9F0G-1H2I3J4K5L6M}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Cria o instalador na pasta Output
OutputDir=Output
OutputBaseFilename=Instalador_SistemaHotel
; Ícone do instalador (opcional, usa o padrão se não tiver)
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Permissões: auto (pede admin se necessário)
PrivilegesRequired=admin

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; O arquivo executável gerado pelo PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; O arquivo de ícone para o atalho
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Atalho no Menu Iniciar
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"
; Atalho na Área de Trabalho
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\app.ico"; Tasks: desktopicon

[Run]
; Opção para rodar ao finalizar a instalação
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
