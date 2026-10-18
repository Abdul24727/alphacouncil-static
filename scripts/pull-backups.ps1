<#
Off-server copy of the AlphaCouncil database backups, kept on the owner's computer
(docs/production.md, "Off-server copy"). Copies every dump in /var/backups/alphacouncil-platform that
this computer lacks, checks each one against the server's SHA-256, and keeps daily dumps 60 days and
weekly ones 400 days, counted from the time in the file name, so a dump the server has already
deleted stays here. Then it tells the server when it last succeeded
(/var/lib/acp-offsite-pull/last.json): the production monitor emails when that is more than 3 days ago.

Run by the scheduled task "AlphaCouncil backup copy" (scripts/install-backup-pull.ps1) every day at
09:00 and a few minutes after sign-in, or by hand:

    powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\AlphaCouncil-Backups\pull-backups.ps1"

Uses the computer's SSH key for root@alphacouncil.tech. Writes file names and counts only, to
pull.log next to the backups.
#>
param(
  [string]$Dest = (Join-Path $env:USERPROFILE 'AlphaCouncil-Backups'),
  [string]$Server = 'root@alphacouncil.tech'
)
$ErrorActionPreference = 'Stop'

$RemoteDir = '/var/backups/alphacouncil-platform'
$MarkerDir = '/var/lib/acp-offsite-pull'
$Marker = "$MarkerDir/last.json"
$KeepDays = @{ daily = 60; weekly = 400 }
$Ssh = Join-Path $env:WINDIR 'System32\OpenSSH\ssh.exe'
$Scp = Join-Path $env:WINDIR 'System32\OpenSSH\scp.exe'
$Opts = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=30', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=4')
$Log = Join-Path $Dest 'pull.log'
# The server's own names (deploy/acp-db-backup.sh): daily/acp_prod-20261018T092109Z.dump,
# daily/globals-….sql, weekly/acp_prod-2026-W42.dump.
$NamePattern = '^(daily|weekly)/([A-Za-z0-9_]+-(\d{8}T\d{6}Z|\d{4}-W\d{2})\.(dump|sql))$'

function Write-Log([string]$Text) {
  $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
  Add-Content -Path $Log -Value $line -Encoding UTF8
  Write-Output $line
}

# ssh and scp write progress and warnings to stderr; only the exit code decides.
function Invoke-Native([string]$Exe, [string[]]$Arguments) {
  $ErrorActionPreference = 'Continue'
  $out = & $Exe @Arguments 2>&1
  $code = $LASTEXITCODE
  $text = @($out | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { "$_" })
  $err = (@($out | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { "$_" }) -join ' ').Trim()
  if ($code -ne 0) {
    if ($err.Length -gt 300) { $err = $err.Substring(0, 300) }
    throw "$(Split-Path $Exe -Leaf) exited with $code $err"
  }
  return $text
}

# The time in a file name: 20261018T092109Z, or an ISO week (2026-W42: the Monday it starts).
function Get-StampUtc([string]$Stamp) {
  if ($Stamp -match '^(\d{4})-W(\d{2})$') {
    $jan4 = New-Object DateTime ([int]$Matches[1]), 1, 4, 0, 0, 0, ([DateTimeKind]::Utc)
    $monday = $jan4.AddDays(-((([int]$jan4.DayOfWeek) + 6) % 7))
    return $monday.AddDays(7 * ([int]$Matches[2] - 1))
  }
  [datetime]::ParseExact($Stamp, "yyyyMMdd'T'HHmmss'Z'", [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal)
}

foreach ($d in @($Dest, (Join-Path $Dest 'daily'), (Join-Path $Dest 'weekly'))) {
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d | Out-Null }
}

try {
  $listing = Invoke-Native $Ssh ($Opts + @($Server, "cd $RemoteDir && find daily weekly -maxdepth 1 -type f -exec sha256sum {} +"))
  $remote = @{}
  foreach ($line in $listing) {
    if ($line -match '^([0-9a-f]{64})  (\S+)$') {
      $hash, $rel = $Matches[1], $Matches[2]
      if ($rel -match $NamePattern) { $remote[$rel] = $hash }
    }
  }
  if ($remote.Count -eq 0) { throw "the server listed no backups in $RemoteDir" }

  $copied = 0
  foreach ($rel in ($remote.Keys | Sort-Object)) {
    $local = Join-Path $Dest ($rel -replace '/', '\')
    if ((Test-Path $local) -and ((Get-FileHash -Algorithm SHA256 $local).Hash.ToLower() -eq $remote[$rel])) { continue }
    $part = "$local.part"
    Invoke-Native $Scp ($Opts + @('-q', "${Server}:$RemoteDir/$rel", $part)) | Out-Null
    $hash = (Get-FileHash -Algorithm SHA256 $part).Hash.ToLower()
    if ($hash -ne $remote[$rel]) {
      Remove-Item -LiteralPath $part -Force
      throw "$rel arrived with a different SHA-256 than the server's"
    }
    Move-Item -LiteralPath $part -Destination $local -Force
    $copied++
  }

  # Older than its keep time and gone from the server: delete. Anything else stays.
  $removed = 0
  foreach ($kind in @('daily', 'weekly')) {
    $cutoff = (Get-Date).ToUniversalTime().AddDays(-$KeepDays[$kind])
    foreach ($f in Get-ChildItem -LiteralPath (Join-Path $Dest $kind) -File) {
      if ($f.Name -like '*.part') { Remove-Item -LiteralPath $f.FullName -Force; continue }  # an interrupted copy
      $rel = "$kind/$($f.Name)"
      if ($remote.ContainsKey($rel) -or $rel -notmatch $NamePattern) { continue }
      if ((Get-StampUtc $Matches[3]) -lt $cutoff) { Remove-Item -LiteralPath $f.FullName -Force; $removed++ }
    }
  }

  $kept = @(Get-ChildItem -LiteralPath (Join-Path $Dest 'daily'), (Join-Path $Dest 'weekly') -File)
  $newest = @($remote.Keys | Where-Object { $_ -like 'daily/acp_prod-*' } | Sort-Object) | Select-Object -Last 1
  $newestName = ''
  if ($newest) { $newestName = $newest.Split('/')[-1] }
  $report = [ordered]@{
    at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
    files = $kept.Count
    copied = $copied
    newest = $newestName
  } | ConvertTo-Json -Compress
  # In base64 on the command line: Windows PowerShell would put a byte-order mark before anything piped to ssh.
  $b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($report))
  Invoke-Native $Ssh ($Opts + @($Server, "umask 022; install -d -m 755 $MarkerDir && echo $b64 | base64 -d > $Marker.new && mv -f $Marker.new $Marker")) | Out-Null

  Write-Log "ok: copied $copied, removed $removed, $($kept.Count) files here; newest $newestName"
  $lines = @(Get-Content -LiteralPath $Log -Encoding UTF8)
  if ($lines.Count -gt 1000) { $lines[-1000..-1] | Set-Content -LiteralPath $Log -Encoding UTF8 }
  exit 0
} catch {
  Write-Log "FAILED: $($_.Exception.Message)"
  exit 1
}
