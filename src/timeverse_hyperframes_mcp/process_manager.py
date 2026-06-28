"""
进程管理器 — 管理长期运行的 HyperFrames 子进程

功能简述:
    管理 preview 等长期运行的后台进程。支持启动、查询、停止。
    进程信息存储在内存中，用 project_dir 作为唯一标识。

使用示例:
    mgr = ProcessManager.get_instance()
    info = await mgr.start("preview", args, cwd="/path/to/project")
    print(info["url"])
    mgr.stop("preview")
"""

import asyncio
import logging
import os
import signal
from typing import Optional

logger = logging.getLogger(__name__)


# ==================== 进程管理类 ====================

class ProcessManager:
    """
    管理长期运行的 HyperFrames 后台进程。
    使用模块级单例模式。
    """

    _instance: Optional["ProcessManager"] = None

    def __init__(self) -> None:
        self._processes: dict[str, dict] = {}

    @classmethod
    def get_instance(cls) -> "ProcessManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start(
        self,
        key: str,
        cmd: list[str],
        cwd: str,
        env: Optional[dict] = None,
        startup_timeout: int = 30,
        startup_keywords: tuple[str, ...] = ("http", "start", "preview"),
    ) -> dict:
        """
        启动一个后台进程，等待启动成功后返回。

        Args:
            key: 进程标识，如 project_dir 路径
            cmd: 命令列表
            cwd: 工作目录
            env: 环境变量
            startup_timeout: 等待启动成功的超时秒数
            startup_keywords: 检测启动成功的 stdout 关键词

        Returns:
            {
                "success": bool,
                "pid": int,
                "url": str,
                "message": str
            }
        """
        # 先停止已有的同名进程
        await self.stop(key)

        env = env or {}
        full_env = {**os.environ, **env, "PAGER": "cat"}

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=full_env,
        )

        result = {
            "success": False,
            "pid": proc.pid,
            "url": "",
            "message": f"进程已启动（PID: {proc.pid}），正在等待就绪...",
        }

        async def _read_until_ready() -> str:
            """读取 stdout 直到检测到就绪信号或超时"""
            collected = ""
            while True:
                try:
                    line_bytes = await asyncio.wait_for(
                        proc.stdout.readline(), timeout=startup_timeout
                    )
                    if not line_bytes:
                        break
                    line = line_bytes.decode("utf-8", errors="replace").rstrip()
                    collected += line + "\n"

                    # 检测 URL / 启动成功关键词
                    lower_line = line.lower()
                    if any(kw in lower_line for kw in startup_keywords):
                        # 提取 URL
                        url = ""
                        for token in line.split():
                            if token.startswith("http://") or token.startswith("https://"):
                                url = token.strip(",").strip(".")
                                break
                            if "localhost" in token or "0.0.0.0" in token or "127.0.0.1" in token:
                                url = token.strip(",").strip(".")
                                break
                        if url:
                            result["url"] = url

                        result["success"] = True
                        result["message"] = f"服务已就绪（PID: {proc.pid}）\n  访问地址: {url or '请查看输出'}\n{collected}"
                        return collected

                except asyncio.TimeoutError:
                    result["message"] = (
                        f"启动超时（{startup_timeout}s），进程仍在运行（PID: {proc.pid}）\n"
                        f"部分输出:\n{collected}"
                    )
                    if collected:
                        result["success"] = True  # 可能已经启动了，只是没捕获到 URL
                    return collected

            # 进程提前退出
            result["message"] = f"进程已退出（PID: {proc.pid}）\n输出:\n{collected}"
            return collected

        stderr_task = asyncio.create_task(self._read_stderr_background(proc))

        await _read_until_ready()

        # 存储进程信息
        self._processes[key] = {
            "process": proc,
            "cmd": cmd,
            "cwd": cwd,
            "pid": proc.pid,
            "result": result,
            "stderr_task": stderr_task,
        }

        return result

    async def _read_stderr_background(self, proc: asyncio.subprocess.Process) -> None:
        """后台读取 stderr（避免管道堵塞）"""
        try:
            while True:
                line = await proc.stderr.readline()
                if not line:
                    break
        except Exception:
            pass

    async def stop(self, key: str) -> dict:
        """
        停止一个后台进程。

        Returns:
            {"success": bool, "message": str}
        """
        info = self._processes.pop(key, None)
        if not info:
            return {"success": False, "message": f"未找到进程: {key}"}

        proc: asyncio.subprocess.Process = info["process"]
        pid = proc.pid

        try:
            if proc.returncode is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.send_signal(signal.SIGKILL)
                    await proc.wait()
            return {"success": True, "message": f"进程已停止（PID: {pid}）"}
        except ProcessLookupError:
            return {"success": True, "message": f"进程已退出（PID: {pid}）"}
        except Exception as exc:
            return {"success": False, "message": f"停止进程失败: {exc}"}

    def get_status(self, key: str) -> dict:
        """查询进程状态"""
        info = self._processes.get(key)
        if not info:
            return {"running": False, "pid": None, "result": None}

        proc = info["process"]
        return {
            "running": proc.returncode is None,
            "pid": proc.pid,
            "returncode": proc.returncode,
            "result": info["result"],
            "cmd": info["cmd"],
            "cwd": info["cwd"],
        }

    def list_all(self) -> dict[str, dict]:
        """列出所有进程"""
        result = {}
        for key, info in self._processes.items():
            proc = info["process"]
            result[key] = {
                "running": proc.returncode is None,
                "pid": proc.pid,
                "cmd": " ".join(info["cmd"]),
            }
        return result
