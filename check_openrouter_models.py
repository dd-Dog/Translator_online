"""检查OpenRouter支持的模型"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("未找到OPENROUTER_API_KEY")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "HTTP-Referer": "https://github.com/dd-Dog/Translator_online",
    "X-Title": "Translator Agent"
}

print("查询OpenRouter支持的模型...")
response = requests.get("https://openrouter.ai/api/v1/models", headers=headers)

if response.status_code == 200:
    data = response.json()
    models = data.get('data', [])
    
    print(f"\n找到 {len(models)} 个模型\n")
    
    # 查找Gemini模型
    gemini_models = [m for m in models if 'gemini' in m['id'].lower()]
    print("Gemini模型:")
    for m in gemini_models[:10]:
        print(f"  {m['id']} - {m.get('name', 'N/A')}")
    
    # 查找Claude模型
    claude_models = [m for m in models if 'claude' in m['id'].lower()]
    print("\nClaude模型:")
    for m in claude_models[:10]:
        print(f"  {m['id']} - {m.get('name', 'N/A')}")
else:
    print(f"错误: {response.status_code}")
    print(response.text)

