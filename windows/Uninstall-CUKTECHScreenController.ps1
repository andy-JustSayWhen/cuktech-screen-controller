[CmdletBinding()]
param([switch]$RemoveUserData)

$ErrorActionPreference = "Stop"
$InstallRoot = Join-Path $env:LOCALAPPDATA "Programs\CUKTECH Screen Controller"
$DataRoot = Join-Path $env:LOCALAPPDATA "CUKTECH Screen Controller"
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\CUKTECH Screen Controller"
$LegacyStartMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\CUKTECH Screen Controller.lnk"
$Startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\CUKTECH Screen Controller Bridge.vbs"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\CUKTECHScreenController"

Get-Process -Name "CUKTECH Screen Controller" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "CUKTECHRuntime" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 400
Remove-Item -Force -ErrorAction SilentlyContinue $LegacyStartMenu, $Startup
if (Test-Path $StartMenuDir) { Remove-Item -Recurse -Force $StartMenuDir }
if (Test-Path $InstallRoot) { Remove-Item -Recurse -Force $InstallRoot }
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $UninstallKey
Write-Host "CUKTECH Screen Controller has been removed."
if ($RemoveUserData -and (Test-Path $DataRoot)) {
    $Escaped = $DataRoot.Replace('"', '""')
    Start-Process -FilePath "$env:SystemRoot\System32\cmd.exe" `
        -ArgumentList "/d /c ping 127.0.0.1 -n 2 >nul & rmdir /s /q `"$Escaped`"" `
        -WindowStyle Hidden
    Write-Host "User screens and logs are scheduled for removal."
} else {
    Write-Host "Screens and logs were kept at: $DataRoot"
}
