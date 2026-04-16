from __future__ import annotations

from pathlib import Path

import yaml
from gtaol_dre_helper.models.config import AppConfig
from gtaol_dre_helper.types import ProfileTypes, RegionDict, Resolution
from gtaol_dre_helper.utils.paths import get_runtime_resource_path
from gtaol_dre_helper.utils.screen import get_primary_screen_resolution

CONFIG_FILE_NAME = "config.yaml"
EXAMPLE_CONFIG_FILE_NAME = "config.example.yaml"

REGION_PRESETS: dict[Resolution, dict[ProfileTypes, RegionDict]] = {
    Resolution(3840, 2160): {
        "ceo": {"left": 3609, "top": 1974, "width": 172, "height": 55},
        "single": {"left": 630, "top": 408, "width": 367, "height": 41},
    },
    Resolution(2560, 1440): {
        "ceo": {"left": 2409, "top": 1314, "width": 105, "height": 37},
        "single": {"left": 420, "top": 272, "width": 244, "height": 27},
    },
    Resolution(1920, 1080): {
        "ceo": {"left": 1807, "top": 986, "width": 78, "height": 27},
        "single": {"left": 315, "top": 204, "width": 183, "height": 20},
    },
}


def _get_config_file_path() -> Path:
    """返回运行时配置文件路径"""
    return get_runtime_resource_path(CONFIG_FILE_NAME)


def get_example_config_file_path() -> Path:
    """返回运行时示例配置文件路径"""
    return get_runtime_resource_path(EXAMPLE_CONFIG_FILE_NAME)


def _replace_region_block(lines: list[str], region_name: str, values: RegionDict) -> None:
    """替换模板内指定 region 块的默认值，同时保留原注释。"""
    block_header = f"  {region_name}:"
    for index, line in enumerate(lines):
        if line.startswith(block_header):
            lines[index + 1:index + 5] = [
                f"    left: {values['left']}",
                f"    top: {values['top']}",
                f"    width: {values['width']}",
                f"    height: {values['height']}",
            ]
            return

    raise ValueError(f"默认模板缺少 region.{region_name} 配置块")


def _build_initial_config_content(example_config_path: Path) -> str:
    """生成首次写入的配置内容"""
    content = example_config_path.read_text(encoding="utf-8")
    resolution = get_primary_screen_resolution()
    if resolution is None:
        return content

    recommended_regions = REGION_PRESETS.get(resolution)
    if recommended_regions is None:
        return content

    lines = content.splitlines()
    for region_name, values in recommended_regions.items():
        _replace_region_block(lines, region_name, values)

    return "\n".join(lines)


def get_or_create_config_file() -> Path:
    """获取或创建配置文件

    若配置文件不存在则根据示例配置文件自动生成默认配置

    Returns:
        配置文件路径
    """
    config_file_path = _get_config_file_path()
    if config_file_path.exists():
        return config_file_path

    example_config_path = get_example_config_file_path()
    if not example_config_path.exists():
        raise FileNotFoundError(
            "程序目录未找到配置文件 config.yaml，且缺少默认模板 config.example.yaml，"
            f"请先在 {config_file_path.parent} 下放置 {EXAMPLE_CONFIG_FILE_NAME}"
        )

    config_file_path.write_text(
        _build_initial_config_content(example_config_path),
        encoding="utf-8",
    )
    return config_file_path


def load_config() -> AppConfig:
    """从 yaml 文件加载配置"""
    config_file_path = get_or_create_config_file()

    with config_file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return AppConfig.model_validate(data)
