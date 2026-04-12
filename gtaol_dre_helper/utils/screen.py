from typing import Tuple, cast
from PIL import Image
from mss.windows import MSS as mss

SINGLE_COLOR_TOLERANCE = 16
SINGLE_COLOR_MIN_MATCH_RATIO = 0.88


_mss_instance = None


def _get_mss():
    global _mss_instance
    if _mss_instance is None:
        _mss_instance = mss()
    return _mss_instance


def get_screen_region_average_color(region: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
    """
    获取屏幕指定区域的平均颜色

    Args:
        region: 屏幕区域，格式为 (x, y, width, height)

    Returns:
        (R, G, B) 颜色三元组
    """
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
    region_pixels = cast(
        tuple[tuple[int, int, int]], screenshot_image.get_flattened_data())

    pixel_count = len(region_pixels)

    avg_r = round(sum(r for r, _, _ in region_pixels) / pixel_count)
    avg_g = round(sum(g for _, g, _ in region_pixels) / pixel_count)
    avg_b = round(sum(b for _, _, b in region_pixels) / pixel_count)

    print(f"区域平均色: {avg_r:.2f}, {avg_g:.2f}, {avg_b:.2f}")

    return (avg_r, avg_g, avg_b)


def check_screen_region_color(region: Tuple[int, int, int, int], init_color: Tuple[float, float, float]) -> bool:
    """
    获取屏幕指定区域颜色，并判断绝大多数像素是否都近似于初始颜色

    Args:
        region: 屏幕区域，格式为 (x, y, width, height)
        init_color: 初始颜色，格式为 (R, G, B)

    Returns:
        如果区域绝大多数像素都近似于初始颜色，则返回 True，否则返回 False
    """
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
    region_pixels = cast(
        tuple[tuple[int, int, int]], screenshot_image.get_flattened_data())

    pixel_count = len(region_pixels)

    init_r, init_g, init_b = init_color

    matched_pixel_count = sum(
        1 for r, g, b in region_pixels
        if (
            abs(r - init_r) <= SINGLE_COLOR_TOLERANCE and
            abs(g - init_g) <= SINGLE_COLOR_TOLERANCE and
            abs(b - init_b) <= SINGLE_COLOR_TOLERANCE
        )
    )

    matched_ratio = matched_pixel_count / pixel_count

    print(f"匹配像素比例: {matched_ratio}")

    return matched_ratio >= SINGLE_COLOR_MIN_MATCH_RATIO
