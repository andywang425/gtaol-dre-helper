import time
import random
import keyboard
from utils import load_config, setup_tesseract, ocr_screen_region, parse_player_count, execute_sequence
from constants import *


def main():
    print("GTAOL CEO Helper 启动中...")

    try:
        # 加载配置
        config = load_config()

        monitor_cfg = config.get("monitor", {})
        region = monitor_cfg.get("region")
        if not region:
            raise ValueError("配置文件 config.yaml 缺少必要字段 monitor.region")
        region_tuple = (region['x'], region['y'],
                        region['width'], region['height'])
        toggle_key = monitor_cfg.get("toggle_key", DEFAULT_TOGGLE_KEY)

        actions_cfg = config.get("actions", {})
        sequence = actions_cfg.get("sequence")
        if not sequence:
            raise ValueError("配置文件 config.yaml 缺少必要字段 actions.sequence")

        # 设置 Tesseract
        setup_tesseract()

        print(f"监控区域: {region}")
        print(f"监控开关按键: {toggle_key}")
        print("--------------------------------")
        print(f"监控状态: 关闭")

        monitoring = False
        toggle_was_pressed = False
        next_check_at = 0.0

        while True:
            toggle_pressed = keyboard.is_pressed(toggle_key)
            if toggle_pressed and not toggle_was_pressed:
                monitoring = not monitoring
                print(f"监控状态: {'开启' if monitoring else '关闭'}")
                if monitoring:
                    next_check_at = 0.0
            toggle_was_pressed = toggle_pressed

            if monitoring:
                now = time.monotonic()
                if now >= next_check_at:
                    text = ocr_screen_region(region_tuple)

                    if text:
                        print(f"识别到的文本: {text}")

                    joined = parse_player_count(text)

                    if joined is not None:
                        print(f"检测到已加入人数: {joined}")

                        if joined >= MIN_PLAYERS_TRIGGER:
                            print(f"满足条件 (>= {MIN_PLAYERS_TRIGGER})，执行操作！")
                            monitoring = False
                            execute_sequence(sequence)
                            print(f"操作完成，监控已自动停止。按 {toggle_key} 重新开启。")
                    next_check_at = time.monotonic() + MONITOR_CHECK_INTERVAL + \
                        random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX)

            time.sleep(MAIN_LOOP_INTERVAL)

    except KeyboardInterrupt:
        print("\n程序已正常退出")

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
