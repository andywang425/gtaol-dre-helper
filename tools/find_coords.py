import time
import ctypes
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils import is_vk_pressed


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_position():
    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def wait_f12(record_prompt):
    print(record_prompt)
    was_pressed = is_vk_pressed(0x7B)

    while True:
        x, y = get_cursor_position()
        print(f"当前坐标: X={x}, Y={y}", end="\r")

        is_pressed = is_vk_pressed(0x7B)
        if is_pressed and not was_pressed:
            print(f"\n已记录坐标: X={x}, Y={y}")
            return x, y

        was_pressed = is_pressed
        time.sleep(0.03)


def main():
    print("GTAOL CEO Helper - 识别区域定位工具")
    print("--------------------------------")

    try:
        left_top = wait_f12("请将鼠标移动到矩形识别区域左上角后按 F12...")
        right_bottom = wait_f12("\n请将鼠标移动到矩形识别区域右下角后按 F12...")

        left = min(left_top[0], right_bottom[0])
        top = min(left_top[1], right_bottom[1])
        width = abs(right_bottom[0] - left_top[0])
        height = abs(right_bottom[1] - left_top[1])

        print("--------------------------------")
        print(f"识别区域左上角坐标: X={left}, Y={top}")
        print(f"识别区域长宽: Width={width}, Height={height}")
        print("请将以上值填入 config.yaml")
        input("\n按回车键退出...")

    except KeyboardInterrupt:
        print("\n已退出。")


if __name__ == "__main__":
    main()
