import time
import argparse
import sys
from constants import MIN_PLAYERS_TRIGGER
from utils import load_config, setup_tesseract, ocr_image_file, parse_player_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path")
    args = parser.parse_args()

    config = load_config()

    monitor_cfg = config.get("monitor")
    region_cfg = monitor_cfg.get("region")
    region = (
        region_cfg.get("x"),
        region_cfg.get("y"),
        region_cfg.get("width"),
        region_cfg.get("height"),
    )

    if not args.image_path:
        print("请提供 image_path")
        sys.exit(2)

    setup_tesseract()

    ocr_time_start = time.time()

    text = ocr_image_file(
        args.image_path,
        region=region,
    )

    ocr_time_end = time.time()
    ocr_time_ms = (ocr_time_end - ocr_time_start) * 1000

    count = parse_player_count(text)

    print("OCR文本:")
    print(text if text else "<空>")
    print(f"解析已加入人数: {count}")
    print(f"是否达到阈值: {count is not None and count >= MIN_PLAYERS_TRIGGER}")
    print(f"OCR耗时: {ocr_time_ms:.2f}ms")


if __name__ == "__main__":
    main()
