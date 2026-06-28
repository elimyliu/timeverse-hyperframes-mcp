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
import threading

from mcp.server import FastMCP

from . import __version__
from .cli_executor import _resolve_hyperframes_command, run_hyperframes
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

# ==================== 后台预热 ====================

_WARMED_UP = False


async def _warmup_npx_cache() -> None:
    """
    后台预热 npx 缓存。
    提前下载 hyperframes npm 包，让后续工具调用更快。
    """
    global _WARMED_UP
    try:
        logger.info("后台预热：检测 hyperframes CLI...")
        base_cmd, display_name = _resolve_hyperframes_command()
        if "npx" in base_cmd:
            logger.info("后台预热：通过 %s 下载 hyperframes 包（首次需联网，约 30-60 秒）...", display_name)
            result = await run_hyperframes(["--help"], timeout=180)
            if result["success"]:
                logger.info("后台预热：完成")
            else:
                logger.warning("后台预热：%s", result["stderr"][:200])
        else:
            logger.info("后台预热：全局 hyperframes 命令已可用，跳过")
        _WARMED_UP = True
    except Exception as exc:
        logger.warning("后台预热失败（不影响后续使用）: %s", exc)
        _WARMED_UP = True  # 标记为已尝试


def _start_background_warmup() -> None:
    """在后台线程中启动预热"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_warmup_npx_cache())
    except Exception:
        pass
    finally:
        loop.close()


# ==================== 注册工具 ====================

register_all(mcp)


# ==================== 启动 ====================

def main() -> None:
    """启动 MCP 服务器（stdio 模式），同时后台预热 npx 缓存"""
    logger.info(
        "启动 timeverse-hyperframes-mcp v%s（stdio 模式），后台预热 hyperframes CLI...",
        __version__,
    )
    threading.Thread(target=_start_background_warmup, daemon=True).start()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
