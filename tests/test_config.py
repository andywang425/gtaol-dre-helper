from pathlib import Path

import pytest
from pydantic import ValidationError

import gtaol_dre_helper.utils.config as config_utils
from gtaol_dre_helper.models.config import AppConfig
from gtaol_dre_helper.types import Resolution
from gtaol_dre_helper.utils.config import EXAMPLE_CONFIG_FILE_NAME


def build_valid_config_data() -> dict:
    return {
        "region": {
            "ceo": {"left": 1, "top": 2, "width": 3, "height": 4},
            "single": {"left": 5, "top": 6, "width": 7, "height": 8},
        },
        "profiles": [
            {
                "name": "方案 A",
                "type": "ceo",
                "toggle_key": "f1",
                "sequence": [{"key": "f5"}],
            }
        ],
    }


def write_config_file(file_path: Path, content: str) -> None:
    file_path.write_text(content, encoding="utf-8")


def test_get_or_create_config_file_returns_existing_config_without_copying(monkeypatch, tmp_path) -> None:
    # 验证配置文件已存在时，会直接返回现有文件，不会覆盖用户配置。
    config_path = tmp_path / "config.yaml"
    example_path = tmp_path / EXAMPLE_CONFIG_FILE_NAME
    write_config_file(config_path, "existing: true\n")
    write_config_file(example_path, "existing: false\n")

    monkeypatch.setattr(
        config_utils, "_get_config_file_path", lambda: config_path)
    monkeypatch.setattr(
        config_utils, "get_example_config_file_path", lambda: example_path)

    returned_path = config_utils.get_or_create_config_file()

    assert returned_path == config_path
    assert config_path.read_text(encoding="utf-8") == "existing: true\n"


def test_get_or_create_config_file_raises_when_config_and_example_are_missing(monkeypatch, tmp_path) -> None:
    # 验证配置文件和示例模板都缺失时，会抛出明确错误提示用户补齐模板。
    config_path = tmp_path / "config.yaml"
    example_path = tmp_path / EXAMPLE_CONFIG_FILE_NAME

    monkeypatch.setattr(
        config_utils, "_get_config_file_path", lambda: config_path)
    monkeypatch.setattr(
        config_utils, "get_example_config_file_path", lambda: example_path)

    with pytest.raises(FileNotFoundError, match="config.example.yaml"):
        config_utils.get_or_create_config_file()


def test_write_initial_config_content_preserves_comments_while_updating_region_values(monkeypatch, tmp_path) -> None:
    # 验证首次写入配置时会更新推荐区域，同时保留模板中的注释和其他 YAML 结构。
    config_path = tmp_path / "config.yaml"
    example_path = tmp_path / EXAMPLE_CONFIG_FILE_NAME
    write_config_file(
        example_path,
        """
# 顶部注释
region:
  # CEO 注释
  ceo:
    left: 1
    top: 2
    width: 3
    height: 4

  # SINGLE 注释
  single:
    left: 5
    top: 6
    width: 7
    height: 8

profiles:
  - name: 室外
    type: ceo
    toggle_key: f11
    sequence:
      - key: m # 打开菜单
""".strip()
        + "\n",
    )
    monkeypatch.setattr(
        config_utils,
        "get_primary_screen_resolution",
        lambda: Resolution(1920, 1080),
    )

    config_utils._write_recommended_config(config_path, example_path)
    content = config_path.read_text(encoding="utf-8")

    assert "# 顶部注释" in content
    assert "# CEO 注释" in content
    assert "# SINGLE 注释" in content
    assert "# 打开菜单" in content
    assert "left: 1807" in content
    assert "top: 986" in content
    assert "width: 78" in content
    assert "height: 27" in content
    assert "left: 315" in content
    assert "top: 204" in content
    assert "width: 183" in content
    assert "height: 20" in content


def test_load_config_returns_validated_app_config(monkeypatch, tmp_path) -> None:
    # 验证 load_config 会读取 YAML 并返回经过 Pydantic 校验后的 AppConfig 对象。
    config_path = tmp_path / "config.yaml"
    write_config_file(
        config_path,
        """
region:
  ceo:
    left: 1
    top: 2
    width: 3
    height: 4
  single:
    left: 5
    top: 6
    width: 7
    height: 8
profiles:
  - name: 方案 A
    type: ceo
    toggle_key: ctrl+f1
    sequence:
      - key: CTRL+C
        times: 2
""".strip(),
    )
    monkeypatch.setattr(
        config_utils, "get_or_create_config_file", lambda: config_path)

    config = config_utils.load_config()

    assert isinstance(config, AppConfig)
    assert config.profiles[0].toggle_key == "ctrl+f1"
    assert config.profiles[0].sequence[0].key == "ctrl+c"
    assert config.profiles[0].sequence[0].times == 2


def test_load_config_raises_validation_error_for_invalid_structure(monkeypatch, tmp_path) -> None:
    # 验证 YAML 结构缺少必填字段时，会把配置校验错误抛给上层处理。
    config_path = tmp_path / "config.yaml"
    write_config_file(config_path, "profiles: []\n")
    monkeypatch.setattr(
        config_utils, "get_or_create_config_file", lambda: config_path)

    with pytest.raises(ValidationError):
        config_utils.load_config()


def test_profile_config_rejects_duplicate_keys_in_same_toggle_combo() -> None:
    # 验证单个方案的组合开关键里不能重复写同一个按键。
    data = build_valid_config_data()
    data["profiles"][0]["toggle_key"] = "ctrl+ctrl"

    with pytest.raises(ValidationError, match="监控开关键不能包含重复按键"):
        AppConfig.model_validate(data)


def test_app_config_rejects_duplicate_toggle_keys_across_profiles_even_if_order_differs() -> None:
    # 验证不同方案即使按键顺序不同，只要逻辑上是同一组组合键也会判定为重复。
    data = build_valid_config_data()
    data["profiles"] = [
        {
            "name": "方案 A",
            "type": "ceo",
            "toggle_key": "ctrl+f1",
            "sequence": [{"key": "f5"}],
        },
        {
            "name": "方案 B",
            "type": "single",
            "toggle_key": "f1+ctrl",
            "sequence": [{"key": "f6"}],
        },
    ]

    with pytest.raises(ValidationError, match="监控开关键重复"):
        AppConfig.model_validate(data)


def test_app_config_rejects_empty_sequence() -> None:
    # 验证每个方案至少要包含一个动作步骤，避免出现无法执行的空方案。
    data = build_valid_config_data()
    data["profiles"][0]["sequence"] = []

    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)


def test_app_config_rejects_invalid_action_key() -> None:
    # 验证动作按键不受支持时会被校验拦截，防止运行时才失败。
    data = build_valid_config_data()
    data["profiles"][0]["sequence"] = [{"key": "not-a-real-key"}]

    with pytest.raises(ValidationError, match="不支持的动作按键"):
        AppConfig.model_validate(data)


def test_app_config_rejects_invalid_region_size() -> None:
    # 验证监控区域宽高必须为正数，避免生成无效截图区域。
    data = build_valid_config_data()
    data["region"]["single"]["width"] = 0

    with pytest.raises(ValidationError):
        AppConfig.model_validate(data)
