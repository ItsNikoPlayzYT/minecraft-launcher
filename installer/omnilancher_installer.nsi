; OmniLauncher Installer Script
; This script creates a professional installer for OmniLauncher

!include "MUI2.nsh"
!include "FileFunc.nsh"

; General Configuration
Name "OmniLauncher"
OutFile "OmniLauncher_Installer.exe"
Unicode True
InstallDir "$PROGRAMFILES\OmniLauncher"
InstallDirRegKey HKCU "Software\OmniLauncher" ""
RequestExecutionLevel admin

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "launcher.ico"
!define MUI_UNICON "launcher.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer\header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer\wizard.bmp"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "1.6.0.0"
VIAddVersionKey "ProductName" "OmniLauncher"
VIAddVersionKey "CompanyName" "OmniLauncher Team"
VIAddVersionKey "FileVersion" "1.6.0.0"
VIAddVersionKey "ProductVersion" "1.6.0.0"
VIAddVersionKey "FileDescription" "Minecraft Launcher with Advanced Features"

; Installer Sections
Section "OmniLauncher" SecOmniLauncher
    SectionIn RO

    SetOutPath "$INSTDIR"

    ; Copy all files from dist directory
    DetailPrint "Installing OmniLauncher..."
    File /r "dist\*.*"

    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\OmniLauncher.lnk" "$INSTDIR\OmniLauncher.exe" "" "$INSTDIR\OmniLauncher.exe" 0

    ; Create start menu entries
    CreateDirectory "$SMPROGRAMS\OmniLauncher"
    CreateShortCut "$SMPROGRAMS\OmniLauncher\OmniLauncher.lnk" "$INSTDIR\OmniLauncher.exe"
    CreateShortCut "$SMPROGRAMS\OmniLauncher\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Store installation folder
    WriteRegStr HKCU "Software\OmniLauncher" "" $INSTDIR

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "DisplayName" "OmniLauncher"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "DisplayVersion" "1.6.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "Publisher" "OmniLauncher Team"
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "NoModify" 1
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher" "NoRepair" 1

SectionEnd

; Uninstaller Section
Section "Uninstall"

    ; Remove files
    Delete "$INSTDIR\OmniLauncher.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    Delete "$DESKTOP\OmniLauncher.lnk"
    RMDir /r "$SMPROGRAMS\OmniLauncher"

    ; Remove registry entries
    DeleteRegKey HKCU "Software\OmniLauncher"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OmniLauncher"

SectionEnd
