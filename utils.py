import pytesseract
from PIL import Image
import re
import yaml
import os
import sys
import pydirectinput
import time
import ctypes
from mss.windows import MSS as mss
from typing import Tuple, Optional, Dict, Any
from constants import *

_mss_instance = None


def load_config(path: str = CONFIG_FILE_PATH):
    """
    从 YAML 文件加载配置

    Args:
        path: 配置文件路径，默认读取项目根目录下的 config.yaml

    Returns:
        解析后的配置字典
    """
    if not os.path.exists(path):
        current_dir = os.getcwd()
        raise FileNotFoundError(
            f"当前目录未找到配置文件 {path}，请先在 {current_dir} 下创建或复制 config.yaml"
        )

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_tesseract():
    """
    设置 Tesseract 可执行文件路径
    优先检查程序目录下的 tesseract/tesseract.exe (便携版/打包版)
    """
    # 优先检查本地 bundled Tesseract
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe，基准路径是 exe 所在目录
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是脚本运行，基准路径是当前文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))

    bundled_tesseract = os.path.join(
        base_path, TESSERACT_SUBDIR, TESSERACT_EXECUTABLE)

    if os.path.exists(bundled_tesseract):
        pytesseract.pytesseract.tesseract_cmd = bundled_tesseract
        print(f"使用内置 Tesseract OCR")


