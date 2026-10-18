<#
Install (or update) the off-server backup copy on the owner's computer (docs/production.md,
"Off-server copy"). Copies scripts/pull-backups.ps1 to %USERPROFILE%\AlphaCouncil-Backups (outside the
repo, so moving or updating the repo never breaks it), registers the scheduled task
"AlphaCouncil backup copy" for the signed-in Windows user (every day at 09:00 and 5 minutes after
sign-in; a missed 09:00 runs as soon as the computer is on), and runs it once.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install-backup-pull.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\install-backup-pull.ps1 -Remove

Needs no administrator rights. -Remove deletes the task only; the copies stay.
#>
param([switch]$Remove)
$ErrorActionPreference = 'Stop'

$TaskName = 'AlphaCouncil backup copy'
$Dest = Join-Path $env:USERPROFILE 'AlphaCouncil-Backups'
$Job = Join-Path $Dest 'pull-backups.ps1'
$User = "$env:USERDOMAIN\$env:USERNAME"

if ($Remove) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Output "removed the task '$TaskName'; the copies in $Dest stay"
  exit 0
}

if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest | Out-Null }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'pull-backups.ps1') -Destination $Job -Force

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Job`""
$daily = New-ScheduledTaskTrigger -Daily -At '09:00'
$logon = New-ScheduledTaskTrigger -AtLogOn -User $User
$logon.Delay = 'PT5M'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
# Only while the user is signed in: the job reads that user's SSH key, and no password is stored.
$principal = New-ScheduledTaskPrincipal -UserId $User -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($daily, $logon) -Settings $settings `
  -Principal $principal -Description 'Copies the alphacouncil.tech database backups to this computer (docs/production.md, "Off-server copy").' `
  -Force | Out-Null
Write-Output "task '$TaskName' registered: every day at 09:00 and 5 minutes after sign-in"

Start-ScheduledTask -TaskName $TaskName
$deadline = (Get-Date).AddMinutes(5)
do { Start-Sleep -Seconds 2; $task = Get-ScheduledTask -TaskName $TaskName } while ($task.State -eq 'Running' -and (Get-Date) -lt $deadline)
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Output "first run: result $($info.LastTaskResult) (0 = ok); next run $($info.NextRunTime)"
Get-Content -LiteralPath (Join-Path $Dest 'pull.log') -Tail 1
