import ctypes
import time
from collections.abc import Sequence
from ctypes import wintypes
from typing import Optional

from gtaol_dre_helper.models.config import RuntimeActionStep
from gtaol_dre_helper.utils.hotkey import CompiledSendInputKey


INPUT_KEYBOARD = 1
ULONG_PTR = ctypes.c_size_t
user32 = ctypes.windll.user32


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


user32.SendInput.argtypes = (
    wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = wintypes.UINT


def _send_compiled_keyboard_input(
    compiled_key: CompiledSendInputKey,
    *,
    is_key_up: bool,
) -> None:
    """通过 Windows SendInput 发送预编译的键盘按下或释放事件"""
    event = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=0,
            wScan=compiled_key.scan_code,
            dwFlags=compiled_key.key_up_flags if is_key_up else compiled_key.key_down_flags,
            time=0,
            dwExtraInfo=0,
        ),
    )
    sent = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
    if sent != 1:
        raise ctypes.WinError()


def _key_down_compiled(compiled_key: CompiledSendInputKey) -> None:
    """按下预编译按键"""
    _send_compiled_keyboard_input(compiled_key, is_key_up=False)


def _key_up_compiled(compiled_key: CompiledSendInputKey) -> None:
    """释放预编译按键"""
    _send_compiled_keyboard_input(compiled_key, is_key_up=True)


def execute_sequence(sequence: Sequence[RuntimeActionStep]) -> None:
    """执行按键动作序列"""
    for action in sequence:
        for _ in range(action.times):
            interval = action.interval
            pressed_keys: list[CompiledSendInputKey] = []
            action_error: Optional[BaseException] = None
            release_errors: list[tuple[str, BaseException]] = []

            try:
                for idx, compiled_key in enumerate(action.compiled_keys):
                    _key_down_compiled(compiled_key)
                    pressed_keys.append(compiled_key)
                    if idx < len(action.compiled_keys) - 1 and interval > 0:
                        time.sleep(interval)

                if action.hold > 0:
                    time.sleep(action.hold)
            except BaseException as exc:
                action_error = exc
            finally:
                for compiled_key in reversed(pressed_keys):
                    try:
                        _key_up_compiled(compiled_key)
                    except BaseException as exc:
                        release_errors.append((compiled_key.key, exc))

            if release_errors:
                release_message = ", ".join(
                    f"{key}: {type(exc).__name__}: {exc}"
                    for key, exc in release_errors
                )
                if action_error is not None:
                    action_error.add_note(f"释放按键失败: {release_message}")
                    raise action_error
                raise RuntimeError(
                    f"释放按键失败: {release_message}") from release_errors[0][1]

            if action_error is not None:
                raise action_error

            if action.delay > 0:
                time.sleep(action.delay)
