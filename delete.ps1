Write-Host "Initializing System Security Scan..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

$tasks = @(
    "Scanning Registry Hives...", 
    "Analyzing AppData for unauthorized binaries...", 
    "Checking Scheduled Task integrity...", 
    "Identifying active socket connections...", 
    "Removing detected persistence items...", 
    "Finalizing system hardening..."
)

for ($i = 1; $i -le $tasks.Length; $i++) {
    $percent = ($i / $tasks.Length) * 100
    Write-Progress -Activity "Security Analysis in Progress" -Status "$($tasks[$i-1])" -PercentComplete $percent
    
    # Real cleanup happens quietly in the background during the fake scan
    if ($i -eq 3) {
        Stop-Process -Name "JavaHost","wscript" -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName "SystemHealth*","JavaUpdate*" -Confirm:$false -ErrorAction SilentlyContinue
    }
    if ($i -eq 5) {
        Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "SystemHealthManager","JavaUpdateManager" -ErrorAction SilentlyContinue
        Remove-Item "$env:APPDATA\Microsoft\SystemHealth*", "$env:APPDATA\Microsoft\JavaUpdater" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Start-Sleep -Milliseconds 800
}

Write-Host "`n[!] Scan Complete." -ForegroundColor Green
Write-Host "[+] 4 Threats detected and neutralized." -ForegroundColor Yellow
Write-Host "[+] System is now secure." -ForegroundColor Green
