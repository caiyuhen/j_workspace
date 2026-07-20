<<<<<<< HEAD
<<<<<<< HEAD

$baseDir = $PSScriptRoot

$jobs = @()

Write-Host "Starting Patient Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/patient-service/src"; & py -3.14 -m uvicorn main:app --port 8003 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Simulation Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/simulation-service/src"; & py -3.14 -m uvicorn main:app --port 8001 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Visualization Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/visualization-service/src"; & py -3.14 -m uvicorn main:app --port 8002 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting OCR Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/ocr-service/src"; & py -3.14 -m uvicorn main:app --port 8004 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Report Gateway..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/report-gateway/src"; & py -3.14 -m uvicorn main:app --port 8000 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "All services started in background jobs."
Write-Host "Press Ctrl+C to stop."

try {
    while ($true) {
        foreach ($job in $jobs) {
            # Receive output from the job. 
            # Note: Since we redirected stderr to stdout (2>&1), all output comes through Receive-Job.
            $output = Receive-Job -Job $job
            if ($output) {
                # Format output with timestamp or service name if desired, 
                # but simple Write-Host is fine for now.
                Write-Host $output
            }
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping all background jobs..."
    foreach ($job in $jobs) {
        Stop-Job $job
        Remove-Job $job
    }
    Write-Host "All services stopped."
}
=======
=======
>>>>>>> origin/main

$baseDir = $PSScriptRoot

$jobs = @()

Write-Host "Starting Patient Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/patient-service/src"; & py -3.14 -m uvicorn main:app --port 8003 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Simulation Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/simulation-service/src"; & py -3.14 -m uvicorn main:app --port 8001 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Visualization Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/visualization-service/src"; & py -3.14 -m uvicorn main:app --port 8002 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting OCR Service..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/ocr-service/src"; & py -3.14 -m uvicorn main:app --port 8004 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "Starting Report Gateway..."
$jobs += Start-Job -ScriptBlock { param($baseDir); Set-Location "$baseDir/services/report-gateway/src"; & py -3.14 -m uvicorn main:app --port 8000 --reload 2>&1 } -ArgumentList $baseDir

Write-Host "All services started in background jobs."
Write-Host "Press Ctrl+C to stop."

try {
    while ($true) {
        foreach ($job in $jobs) {
            # Receive output from the job. 
            # Note: Since we redirected stderr to stdout (2>&1), all output comes through Receive-Job.
            $output = Receive-Job -Job $job
            if ($output) {
                # Format output with timestamp or service name if desired, 
                # but simple Write-Host is fine for now.
                Write-Host $output
            }
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    Write-Host "`nStopping all background jobs..."
    foreach ($job in $jobs) {
        Stop-Job $job
        Remove-Job $job
    }
    Write-Host "All services stopped."
}
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
