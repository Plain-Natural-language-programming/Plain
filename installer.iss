; Inno Setup Script for Plain Language
; This creates a professional Windows installer

[Setup]
AppName=Plain Language
AppVersion=0.1.0
AppPublisher=Plain Language Team
AppPublisherURL=https://github.com/yourusername/plain-lang
AppSupportURL=https://github.com/yourusername/plain-lang
AppUpdatesURL=https://github.com/yourusername/plain-lang
DefaultDirName={pf}\Plain Language
DefaultGroupName=Plain Language
AllowNoIcons=yes
LicenseFile=
OutputDir=dist
OutputBaseFilename=PlainLanguage-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "associatepln"; Description: "Associate .pln files with Plain Language"; GroupDescription: "File associations"; Flags: checkedonce

[Files]
Source: "plain\*"; DestDir: "{app}\plain"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Plain Language"; Filename: "python"; Parameters: "-m plain.cli --version"; WorkingDir: "{app}"
Name: "{group}\Plain Language REPL"; Filename: "python"; Parameters: "-m plain.cli repl"; WorkingDir: "{app}"
Name: "{group}\Examples"; Filename: "{app}\examples"; WorkingDir: "{app}\examples"
Name: "{group}\{cm:UninstallProgram,Plain Language}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Plain Language"; Filename: "python"; Parameters: "-m plain.cli --version"; Tasks: desktopicon; WorkingDir: "{app}"

[Registry]
Root: HKCR; Subkey: ".pln"; ValueType: string; ValueName: ""; ValueData: "PlainLanguageFile"; Flags: uninsdeletevalue; Tasks: associatepln
Root: HKCR; Subkey: "PlainLanguageFile"; ValueType: string; ValueName: ""; ValueData: "Plain Language File"; Flags: uninsdeletekey; Tasks: associatepln
Root: HKCR; Subkey: "PlainLanguageFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{sys}\python.exe,0"; Tasks: associatepln
Root: HKCR; Subkey: "PlainLanguageFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """python"" ""-m"" ""plain.cli"" ""run"" ""%1"""; Tasks: associatepln

[Run]
Filename: "python"; Parameters: "-m plain.cli --version"; Description: "Verify installation"; Flags: nowait postinstall skipifsilent
Filename: "python"; Parameters: "-m plain.cli run ""{app}\examples\hello.pln"""; Description: "Run example"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  PythonPath: String;
  PathEnv: String;
  PythonScriptsPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Find Python Scripts directory and add to PATH
    if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonPath) then
    begin
      PythonScriptsPath := PythonPath + 'Scripts';
    end
    else if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonPath) then
    begin
      PythonScriptsPath := PythonPath + 'Scripts';
    end
    else if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', PythonPath) then
    begin
      PythonScriptsPath := PythonPath + 'Scripts';
    end;
    
    // Add Python Scripts to PATH if not already there
    if PythonScriptsPath <> '' then
    begin
      RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', PathEnv);
      if Pos(PythonScriptsPath, PathEnv) = 0 then
      begin
        PathEnv := PathEnv + ';' + PythonScriptsPath;
        RegWriteStringValue(HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', PathEnv);
      end;
    end;
  end;
end;

function InitializeSetup(): Boolean;
var
  PythonVersion: String;
begin
  // Check if Python is installed
  if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.11\InstallPath', '', PythonVersion) then
  begin
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.10\InstallPath', '', PythonVersion) then
    begin
      if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'SOFTWARE\Python\PythonCore\3.9\InstallPath', '', PythonVersion) then
      begin
        MsgBox('Python 3.9+ is required. Please install Python first.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
    end;
  end;
  Result := True;
end;

