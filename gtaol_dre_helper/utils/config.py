from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML
from gtaol_dre_helper.models.config import AppConfig
from gtaol_dre_helper.types import ProfileTypes, RegionDict, Resolution
from gtaol_dre_helper.utils.paths import get_runtime_resource_path
from gtaol_dre_helper.utils.screen import get_primary_screen_resolution

CONFIG_FILE_NAME = "config.yaml"
EXAMPLE_CONFIG_FILE_NAME = "config.example.yaml"

REGION_PRESETS: dict[Resolution, dict[ProfileTypes, RegionDict]] = {
    Resolution(3840, 2160): {
        "ceo": {"left": 3609, "top": 1974, "width": 172, "height": 55},
        "single": {"left": 633, "top": 408, "width": 367, "height": 55},
    },
    Resolution(2560, 1440): {
        "ceo": {"left": 2409, "top": 1314, "width": 105, "height": 37},
        "single": {"left": 424, "top": 275, "width": 241, "height": 29},
    },
    Resolution(1920, 1080): {
        "ceo": {"left": 1807, "top": 986, "width": 78, "height": 27},
        "single": {"left": 319, "top": 206, "width": 180, "height": 22},
    },
}


def _get_config_file_path() -> Path:
    """返回运行时配置文件路径"""
    return get_runtime_resource_path(CONFIG_FILE_NAME)


def get_example_config_file_path() -> Path:
    """返回运行时示例配置文件路径"""
    return get_runtime_resource_path(EXAMPLE_CONFIG_FILE_NAME)


def _replace_region_values(data: dict[str, object], regions: dict[ProfileTypes, RegionDict]) -> None:
    """替换模板内 region 块的默认值"""
    region_config = data.get("region")
    assert isinstance(region_config, dict)

    for profile_type, values in regions.items():
        target_region = region_config.get(profile_type)
        assert isinstance(target_region, dict)

        for key, value in values.items():
            target_region[key] = value


def _write_recommended_config(config_file_path: Path, example_config_path: Path) -> None:
    """写入推荐的配置

    Args:
        config_file_path: 写入的配置文件路径
        example_config_path: 参考的示例配置文件路径
    """
    yaml = YAML()
    content = example_config_path.read_text(encoding="utf-8")
    resolution = get_primary_screen_resolution()
    if resolution is None:
        config_file_path.write_text(content, encoding="utf-8")
        return

    recommended_regions = REGION_PRESETS.get(resolution)
    if recommended_regions is None:
        config_file_path.write_text(content, encoding="utf-8")
        return

    data = yaml.load(content)

    _replace_region_values(data, recommended_regions)

    with config_file_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


def get_or_create_config_file(always_create: bool = False) -> Path:
    """获取或创建配置文件

    若配置文件不存在则根据示例配置文件自动生成默认配置

    Args:
        always_create: 是否强制创建配置文件

    Returns:
        配置文件路径
    """
    config_file_path = _get_config_file_path()
    if config_file_path.exists() and not always_create:
        return config_file_path

    example_config_path = get_example_config_file_path()
    if not example_config_path.exists():
        raise FileNotFoundError(f"缺少示例配置文件 {EXAMPLE_CONFIG_FILE_NAME}")

    _write_recommended_config(config_file_path, example_config_path)
    return config_file_path


def load_config() -> AppConfig:
    """从 yaml 文件加载配置"""
    config_file_path = get_or_create_config_file()
    yaml = YAML()

    with config_file_path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)

    return AppConfig.model_validate(data)
