# 修复提交信息脚本
# 将乱码的中文提交信息改为英文

# 获取当前分支
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "当前分支: $branch" -ForegroundColor Cyan

# 备份当前状态
Write-Host "`n正在备份当前状态..." -ForegroundColor Yellow
git stash

# 使用 git filter-branch 修改提交信息
Write-Host "`n正在修改提交信息..." -ForegroundColor Yellow

# 创建一个临时脚本来修改提交信息
$script = @"
#!/bin/sh
if [ `$GIT_COMMIT = 'bd923b1' ]; then
    cat <<'EOF'
feat: implement Web translation tool with detailed history and stage information

- Implement FastAPI and Vue3 based Web translation interface
- Add real-time translation progress display (WebSocket)
- Implement history management with pagination and deduplication
- Add detailed translation stage information display (input, output, models used)
- Integrate evaluation functionality
- Fix duplicate history record saving issue
- Optimize frontend UI with three-column layout design
- Add detailed error handling and logging
EOF
else
    git commit-tree `$@
fi
"@

# 使用 git rebase 来修改提交信息
Write-Host "`n注意: 这将修改提交历史。如果已经推送到远程，需要使用 force push。" -ForegroundColor Red
Write-Host "`n建议: 如果已经推送到远程，请使用以下命令查看正确的提交信息:" -ForegroundColor Yellow
Write-Host "  git log --all --format='%H %s' | Select-String 'bd923b1'" -ForegroundColor Cyan
Write-Host "`n或者使用 Git GUI 工具（如 SourceTree, GitKraken）来查看，它们通常能正确显示中文。" -ForegroundColor Yellow

