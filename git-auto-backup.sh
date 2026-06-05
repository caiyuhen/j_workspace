#!/bin/bash
# Git Auto Backup Script
# Target: http://192.168.0.76:10086/root/Reinforcement_Learning.git
# Branch: main

repo="/d/workspace"
remote="origin"
branch="main"
timestamp=$(date +"%Y-%m-%d %H:%M")
commitMsg="Auto backup: $timestamp"

cd $repo

echo "========== Git 自动备份开始 =========="
echo "时间：$timestamp"
echo "仓库：$repo"
echo "远程：$remote"
echo "分支：$branch"
echo "目标：http://192.168.0.76:10086/root/Reinforcement_Learning.git"
echo ""

# Git config for reliability
git config http.lowSpeedLimit 0
git config http.lowSpeedTime 600
export GIT_TERMINAL_PROMPT="0"

echo "添加文件（排除 ne4j/inputfile 目录）..."
git add -A -- ':!ne4j/inputfile/' 2>/dev/null

# Check if there is anything to commit
staged=$(git diff --cached --name-only 2>/dev/null)

if [ -n "$staged" ]; then
    echo ""
    echo "发现变更的文件（最多显示 20 个）："
    echo "$staged" | head -20
    total=$(echo "$staged" | wc -l)
    if [ "$total" -gt 20 ]; then
        echo "... 共 $total 个文件"
    fi
    echo ""
    echo "正在提交..."
    git commit -m "$commitMsg" 2>&1
    commit_status=$?
    
    if [ $commit_status -eq 0 ]; then
        echo ""
        echo "提交成功！正在推送到 GitLab..."
        git push --no-progress $remote $branch 2>&1
        push_status=$?
        if [ $push_status -eq 0 ]; then
            echo ""
            echo "✓ 推送成功！"
        else
            echo ""
            echo "✗ 推送失败"
        fi
    else
        echo "✗ 提交失败"
    fi
else
    echo ""
    echo "暂无新变更，同步远程分支..."
    git fetch $remote $branch 2>&1
    fetch_status=$?
    if [ $fetch_status -eq 0 ]; then
        echo "✓ 同步完成"
    else
        echo "✗ 同步失败"
    fi
fi

echo ""
echo "========== Git 自动备份完成 =========="
