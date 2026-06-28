"""
hyperframes_init — 视频项目初始化工具

功能简述:
    封装 npx hyperframes init 命令，支持创建新视频项目。
    可选择模板、预设示例、附带视频/音频素材。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_init / hyperframes_list_templates
"""

import os
from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace

# ==================== 常量定义 ====================

AVAILABLE_TEMPLATES = [
    "blank",
    "warm-grain",
    "play-mode",
    "swiss-grid",
    "vignelli",
    "decision-tree",
    "kinetic-type",
    "product-promo",
    "nyt-graph",
]


def register_tools(mcp) -> None:
    """注册初始化相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_init",
        description="创建新的 HyperFrames 视频项目。初始化目录结构、安装依赖。"
    )
    async def hyperframes_init(
        project_name: str,
        template: Optional[str] = None,
        video_path: Optional[str] = None,
        audio_path: Optional[str] = None,
        non_interactive: bool = True,
        parent_dir: Optional[str] = None,
    ) -> str:
        """
        创建新的 HyperFrames 视频项目

        Args:
            project_name: 项目目录名称（如 "my-video"）
            template: 模板名称。可选值：blank, warm-grain, play-mode, swiss-grid, vignelli, decision-tree, kinetic-type, product-promo, nyt-graph
            video_path: 附带已有视频文件路径（将自动拷贝到项目中）
            audio_path: 附带音频文件路径（将自动拷贝并转写）
            non_interactive: 是否静默模式（默认 True，适合 AI 调用）
            parent_dir: 父级目录，默认为当前工作空间

        Returns:
            项目的标准输出信息
        """
        args = ["init", project_name]

        if non_interactive:
            args.append("--non-interactive")

        if template:
            if template not in AVAILABLE_TEMPLATES:
                available = ", ".join(AVAILABLE_TEMPLATES)
                return (
                    f"❌ 无效模板: {template}\n"
                    f"可用模板: {available}"
                )
            args.extend(["--example", template])

        if video_path:
            args.extend(["--video", video_path])

        if audio_path:
            args.extend(["--audio", audio_path])

        workspace = parent_dir or find_workspace()
        result = await run_hyperframes(args, cwd=workspace)

        if result["success"]:
            project_dir = os.path.join(workspace, project_name)
            return (
                f"✅ 项目创建成功\n"
                f"   路径: {project_dir}\n"
                f"   模板: {template or 'blank'}\n"
                f"{result['stdout']}"
            )
        else:
            return f"❌ 项目创建失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_list_templates",
        description="列出 HyperFrames 所有可用的项目模板。"
    )
    async def hyperframes_list_templates() -> str:
        """
        列出所有可用的项目模板

        Returns:
            模板列表与说明
        """
        templates_info = {
            "blank": "空项目，从零开始",
            "warm-grain": "暖色颗粒纹理风格",
            "play-mode": "Play 模式示例",
            "swiss-grid": "瑞士网格排版风格",
            "vignelli": "Vignelli 风格",
            "decision-tree": "决策树流程图",
            "kinetic-type": "动态文字排版",
            "product-promo": "产品宣传视频模板",
            "nyt-graph": "纽约时报风格数据可视化",
        }
        lines = ["📁 HyperFrames 可用模板：\n"]
        for t in AVAILABLE_TEMPLATES:
            desc = templates_info.get(t, "")
            lines.append(f"  - {t}: {desc}")
        return "\n".join(lines)
