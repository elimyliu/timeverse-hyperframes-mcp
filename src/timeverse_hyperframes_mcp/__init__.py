"""
timeverse-hyperframes-mcp — MCP server for HyperFrames

功能简述:
    MCP 服务器，将 HyperFrames CLI（HTML 转视频渲染引擎）包装为 MCP 工具。
    支持视频项目初始化、预览、渲染、lint、TTS 等能力。
    兼容 TimeVerseStudio 的 MCP 注册体系（local/stdio 模式）。

主要工具清单:
    - hyperframes_init: 创建新的视频项目
    - hyperframes_render: 渲染视频为 MP4/WebM
    - hyperframes_preview: 启动本地实时预览
    - hyperframes_lint: 检查项目语法完整性
    - hyperframes_doctor: 检测运行环境
    - hyperframes_tts: 文本转语音
    - hyperframes_transcribe: 音频/视频转录文字

使用示例:
    # 作为 stdio MCP 服务器运行
    python -m timeverse_hyperframes_mcp.server
"""

__version__ = "0.1.0"
