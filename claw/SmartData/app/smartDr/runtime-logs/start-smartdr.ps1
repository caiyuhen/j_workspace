$services = @(
  @{ Name='auth-service'; Dir='backend/auth-service'; Port=3001; Command='node server.js' },
  @{ Name='ctms-service'; Dir='backend/ctms-service'; Port=3002; Command='node server.js' },
  @{ Name='edc-service'; Dir='backend/edc-service'; Port=3003; Command='node server.js' },
  @{ Name='iwrs-service'; Dir='backend/iwrs-service'; Port=3004; Command='node server.js' },
  @{ Name='patient-folder-service'; Dir='backend/patient-folder-service'; Port=3005; Command='node server.js' },
  @{ Name='api-gateway'; Dir='backend/api-gateway'; Port=3000; Command='node server.js' },
  @{ Name='frontend'; Dir='.'; Port=8080; Command='node runtime-logs/serve-frontend.js' }
)

$started = @()
foreach ($svc in $services) {
  $out = Join-Path (Resolve-Path 'runtime-logs') ($svc.Name + '.out.log')
  $err = Join-Path (Resolve-Path 'runtime-logs') ($svc.Name + '.err.log')
  $wd = Resolve-Path $svc.Dir
  $command = "`$env:PORT='$($svc.Port)'; `$env:JWT_SECRET='dev-secret'; `$env:DATABASE_URL='postgresql://postgres:root@123@127.0.0.1:5432/clinical_trials_db'; " + $svc.Command
  $proc = Start-Process powershell -ArgumentList @('-NoProfile', '-Command', $command) -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  $started += [PSCustomObject]@{ name=$svc.Name; pid=$proc.Id; port=$svc.Port }
}
$started | ConvertTo-Json -Depth 3 | Set-Content 'runtime-logs/pids.json'
Get-Content 'runtime-logs/pids.json'
