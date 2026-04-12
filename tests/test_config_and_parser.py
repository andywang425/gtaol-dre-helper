import pytest
from pydantic import ValidationError

from gtaol_dre_helper.models.config import ActionStep, AppConfig, ProfileConfig, Region, RegionConfig
from gtaol_dre_helper.utils.text_parser import parse_player_count


def test_parse_player_count_handles_whitespace_and_noise() -> None:
    # 验证 OCR 文本中带空白和无关字符时，仍能正确提取已加入人数。
    assert parse_player_count("黑心基金  2 / 4  ") == 2


def test_parse_player_count_returns_none_for_invalid_text() -> None:
    # 验证 OCR 文本不包含有效人数格式时，解析函数会安全返回空值。
    assert parse_player_count("13") is None


def test_action_step_normalizes_combo_keys_and_builds_runtime_step(monkeypatch: pytest.MonkeyPatch) -> None:
    # 验证组合键动作会被规范化，并转换为按顺序执行的运行时动作配置。
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey.is_sendinput_supported_key",
        lambda key: key in {"ctrl", "shift", "c"},
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey._compile_sendinput_key",
        lambda key: type(
            "CompiledKey",
            (),
            {
                "key": key,
                "scan_code": len(key),
                "key_down_flags": 8,
                "key_up_flags": 10,
            },
        )(),
    )

    action = ActionStep(key=" Ctrl + Shift + C ",
                        interval=0.2, hold=0.3, delay=0.4, times=2)
    runtime_step = action.to_runtime_action_step()

    assert action.key == "ctrl+shift+c"
    assert runtime_step.keys == ("ctrl", "shift", "c")
    assert runtime_step.interval == 0.2
    assert runtime_step.hold == 0.3
    assert runtime_step.delay == 0.4
    assert runtime_step.times == 2
    assert tuple(compiled_key.key for compiled_key in runtime_step.compiled_keys) == (
        "ctrl", "shift", "c")


def test_action_step_rejects_invalid_combo_format(monkeypatch: pytest.MonkeyPatch) -> None:
    # 验证组合键格式中出现空片段时，会阻止生成无效的动作配置。
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey.is_sendinput_supported_key", lambda _: True)

    with pytest.raises(ValidationError):
        ActionStep(key="ctrl++c")


def test_action_step_rejects_keys_without_sendinput_scancode(monkeypatch: pytest.MonkeyPatch) -> None:
    # 验证仅有虚拟键码但无法映射扫描码的按键，会在动作配置阶段被拒绝。
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey.is_sendinput_supported_key",
        lambda key: key != "pause",
    )

    with pytest.raises(ValidationError):
        ActionStep(key="pause")


def test_profile_config_builds_runtime_profile_with_combo_toggle_and_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    # 验证监控方案支持组合开关键，并会生成包含多个虚拟键码的运行时方案。
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey.is_sendinput_supported_key",
        lambda key: key in {"ctrl", "shift", "c"},
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.hotkey.get_virtual_key_code",
        lambda key: {"ctrl": 17, "shift": 16, "c": 67,
                     "f1": 112}.get(str(key).strip().lower()),
    )

    profile = ProfileConfig(
        name="方案 A",
        type="ceo",
        toggle_key=" Ctrl + F1 ",
        sequence=[ActionStep(key="ctrl+shift+c")],
    )
    runtime_profile = profile.to_runtime_profile()

    assert runtime_profile.name == "方案 A"
    assert profile.toggle_key == "ctrl+f1"
    assert runtime_profile.toggle_vk_codes == (17, 112)
    assert runtime_profile.sequence[0].keys == ("ctrl", "shift", "c")


def test_app_config_rejects_duplicate_toggle_keys_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 验证监控方案的开关键在忽略大小写与组合顺序后不能重复，避免运行时冲突。
    monkeypatch.setattr(
        "gtaol_dre_helper.models.config.is_sendinput_supported_key",
        lambda key: key == "c",
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.models.config.get_virtual_key_code",
        lambda key: {"ctrl": 17, "c": 67, "f1": 112,
                     "f2": 113}.get(str(key).strip().lower()),
    )

    with pytest.raises(ValidationError):
        AppConfig(
            region=RegionConfig(
                ceo=Region(x=1, y=2, width=3, height=4),
                single=Region(x=5, y=6, width=7, height=8),
            ),
            profiles=[
                ProfileConfig(
                    name="方案 A",
                    type="ceo",
                    toggle_key="Ctrl+F1",
                    sequence=[ActionStep(key="c")],
                ),
                ProfileConfig(
                    name="方案 B",
                    type="single",
                    toggle_key="f1+ctrl",
                    sequence=[ActionStep(key="c")],
                ),
            ],
        )
