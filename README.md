# TimeVerse HyperFrames MCP

将 [HyperFrames](https://github.com/heygen-com/hyperframes) CLI 包装为 MCP 工具服务，让 AI Agent 可以：
- 创建/初始化视频项目
- 实时预览 HTML 视频
- 渲染为 MP4/WebM
- 检查语法完整性
- 文本转语音 / 音频转录

## 前置依赖

- Python >= 3.11
- Node.js >= 22
- FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu
sudo apt install ffmpeg
```

## 安装

### 方式一：pip 安装

```bash
pip install -e .
```

### 方式二：uvx 运行（无需安装）

需要先安装 [uv](https://docs.astral.sh/uv/)：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 然后直接通过 uvx 运行
uvx timeverse-hyperframes-mcp
```

`uvx` 会自动下载依赖并缓存，下次运行更快。

## 使用

### 直接运行 MCP 服务器

```bash
# pip 安装后
timeverse-hyperframes-mcp

# 或用 uvx
uvx timeverse-hyperframes-mcp

# 或用 python -m
python -m timeverse_hyperframes_mcp.server
```

### 注册到 TimeVerseStudio

在 MCP 设置页面点击 **JSON 导入**，填入以下内容：

```json
{
  "mcpServers": {
    "hyperframes": {
      "description": "HyperFrames MCP — 将 HTML/CSS/JS 渲染为 MP4 视频",
      "command": "uvx",
      "args": ["timeverse-hyperframes-mcp"]
    }
  }
}
```

或通过 API 创建：

```json
{
  "name": "hyperframes",
  "server_type": "local",
  "transport": "stdio",
  "command": "uvx",
  "args": "timeverse-hyperframes-mcp",
  "description": "HyperFrames MCP — 将 HTML/CSS/JS 渲染为 MP4 视频"
}
```

完整示例见 `examples/timeverse-integration.json`。

## 可用工具

| 工具 | 对应 CLI 命令 | 说明 |
|---|---|---|
| `hyperframes_init` | `npx hyperframes init` | 创建视频项目 |
| `hyperframes_list_templates` | - | 列出可用模板 |
| `hyperframes_render` | `npx hyperframes render` | 渲染视频 |
| `hyperframes_preview` | `npx hyperframes preview` | 启动本地预览 |
| `hyperframes_lint` | `npx hyperframes lint` | 语法检查 |
| `hyperframes_doctor` | `npx hyperframes doctor` | 环境检测 |
| `hyperframes_info` | `npx hyperframes info` | 版本信息 |
| `hyperframes_upgrade` | `npx hyperframes upgrade` | 检查更新 |
| `hyperframes_compositions` | `npx hyperframes compositions` | 列出 composition |
| `hyperframes_benchmark` | `npx hyperframes benchmark` | 性能基准测试 |
| `hyperframes_tts` | `npx hyperframes tts` | 文本转语音 |
| `hyperframes_list_voices` | `npx hyperframes tts --list` | 列出语音角色 |
| `hyperframes_transcribe` | `npx hyperframes transcribe` | 音频/视频转录 |

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `HYPERFRAMES_WORKSPACE_DIR` | 视频项目工作目录 | 当前工作目录 |
