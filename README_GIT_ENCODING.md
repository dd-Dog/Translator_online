# Git 中文提交记录显示问题解决方案

## 问题描述

在 Windows PowerShell 中，git 提交记录中的中文可能显示为乱码。

## 解决方案

### 方案 1: 配置 Git 和 PowerShell 编码（推荐）

运行以下命令配置 Git 编码：

```powershell
# 设置 Git 编码
git config --global core.quotepath false
git config --global i18n.commitencoding utf-8
git config --global i18n.logoutputencoding utf-8

# 设置 PowerShell 编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

或者直接运行提供的脚本：

```powershell
.\fix-git-encoding.ps1
```

### 方案 2: 使用 Git GUI 工具

使用图形化 Git 工具（如 SourceTree、GitKraken、GitHub Desktop）可以正确显示中文提交记录。

### 方案 3: 使用 Git Bash

在 Git Bash 中运行 `git log` 通常能正确显示中文。

### 方案 4: 查看原始提交信息

使用以下命令查看提交的原始信息（可能包含正确的中文）：

```powershell
git log -1 --format=%B bd923b1 | Out-File -Encoding utf8 commit-message.txt
notepad commit-message.txt
```

### 方案 5: 修改提交信息为英文

如果提交信息已经乱码，可以使用以下方法修改：

1. **修改最近的提交**（如果还没推送）：
   ```powershell
   git commit --amend -m "新的提交信息"
   ```

2. **修改历史提交**（需要 rebase）：
   ```powershell
   git rebase -i HEAD~n  # n 是要修改的提交数量
   ```
   然后将 `pick` 改为 `reword`，保存后会打开编辑器让你修改提交信息。

## 当前提交记录

- **aa14cec**: feat: implement Web translation tool with detailed history and stage information (已修复为英文)
- **bd923b1**: 原始提交（中文，可能在 PowerShell 中显示为乱码，但在 Git GUI 中正常）

## 注意事项

1. 如果已经推送到远程仓库，修改提交历史需要使用 `git push --force`，请谨慎操作。
2. 建议团队统一使用英文提交信息，避免编码问题。
3. 如果必须使用中文，建议在提交前运行 `fix-git-encoding.ps1` 脚本配置编码。

