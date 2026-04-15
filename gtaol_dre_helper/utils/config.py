from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from gtaol_dre_helper.models.config import AppConfig
from gtaol_dre_helper.utils.paths import get_runtime_resource_path

CONFIG_FILE_NAME = "config.yaml"
EXAMPLE_CONFIG_FILE_NAME = "config.example.yaml"


def _get_config_file_path() -> Path:
    """返回运行时配置文件路径"""
    return get_runtime_resource_path(CONFIG_FILE_NAME)


def get_example_config_file_path() -> Path:
    """返回运行时示例配置文件路径"""
    return get_runtime_resource_path(EXAMPLE_CONFIG_FILE_NAME)


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

    shutil.copyfile(example_config_path, config_file_path)
    return config_file_path


def load_config() -> AppConfig:
    """从 yaml 文件加载配置"""
    config_file_path = get_or_create_config_file()

    with config_file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return AppConfig.model_validate(data)
