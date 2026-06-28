"""
hyperframes_media — 媒体处理工具（TTS / 转录）

功能简述:
    封装 npx hyperframes tts 和 npx hyperframes transcribe 命令。
    支持文本转语音、音频/视频转录字幕、字幕导入导出。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_tts / hyperframes_transcribe / hyperframes_list_voices
"""

from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace


def register_tools(mcp) -> None:
    """注册媒体处理相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_tts",
        description="文本转语音（Text-to-Speech）。生成配音音频文件。"
    )
    async def hyperframes_tts(
        text: str,
        voice: Optional[str] = None,
        output: Optional[str] = None,
        project_dir: Optional[str] = None,
    ) -> str:
        """
        文本转语音

        Args:
            text: 需要朗读的文本内容，或包含文本的文件路径
            voice: 语音角色（如 af_nova, bf_emma）。不指定则用默认角色
            output: 输出音频文件路径，默认 narration.wav
            project_dir: 项目目录路径

        Returns:
            TTS 执行结果
        """
        args = ["tts"]

        # 判断 text 是文件路径还是纯文本
        args.append(text)

        if voice:
            args.extend(["--voice", voice])

        if output:
            args.extend(["--output", output])

        workspace = find_workspace() if not project_dir else project_dir
        result = await run_hyperframes(args, cwd=workspace)

        if result["success"]:
            return f"✅ TTS 生成成功\n{result['stdout']}"
        else:
            return f"❌ TTS 生成失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_list_voices",
        description="列出所有可用的 TTS 语音角色。"
    )
    async def hyperframes_list_voices(
        project_dir: Optional[str] = None,
    ) -> str:
        """
        列出所有可用的 TTS 语音角色

        Args:
            project_dir: 项目目录路径

        Returns:
            可用语音角色列表
        """
        result = await run_hyperframes(
            ["tts", "--list"],
            cwd=find_workspace() if not project_dir else project_dir,
        )

        if result["success"]:
            return result["stdout"]
        else:
            return f"❌ 获取语音列表失败\n{result['stderr']}"

    @mcp.tool(
        name="hyperframes_transcribe",
        description="音频/视频转录为文字字幕。支持多种输入格式。"
    )
    async def hyperframes_transcribe(
        input_path: str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        output_format: Optional[str] = None,
        project_dir: Optional[str] = None,
    ) -> str:
        """
        音频/视频转录文字

        Args:
            input_path: 输入音频/视频文件路径，或现有字幕文件路径（.srt/.vtt/.json）
            model: Whisper 模型大小（如 tiny, base, small, medium, large）。默认 medium.en
            language: 语言代码（如 en, zh, ja）。不指定则自动检测
            output_format: 输出字幕格式（当输入是媒体文件时）。不指定则自动推断
            project_dir: 项目目录路径

        Returns:
            转录结果
        """
        args = ["transcribe", input_path]

        if model:
            args.extend(["--model", model])

        if language:
            args.extend(["--language", language])

        if output_format:
            args.extend(["--output-format", output_format])

        workspace = find_workspace() if not project_dir else project_dir
        result = await run_hyperframes(args, cwd=workspace, timeout=300)

        if result["success"]:
            return f"✅ 转录成功\n{result['stdout']}"
        else:
            return f"❌ 转录失败\n{result['stderr']}"
