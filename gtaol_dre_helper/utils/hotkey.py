import ctypes
from dataclasses import dataclass
from ctypes import wintypes
from typing import Optional


# 按键别名映射（别名 -> 内部标准名称）
KEY_ALIASES = {
    "control": "ctrl",
    "return": "enter",
    "escape": "esc",
    "del": "delete",
    "ins": "insert",
    "pgup": "pageup",
    "pgdn": "pagedown",
    "kp0": "numpad0",
    "kp1": "numpad1",
    "kp2": "numpad2",
    "kp3": "numpad3",
    "kp4": "numpad4",
    "kp5": "numpad5",
    "kp6": "numpad6",
    "kp7": "numpad7",
    "kp8": "numpad8",
    "kp9": "numpad9",
    "num_mul": "numpad_mul",
    "num_add": "numpad_add",
    "num_sub": "numpad_sub",
    "num_decimal": "numpad_decimal",
    "num_div": "numpad_div",
}

MAPVK_VK_TO_VSC = 0
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
user32 = ctypes.windll.user32
user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
user32.MapVirtualKeyW.restype = wintypes.UINT

EXTENDED_KEYS = {
    "up",
    "down",
    "left",
    "right",
    "insert",
    "delete",
    "home",
    "end",
    "pageup",
    "pagedown",
    "numpad_div",
    "num_div",
}


# Windows 虚拟键码映射
VIRTUAL_KEY_CODES = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
    "numpad0": 0x60,
    "numpad1": 0x61,
    "numpad2": 0x62,
    "numpad3": 0x63,
    "numpad4": 0x64,
    "numpad5": 0x65,
    "numpad6": 0x66,
    "numpad7": 0x67,
    "numpad8": 0x68,
    "numpad9": 0x69,
    "numpad_mul": 0x6A,
    "numpad_add": 0x6B,
    "numpad_sub": 0x6D,
    "numpad_decimal": 0x6E,
    "numpad_div": 0x6F,
}


@dataclass(slots=True, frozen=True)
class CompiledSendInputKey:
    key: str
    scan_code: int
    key_down_flags: int
    key_up_flags: int


def _normalize_key_name(key: str) -> str:
    """将按键名称规范化为内部统一使用的格式"""
    normalized_key = str(key).strip().lower()
    return KEY_ALIASES.get(normalized_key, normalized_key)


def get_virtual_key_code(key: str) -> Optional[int]:
    """将按键名称转换为对应的虚拟键码"""
    normalized_key = _normalize_key_name(key)
    if normalized_key in VIRTUAL_KEY_CODES:
        return VIRTUAL_KEY_CODES[normalized_key]
    if normalized_key.startswith("f") and normalized_key[1:].isdigit():
        function_index = int(normalized_key[1:])
        if 1 <= function_index <= 24:
            return 0x6F + function_index
    if len(normalized_key) == 1 and normalized_key.isalnum():
        return ord(normalized_key.upper())
    return None


def _get_scan_code(key: str) -> Optional[int]:
    """将按键名称转换为 SendInput 所需的扫描码"""
    vk_code = get_virtual_key_code(key)
    if vk_code is None:
        return None

    scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    if scan_code == 0:
        return None
    return scan_code


def _compile_sendinput_key(key: str) -> Optional[CompiledSendInputKey]:
    """将按键名称预编译为可直接发送的运行时结构"""
    normalized_key = _normalize_key_name(key)
    scan_code = _get_scan_code(normalized_key)
    if scan_code is None:
        return None

    key_down_flags = KEYEVENTF_SCANCODE
    if normalized_key in EXTENDED_KEYS:
        key_down_flags |= KEYEVENTF_EXTENDEDKEY

    return CompiledSendInputKey(
        key=normalized_key,
        scan_code=scan_code,
        key_down_flags=key_down_flags,
        key_up_flags=key_down_flags | KEYEVENTF_KEYUP,
    )


def compile_action_keys(keys: tuple[str, ...]) -> tuple[CompiledSendInputKey, ...]:
    """将按键名称编译为 RuntimeActionStep 的 compiled_keys 字段"""
    compiled_keys: list[CompiledSendInputKey] = []
    for key in keys:
        compiled_key = _compile_sendinput_key(key)
        if compiled_key is None:
            raise ValueError(f"不支持的动作按键: {key}")
        compiled_keys.append(compiled_key)
    return tuple(compiled_keys)


def is_sendinput_supported_key(key: str) -> bool:
    """检查当前实现能否通过 SendInput 发送该按键"""
    return _compile_sendinput_key(key) is not None


def is_vk_pressed(vk_code: int) -> bool:
    """检查指定的按键是否当前被按下"""
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0


def parse_key_combo(value: str, *, field_name: str) -> tuple[str, ...]:
    """将按键字符串解析为规范化后的按键序列"""
    normalized_value = str(value).strip().lower()
    if not normalized_value:
        raise ValueError(f"{field_name}不能为空")

    parts = tuple(part.strip() for part in normalized_value.split("+"))
    if any(len(part) == 0 for part in parts):
        raise ValueError(f"无效的组合键格式: {value}")

    return parts
