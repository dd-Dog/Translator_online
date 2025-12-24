# 模型配置说明

## 默认配置文件

项目提供了一个默认配置文件 `model-config.example.json`，你可以：

1. **复制并重命名**：将 `model-config.example.json` 复制为 `model-config.json`
2. **填写API密钥**：在 `model-config.json` 中填入你的真实API密钥
3. **加载配置**：在Web界面左侧"翻译Agent架构"面板的右上角，点击"加载默认配置"按钮

## 配置文件格式

```json
{
  "planner": {
    "model_type": "deepseek",
    "api_key": "sk-your-deepseek-api-key-here"
  },
  "translator_a": {
    "model_type": "deepseek",
    "api_key": "sk-your-deepseek-api-key-here"
  },
  "translator_b": {
    "model_type": "qwen",
    "api_key": "your-qwen-api-key-here"
  },
  "checker": {
    "model_type": "deepseek",
    "api_key": "sk-your-deepseek-api-key-here"
  },
  "stylist": {
    "model_type": "qwen",
    "api_key": "your-qwen-api-key-here"
  },
  "aggregator": {
    "model_type": "deepseek",
    "api_key": "sk-your-deepseek-api-key-here"
  }
}
```

## 支持的模型类型

- `deepseek` - DeepSeek模型
- `qwen` - 通义千问模型
- `doubao` - 豆包模型
- `openai` - OpenAI模型
- `gemini` - Google Gemini模型

## 注意事项

1. **API密钥安全**：配置文件中的API密钥会被保存到浏览器的本地存储中，不会上传到服务器
2. **配置文件位置**：配置文件需要放在 `public` 目录下，才能通过Web界面加载
3. **占位符**：示例文件中的 `your-xxx-api-key-here` 是占位符，需要替换为真实的API密钥

## 使用步骤

1. 编辑 `model-config.example.json`，填入你的API密钥
2. 将文件复制为 `model-config.json`（可选，也可以直接修改示例文件）
3. 在Web界面点击"加载默认配置"按钮
4. 配置会自动加载并保存到浏览器本地存储

## 手动配置

如果不使用配置文件，也可以直接在Web界面的左侧面板中：
1. 为每个阶段选择模型类型
2. 输入对应的API密钥
3. 配置会自动保存到浏览器本地存储

