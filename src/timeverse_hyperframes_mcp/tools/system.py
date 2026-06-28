"""
hyperframes_system — 系统管理工具

功能简述:
    封装 doctor / info / upgrade / benchmark / compositions 等管理类命令。
    用于检测环境、获取版本信息、列出 composition、跑基准测试等。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_doctor / hyperframes_info / 等
"""

from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace, check_environment


def register_tools(mcp) -> None:
    """注册系统管理相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_doctor",
        description="检测 HyperFrames 运行环境（Node.js, FFmpeg, Chrome 等）。渲染前建议先运行。"
    )
    async def hyperframes_doctor(
        project_dir: Optional[str] = None,
    ) -> str:
        """
        检测运行环境

        Args:
            project_dir: 项目目录。不指定则检查全局环境

        Returns:
            环境检测结果
        """
        env_check = await check_environment()
        lines = ["🔍 HyperFrames 环境检测\n"]
        lines.append(f"  Node.js: {'✅' if env_check['node_ok'] else '❌'} {env_check['node_version']}")
        lines.append(f"  npx:     {'✅' if env_check['npx_ok'] else '❌'}")
        lines.append(f"  FFmpeg:  {'✅' if env_check['ffmpeg_ok'] else '❌'} {env_check['ffmpeg_version']}")

        if not env_check["all_ok"]:
            lines.append("\n⚠️ 环境不完整，请安装缺失依赖：")
            if not env_check["node_ok"]:
                lines.append("  - Node.js >= 22: https://nodejs.org")
            if not env_check["ffmpeg_ok"]:
                lines.append("  - FFmpeg: brew install ffmpeg / apt install ffmpeg")
            if not env_check["npx_ok"]:
                lines.append("  - npx: npm install -g npx")

        # 也跑一下 hyperframes doctor
        workspace = find_workspace() if not project_dir else project_dir
        hf_result = await run_hyperframes(["doctor"], cwd=workspace, timeout=30)
        if hf_result["stdout"]:
            lines.append(f"\n--- HyperFrames Doctor ---\n{hf_result['stdout']}")

        return "\n".join(lines)

    @mcp.tool(
        name="hyperframes_info",
        description="获取 HyperFrames 版本和环境详细信息。"
    )
    async def hyperframes_info(
        project_dir: Optional[str] = None,
    ) -> str:
        """
        获取版本和环境信息

        Args:
            project_dir: 项目目录路径

        Returns:
            版本和环境信息
        """
        result = await run_hyperframes(
            ["info"],
            cwd=find_workspace() if not project_dir else project_dir,
        )
        if result["success"]:
            return result["stdout"]
        else:
            return f"❌ 获取信息失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_upgrade",
        description="检查 HyperFrames 是否有更新版本。"
    )
    async def hyperframes_upgrade(
        check_only: bool = True,
        json_output: bool = True,
    ) -> str:
        """
        检查 HyperFrames 版本更新

        Args:
            check_only: 仅检查不升级（默认 True）
            json_output: JSON 格式输出（默认 True，适合 AI 解析）

        Returns:
            版本更新信息
        """
        args = ["upgrade"]
        if check_only:
            args.append("--check")
        if json_output:
            args.extend(["--check", "--json"])

        result = await run_hyperframes(args)

        if result["success"]:
            return result["stdout"]
        else:
            return f"❌ 检查更新失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_compositions",
        description="列出 HyperFrames 项目中的所有 composition 文件。"
    )
    async def hyperframes_compositions(
        project_dir: Optional[str] = None,
    ) -> str:
        """
        列出项目中的 composition 文件

        Args:
            project_dir: 项目目录路径

        Returns:
            composition 列表
        """
        result = await run_hyperframes(
            ["compositions"],
            cwd=find_workspace() if not project_dir else project_dir,
        )
        if result["success"]:
            return f"📄 Composition 列表：\n{result['stdout']}"
        else:
            return f"❌ 获取 composition 列表失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_benchmark",
        description="对 HyperFrames 项目运行渲染基准测试。"
    )
    async def hyperframes_benchmark(
        composition: Optional[str] = None,
        project_dir: Optional[str] = None,
    ) -> str:
        """
        运行渲染性能基准测试

        Args:
            composition: 指定的 composition 文件路径（相对于项目目录）
            project_dir: 项目目录路径

        Returns:
            基准测试结果
        """
        args = ["benchmark"]
        if composition:
            args.append(composition)

        workspace = find_workspace() if not project_dir else project_dir
        result = await run_hyperframes(args, cwd=workspace, timeout=300)

        if result["success"]:
            return f"📊 基准测试结果：\n{result['stdout']}"
        else:
            return f"❌ 基准测试失败\n{result['stderr']}"
