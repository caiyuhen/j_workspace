# Git Push to GitHub Script
# This script pushes all changes to the specified GitHub repository

$ErrorActionPreference = "Stop"
$logFile = "D:\workspace\git-push.log"
$workspace = "D:\workspace"
$githubRepo = "https://github.com/caiyuhen/j_workspace.git"
$username = "caiyuhen"
$password = "Cai@177480"

function Log-Message {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logEntry
    Write-Host $logEntry
}

try {
    Log-Message "Starting Git push to GitHub..."
    Set-Location -Path $workspace
    
    # Configure Git
    Log-Message "Configuring Git..."
    git config --global http.postBuffer 524288000
    git config --global http.lowSpeedLimit 0
    git config --global http.lowSpeedTime 999999
    
    # Check current status
    Log-Message "Checking Git status..."
    $status = git status --porcelain
    if (-not $status) {
        Log-Message "No changes to commit."
        exit 0
    }
    
    # Count files
    $fileCount = ($status | Measure-Object).Count
    Log-Message "Found $fileCount files to commit."
    
    # Add all changes
    Log-Message "Adding all changes to staging area..."
    git add -A --force 2>&1 | ForEach-Object { if ($_ -match "error") { Log-Message "Git Add Warning: $_" } }
    
    # Verify staged files
    $stagedCount = git diff --cached --name-only | Measure-Object | Select-Object -ExpandProperty Count
    Log-Message "Staged $stagedCount files."
    
    # Commit
    Log-Message "Creating commit..."
    $commitDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "Auto-push to GitHub: $commitDate"
    
    $commitResult = git commit -m "$commitMsg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Commit failed: $commitResult"
    }
    Log-Message "Commit successful: $commitMsg"
    
    # Push to GitHub
    Log-Message "Pushing to GitHub repository..."
    $pushCmd = "git push --force-with-lease $githubRepo main"
    Log-Message "Executing: $pushCmd"
    
    $pushResult = git push --force-with-lease $githubRepo main 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Push failed. Error: $pushResult"
    }
    
    Log-Message "Push successful!"
    Log-Message "Repository: $githubRepo"
    Log-Message "Branch: main"
    
    # Show summary
    Log-Message "=== PUSH SUMMARY ==="
    Log-Message "Files committed: $stagedCount"
    Log-Message "Commit message: $commitMsg"
    Log-Message "Remote: $githubRepo"
    Log-Message "===================="
    
} catch {
    Log-Message "ERROR: $($_.Exception.Message)"
    exit 1
}
