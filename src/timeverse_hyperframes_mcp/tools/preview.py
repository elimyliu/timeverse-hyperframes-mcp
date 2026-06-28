"""
hyperframes_preview — 视频预览工具

功能简述:
    封装 hyperframes preview 命令，启动本地实时预览服务。
    使用进程管理器在后台运行预览服务，支持 stop_preview 停止。
    支持自定义端口，热重载。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_preview / hyperframes_stop_preview
    - hyperframes_preview: 启动预览服务
    - hyperframes_stop_preview: 停止预览服务
"""

from typing import Optional

from ..cli_executor import _resolve_hyperframes_command, find_workspace
from ..process_manager import ProcessManager


def register_tools(mcp) -> None:
    """注册预览相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_preview",
        description="启动 HyperFrames 项目的本地实时预览服务（后台运行）。热重载，编辑即更新。预览启动后会自动返回访问地址。若需停止请使用 hyperframes_stop_preview。"
    )
    async def hyperframes_preview(
        project_dir: Optional[str] = None,
        port: Optional[int] = None,
        startup_timeout: int = 30,
    ) -> str:
        """
        启动本地预览服务（后台进程）

        Args:
            project_dir: 项目目录路径。默认为当前工作空间
            port: 端口号（默认由 hyperframes 决定，通常为 3002）
            startup_timeout: 等待启动的超时秒数（默认 30）

        Returns:
            预览服务信息，包含访问地址和 PID
        """
        workspace = find_workspace() if not project_dir else project_dir

        # 检查是否已有预览进程在运行
        mgr = ProcessManager.get_instance()
        existing = mgr.get_status(workspace)
        if existing["running"]:
            return (
                f"⚠️ 该项目已有预览服务在运行（PID: {existing['pid']}）\n"
                f"   如需重启请先调用 hyperframes_stop_preview\n"
                f"   访问地址: {existing['result'].get('url', '未知') if existing.get('result') else '未知'}"
            )

        base_cmd, display_name = _resolve_hyperframes_command()
        cmd = [*base_cmd, "preview"]
        if port:
            cmd.extend(["--port", str(port)])

        cmd_display = f"{display_name} preview"
        if port:
            cmd_display += f" --port {port}"

        result = await mgr.start(
            key=workspace,
            cmd=cmd,
            cwd=workspace,
            startup_timeout=startup_timeout,
        )

        if result["success"]:
            return (
                f"✅ 预览服务已启动\n"
                f"   PID: {result['pid']}\n"
                f"   项目: {workspace}\n"
                f"   命令: {cmd_display}\n"
                f"   访问地址: {result['url'] or '请查看输出'}\n"
                f"\n{result['message']}"
            )
        else:
            return f"❌ 预览启动失败\n{result['message']}"

    @mcp.tool(
        name="hyperframes_stop_preview",
        description="停止项目的本地预览服务。需要传入 project_dir 参数。"
    )
    async def hyperframes_stop_preview(
        project_dir: Optional[str] = None,
    ) -> str:
        """
        停止正在运行的预览服务

        Args:
            project_dir: 项目目录路径。默认为当前工作空间

        Returns:
            停止结果信息
        """
        workspace = find_workspace() if not project_dir else project_dir
        mgr = ProcessManager.get_instance()
        result = await mgr.stop(workspace)
        if result["success"]:
            return f"✅ 预览服务已停止\n{result['message']}"
        else:
            return f"⚠️ {result['message']}"
