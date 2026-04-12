from __future__ import annotations

import yaml
from gtaol_dre_helper.models.config import AppConfig
from gtaol_dre_helper.utils.paths import get_runtime_resource_path

CONFIG_FILE_NAME = "config.yaml"


def load_config() -> AppConfig:
    """从 yaml 文件加载配置"""
    config_file_path = get_runtime_resource_path(CONFIG_FILE_NAME)

    if not config_file_path.exists():
        raise FileNotFoundError(
            f"程序目录未找到配置文件 {CONFIG_FILE_NAME}，请先在 {config_file_path.parent} 下创建或复制 {CONFIG_FILE_NAME}"
        )

    with config_file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return AppConfig.model_validate(data)
