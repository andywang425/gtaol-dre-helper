from typing import Tuple, cast

import pytesseract

from PIL import Image

from gtaol_dre_helper.types import ColorTuple, RegionDict
from gtaol_dre_helper.utils.paths import get_runtime_resource_path
from gtaol_dre_helper.utils.screen import get_mss


# Tesseract 默认配置
OCR_DEFAULT_LANG = "eng"
OCR_TESSERACT_CONFIG = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/"


# OCR 图像预处理配置
OCR_PREPROCESS_UPSCALE = 1.5
OCR_PREPROCESS_COLOR_TARGET = (238, 238, 238)
OCR_PREPROCESS_COLOR_TOLERANCE = 28


def setup_tesseract() -> None:
    """使用软件内置的 Tesseract OCR"""
    bundled_tesseract = get_runtime_resource_path("tesseract", "tesseract.exe")

    if bundled_tesseract.exists():
        pytesseract.pytesseract.tesseract_cmd = str(bundled_tesseract)
    else:
        raise FileNotFoundError(f"未找到 Tesseract 可执行文件: {bundled_tesseract}")


def preprocess_ocr_image(image: Image.Image) -> Image.Image:
    """
    对 OCR 输入图像执行预处理

    Args:
        image: 原始图像对象

    Returns:
        预处理后的图像
    """
    target_r, target_g, target_b = OCR_PREPROCESS_COLOR_TARGET

    rgb_image = image.convert("RGB")
    rgb_pixels = cast(Tuple[ColorTuple], rgb_image.get_flattened_data())
    binary = Image.new("L", rgb_image.size)
    mask_data = [
        255 if abs(r - target_r) <= OCR_PREPROCESS_COLOR_TOLERANCE
        and abs(g - target_g) <= OCR_PREPROCESS_COLOR_TOLERANCE
        and abs(b - target_b) <= OCR_PREPROCESS_COLOR_TOLERANCE
        else 0
        for r, g, b in rgb_pixels
    ]
    binary.putdata(mask_data)

    width, height = binary.size
    binary = binary.resize(
        (int(width * OCR_PREPROCESS_UPSCALE),
         int(height * OCR_PREPROCESS_UPSCALE)),
        resample=Image.Resampling.NEAREST
    )

    return binary


def _ocr_image(
    image: Image.Image,
) -> str:
    """
    对单张图像执行 OCR 识别

    Args:
        image: 待识别图像

    Returns:
        识别到的文本
    """
    processed_image = preprocess_ocr_image(image)
    text = pytesseract.image_to_string(
        processed_image, lang=OCR_DEFAULT_LANG, config=OCR_TESSERACT_CONFIG)
    return text.strip()


def ocr_screen_region(
    region: RegionDict,
) -> str:
    """
    截取屏幕指定区域并执行 OCR 识别

    Args:
        region: 屏幕区域，格式为 (x, y, width, height)

    Returns:
        识别到的文本
    """
    screenshot = get_mss().grab(cast(dict[str, int], region))
    screenshot_image = Image.frombytes(
        "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    return _ocr_image(screenshot_image)
