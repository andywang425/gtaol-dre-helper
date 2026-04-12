from pathlib import Path
import sys


def _get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


def get_runtime_resource_path(*parts: str) -> Path:
    return _get_runtime_root().joinpath(*parts)
