[Setup]
AppName=Unilab Diagnostic System
AppVersion=1.0
AppPublisher=Unilab Diagnostics
DefaultDirName={autopf}\Unilab
DefaultGroupName=Unilab
OutputDir=installer
OutputBaseFilename=Unilab_Setup_v1.0
Compression=lzma
SolidCompression=yes
DiskSpanning=no
PrivilegesRequired=admin
UninstallDisplayIcon={app}\UnilabSystem.exe

[Files]
; Include the generated executables and environment file
Source: "..\dist\UnilabSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\backup_db.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Create Desktop and Start Menu Shortcuts
Name: "{autodesktop}\Unilab Diagnostic Server"; Filename: "{app}\UnilabSystem.exe"
Name: "{group}\Unilab Diagnostic Server"; Filename: "{app}\UnilabSystem.exe"
Name: "{group}\Uninstall Unilab"; Filename: "{uninstallexe}"

[Registry]
; Configure Auto-Start on System Boot
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "UnilabServer"; ValueData: """{app}\UnilabSystem.exe"""; Flags: uninsdeletevalue

[Run]
; Option to launch the server immediately when installation finishes
Filename: "{app}\UnilabSystem.exe"; Description: "Start Unilab Server now"; Flags: nowait postinstall skipifsilent

; Register the automatic daily database backup via Windows Task Scheduler
Filename: "schtasks"; Parameters: "/create /tn ""Unilab_Daily_Backup"" /tr ""\""{app}\backup_db.exe\"""" /sc daily /st 23:00 /f"; Flags: runhidden

[UninstallRun]
; Clean up the scheduled task when uninstalling
Filename: "schtasks"; Parameters: "/delete /tn ""Unilab_Daily_Backup"" /f"; Flags: runhidden

[Code]
var
  PasswordPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  PasswordPage := CreateInputQueryPage(wpSelectDir,
    'MySQL Database Configuration', 'Please enter your local MySQL credentials.',
    'The system requires the MySQL password for the "root" user to setup the database.');
  PasswordPage.Add('MySQL Password (user: root):', True);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: String;
  Lines: TArrayOfString;
begin
  if CurStep = ssPostInstall then
  begin
    EnvFile := ExpandConstant('{app}\.env');
    SetArrayLength(Lines, 5);
    Lines[0] := 'SECRET_KEY=super-secret-key-diagnostic';
    Lines[1] := 'MYSQL_HOST=localhost';
    Lines[2] := 'MYSQL_USER=root';
    Lines[3] := 'MYSQL_PASSWORD=' + PasswordPage.Values[0];
    Lines[4] := 'MYSQL_DB=diagnostic_lab';
    SaveStringsToFile(EnvFile, Lines, False);
  end;
end;
