#!/usr/bin/env python3
"""
timeverse-hyperframes-mcp — MCP 服务器主入口

功能简述:
    使用 FastMCP 创建 MCP 服务器，将所有 HyperFrames CLI 命令包装为 MCP 工具。
    通过 stdio 协议与 MCP 客户端（如 TimeVerseStudio）通信。

使用示例:
    # 直接运行
    python -m timeverse_hyperframes_mcp.server

    # 或作为 CLI 命令（安装后）
    timeverse-hyperframes-mcp
"""

import asyncio
import logging
import sys

from mcp.server import FastMCP

from . import __version__
from .tools import register_all

# ==================== 日志配置 ====================

logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ==================== 创建 MCP 服务器 ====================

mcp = FastMCP(
    name="timeverse-hyperframes-mcp",
    instructions="HyperFrames MCP Server — 将 HTML/CSS/JS 渲染为 MP4 视频。支持 init / preview / render / lint / TTS / transcribe 等命令。",
)


# ==================== 注册工具 ====================

register_all(mcp)


# ==================== 启动 ====================

def main() -> None:
    """启动 MCP 服务器（stdio 模式）"""
    logger.info("启动 timeverse-hyperframes-mcp v%s（stdio 模式）", __version__)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
