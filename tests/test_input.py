import ctypes
import pytest

from gtaol_dre_helper.models.config import RuntimeActionStep
from gtaol_dre_helper.utils.input import INPUT, execute_sequence


def test_input_structure_size_matches_windows_expectation() -> None:
    # 验证 SendInput 使用的 INPUT 结构体尺寸正确，避免因 cbSize 错误触发 WinError 87。
    expected_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
    assert ctypes.sizeof(INPUT) == expected_size


def test_execute_sequence_presses_combo_in_order_and_releases_in_reverse(
    monkeypatch,
) -> None:
    # 验证组合键会按声明顺序按下、按相反顺序释放，并保留间隔与延迟节奏。
    events: list[tuple[str, str] | tuple[str, float]] = []

    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_down_compiled",
        lambda compiled_key: events.append(("down", compiled_key.key)),
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_up_compiled",
        lambda compiled_key: events.append(("up", compiled_key.key)),
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input.time.sleep",
        lambda seconds: events.append(("sleep", seconds)),
    )

    execute_sequence(
        [
            RuntimeActionStep(
                keys=("ctrl", "1"),
                interval=0.2,
                hold=0.3,
                delay=0.4,
                times=1,
            )
        ]
    )

    assert events == [
        ("down", "ctrl"),
        ("sleep", 0.2),
        ("down", "1"),
        ("sleep", 0.3),
        ("up", "1"),
        ("up", "ctrl"),
        ("sleep", 0.4),
    ]


def test_execute_sequence_releases_pressed_keys_when_combo_press_fails(
    monkeypatch,
) -> None:
    # 验证组合键按下过程中若中途失败，已按下的按键仍会被安全释放。
    events: list[tuple[str, str]] = []

    def fake_key_down(compiled_key) -> None:
        events.append(("down", compiled_key.key))
        if compiled_key.key == "1":
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_down_compiled", fake_key_down)
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_up_compiled",
        lambda compiled_key: events.append(("up", compiled_key.key)),
    )
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input.time.sleep", lambda _: None)

    try:
        execute_sequence(
            [
                RuntimeActionStep(
                    keys=("ctrl", "1"),
                    interval=0.2,
                    hold=0.3,
                    delay=0.4,
                    times=1,
                )
            ]
        )
    except RuntimeError as exc:
        assert str(exc) == "boom"
    else:
        raise AssertionError("应当抛出按键发送异常")

    assert events == [
        ("down", "ctrl"),
        ("down", "1"),
        ("up", "ctrl"),
    ]


def test_execute_sequence_continues_releasing_remaining_keys_when_key_up_fails(
    monkeypatch,
) -> None:
    # 验证释放某个按键失败时，仍会继续释放其余已按下的按键。
    events: list[tuple[str, str]] = []

    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_down_compiled",
        lambda compiled_key: events.append(("down", compiled_key.key)),
    )

    def fake_key_up(compiled_key) -> None:
        events.append(("up", compiled_key.key))
        if compiled_key.key == "1":
            raise OSError("stuck")

    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_up_compiled", fake_key_up)
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input.time.sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="释放按键失败: 1: OSError: stuck") as exc_info:
        execute_sequence(
            [
                RuntimeActionStep(
                    keys=("ctrl", "1"),
                    interval=0.2,
                    hold=0.3,
                    delay=0.4,
                    times=1,
                )
            ]
        )

    assert events == [
        ("down", "ctrl"),
        ("down", "1"),
        ("up", "1"),
        ("up", "ctrl"),
    ]
    assert isinstance(exc_info.value.__cause__, OSError)


def test_execute_sequence_keeps_original_error_when_release_also_fails(
    monkeypatch,
) -> None:
    # 验证动作执行失败且释放也失败时，仍保留原始异常并附带释放失败信息。
    events: list[tuple[str, str]] = []

    def fake_key_down(compiled_key) -> None:
        events.append(("down", compiled_key.key))
        if compiled_key.key == "1":
            raise RuntimeError("boom")

    def fake_key_up(compiled_key) -> None:
        events.append(("up", compiled_key.key))
        raise OSError("stuck ctrl")

    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_down_compiled", fake_key_down)
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input._key_up_compiled", fake_key_up)
    monkeypatch.setattr(
        "gtaol_dre_helper.utils.input.time.sleep", lambda _: None)

    with pytest.raises(RuntimeError, match="boom") as exc_info:
        execute_sequence(
            [
                RuntimeActionStep(
                    keys=("ctrl", "1"),
                    interval=0.2,
                    hold=0.3,
                    delay=0.4,
                    times=1,
                )
            ]
        )

    assert events == [
        ("down", "ctrl"),
        ("down", "1"),
        ("up", "ctrl"),
    ]
    assert exc_info.value.__notes__ == ["释放按键失败: ctrl: OSError: stuck ctrl"]
