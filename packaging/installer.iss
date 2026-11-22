; Inno Setup 6 Per-User Installer for Suno Director (`sudirector`) + Global AI Skills

#ifndef MyAppVersion
  #define MyAppVersion "0.2.0"
#endif

[Setup]
AppId={{B4A1E9F2-7D3C-48E5-9A1B-6C0E4D2F81A3}
AppName=Suno Director
AppVersion={#MyAppVersion}
AppVerName=Suno Director {#MyAppVersion}
AppPublisher=codevcn
AppPublisherURL=https://github.com/codevcn/suno-director
AppSupportURL=https://github.com/codevcn/suno-director/issues
DefaultDirName={localappdata}\Programs\SunoDirector
DefaultGroupName=Suno Director
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ChangesEnvironment=yes
CloseApplications=yes
RestartApplications=no
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
OutputDir=..\dist\installer
OutputBaseFilename=SunoDirector-Setup-{#MyAppVersion}
SetupIconFile=..\assets\logos\music-director.ico
UninstallDisplayIcon={app}\sudirector.exe
WizardImageFile=..\assets\logos\inno-wizard.bmp
WizardSmallImageFile=..\assets\logos\inno-wizard-small.bmp
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addtopath"; Description: "Add sudirector CLI to current user PATH"; Flags: checkedonce
Name: "skill_codex"; Description: "Install Global AI Skill for Codex (~\\.codex\\skills\\suno-director)"; Flags: checkedonce
Name: "skill_antigravity"; Description: "Install Global AI Skill for Antigravity (~\\.gemini\\config\\skills\\suno-director)"; Flags: checkedonce
Name: "skill_claude"; Description: "Install Global AI Skill for Claude Code (~\\.claude\\skills\\suno-director)"; Flags: checkedonce

[Files]
Source: "..\dist\sudirector\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "global-skill\suno-director\*"; DestDir: "{%USERPROFILE}\.codex\skills\suno-director"; Tasks: skill_codex; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "global-skill\suno-director\*"; DestDir: "{%USERPROFILE}\.gemini\config\skills\suno-director"; Tasks: skill_antigravity; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "global-skill\suno-director\*"; DestDir: "{%USERPROFILE}\.claude\skills\suno-director"; Tasks: skill_claude; Flags: ignoreversion recursesubdirs createallsubdirs

[Code]
const
  ENV_KEY = 'Environment';

function NormalizePathPart(const S: string): string;
begin
  Result := Trim(S);
  while (Length(Result) > 0) and (Result[Length(Result)] = '\') do
    Delete(Result, Length(Result), 1);
end;

procedure AddDirToUserPath(const DirToAdd: string);
var
  Paths, NormDir, Check: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, ENV_KEY, 'Path', Paths) then
    Paths := '';
  NormDir := NormalizePathPart(DirToAdd);
  Check := ';' + Uppercase(Paths) + ';';
  if (Pos(';' + Uppercase(NormDir) + ';', Check) > 0) or
     (Pos(';' + Uppercase(NormDir + '\') + ';', Check) > 0) then
    exit;
  if (Length(Paths) > 0) and (Paths[Length(Paths)] <> ';') then
    Paths := Paths + ';';
  Paths := Paths + NormDir;
  RegWriteExpandStringValue(HKEY_CURRENT_USER, ENV_KEY, 'Path', Paths);
end;

procedure RemoveDirFromUserPath(const DirToRemove: string);
var
  Paths, NormDir, Entry, OutPaths: string;
  P: Integer;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, ENV_KEY, 'Path', Paths) then
    exit;
  NormDir := Uppercase(NormalizePathPart(DirToRemove));
  OutPaths := '';
  while Length(Paths) > 0 do
  begin
    P := Pos(';', Paths);
    if P = 0 then
    begin
      Entry := Paths;
      Paths := '';
    end else
    begin
      Entry := Copy(Paths, 1, P - 1);
      Delete(Paths, 1, P);
    end;
    if (Length(Trim(Entry)) > 0) and (Uppercase(NormalizePathPart(Entry)) <> NormDir) then
    begin
      if Length(OutPaths) > 0 then
        OutPaths := OutPaths + ';';
      OutPaths := OutPaths + Entry;
    end;
  end;
  RegWriteExpandStringValue(HKEY_CURRENT_USER, ENV_KEY, 'Path', OutPaths);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtopath') then
    AddDirToUserPath(ExpandConstant('{app}'));
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    RemoveDirFromUserPath(ExpandConstant('{app}'));
end;
