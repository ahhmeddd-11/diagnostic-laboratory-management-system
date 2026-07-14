#define MyAppName "UNILAB Diagnostic Laboratory Management System"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Ahmed"
#define MyAppExeName "UNILAB.exe"

[Setup]
AppId={{F85FBD48-9D2E-4B1C-AE62-UNILAB2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\UNILAB
DefaultGroupName=UNILAB

DisableProgramGroupPage=yes

OutputDir=Installer
OutputBaseFilename=UNILAB_Setup_v1.0.0

Compression=lzma2
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin

SetupIconFile=assets\icons\logo.ico
UninstallDisplayIcon={app}\UNILAB.exe

ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\UNILAB\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\UNILAB"; Filename: "{app}\UNILAB.exe"
Name: "{autodesktop}\UNILAB"; Filename: "{app}\UNILAB.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\UNILAB.exe"; Description: "Launch UNILAB"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    WizardForm.StatusLabel.Caption :=
      'Installing UNILAB Diagnostic Laboratory Management System...';
  end;
end;