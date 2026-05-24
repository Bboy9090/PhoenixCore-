; Bobby's PhoenixDrive - NSIS Installer Script
; Creates Windows installer for desktop app

!include "MUI2.nsh"
!include "x64.nsh"

; Basic settings
Name "Bobby's PhoenixDrive"
OutFile "dist\PhoenixDrive-1.0.0-installer.exe"
InstallDir "$PROGRAMFILES\PhoenixDrive"
InstallDirRegKey HKCU "Software\PhoenixDrive" ""

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
    SetOutPath "$INSTDIR"
    
    ; Copy executable
    File "dist\PhoenixDrive.exe"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\PhoenixDrive"
    CreateShortCut "$SMPROGRAMS\PhoenixDrive\PhoenixDrive.lnk" "$INSTDIR\PhoenixDrive.exe"
    CreateShortCut "$SMPROGRAMS\PhoenixDrive\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    CreateShortCut "$DESKTOP\PhoenixDrive.lnk" "$INSTDIR\PhoenixDrive.exe"
    
    ; Write registry
    WriteRegStr HKCU "Software\PhoenixDrive" "" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixDrive" "DisplayName" "Bobby's PhoenixDrive"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixDrive" "UninstallString" "$INSTDIR\uninstall.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\PhoenixDrive.exe"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\PhoenixDrive\PhoenixDrive.lnk"
    Delete "$SMPROGRAMS\PhoenixDrive\Uninstall.lnk"
    RMDir "$SMPROGRAMS\PhoenixDrive"
    
    Delete "$DESKTOP\PhoenixDrive.lnk"
    
    DeleteRegKey HKCU "Software\PhoenixDrive"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhoenixDrive"
SectionEnd
