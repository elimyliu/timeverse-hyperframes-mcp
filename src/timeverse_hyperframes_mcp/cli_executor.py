"""
CLI 执行器 — 统一执行 HyperFrames CLI 命令

功能简述:
    提供异步执行 npx hyperframes 命令的统一接口。
    处理命令超时、错误捕获、标准输出解析。

主要方法清单:
    - run_hyperframes: 执行任意 hyperframes 子命令
    - check_environment: 检测 ffmpeg / node 环境
    - parse_lint_output: 解析 lint --json 输出
    - find_workspace: 查找或创建项目工作目录

使用示例:
    result = await run_hyperframes(["init", "my-video", "--non-interactive"])
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ==================== 常量定义 ====================

DEFAULT_TIMEOUT = 300  # 默认超时（秒，首次 npx 下载约 30-60 秒）
RENDER_TIMEOUT = 600  # 渲染超时（秒）
WORKSPACE_ENV_VAR = "HYPERFRAMES_WORKSPACE_DIR"


# ==================== 核心方法 ====================

def _resolve_hyperframes_command() -> tuple[list[str], str]:
    """
    解析 hyperframes 可执行路径。
    优先使用全局安装的 hyperframes，否则回退到 npx hyperframes。

    Returns:
        (cmd_parts, display_name)
        如 (["hyperframes"], "hyperframes") 或 (["npx", "hyperframes"], "npx hyperframes")
    """
    global_cmd = shutil.which("hyperframes")
    if global_cmd:
        return [global_cmd], "hyperframes"
    return ["npx", "hyperframes"], "npx hyperframes"


async def run_hyperframes(
    args: list[str],
    cwd: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """
    执行 hyperframes <args> 命令（优先全局命令，回退 npx）

    Args:
        args: 子命令及参数列表，如 ["init", "my-video", "--non-interactive"]
        cwd: 工作目录，默认为 WORKSPACE_ENV_VAR 指向的目录或当前目录
        timeout: 超时秒数

    Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "exit_code": int,
            "command": str
        }

    Raises:
        TimeoutError: 命令执行超时
    """
    base_cmd, display_name = _resolve_hyperframes_command()
    cmd = [*base_cmd, *args]
    cmd_str = f"{display_name} {' '.join(args)}"

    if cwd is None:
        cwd = os.environ.get(WORKSPACE_ENV_VAR, os.getcwd())

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PAGER": "cat"},
            ),
            timeout=timeout,
        )
        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode("utf-8", errors="replace").strip()
        stderr_str = stderr.decode("utf-8", errors="replace").strip()

        return {
            "success": proc.returncode == 0,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": proc.returncode or 0,
            "command": cmd_str,
        }
    except asyncio.TimeoutError:
        raise TimeoutError(f"命令超时（{timeout}s）: {cmd_str}")
    except FileNotFoundError:
        hints = "请安装 Node.js >= 22，或执行 npm install -g hyperframes 全局安装"
        return {
            "success": False,
            "stdout": "",
            "stderr": f"未找到 hyperframes / npx 命令。{hints}",
            "exit_code": -1,
            "command": cmd_str,
        }


async def check_environment() -> dict:
    """
    检测运行环境是否满足 HyperFrames 要求

    Returns:
        {
            "node_ok": bool, "node_version": str,
            "ffmpeg_ok": bool, "ffmpeg_version": str,
            "npx_ok": bool,
            "all_ok": bool
        }
    """
    checks = {
        "node_ok": False,
        "node_version": "",
        "ffmpeg_ok": False,
        "ffmpeg_version": "",
        "npx_ok": False,
        "all_ok": False,
    }

    # 检测 Node.js
    try:
        proc = await asyncio.create_subprocess_exec(
            "node", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        version = stdout.decode("utf-8", errors="replace").strip()
        checks["node_version"] = version
        checks["node_ok"] = bool(version) and proc.returncode == 0
    except FileNotFoundError:
        checks["node_version"] = "未安装"

    # 检测 npx
    try:
        proc = await asyncio.create_subprocess_exec(
            "npx", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        checks["npx_ok"] = proc.returncode == 0
    except FileNotFoundError:
        pass

    # 检测 ffmpeg
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            first_line = stdout.decode("utf-8", errors="replace").split("\n")[0].strip()
            checks["ffmpeg_version"] = first_line
            checks["ffmpeg_ok"] = True
    except FileNotFoundError:
        checks["ffmpeg_version"] = "未安装"

    checks["all_ok"] = checks["node_ok"] and checks["ffmpeg_ok"] and checks["npx_ok"]
    return checks


def parse_lint_json(stdout: str) -> dict:
    """
    解析 hyperframes lint --json 输出

    Args:
        stdout: lint --json 的标准输出

    Returns:
        解析后的 lint 结果字典，包含 errorCount, warningCount, findings 等字段
    """
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": "无法解析 lint 输出", "raw": stdout}


# ==================== 工具函数 ====================

def find_workspace() -> str:
    """
    获取工作目录（优先从环境变量读取，否则用当前目录）

    Returns:
        工作目录绝对路径
    """
    workspace = os.environ.get(WORKSPACE_ENV_VAR)
    if workspace and os.path.isdir(workspace):
        return workspace
    return os.getcwd()
