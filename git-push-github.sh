#!/bin/bash
# Git Push Script for CTMS Project

set -e

WORKSPACE="/d/workspace"
LOG_FILE="$WORKSPACE/git-push-summary.md"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "=== Git Push Script Started ==="
echo "Timestamp: $TIMESTAMP"
echo "Working directory: $WORKSPACE"
echo ""

cd "$WORKSPACE"

# Step 1: Add all files
echo "Step 1: Adding all files to staging area..."
git add -A --force 2>&1 | grep -v "warning:" || true

# Count staged files
STAGED_COUNT=$(git diff --cached --name-only | wc -l)
echo "Staged files: $STAGED_COUNT"
echo ""

# Step 2: Commit
echo "Step 2: Creating commit..."
COMMIT_MSG="Auto-sync to GitHub: $TIMESTAMP"
git commit -m "$COMMIT_MSG" 2>&1 | tail -5 || {
    echo "No changes to commit or commit failed"
    exit 1
}
echo "Commit successful!"
echo ""

# Step 3: Push to GitHub
echo "Step 3: Pushing to GitHub..."
echo "Repository: https://github.com/caiyuhen/j_workspace.git"
git push --force-with-lease origin main 2>&1 | tail -20 || {
    echo "Push failed!"
    exit 1
}
echo ""

# Step 4: Summary
echo "=== Push Summary ==="
echo "Files committed: $STAGED_COUNT"
echo "Commit message: $COMMIT_MSG"
echo "Remote: origin (GitHub)"
echo "Branch: main"
echo "Timestamp: $TIMESTAMP"
echo "===================="
echo ""
echo "Git push completed successfully!"
