# LLM 模型切换功能使用指南

## 1. 功能概述

本项目支持在前端聊天界面动态切换多个 LLM 模型。目前支持 CherryIn 开放平台的 Qwen 系列模型，包括：
- Qwen3.6 Plus
- Qwen3.5 
- Qwen3.1

## 2. 配置文件说明

配置文件：`model_configs.json`

```json
[
  {
    "name": "qwen3.6-plus",
    "display_name": "Qwen3.6 Plus",
    "type": "openai",
    "endpoint": "https://open.cherryin.cc/v1",
    "api_key": "sk-WfQTm2EfCEY5F46QxaxMDnMPapjxDBzweimd9ouR9NQ28Qsi",
    "model": "agent/qwen3.6-plus",
    "default": true
  },
  {
    "name": "qwen3.5",
    "display_name": "Qwen3.5",
    "type": "openai",
    "endpoint": "https://open.cherryin.cc/v1",
    "api_key": "sk-WfQTm2EfCEY5F46QxaxMDnMPapjxDBzweimd9ouR9NQ28Qsi",
    "model": "agent/qwen3.5",
    "default": false
  },
  {
    "name": "qwen3.1",
    "display_name": "Qwen3.1",
    "type": "openai",
    "endpoint": "https://open.cherryin.cc/v1",
    "api_key": "sk-WfQTm2EfCEY5F46QxaxMDnMPapjxDBzweimd9ouR9NQ28Qsi",
    "model": "agent/qwen3.1",
    "default": false
  }
]
```

## 3. 前端集成

在聊天页面的输入框上方添加模型选择下拉菜单：

```tsx
<Select
  value={selectedModel}
  onChange={setSelectedModel}
  style={{ width: 150 }}
>
  <Select.Option value="qwen3.6-plus">Qwen3.6 Plus</Select.Option>
  <Select.Option value="qwen3.5">Qwen3.5</Select.Option>
  <Select.Option value="qwen3.1">Qwen3.1</Select.Option>
</Select>
```

发送消息时传递 model 参数：

```ts
const body = {
  message,
  conversation_id: currentConversationId,
  model: selectedModel, // 模型选择参数
}
```

## 4. 后端接口说明

### 4.1 聊天接口支持的参数

`POST /api/v1/conversations/chat`

请求体参数：
- `message`: 用户输入内容
- `conversation_id`: 对话ID（可选）
- `agent_type`: 代理类型（可选）
- `model`: 模型名称（可选）

### 4.2 模型切换逻辑

后端将根据 `model` 参数决定调用哪个模型配置，优先级：
1. 传入的 `model` 参数
2. 配置文件中的默认模型（default: true 的那个）
3. 本地设置的默认模型（settings.LLM_MODEL）

## 5. 部署建议

### 5.1 本地验证

确保安装了所需依赖：
```bash
pip install aiosqlite
```

### 5.2 服务启动

启动后端 API：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.3 最终效果

在前端聊天界面中选择模型后，发送的消息将使用指定模型处理，返回结果将来自指定的 LLM。