"""
安全检查脚本
检查是否有API密钥泄露风险
"""

import os
import re
from pathlib import Path

def check_api_keys():
    """检查代码中是否有硬编码的API密钥"""
    print("=" * 60)
    print("🔒 安全检查 - API密钥泄露检测")
    print("=" * 60)
    
    # API密钥模式
    patterns = {
        'OpenRouter': r'sk-or-v1-[a-zA-Z0-9]{64,}',
        'OpenAI': r'sk-[a-zA-Z0-9]{32,}',
        'Qwen': r'[a-zA-Z0-9]{32,}',
        'DeepSeek': r'[a-zA-Z0-9]{32,}'
    }
    
    issues = []
    
    # 检查所有Python文件
    for py_file in Path('.').rglob('*.py'):
        # 跳过虚拟环境和缓存
        if any(skip in str(py_file) for skip in ['venv', '__pycache__', '.git']):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for key_type, pattern in patterns.items():
                        matches = re.findall(pattern, line)
                        for match in matches:
                            # 排除环境变量读取
                            if 'os.getenv' in line or 'os.environ' in line:
                                continue
                            # 排除注释
                            if line.strip().startswith('#'):
                                continue
                            
                            issues.append({
                                'file': str(py_file),
                                'line': i,
                                'type': key_type,
                                'content': line.strip()[:80]
                            })
        except Exception as e:
            pass
    
    # 检查配置文件
    config_files = ['config/models.yaml', 'config/config.yaml']
    for config_file in config_files:
        if Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for key_type, pattern in patterns.items():
                        matches = re.findall(pattern, content)
                        if matches:
                            issues.append({
                                'file': config_file,
                                'line': 'N/A',
                                'type': key_type,
                                'content': f'Found {len(matches)} potential keys'
                            })
            except:
                pass
    
    # 检查.env文件是否在git中
    print("\n【1】检查.env文件")
    print("-" * 60)
    if Path('.env').exists():
        print("✓ .env文件存在（本地）")
        
        # 检查是否在git中
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'ls-files', '.env'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                print("❌ 警告: .env文件在Git仓库中！")
                print("   请立即从Git中移除: git rm --cached .env")
            else:
                print("✓ .env文件不在Git仓库中（安全）")
        except:
            print("⚠️  无法检查Git状态")
    else:
        print("ℹ️  .env文件不存在（正常，使用环境变量）")
    
    # 检查.gitignore
    print("\n【2】检查.gitignore配置")
    print("-" * 60)
    if Path('.gitignore').exists():
        with open('.gitignore', 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
            if '.env' in gitignore_content:
                print("✓ .env已在.gitignore中")
            else:
                print("❌ 警告: .env未在.gitignore中")
            
            if '.env.*' in gitignore_content or '.env.local' in gitignore_content:
                print("✓ .env.*模式已在.gitignore中")
            else:
                print("⚠️  建议添加 .env.* 到.gitignore")
    else:
        print("❌ 警告: .gitignore文件不存在")
    
    # 检查硬编码密钥
    print("\n【3】检查硬编码的API密钥")
    print("-" * 60)
    if issues:
        print(f"❌ 发现 {len(issues)} 个潜在问题:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"\n  文件: {issue['file']}")
            print(f"  行号: {issue['line']}")
            print(f"  类型: {issue['type']}")
            print(f"  内容: {issue['content']}")
        if len(issues) > 10:
            print(f"\n  ... 还有 {len(issues) - 10} 个问题未显示")
        print("\n⚠️  请立即检查并移除硬编码的API密钥！")
    else:
        print("✓ 未发现硬编码的API密钥")
    
    # 检查环境变量
    print("\n【4】检查环境变量配置")
    print("-" * 60)
    required_vars = ['OPENROUTER_API_KEY', 'QWEN_API_KEY']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 只显示前20个字符
            masked = value[:20] + '...' if len(value) > 20 else value
            print(f"✓ {var}: {masked}")
        else:
            print(f"ℹ️  {var}: 未设置（如果不需要可以忽略）")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 安全检查总结")
    print("=" * 60)
    
    if issues:
        print("❌ 发现安全问题，请立即处理！")
        return False
    else:
        print("✅ 未发现明显的安全问题")
        print("\n建议:")
        print("  1. 确保.env文件不在Git仓库中")
        print("  2. 定期更换API密钥")
        print("  3. 不要将API密钥分享给他人")
        print("  4. 如果密钥泄露，立即在OpenRouter/Qwen平台更换")
        return True

if __name__ == "__main__":
    check_api_keys()

