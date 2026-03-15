"""
常量定义模块
"""

# ========== 文件和路径配置 ==========
CONFIG_FILE_PATH = "config.yaml"
TESSERACT_SUBDIR = "tesseract"
TESSERACT_EXECUTABLE = "tesseract.exe"

# ========== OCR 配置 ==========
# Tesseract 默认配置
OCR_DEFAULT_LANG = "eng"
OCR_TESSERACT_CONFIG = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/"

# 图像预处理配置
OCR_PREPROCESS_CONFIG = {
    "upscale": 1.5,
    "color_filter": {
        "enabled": True,
        "target_hex": "#eeeeee",
        "tolerance": 28
    }
}

# 图像预处理默认值 (用于 utils.py 中的函数默认参数)
OCR_DEFAULT_UPSCALE = 1.0
OCR_DEFAULT_COLOR_TARGET = "#eeeeee"
OCR_DEFAULT_COLOR_TOLERANCE = 24

# ========== 监控配置 ==========
# 主循环间隔 (秒)
MAIN_LOOP_INTERVAL = 0.05

# OCR 检测间隔 (秒)
MONITOR_CHECK_INTERVAL = 0.6

# 触发条件
MIN_PLAYERS_TRIGGER = 2

# 随机延迟范围 (秒)
RANDOM_DELAY_MIN = 0.05
RANDOM_DELAY_MAX = 0.15

# 默认切换按键
DEFAULT_TOGGLE_KEY = "f12"

# ========== 按键操作默认值 ==========
ACTION_DEFAULT_DELAY = 0.05
ACTION_DEFAULT_HOLD = 0.03
ACTION_DEFAULT_REPEAT = 1

# ========== 颜色处理 ==========
COLOR_HEX_LENGTH = 6

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
    "kp0": 0x60,
    "kp1": 0x61,
    "kp2": 0x62,
    "kp3": 0x63,
    "kp4": 0x64,
    "kp5": 0x65,
    "kp6": 0x66,
    "kp7": 0x67,
    "kp8": 0x68,
    "kp9": 0x69,
    "num_mul": 0x6A,
    "num_add": 0x6B,
    "num_sub": 0x6D,
    "num_decimal": 0x6E,
    "num_div": 0x6F,
    "numpad_mul": 0x6A,
    "numpad_add": 0x6B,
    "numpad_sub": 0x6D,
    "numpad_decimal": 0x6E,
    "numpad_div": 0x6F,
}
