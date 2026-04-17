from functools import cache
from pathlib import Path
import sys


REGION_LOCATOR_EXE_NAME = "RegionLocator.exe"


@cache
def _get_runtime_root() -> Path:
    """返回程序运行时的根目录

    打包后返回可执行文件所在目录；开发环境下返回项目根目录
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def get_runtime_resource_path(*parts: str) -> Path:
    """基于运行时根目录拼接资源路径"""
    return _get_runtime_root().joinpath(*parts)


def get_region_locator_path() -> Path:
    """返回 RegionLocator 辅助工具路径"""
    return get_runtime_resource_path(REGION_LOCATOR_EXE_NAME)
