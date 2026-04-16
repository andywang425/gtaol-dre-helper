import threading
import time
from collections.abc import Callable
import traceback
from typing import Optional

from textual.message import Message
from gtaol_dre_helper.models.config import AppConfig, RuntimeProfile
from gtaol_dre_helper.utils.logging import LogLevel, LogStyle
from gtaol_dre_helper.models.monitor import MonitorDependencies, MonitorState
from gtaol_dre_helper.utils.screen import clean_mss

# 主循环间隔 (秒)
MAIN_LOOP_INTERVAL = 0.05
# 监控检测间隔 (秒)
MONITOR_CHECK_INTERVAL = 0.5
# 卡 CEO 触发条件（已加入人数 >= 2）
MIN_PLAYERS_TRIGGER = 2


class MonitorService:
    """承载主监控循环的运行时服务"""

    class Logged(Message):
        """日志消息"""
        level: LogLevel
        message: str
        style: LogStyle
        markup: bool

        def __init__(self, level: LogLevel, message: str, style: LogStyle, markup: bool) -> None:
            self.level = level
            self.message = message
            self.style = style
            self.markup = markup
            super().__init__()

    class OverviewChanged(Message):
        """监控概览信息改变消息"""
        monitoring: bool
        active_profile: Optional[RuntimeProfile]

        def __init__(self, monitoring: bool, active_profile: Optional[RuntimeProfile]) -> None:
            self.monitoring = monitoring
            self.active_profile = active_profile
            super().__init__()

    class ProfilesLoaded(Message):
        """监控方案加载完成消息"""
        profiles: list[RuntimeProfile]

        def __init__(self, profiles: list[RuntimeProfile]) -> None:
            self.profiles = profiles
            super().__init__()

    config: AppConfig | None = None

    def __init__(
        self,
        *,
        post_message: Callable[[Message], bool],
        bell: Callable[[], None] = lambda: None,
        dependencies: Optional[MonitorDependencies] = None,
    ) -> None:
        """创建监控服务实例

        Args:
            post_message: textual.app post_message
            dependencies: 依赖
        """
        self.post_message: Callable[[Message], bool] = lambda msg: post_message(
            msg) if not self.stop_event.is_set() else False
        self.bell: Callable[[], None] = lambda: bell(
        ) if not self.stop_event.is_set() else None

        dependencies = dependencies or MonitorDependencies()

        self.setup_tesseract_fn = dependencies.setup_tesseract
        self.ocr_screen_region_fn = dependencies.ocr_screen_region
        self.get_screen_region_average_color_fn = dependencies.get_screen_region_average_color
        self.check_screen_region_color_fn = dependencies.check_screen_region_color
        self.parse_player_count_fn = dependencies.parse_player_count
        self.execute_sequence_fn = dependencies.execute_sequence
        self.is_vk_pressed_fn = dependencies.is_vk_pressed

        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        self.state = MonitorState()

    def set_config(self, config: AppConfig) -> None:
        """设置监控配置"""
        self.config = config

    @property
    def is_running(self) -> bool:
        """服务是否正在运行"""
        return self.thread is not None and self.thread.is_alive()

    def start(self) -> None:
        """启动服务"""
        if self.is_running:
            return

        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self.run,
            name="gtaol-dre-helper-monitor-service",
            daemon=True,
        )
        self.thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        """停止服务"""
        self.stop_event.set()
        if self.thread is None:
            return
        if threading.current_thread() is self.thread:
            return
        self.thread.join(timeout=timeout)

    def run(self) -> None:
        """服务主要逻辑"""
        try:
            self.initialize_runtime()
            self.run_loop()
        except Exception as e:
            self.log("error", f"监控服务出错: {e}\n{traceback.format_exc()}")
        finally:
            clean_mss()

    def initialize_runtime(self) -> None:
        """初始化服务运行时环境"""
        if self.config is None:
            raise ValueError("配置缺失，无法初始化监控服务")

        self.state.configure(self.config)

        self.post_message(self.ProfilesLoaded(
            list(self.state.profiles.values())))

        self.setup_tesseract_fn()

        self.log("info", f"监控区域: {self.state.regions}")
        self.log(
            "info", f"监控方案: {[p.name for p in self.state.profiles.values()]}")
        self.log("info", "监控状态: 关闭")

    def run_loop(self) -> None:
        """服务主循环"""
        while not self.stop_event.is_set():
            triggered_profile_key = self.poll_triggered_profile_key()

            if triggered_profile_key is not None:
                self.handle_toggle(triggered_profile_key)

            if self.state.monitoring:
                self.run_monitor_cycle()

            time.sleep(MAIN_LOOP_INTERVAL)

    def poll_triggered_profile_key(self) -> Optional[str]:
        """轮询所有监控方案

        依次判断每个方案的快捷键是否被按下

        Returns:
            触发的方案的key
        """
        for key, profile in self.state.profiles.items():
            toggle_pressed = all(
                self.is_vk_pressed_fn(vk_code)
                for vk_code in profile.toggle_vk_codes
            )
            if toggle_pressed and not self.state.pressed_states[key]:
                self.state.set_pressed(key, toggle_pressed)
                return key
            self.state.set_pressed(key, toggle_pressed)
        return None

    def handle_toggle(self, triggered_profile_key: str) -> None:
        """处理监控状态切换"""

        triggered_profile = self.state.profiles[triggered_profile_key]

        if self.state.active_profile_key is None:
            self.state.activate(triggered_profile_key)
            self.log("info", f"监控状态: 开启（当前方案【{triggered_profile.name}】）")
        elif self.state.active_profile_key == triggered_profile_key:
            self.state.deactivate()
            self.log("info", "监控状态: 关闭")
        else:
            self.state.activate(triggered_profile_key)
            self.log("info", f"监控状态: 切换至方案【{triggered_profile.name}】")

        self.monitoring_overview_changed()
        self.bell()

    def run_monitor_cycle(self) -> None:
        """运行一轮监控检查"""
        now = time.monotonic()
        if now < self.state.next_check_at:
            return

        current_profile = self.state.active_profile
        assert current_profile is not None

        if current_profile.type == "ceo":
            self.run_ceo_monitor_cycle()
        elif current_profile.type == "single":
            self.run_single_monitor_cycle()

        self.state.schedule_next_check(
            time.monotonic() + MONITOR_CHECK_INTERVAL)

    def run_ceo_monitor_cycle(self) -> None:
        """运行一轮卡CEO监控检查"""
        text = self.ocr_screen_region_fn(self.state.region_for("ceo"))

        if not text:
            return

        self.log("info", f"识别到的文本: {text}")
        joined_players = self.parse_player_count_fn(text)

        if joined_players is None:
            return

        self.log("info", f"检测到已加入人数: {joined_players}")
        if joined_players >= MIN_PLAYERS_TRIGGER:
            self.trigger_sequence_for_active_profile()

    def run_single_monitor_cycle(self) -> None:
        """运行一轮卡单监控检查"""
        single_region = self.state.region_for("single")

        if self.state.menu_color is None:
            self.state.set_menu_color(
                self.get_screen_region_average_color_fn(single_region)
            )
            return

        if not self.check_screen_region_color_fn(single_region, self.state.menu_color):
            self.trigger_sequence_for_active_profile()

    def trigger_sequence_for_active_profile(self) -> None:
        """触发当前监控方案的按键序列"""
        current_profile = self.state.active_profile
        assert current_profile is not None

        self.state.deactivate()
        self.monitoring_overview_changed()

        self.log(
            "info",
            f"执行方案【{current_profile.name}】的按键序列"
        )
        self.execute_sequence_fn(current_profile.sequence)
        self.log("info", "操作完成，监控已自动停止", "success")

    def monitoring_overview_changed(self) -> None:
        """给 App 发送一条消息：监控状态和当前监控方案改变"""
        self.post_message(self.OverviewChanged(
            self.state.monitoring,
            self.state.active_profile
        ))

    def log(self, level: LogLevel, message: str, style: LogStyle = "auto", markup: bool = False) -> None:
        """给 App 发送一条消息：日志"""
        self.post_message(self.Logged(level, message, style, markup))
