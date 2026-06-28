"""
hyperframes_lint — 项目语法检查工具

功能简述:
    封装 npx hyperframes lint 命令，验证 composition 语法正确性。
    检查 data-composition-id、track 重叠、timeline 注册等问题。

主要方法清单:
    - register_tools(mcp): 注册 hyperframes_lint
"""

from typing import Optional

from ..cli_executor import run_hyperframes, find_workspace, parse_lint_json


def register_tools(mcp) -> None:
    """注册 lint 相关的 MCP 工具"""

    @mcp.tool(
        name="hyperframes_lint",
        description="检查 HyperFrames 项目的语法和结构完整性。建议在 preview/render 前运行。"
    )
    async def hyperframes_lint(
        project_dir: Optional[str] = None,
        verbose: bool = False,
        json_output: bool = True,
    ) -> str:
        """
        检查 HyperFrames 项目的语法和结构完整性

        Args:
            project_dir: 项目目录路径。默认为当前工作空间
            verbose: 是否显示 info 级别的详细信息（默认只显示 errors 和 warnings）
            json_output: 是否输出结构化 JSON 结果（默认 True）

        Returns:
            lint 检查结果
        """
        args = ["lint"]

        if verbose:
            args.append("--verbose")

        if json_output:
            args.append("--json")

        workspace = find_workspace() if not project_dir else project_dir
        result = await run_hyperframes(args, cwd=workspace)

        if not result["success"] and not result["stdout"]:
            return f"❌ lint 检查失败\n{result['stderr']}"

        if json_output and result["stdout"]:
            parsed = parse_lint_json(result["stdout"])
            if "errorCount" in parsed:
                ec = parsed.get("errorCount", 0)
                wc = parsed.get("warningCount", 0)
                ic = parsed.get("infoCount", 0)
                findings = parsed.get("findings", [])
                lines = [f"📋 Lint 结果：{ec} 个错误, {wc} 个警告, {ic} 个信息\n"]
                for f in findings:
                    severity = f.get("severity", "info")
                    icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(severity, "•")
                    msg = f.get("message", "")
                    loc = f.get("location", "")
                    lines.append(f"  {icon} [{severity}] {msg}")
                    if loc:
                        lines[-1] += f" ({loc})"
                if ec > 0:
                    lines.append("\n💡 存在错误，建议修复后再 preview/render")
                return "\n".join(lines)

        return result["stdout"] or result["stderr"]
