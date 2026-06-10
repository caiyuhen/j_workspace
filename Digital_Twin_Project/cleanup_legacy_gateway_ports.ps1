param(
    [int[]]$Ports = @(8000, 8003, 9000),
    [int]$Attempts = 3
)

function Get-ListeningConnections {
    param([int]$Port)

    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
}

foreach ($port in $Ports) {
    Write-Host "Checking port $port..."

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        $connections = @(Get-ListeningConnections -Port $port)
        if (-not $connections) {
            Write-Host "Port $port is clear."
            break
        }

        foreach ($connection in $connections) {
            $procId = $connection.OwningProcess
            Write-Host "Attempt ${attempt}: stopping PID ${procId} on port ${port}"
            try {
                Stop-Process -Id $procId -Force -ErrorAction Stop
            }
            catch {
                & taskkill /PID $procId /F | Out-Null
            }
        }

        Start-Sleep -Seconds 1
    }

    $remaining = @(Get-ListeningConnections -Port $port)
    if ($remaining) {
        $remainingPids = ($remaining | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique) -join ", "
        Write-Warning "Port $port is still occupied by PID(s): $remainingPids"
    }
    else {
        Write-Host "Port $port cleanup complete."
    }
}
