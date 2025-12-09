"""
修复日志文件编码，确保UTF-8
"""

import sys
import io

# 确保输出使用UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def fix_log_file():
    """读取并重新保存日志文件为UTF-8"""
    input_file = "V2_evaluation_verbose_output.txt"
    output_file = "V2_evaluation_verbose_log_UTF8.txt"
    
    print("正在读取原始日志文件...")
    
    # 尝试多种编码读取
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp1252']
    content = None
    
    for enc in encodings:
        try:
            with open(input_file, 'r', encoding=enc, errors='replace') as f:
                content = f.read()
            print(f"✓ 使用 {enc} 编码成功读取文件")
            break
        except Exception as e:
            print(f"✗ 使用 {enc} 编码失败: {e}")
            continue
    
    if content is None:
        print("❌ 无法读取文件")
        return
    
    # 保存为UTF-8
    print(f"\n正在保存为UTF-8编码到: {output_file}")
    with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
        f.write(content)
    
    print("✓ 文件已保存为UTF-8编码")
    print(f"\n文件大小: {len(content)} 字符")
    print(f"输出文件: {output_file}")
    
    # 显示前几行验证
    print("\n前5行内容预览:")
    lines = content.split('\n')[:5]
    for i, line in enumerate(lines, 1):
        print(f"{i}: {line[:80]}")

if __name__ == "__main__":
    fix_log_file()

