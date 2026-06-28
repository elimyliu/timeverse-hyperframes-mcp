"""
HyperFrames MCP 工具模块

功能简述:
    将所有工具函数注册到 FastMCP 服务器实例。
    每个子模块的 register_xxx(mcp) 函数负责注册对应的 MCP 工具。

主要方法清单:
    - register_all(mcp): 注册所有工具到指定 FastMCP 实例

使用示例:
    from . import register_all
    register_all(mcp)
"""

from . import init, render, preview, lint, media, system


def register_all(mcp) -> None:
    """注册所有 HyperFrames MCP 工具"""
    init.register_tools(mcp)
    render.register_tools(mcp)
    preview.register_tools(mcp)
    lint.register_tools(mcp)
    media.register_tools(mcp)
    system.register_tools(mcp)
