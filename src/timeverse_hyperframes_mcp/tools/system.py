"""
hyperframes_system — 系统管理工具

功能简述:
    封装 doctor / info / upgrade / benchmark / compositions / install-ffmpeg 等管理类命令。
    用于检测环境、获取版本信息、列出 composition、跑基准测试等。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_doctor / hyperframes_info / 等
"""

import asyncio
import logging
from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace, check_environment

logger = logging.getLogger(__name__)


# ==================== FFmpeg 检测工具 ====================

async def _detect_ffmpeg_image2_support() -> tuple[bool, str]:
    """
    检测 FFmpeg 是否支持 image2 demuxer（读取帧截图序列必须）。

    Returns:
        (ok: bool, detail: str)
        如 (True, "支持 image2 demuxer")
        如 (False, "FFmpeg 未安装 或 缺少 image2 demuxer（精简版）")
    """
    try:
        # 检查 demuxers 列表
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-demuxers",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        demuxers = (stdout + stderr).decode("utf-8", errors="replace")

        if not demuxers or proc.returncode != 0:
            return False, "FFmpeg 未安装"

        if "image2" in demuxers:
            return True, "FFmpeg 正常（支持 image2 demuxer）"

        # image2 缺失 — 检查是否是自定义精简版
        if "--disable-everything" in demuxers:
            return False, "FFmpeg 为自定义精简版（--disable-everything），缺少 image2 demuxer，无法合成帧截图视频"
        return False, "FFmpeg 缺少 image2 demuxer，无法读取 frame_%06d.jpg 帧序列模式"

    except FileNotFoundError:
        return False, "FFmpeg 未安装"


def _parse_ffmpeg_version_from_demuxers(demuxers_output: str) -> str:
    """从 demuxers 输出中提取 FFmpeg 版本"""
    for line in demuxers_output.splitlines():
        if "ffmpeg version" in line:
            return line.split("ffmpeg version", 1)[1].split()[0].strip(",")
    return "未知"


def _detect_brew_available() -> bool:
    """检测是否可用 brew 包管理器"""
    import shutil
    return shutil.which("brew") is not None


# ==================== 工具注册 ====================

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

        # 额外检测 FFmpeg image2 demuxer
        if env_check["ffmpeg_ok"]:
            ok, detail = await _detect_ffmpeg_image2_support()
            lines.append(f"  image2 demuxer: {'✅' if ok else '❌'} {detail}")
            if not ok:
                lines.append("\n  💡 建议: 运行 hyperframes_install_ffmpeg 修复")

        if not env_check["all_ok"]:
            lines.append("\n⚠️ 环境不完整，请安装缺失依赖：")
            if not env_check["node_ok"]:
                lines.append("  - Node.js >= 22: https://nodejs.org")
            if not env_check["ffmpeg_ok"]:
                lines.append("  - FFmpeg: brew install ffmpeg / apt install ffmpeg\n    或运行 hyperframes_install_ffmpeg")
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

    @mcp.tool(
        name="hyperframes_install_ffmpeg",
        description="检测并修复 FFmpeg 依赖问题。如果 FFmpeg 是精简版（缺少 image2 demuxer，导致渲染报错），自动重装完整版。"
    )
    async def hyperframes_install_ffmpeg(
        force: bool = False,
    ) -> str:
        """
        检测 FFmpeg 并修复（如缺失 image2 demuxer 则重装）

        Args:
            force: 即使 FFmpeg 正常也强制重装

        Returns:
            检测/修复结果
        """
        ok, detail = await _detect_ffmpeg_image2_support()

        if ok and not force:
            return (
                f"✅ FFmpeg 检测正常\n"
                f"   {detail}\n"
                f"   无需修复。"
            )

        # 检测 brew
        if not _detect_brew_available():
            return (
                "❌ 未检测到 Homebrew\n\n"
                "请手动安装完整 FFmpeg：\n"
                "  macOS:   brew install ffmpeg\n"
                "  Ubuntu:  sudo apt install ffmpeg\n"
                "  Windows: choco install ffmpeg\n"
                "  或从 https://ffmpeg.org/download.html 下载"
            )

        # 自动重装 FFmpeg
        lines = [
            f"🔧 FFmpeg 检测结果: {detail}",
            "📦 正在通过 Homebrew 重装完整 FFmpeg...",
            "   可能需要 1-3 分钟，请耐心等待",
            "",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                "brew", "reinstall", "ffmpeg",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0:
                # 验证重装结果
                ok2, detail2 = await _detect_ffmpeg_image2_support()
                if ok2:
                    lines.append("✅ FFmpeg 重装成功！")
                    lines.append(f"   {detail2}")
                else:
                    lines.append(f"⚠️ FFmpeg 已重装但仍存在问题")
                    lines.append(f"   {detail2}")
            else:
                # brew reinstall 可能需要交互确认（y/n）
                # 可能是询问了 "Proceed? [y/n]"
                if "y/n" in stderr_str or "[y/n]" in stderr_str:
                    lines.append("⚠️ brew 需要确认操作，尝试自动应答...")
                    # 用 echo y 再试一次
                    proc2 = await asyncio.create_subprocess_exec(
                        "bash", "-c", "echo y | brew reinstall ffmpeg",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout2, stderr2 = await asyncio.wait_for(proc2.communicate(), timeout=300)
                    if proc2.returncode == 0:
                        ok3, detail3 = await _detect_ffmpeg_image2_support()
                        if ok3:
                            lines.append("✅ FFmpeg 重装成功！")
                            lines.append(f"   {detail3}")
                        else:
                            lines.append(f"⚠️ FFmpeg 已重装但仍存在问题: {detail3}")
                    else:
                        lines.append(f"❌ 重装失败:\n{stderr2.decode('utf-8', errors='replace')[:500]}")
                else:
                    lines.append(f"❌ 重装失败 (exit code {proc.returncode}):\n{stderr_str[:500]}")

        except asyncio.TimeoutError:
            lines.append("❌ 重装超时（> 5 分钟），请手动运行：")
            lines.append("   brew reinstall ffmpeg")
        except Exception as exc:
            lines.append(f"❌ 重装出错: {exc}")
            lines.append("   请手动运行：brew reinstall ffmpeg")

        return "\n".join(lines)
