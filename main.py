import time
import random
from utils import load_config, setup_tesseract, ocr_screen_region, parse_player_count, execute_sequence, is_vk_pressed, build_action_profiles
from constants import *


def main():
    print("GTAOL CEO Helper 启动中...")

    try:
        # 加载配置
        config = load_config()

        region = config.get("region")
        if not region:
            raise ValueError("配置文件 config.yaml 缺少必要字段 region")
        region_tuple = (region['x'], region['y'],
                        region['width'], region['height'])

        profiles_cfg = config.get("profiles", [])
        if len(profiles_cfg) == 0:
            raise ValueError("配置文件 config.yaml 缺少必要字段 profiles")
        profiles = build_action_profiles(profiles_cfg)

        setup_tesseract()

        print(f"监控区域: {region}")
        print("监控方案:")
        for profile in profiles:
            print(f"- {profile['name']}: 按 {profile['toggle_key']} 开/关监控")
        print("--------------------------------")
        print(f"监控状态: 关闭")

        # 是否正在监控
        monitoring = False
        # 当前监控方案索引
        active_profile_index = None
        # 每个监控方案的开关键是否被按下状态
        pressed_states = [False] * len(profiles)
        # 下一次检查时间
        next_check_at = 0.0

        while True:
            # 刚刚被按下开关键的监控方案索引
            triggered_profile_index = None

            for index, profile in enumerate(profiles):
                # 当前方案的开关键是否被按下
                toggle_pressed = is_vk_pressed(profile["toggle_vk_code"])
                if toggle_pressed and not pressed_states[index]:
                    # 如果被按下且之前未被记录为按下，记录为按下（防止重复触发）
                    triggered_profile_index = index
                # 更新当前方案的开关键是否被按下状态
                pressed_states[index] = toggle_pressed
                # 如果有方案的开关键被按下，跳出循环
                if triggered_profile_index is not None:
                    break

            if triggered_profile_index is not None:
                # 获取刚刚被触发的监控方案
                profile = profiles[triggered_profile_index]

                if active_profile_index is None:
                    # 目前无监控方案，开启监控
                    monitoring = True
                    active_profile_index = triggered_profile_index
                    next_check_at = 0.0
                    print(f"监控状态: 开启（当前方案【{profile['name']}】）")
                else:
                    # 当前正在监控中
                    # 当前监控方案与刚刚触发的方案是否相同
                    same_profile_toggle = active_profile_index == triggered_profile_index
                    if same_profile_toggle:
                        # 如果当前监控方案与刚刚触发的方案相同，关闭监控
                        monitoring = False
                        active_profile_index = None
                        print(f"监控状态: 关闭")
                    else:
                        # 若不同，切换监控方案
                        monitoring = True
                        active_profile_index = triggered_profile_index
                        next_check_at = 0.0
                        print(f"监控状态: 切换至方案【{profile['name']}】")

            if monitoring:
                # 监控中
                now = time.monotonic()
                if now >= next_check_at:
                    # 检查监控区域文本
                    text = ocr_screen_region(region_tuple)

                    if text:
                        print(f"识别到的文本: {text}")
                        # 解析文本中的已加入人数
                        joined_players = parse_player_count(text)

                        if joined_players is not None:
                            print(f"检测到已加入人数: {joined_players}")

                            if joined_players >= MIN_PLAYERS_TRIGGER:
                                current_profile = profiles[active_profile_index]
                                monitoring = False
                                active_profile_index = None

                                print(
                                    f"满足条件 (已加入人数 >= {MIN_PLAYERS_TRIGGER})，执行方案【{current_profile['name']}】的按键序列")
                                execute_sequence(current_profile["sequence"])
                                print(
                                    f"操作完成，监控已自动停止")
                    next_check_at = time.monotonic() + MONITOR_CHECK_INTERVAL + \
                        random.uniform(RANDOM_DELAY_MIN, RANDOM_DELAY_MAX)

            time.sleep(MAIN_LOOP_INTERVAL)

    except KeyboardInterrupt:
        print("\n程序已正常退出")

    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
