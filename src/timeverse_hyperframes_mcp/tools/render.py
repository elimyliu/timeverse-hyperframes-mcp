"""
hyperframes_render — 视频渲染工具

功能简述:
    封装 npx hyperframes render 命令，支持多种质量/格式/帧率。
    支持指定 composition、GPU 加速、Docker 可重现构建等高级选项。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_render
"""

from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace, RENDER_TIMEOUT


def register_tools(mcp) -> None:
    """注册渲染相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_render",
        description="将 HyperFrames 项目渲染为 MP4/WebM 视频。"
    )
    async def hyperframes_render(
        project_dir: Optional[str] = None,
        output: Optional[str] = None,
        fps: Optional[int] = None,
        quality: Optional[str] = None,
        format: Optional[str] = None,
        composition: Optional[str] = None,
        workers: Optional[int] = None,
        gpu: bool = False,
        docker: bool = False,
        strict: bool = False,
        strict_all: bool = False,
        timeout: int = RENDER_TIMEOUT,
    ) -> str:
        """
        渲染 HyperFrames 视频项目

        Args:
            project_dir: 项目目录路径。默认为当前工作空间
            output: 输出视频路径。默认保存在 renders/ 目录
            fps: 帧率，可选 24/30/60。默认 30
            quality: 渲染质量。可选 draft（快速迭代）/ standard（审阅）/ high（最终交付）
            format: 输出格式。mp4 或 webm（webm 支持透明背景）
            composition: 只渲染指定的 composition 文件（相对于项目目录的路径）
            workers: 并行工作进程数，可选 1-8 或 auto。默认 auto
            gpu: 启用 GPU 加速编码（默认关闭）
            docker: 使用 Docker 可重现构建（默认关闭）
            strict: lint 错误时中止渲染（默认关闭）
            strict_all: lint 错误和警告时都中止（默认关闭）
            timeout: 渲染超时秒数，默认 600

        Returns:
            渲染结果输出信息
        """
        args = ["render"]

        if output:
            args.extend(["--output", output])

        if fps:
            if fps not in (24, 30, 60):
                return f"❌ 无效帧率: {fps}。可选值: 24, 30, 60"
            args.extend(["--fps", str(fps)])

        if quality:
            if quality not in ("draft", "standard", "high"):
                return "❌ 无效质量值。可选: draft, standard, high"
            args.extend(["--quality", quality])

        if format:
            if format not in ("mp4", "webm"):
                return "❌ 无效格式。可选: mp4, webm"
            args.extend(["--format", format])

        if composition:
            args.extend(["--composition", composition])

        if workers is not None:
            w = str(workers)
            if w not in ("auto", "1", "2", "3", "4", "5", "6", "7", "8"):
                return "❌ 无效 workers 值。可选: auto, 1-8"
            args.extend(["--workers", w])

        if gpu:
            args.append("--gpu")

        if docker:
            args.append("--docker")

        if strict:
            args.append("--strict")

        if strict_all:
            args.append("--strict-all")

        workspace = find_workspace() if not project_dir else project_dir
        result = await run_hyperframes(args, cwd=workspace, timeout=timeout)

        if result["success"]:
            return f"✅ 渲染成功\n{result['stdout']}"
        else:
            return f"❌ 渲染失败\n{result['stderr']}"
