# Git 中文编码修复脚本
# 使用方法: .\fix-git-encoding.ps1

# 设置 PowerShell 输出编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 配置 Git 编码设置
git config --global core.quotepath false
git config --global i18n.commitencoding utf-8
git config --global i18n.logoutputencoding utf-8

Write-Host "Git 编码配置已更新！" -ForegroundColor Green
Write-Host ""
Write-Host "现在可以正确显示中文提交记录了：" -ForegroundColor Yellow
Write-Host ""

# 显示最近的提交记录
git log --oneline -5

