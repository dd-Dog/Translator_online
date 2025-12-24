# Please install OpenAI SDK first: `pip3 install openai`
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量获取API密钥，如果没有则使用硬编码的（仅用于测试）
api_key = os.getenv("DEEPSEEK_API_KEY") or "sk-67103734d35443559292138651639229"

if not api_key:
    print("错误: 未找到DEEPSEEK_API_KEY环境变量")
    sys.exit(1)

print("正在测试 DeepSeek API...")
print(f"使用API密钥: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '****'}")
print("-" * 50)

try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"  # 注意：需要添加 /v1 路径
    )
    
    print("发送请求到 DeepSeek API...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello, please respond in Chinese."},
        ],
        stream=False,
        temperature=0.7
    )
    
    print("✅ API调用成功！")
    print("-" * 50)
    print("响应内容:")
    print(response.choices[0].message.content)
    print("-" * 50)
    
    # 显示使用信息
    if hasattr(response, 'usage'):
        usage = response.usage
        print(f"Token使用情况:")
        print(f"  提示词tokens: {usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else 'N/A'}")
        print(f"  完成tokens: {usage.completion_tokens if hasattr(usage, 'completion_tokens') else 'N/A'}")
        print(f"  总计tokens: {usage.total_tokens if hasattr(usage, 'total_tokens') else 'N/A'}")
    
    print("\n✅ DeepSeek API 测试通过！")
    
except Exception as e:
    print(f"❌ API调用失败: {str(e)}")
    print("-" * 50)
    
    # 检查常见错误
    error_str = str(e)
    if '401' in error_str or 'Unauthorized' in error_str:
        print("⚠️  错误: API密钥无效")
        print("   请检查:")
        print("   1. API密钥是否正确")
        print("   2. 是否在.env文件中设置了DEEPSEEK_API_KEY")
        print("   3. API密钥是否已过期或被撤销")
    elif '402' in error_str or 'Insufficient Balance' in error_str:
        print("⚠️  错误: API余额不足")
        print("   请登录DeepSeek账户检查余额并充值")
    elif '429' in error_str or 'Rate limit' in error_str:
        print("⚠️  错误: 请求频率过高")
        print("   请稍后重试")
    elif 'Connection' in error_str or 'timeout' in error_str.lower():
        print("⚠️  错误: 网络连接问题")
        print("   请检查网络连接")
    else:
        print(f"   错误详情: {type(e).__name__}: {str(e)}")
    
    sys.exit(1)