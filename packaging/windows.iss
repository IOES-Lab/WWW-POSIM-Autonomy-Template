#define AppVersion "0.2.2"
[Setup]
AppName=WWW-POSIM Evaluation
AppVersion={#AppVersion}
AppId={{954D9B4D-380B-456E-AB59-743903C7F9DC}
DefaultDirName={localappdata}\WWW-POSIM
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=WWW-POSIM-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
[Files]
Source: "..\dist\www-posim\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{userprograms}\WWW-POSIM Evaluation"; Filename: "{app}\www-posim.exe"; Parameters: "evaluation"
[Run]
Filename: "{app}\www-posim.exe"; Parameters: "evaluation"; Description: "Open Evaluation"; Flags: nowait postinstall skipifsilent
