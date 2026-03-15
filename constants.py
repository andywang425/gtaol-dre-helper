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
