$logFile = "D:\workspace\auto_commit.log"
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Function to log messages
function Log-Message {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] $Message"
}

Log-Message "Starting auto-commit task..."

try {
    Set-Location -Path "D:\workspace"
    
    # Check for git status
    $status = git status --porcelain
    
    if ($status) {
        Log-Message "Changes detected. Committing..."
        
        # Add all changes
        git add . 2>&1 | Out-String | ForEach-Object { Log-Message "Git Add: $_" }
        
        # Commit
        $commitMsg = "Auto-commit: $date"
        git commit -m "$commitMsg" 2>&1 | Out-String | ForEach-Object { Log-Message "Git Commit: $_" }
        
        # Push to origin
        Log-Message "Pushing to origin..."
        git push origin main 2>&1 | Out-String | ForEach-Object { Log-Message "Git Push Origin: $_" }
        
        # Push to remote_rl
        Log-Message "Pushing to remote_rl..."
        git push remote_rl main 2>&1 | Out-String | ForEach-Object { Log-Message "Git Push Remote_rl: $_" }
        
        Log-Message "Auto-commit completed successfully."
    } else {
        Log-Message "No changes detected. Skipping commit."
    }
} catch {
    Log-Message "Error occurred: $($_.Exception.Message)"
}
