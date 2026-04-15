from datetime import datetime
from typing import Literal, Union

from textual.content import Content
from textual.markup import escape

LogLevel = Literal["info", "error", "warning"]

LogStyle = Union[LogLevel, Literal["auto", "success", "accent"]]

STYLE2CSSVARS: dict[LogStyle, str] = {
    "success": "$text-success",
    "error": "$text-error",
    "warning": "$text-warning",
    "accent": "$text-accent",
}

LEVEL2MARKUP: dict[LogLevel, str] = {
    "info": "[b]\\[INFO][/]",
    "error": "[b $text-error]\\[ERROR][/]",
    "warning": "[b $text-warning]\\[WARNING][/]",
}


def _log_time() -> str:
    """当前时间"""
    return datetime.now().strftime("[%H:%M:%S]")


def _style_message(level: LogLevel, message: str, style: LogStyle, markup: bool = False) -> str:
    """使用 markup 装饰日志消息"""
    if style == "auto":
        style = level
    if style == "info":
        # 使用默认文本颜色
        return message
    return f"[{STYLE2CSSVARS[style]}]{message if markup else escape(message)}[/]"


def build_log_content(level: LogLevel, message: str, style: LogStyle, markup: bool = False) -> Content:
    """构建日志内容"""
    return Content.from_markup(
        f"[b dim]$time[/] {LEVEL2MARKUP[level]} {_style_message(level, message, style, markup)}",
        time=_log_time()
    )
