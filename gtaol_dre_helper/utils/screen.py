from typing import cast
from PIL import Image
from mss.windows import MSS as mss

from gtaol_dre_helper.types import ColorTuple, RegionDict, Resolution

SINGLE_COLOR_TOLERANCE = 16
SINGLE_COLOR_MIN_MATCH_RATIO = 0.88

# Python MSS bug：mss实例只能在创建它的线程中使用
# https://github.com/BoboTiG/python-mss/issues/273
# 因此该实例目前仅在 MonitorService 线程中使用，并且结束线程时要清理该示例，在新线程中再创建
_mss_instance: mss | None = None


def get_mss():
    """获取全局 mss 实例"""
    global _mss_instance
    if _mss_instance is None:
        _mss_instance = mss()
    return _mss_instance


def clean_mss():
    """清理全局 mss 实例"""
    global _mss_instance
    if _mss_instance is not None:
        try:
            _mss_instance.close()
        except Exception as e:
            print(f"关闭 mss 实例时出错: {e}")
        finally:
            _mss_instance = None


def get_primary_screen_resolution() -> Resolution | None:
    """返回主屏幕分辨率，获取失败时返回 None"""
    with mss() as sct:
        primary_monitor = sct.monitors[1]

    width = primary_monitor.get("width")
    height = primary_monitor.get("height")

    if width is None or height is None:
        return None

    return Resolution(width, height)


def get_screen_region_average_color(region: RegionDict) -> ColorTuple:
    """
    获取屏幕指定区域的平均颜色

    Args:
        region: 屏幕区域

    Returns:
        区域平均颜色
    """
    screenshot = get_mss().grab(cast(dict[str, int], region))
    screenshot_image = Image.frombytes(
        "RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    region_pixels = cast(
        tuple[ColorTuple], screenshot_image.get_flattened_data())

    pixel_count = len(region_pixels)

    avg_r = round(sum(r for r, _, _ in region_pixels) / pixel_count)
    avg_g = round(sum(g for _, g, _ in region_pixels) / pixel_count)
    avg_b = round(sum(b for _, _, b in region_pixels) / pixel_count)

    print(f"区域平均色: {avg_r:.2f}, {avg_g:.2f}, {avg_b:.2f}")

    return ColorTuple(avg_r, avg_g, avg_b)


def check_screen_region_color(region: RegionDict, init_color: ColorTuple) -> bool:
    """
    获取屏幕指定区域颜色，并判断绝大多数像素是否都近似于初始颜色

    Args:
        region: 屏幕区域
        init_color: 初始颜色

    Returns:
        如果区域绝大多数像素都近似于初始颜色，则返回 True，否则返回 False
    """
    screenshot = get_mss().grab(cast(dict[str, int], region))
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
