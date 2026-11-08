; Inno Setup script for Clips
; 1) run build.bat first (creates dist\Clips.exe)
; 2) open this file in Inno Setup and press Ctrl+F9 (Build > Compile)
; 3) the installer appears in installer_output\

#define MyAppName "Clips"
#define MyAppVersion "0.1.3"
#define MyAppPublisher "sanz & clawd"
#define MyAppExeName "Clips.exe"

[Setup]
AppId={{3FA2E02C-4484-4DB3-9A36-EE60FF1C70CF}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
OutputDir=..\installer_output
OutputBaseFilename=Clips-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; per-user install: no admin prompt (installs to %LOCALAPPDATA%\Programs\Clips)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Clips lives in the tray with no normal window, so close it ourselves before
// installing / uninstalling (otherwise the old Clips.exe stays locked).
procedure KillClips();
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  KillClips();
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    KillClips();
    // remove the "run at Windows startup" entry the app may have added
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'Clips');
  end;
  if (CurUninstallStep = usPostUninstall) and (not UninstallSilent) then
  begin
    if MsgBox('Also delete your Clips history and settings?', mbConfirmation, MB_YESNO) = IDYES then
      DelTree(ExpandConstant('{userappdata}\Clips'), True, True, True);
  end;
end;
