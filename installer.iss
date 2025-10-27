[Setup]
AppName=System Monitor Dashboard
AppVersion=1.4
DefaultDirName={pf}\SystemMonitor
DefaultGroupName=System Monitor
OutputDir=output
OutputBaseFilename=SystemMonitor_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\SystemMonitor.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\System Monitor"; Filename: "{app}\SystemMonitor.exe"
Name: "{userdesktop}\System Monitor"; Filename: "{app}\SystemMonitor.exe"

[Run]
Filename: "{app}\SystemMonitor.exe"; Description: "Launch System Monitor"; Flags: postinstall nowait skipifsilent