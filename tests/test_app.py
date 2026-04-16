import sys
from pathlib import Path
from typing import cast

import gtaol_dre_helper.app as app_module
from gtaol_dre_helper.app import DreHelperApp
from gtaol_dre_helper.utils.config import CONFIG_FILE_NAME, EXAMPLE_CONFIG_FILE_NAME
from gtaol_dre_helper.utils.paths import REGION_LOCATOR_EXE_NAME, get_region_locator_path, get_runtime_resource_path


def test_css_path_points_to_packaged_stylesheet() -> None:
    # 验证应用样式文件路径始终绑定到 app.py 同目录下的 style.scss，便于源码运行和打包后都能找到资源。
    expected_path = Path(app_module.__file__).with_name("style.scss")
    actual_path = Path(cast(str, DreHelperApp.CSS_PATH))

    assert actual_path == expected_path
    assert actual_path.name == "style.scss"
    assert actual_path.is_absolute()
    assert actual_path.exists()


def test_runtime_resource_paths_use_project_root_in_source_mode(monkeypatch) -> None:
    # 验证源码运行时，配置文件模板与 Tesseract 都会相对项目根目录定位，而不是依赖当前工作目录。
    monkeypatch.delattr(sys, "frozen", raising=False)
    expected_root = Path(app_module.__file__).resolve().parents[1]

    config_path = get_runtime_resource_path(CONFIG_FILE_NAME)
    example_config_path = get_runtime_resource_path(EXAMPLE_CONFIG_FILE_NAME)
    tesseract_path = get_runtime_resource_path("tesseract", "tesseract.exe")
    region_locator_path = get_region_locator_path()

    assert config_path == expected_root / CONFIG_FILE_NAME
    assert example_config_path == expected_root / EXAMPLE_CONFIG_FILE_NAME
    assert tesseract_path == expected_root / "tesseract" / "tesseract.exe"
    assert region_locator_path == expected_root / REGION_LOCATOR_EXE_NAME
    assert example_config_path.exists()


def test_runtime_resource_paths_use_executable_directory_in_frozen_mode(monkeypatch, tmp_path) -> None:
    # 验证打包后会相对 exe 所在目录查找配置与外部资源，避免从其他命令行目录启动时找不到文件。
    executable_path = tmp_path / "gtaol-dre-helper.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable_path))

    config_path = get_runtime_resource_path(CONFIG_FILE_NAME)
    example_config_path = get_runtime_resource_path(EXAMPLE_CONFIG_FILE_NAME)
    tesseract_path = get_runtime_resource_path("tesseract", "tesseract.exe")
    region_locator_path = get_region_locator_path()

    assert config_path == tmp_path / "config.yaml"
    assert example_config_path == tmp_path / "config.example.yaml"
    assert tesseract_path == tmp_path / "tesseract" / "tesseract.exe"
    assert region_locator_path == tmp_path / REGION_LOCATOR_EXE_NAME
