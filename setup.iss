; ===================================================================
;  Script Inno Setup para o Sistema Hotel Santos
; ===================================================================

#define MyAppName "Sistema Hotel Santos"
#define MyAppVersion "4.3.0" 
#define MyAppPublisher "Gabriel Ramos"
#define MyAppURL "https://github.com/gabriel-ram0s/sistemahotelsantos"
#define MyAppExeName "SistemaHotel.exe"
; #define AppIcon "sistemahotelsantos/app.ico" // Desativado temporariamente para corrigir o build.

[Setup]
; AppId: Identificador único gerado (GUID). 
; Garante que o Windows reconheça atualizações corretamente.
AppId={{8DD86653-6C3C-4336-8343-9C5488408762}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Instala na pasta de dados do usuário local. Essencial para:
; 1. Permitir instalação sem privilégios de administrador.
; 2. Permitir que o app escreva no seu próprio diretório (banco de dados, logs).
; 3. Permitir que o mecanismo de auto-update funcione.
DefaultDirName={localappdata}\{#MyAppName}

; Desabilita a página de seleção de pasta, pois a instalação é sempre no local padrão.
DisableDirPage=yes
; Desabilita a página de grupo do Menu Iniciar.
DisableProgramGroupPage=yes

; Diretório de saída e nome do arquivo do instalador.
OutputDir=Output
OutputBaseFilename=Instalador_SistemaHotel

; Ícone do arquivo do instalador.
; SetupIconFile={#AppIcon}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Não exige privilégios de administrador para instalar.
PrivilegesRequired=lowest

; Adiciona informações de versão ao executável do instalador.
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription="Instalador do {#MyAppName}"
VersionInfoTextVersion="{#MyAppVersion}"

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
; Permite ao usuário escolher se quer um ícone na área de trabalho.
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Arquivo principal da aplicação, gerado pelo PyInstaller na pasta 'dist'.
Source: "dist/{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Copia o ícone para a pasta de instalação para ser usado nos atalhos e na janela do app.
; A linha abaixo é desnecessária, pois o PyInstaller já embute o ícone no .exe principal.
; Source: "{#AppIcon}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Atalho no Menu Iniciar.
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
; Atalho na Área de Trabalho (se a task 'desktopicon' for selecionada).
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Executa o aplicativo após a instalação ser concluída.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove arquivos e pastas criados pelo aplicativo durante a desinstalação.
Type: files; Name: "{app}\hotel.db"
Type: files; Name: "{app}\*.log"
Type: dirifempty; Name: "{app}\backups"
