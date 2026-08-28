; 小七 Windows 安装程序 (Inno Setup)
; 用 Inno Setup 6 编译: iscc packaging\installer.iss

#define MyAppName "小七"
#define MyAppVersion "0.1.0"
#define MyAppExeName "xiaoqi.exe"
#define MyAppDir "dist\xiaoqi"

[Setup]
AppId={{8E5C0E8C-3A5B-4F2D-9C11-XIAOQI0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Xiaoqi
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=dist
OutputBaseFilename=小七 Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
; 注：本机 Inno Setup 6.7.3 的 Languages\ 目录无 ChineseSimplified.isl（官方默认不含中文）。
; 故暂用 English 编译；如需中文界面，从 Inno Setup 官网下载 ChineseSimplified.isl 放入该目录后取消下一行注释。
; Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 不删除用户数据 %APPDATA%\xiaoqi（默认保留记忆）
