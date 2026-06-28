"""
hyperframes_preview — 视频预览工具

功能简述:
    封装 npx hyperframes preview 命令，启动本地实时预览服务。
    支持自定义端口，热重载。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_preview
"""

from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace


def register_tools(mcp) -> None:
    """注册预览相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_preview",
        description="启动 HyperFrames 项目的本地实时预览服务。热重载，编辑即更新。"
    )
    async def hyperframes_preview(
        project_dir: Optional[str] = None,
        port: Optional[int] = None,
    ) -> str:
        """
        启动本地预览服务

        Args:
            project_dir: 项目目录路径。默认为当前工作空间
            port: 端口号（默认 3002）

        Returns:
            预览服务信息，包含访问地址
        """
        args = ["preview"]

        if port:
            args.extend(["--port", str(port)])

        workspace = find_workspace() if not project_dir else project_dir
        # preview 是一个持续运行的服务，设置较短超时拿到初始输出即可
        result = await run_hyperframes(args, cwd=workspace, timeout=15)

        if result["success"]:
            output = result["stdout"]
            # 从 stdout 中提取 URL
            url = ""
            for line in output.split("\n"):
                if "http" in line:
                    url = line.strip()
                    break
            msg = f"✅ 预览服务已启动\n"
            if url:
                msg += f"   访问地址: {url}\n"
            msg += output
            return msg
        else:
            return f"❌ 预览启动失败\n{result['stderr']}"
