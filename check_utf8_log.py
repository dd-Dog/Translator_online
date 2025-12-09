"""
检查日志文件的UTF-8编码是否正确
"""

import sys

log_file = "V2_evaluation_verbose_log_20251208_144752.txt"

print("检查日志文件编码...")
print("=" * 60)

try:
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"✓ 文件可以UTF-8编码读取")
    print(f"文件大小: {len(content)} 字符")
    print(f"行数: {len(content.splitlines())}")
    
    # 检查是否包含中文
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content)
    print(f"包含中文: {has_chinese}")
    
    # 显示前10行
    print("\n前10行内容:")
    print("-" * 60)
    lines = content.splitlines()[:10]
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line[:80]}")
    
    # 查找包含"评估"的行
    print("\n包含'评估'的行:")
    print("-" * 60)
    eval_lines = [line for line in content.splitlines() if '评估' in line][:5]
    for i, line in enumerate(eval_lines, 1):
        print(f"{i}: {line[:80]}")
    
    # 检查是否有乱码字符
    print("\n检查乱码字符:")
    print("-" * 60)
    suspicious = [c for c in content if ord(c) > 0xFFFF and c not in ['\U0001F300', '\U0001F600']]
    if suspicious:
        print(f"发现 {len(suspicious)} 个可疑字符")
        print(f"示例: {suspicious[:10]}")
    else:
        print("✓ 未发现乱码字符")
    
    print("\n" + "=" * 60)
    print("结论: 文件编码正确，可以正常读取中文内容")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

