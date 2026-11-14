[Setup]
AppId={{B16C8B1D-0C41-4F93-9075-10937FD5E963}
AppName=Karaoke Studio
AppVersion=1.0.2
AppPublisher=Proyecto de tesis de Diego Tapia
DefaultDirName={localappdata}\Programs\Karaoke Studio
DefaultGroupName=Karaoke Studio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=KaraokeStudio-1.0.2-Setup
SetupIconFile=..\ui_live\icon.ico
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\KaraokeStudio.exe
DisableProgramGroupPage=yes
CloseApplications=no
InfoBeforeFile=ANTES-DE-INSTALAR.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; Flags: unchecked

[Files]
Source: "payload\*"; DestDir: "{app}"; Excludes: "\*\__pycache__\*,\*\tests\*,\*\test\*,*.pyc"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "tools\WebView2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{userprograms}\Karaoke Studio"; Filename: "{app}\KaraokeStudio.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Karaoke Studio"; Filename: "{app}\KaraokeStudio.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\KaraokeStudio.exe"; Description: "Abrir Karaoke Studio"; Flags: nowait postinstall skipifsilent

[Code]
function HasWebView: Boolean;
var Version: String;
begin
  Result := (RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version)
    and (Version <> '') and (Version <> '0.0.0.0'));
  if not Result then
    Result := (RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version)
      and (Version <> '') and (Version <> '0.0.0.0'));
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var Code: Integer;
begin
  Result := '';
  if not HasWebView then begin
    ExtractTemporaryFile('WebView2Setup.exe');
    if not Exec(ExpandConstant('{tmp}\WebView2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, Code) then
      Result := 'No se pudo iniciar la instalación de Microsoft WebView2. Comprueba tu conexión e inténtalo nuevamente.'
    else if not HasWebView then
      Result := 'Microsoft WebView2 aún no está disponible. Revisa tu conexión y vuelve a ejecutar este instalador.';
  end;
end;
