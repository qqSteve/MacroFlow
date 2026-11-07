#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#define AppName "MacroFlow"

[Setup]
AppId={{DA3DFBAF-4905-4337-B858-83415D7B3FCA}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=MacroFlow Project
DefaultDirName={autopf}\MacroFlow
DefaultGroupName=MacroFlow
OutputDir=..\installer_output
OutputBaseFilename=MacroFlow-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\MacroFlow.exe
PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Значки:"; Flags: unchecked

[Files]
Source: "..\dist\MacroFlow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MacroFlow"; Filename: "{app}\MacroFlow.exe"
Name: "{autodesktop}\MacroFlow"; Filename: "{app}\MacroFlow.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MacroFlow.exe"; Description: "Запустить MacroFlow"; Flags: nowait postinstall skipifsilent
