# Register the APIx daily collection clock in Windows Task Scheduler.
#
# Runs once a day at 03:00 LOCAL machine time. If this machine is not on IST,
# adjust -At accordingly: New-ScheduledTaskTrigger has no timezone parameter,
# so "03:00 IST" is only true when the machine's clock is IST.
#
# The task invokes scripts/run_daily_collection.py, which:
#   - never collects a date later than today,
#   - replaces rather than duplicates a date already in the log (so a
#     -StartWhenAvailable catch-up run after a missed day cannot double-count),
#   - writes a `failed` row to the audit log if the run errors, so a failure is
#     never indistinguishable from "not due yet".
#
# stdout and stderr are captured to logs/daily_collection.log. Without this,
# a scheduled failure leaves no trace anywhere.

$ErrorActionPreference = "Stop"

$TaskName    = "APIx_Daily_Collection_Clock"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ScriptPath  = Join-Path $PSScriptRoot "run_daily_collection.py"
$LogDir      = Join-Path $ProjectRoot "logs"
$LogPath     = Join-Path $LogDir "daily_collection.log"

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) { $PythonCmd = Get-Command py -ErrorAction SilentlyContinue }
if (-not $PythonCmd) {
    Write-Error "No 'python' or 'py' on PATH. Install Python 3.11+ and re-run."
    exit 1
}
$PythonExe = $PythonCmd.Source

if (-not (Test-Path $ScriptPath)) {
    Write-Error "Collection script not found at $ScriptPath"
    exit 1
}
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host "Registering scheduled task : $TaskName"
Write-Host "Target script              : $ScriptPath"
Write-Host "Python                     : $PythonExe"
Write-Host "Log file                   : $LogPath"
Write-Host "Machine timezone           : $((Get-TimeZone).Id)"

# Run through cmd so both streams land in the log file.
$InnerCmd = "`"$PythonExe`" `"$ScriptPath`" >> `"$LogPath`" 2>&1"

$Trigger  = New-ScheduledTaskTrigger -Daily -At "03:00"
$Action   = New-ScheduledTaskAction `
                -Execute "cmd.exe" `
                -Argument "/c $InnerCmd" `
                -WorkingDirectory $ProjectRoot
$Settings = New-ScheduledTaskSettingsSet `
                -AllowStartIfOnBatteries `
                -DontStopIfGoingOnBatteries `
                -StartWhenAvailable `
                -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

try {
    $Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Unregistered existing task: $TaskName"
    }

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Daily APIx airfare collection clock for SIH-26056." | Out-Null

    Write-Host "Registered $TaskName (daily at 03:00 local time)." -ForegroundColor Green
    Write-Host "Verify with : Get-ScheduledTask -TaskName $TaskName"
    Write-Host "Run now with: Start-ScheduledTask -TaskName $TaskName"
    Write-Host "Tail log    : Get-Content '$LogPath' -Tail 20 -Wait"
}
catch {
    Write-Warning "Could not register the task automatically (this usually needs Administrator)."
    Write-Host "Equivalent command:" -ForegroundColor Yellow
    Write-Host "schtasks /Create /SC DAILY /TN `"$TaskName`" /TR `"cmd /c $InnerCmd`" /ST 03:00" -ForegroundColor Yellow
}