def _get_mss():
    global _mss_instance
    if _mss_instance is None:
        _mss_instance = mss()
    return _mss_instance


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    将十六进制颜色字符串转换为 RGB 三元组

    Args:
        hex_color: 十六进制颜色值，支持带或不带 # 前缀

    Returns:
        (R, G, B) 颜色三元组

    Raises:
        ValueError: 颜色值长度不是 6 位时抛出
    """
    cleaned = hex_color.strip().lstrip("#")
    if len(cleaned) != COLOR_HEX_LENGTH:
        raise ValueError(f"无效颜色值: {hex_color}")
    return tuple(int(cleaned[i:i + 2], 16) for i in (0, 2, 4))


def preprocess_ocr_image(image: Image.Image, preprocess_config: Optional[Dict[str, Any]] = None) -> Image.Image:
    """
    对 OCR 输入图像执行预处理

    预处理流程包括：
    - 可选颜色过滤（根据目标颜色与容差生成二值图）
    - 可选图像放大（使用最近邻插值）

    Args:
        image: 原始图像对象
        preprocess_config: 预处理配置，可包含 upscale 和 color_filter

    Returns:
        预处理后的图像对象
    """
    config = preprocess_config or {}
    color_filter_cfg = config.get("color_filter", {})
    use_color_filter = bool(color_filter_cfg.get("enabled", False))

    if not use_color_filter:
        processed = image.convert("L")
    else:
        target_hex = color_filter_cfg.get(
            "target_hex", OCR_DEFAULT_COLOR_TARGET)
        tolerance = int(color_filter_cfg.get(
            "tolerance", OCR_DEFAULT_COLOR_TOLERANCE))
        target_r, target_g, target_b = _hex_to_rgb(target_hex)

        rgb_image = image.convert("RGB")
        binary = Image.new("L", rgb_image.size, 0)
        mask_data = [
            255 if abs(r - target_r) <= tolerance and abs(g -
                                                          target_g) <= tolerance and abs(b - target_b) <= tolerance else 0
            for r, g, b in rgb_image.getdata()
        ]
        binary.putdata(mask_data)
        processed = binary

    upscale = float(config.get("upscale", OCR_DEFAULT_UPSCALE))
    if upscale > 1.0:
        width, height = processed.size
        processed = processed.resize(
            (max(1, int(width * upscale)), max(1, int(height * upscale))),
            resample=Image.NEAREST
        )

    return processed


def ocr_image(
    image: Image.Image,
) -> str:
    """
    对单张图像执行 OCR 识别

    Args:
        image: 待识别图像

    Returns:
        识别后的文本，失败时返回空字符串
    """
    try:
        processed_image = preprocess_ocr_image(
            image, preprocess_config=OCR_PREPROCESS_CONFIG)
        text = pytesseract.image_to_string(
            processed_image, lang=OCR_DEFAULT_LANG, config=OCR_TESSERACT_CONFIG)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print("错误: 未找到 Tesseract OCR，请确保已安装并在 config.yaml 中配置正确路径")
        return ""
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def ocr_screen_region(
    region: Tuple[int, int, int, int],
) -> str:
    """
    截取屏幕指定区域并执行 OCR 识别

    Args:
        region: 屏幕区域，格式为 (x, y, width, height)

    Returns:
        识别后的文本，失败时返回空字符串
    """
    try:
        x, y, width, height = region
        monitor = {
            "left": int(x),
            "top": int(y),
            "width": int(width),
            "height": int(height),
        }
        screenshot = _get_mss().grab(monitor)
        screenshot_image = Image.frombytes(
            "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        return ocr_image(screenshot_image)
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""


def ocr_image_file(
    image_path: str,
    region: Tuple[int, int, int, int],
) -> str:
    """
    从图片文件中裁剪指定区域并执行 OCR 识别 (调试用)

    Args:
        image_path: 图片文件路径
        region: 裁剪区域，格式为 (x, y, width, height)

    Returns:
        识别后的文本，失败时返回空字符串
    """
    try:
        with Image.open(image_path) as image:
            x, y, width, height = region
            cropped_image = image.crop((x, y, x + width, y + height))
            return ocr_image(
                cropped_image,
            )
    except FileNotFoundError:
        print(f"错误: 文件不存在: {image_path}")
        return ""
    except Exception as e:
        print(f"读取图片失败: {e}")
        return ""


def parse_player_count(text: str) -> Optional[int]:
    """
    从文本中解析"已加入人数/人数上限"格式的人数

    例如："2/4"会返回 2

    Args:
        text: OCR 识别得到的原始文本

    Returns:
        解析成功时返回当前加入人数，解析失败时返回 None
    """
    if not text:
        return None

    normalized = re.sub(r"\s+", "", text)
    match = re.search(r"(\d+)/(\d+)", normalized)
    if not match:
        return None
    return int(match.group(1))


def execute_sequence(sequence: list):
    """
    依次执行按键动作序列

    Args:
        sequence: 动作列表。每个动作示例：
            {"key": "m", "delay": 0.1, "hold": 0.03, "times": 1}
    """
    for action in sequence:
        key = action.get("key")
        if not key:
            continue

        delay = float(action.get("delay", ACTION_DEFAULT_DELAY))
        hold = float(action.get("hold", ACTION_DEFAULT_HOLD))
        times = int(action.get("times", ACTION_DEFAULT_TIMES))

        for _ in range(times):
            pydirectinput.keyDown(key, _pause=False)
            if hold > 0:
                time.sleep(hold)
            pydirectinput.keyUp(key, _pause=False)
            if delay > 0:
                time.sleep(delay)


def get_virtual_key_code(key: str) -> Optional[int]:
    """
    将按键名称转换为对应的虚拟键码 (Virtual-Key Code)

    Args:
        key: 按键名称

    Returns:
        成功时返回对应的虚拟键码 (int)，无法识别时返回 None
    """
    normalized_key = str(key).strip().lower()
    if normalized_key in VIRTUAL_KEY_CODES:
        return VIRTUAL_KEY_CODES[normalized_key]
    if normalized_key.startswith("f") and normalized_key[1:].isdigit():
        function_index = int(normalized_key[1:])
        if 1 <= function_index <= 24:
            return 0x6F + function_index
    if len(normalized_key) == 1 and normalized_key.isalnum():
        return ord(normalized_key.upper())
    return None


def is_vk_pressed(vk_code: int) -> bool:
    """
    检查指定的虚拟键码是否当前被按下

    Args:
        vk_code: 虚拟键码

    Returns:
        如果键被按下则返回 True，否则返回 False
    """
    return (ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000) != 0
