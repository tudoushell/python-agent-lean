# AI Chat Service

一个基于 FastAPI 的轻量级 AI 聊天服务，支持普通聊天响应和流式聊天响应。项目通过 OpenAI Python SDK 访问 OpenAI 兼容接口，可用于对接 OpenAI、Ollama、vLLM、LM Studio、OneAPI 等兼容服务。

## 功能

- 健康检查接口
- 普通聊天接口
- 流式聊天接口
- 基于 `.env` 的配置管理
- 请求日志记录
- 统一异常响应
- 预置多套 Prompt 模板

## 项目结构

```text
ai_chat_service/
  app/
    main.py                 FastAPI 应用入口
    llm_config.py           LLM 客户端与调用逻辑
    schemas.py              请求和响应模型
    core/
      config.py             配置读取
      exception.py          异常处理
      logging_config.py     日志配置
    middleware/
      request_log.py        请求日志中间件
  prompts/
    general/                通用助手 Prompt
    interviewer/            Java 面试官 Prompt
    java_teacher/           Java 老师 Prompt
    summary/                总结助手 Prompt
    tool_assistant/         工具助手 Prompt
requirements.txt
README.md
```

## 环境要求

- Python 3.12 或兼容版本
- 可访问的 OpenAI 兼容 API 服务

## 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置

在项目根目录创建 `.env` 文件：

```env
BASE_URL=http://127.0.0.1:11434/v1
API_KEY=your-api-key
MODEL_NAME=qwen3-vl:2b
LOG_LEVEL=INFO
```

配置说明：

| 变量 | 说明 |
| --- | --- |
| `BASE_URL` | OpenAI 兼容 API 地址 |
| `API_KEY` | API Key |
| `MODEL_NAME` | 模型名称 |
| `LOG_LEVEL` | 日志级别，默认 `INFO` |

## 启动服务

```bash
source .venv/bin/activate
uvicorn ai_chat_service.app.main:api --reload
```

默认服务地址：

```text
http://127.0.0.1:8000
```

FastAPI 自动生成的接口文档：

```text
http://127.0.0.1:8000/docs
```

## 接口说明

### 健康检查

```http
GET /health
```

示例：

```bash
curl http://127.0.0.1:8000/health
```

响应：

```json
{
  "status": "ok"
}
```

### 普通聊天

```http
GET /chat?message=你好
```

示例：

```bash
curl "http://127.0.0.1:8000/chat?message=你好"
```

响应：

```json
{
  "answer": "你好，有什么可以帮你？"
}
```

### 流式聊天

```http
GET /chat2?message=介绍一下FastAPI
```

示例：

```bash
curl -N "http://127.0.0.1:8000/chat2?message=介绍一下FastAPI"
```

响应为流式文本。

## Prompt 模板

`ai_chat_service/prompts` 目录下预置了多套 Prompt：

- `general`: 通用 AI 助手
- `java_teacher`: Java 后端老师
- `interviewer`: Java 高级面试官
- `summary`: 内容总结助手
- `tool_assistant`: 企业业务工具助手

当前主流程尚未自动加载这些 Prompt 模板。如需支持多角色聊天，可以在接口中增加 `prompt_type` 参数，并根据该参数读取对应目录下的 `system.md` 和 `user.md`。

## 注意事项

- 当前 `/chat` 和 `/chat2` 使用 GET 请求传递消息，适合本地调试。生产环境建议改为 POST 请求。
- `schemas.py` 中已定义 `ChatRequest`，但当前接口暂未使用。
- 如果对接的服务需要真实鉴权，请确认 LLM 客户端初始化时使用的是 `.env` 中的 `API_KEY`。
- 流式接口当前返回文本流，如需标准 SSE，可以将每个分片包装为 `data: ...\n\n`。

## 开发检查

可以运行下面的命令做基础语法检查：

```bash
source .venv/bin/activate
python -m compileall -q ai_chat_service
```
