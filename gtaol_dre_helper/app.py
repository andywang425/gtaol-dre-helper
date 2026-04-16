import os
from pathlib import Path
from typing import Iterable, cast

from textual.app import App, SystemCommand
from textual.binding import Binding
from textual.content import Content
from textual.screen import Screen
from gtaol_dre_helper.models.config import AppConfig, RuntimeProfile
from gtaol_dre_helper.screens.dashboard import DashboardScreen
from gtaol_dre_helper.utils.config import get_example_config_file_path, get_or_create_config_file, load_config
from gtaol_dre_helper.services.monitor import MonitorService
from gtaol_dre_helper.utils.logging import LogLevel, LogStyle, build_log_content
from gtaol_dre_helper.utils.paths import get_region_locator_path


class DreHelperApp(App):
    TITLE = "GTAOL Dre Helper"

    CSS_PATH = Path(__file__).with_name("style.scss")

    BINDINGS = [
        Binding(key="ctrl+q", action="quit", description="退出"),
        Binding(key="ctrl+e", action="open_config",
                description="编辑配置"),
        Binding(key="ctrl+r", action="reload_config", description="重载配置"),
        Binding(key="ctrl+x", action="open_example_config",
                description="打开示例配置"),
    ]

    SCREENS = {
        "dashboard_screen": DashboardScreen,
    }

    MODES = {
        "dashboard": "dashboard_screen",
    }

    monitor_service: MonitorService | None = None
    config: AppConfig | None = None

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield SystemCommand("Open RegionLocator", "启动用于定位OCR/颜色识别区域的辅助工具", self.open_region_locator)
        yield SystemCommand("Reset Config", "重置配置为默认", self.reset_config)

    def open_region_locator(self) -> None:
        """打开 RegionLocator 辅助工具"""
        region_locator_path = get_region_locator_path()
        if not region_locator_path.exists():
            self.notify("未找到 RegionLocator.exe", severity="error")
            return

        try:
            os.startfile(region_locator_path)
        except OSError as e:
            self.notify(f"打开 RegionLocator 失败: {e}", severity="error")

    def reset_config(self) -> None:
        """重置配置"""

        try:
            get_or_create_config_file(always_create=True)
            self.notify("已将配置重置为默认（重载后生效）")
        except FileNotFoundError as e:
            self.notify(f"重置配置失败: {e}", severity="error")

    @property
    def dashboard(self) -> DashboardScreen:
        """获取 Dashboard Screen"""
        return cast(DashboardScreen, self.get_screen("dashboard_screen"))

    def update_overview(self, enabled: bool, active_profile_name: str) -> None:
        """更新概览信息"""
        self.dashboard.set_overview(enabled, active_profile_name)

    def update_available_profiles(self, profiles: list[RuntimeProfile]) -> None:
        """更新可用方案"""
        dashboard = self.dashboard
        dashboard.set_available_profiles(profiles)

    def write_app_log(self, message: Content) -> None:
        """写入 App 的 RichLog 日志"""
        self.dashboard.write_log(message)

    def write_log_content(self, content: Content) -> None:
        """写日志内容"""
        self.log(content)
        self.write_app_log(content)

    def write_log(
        self,
        level: LogLevel,
        message: str,
        style: LogStyle = "auto",
        markup: bool = False,
    ) -> None:
        """写日志"""
        content = build_log_content(level, message, style, markup)
        self.write_log_content(content)

    def on_monitor_service_logged(self, message: MonitorService.Logged) -> None:
        """处理日志消息"""
        content = build_log_content(
            message.level, message.message, message.style, message.markup)
        self.write_log_content(content)

    def on_monitor_service_overview_changed(self, message: MonitorService.OverviewChanged):
        """处理监控概览改变"""
        self.update_overview(
            message.monitoring,
            message.active_profile.name if message.active_profile else ""
        )

    def on_monitor_service_profiles_loaded(self, message: MonitorService.ProfilesLoaded):
        """处理监控方案加载完成消息"""
        self.update_available_profiles(message.profiles)
        self.write_log("info", "配置加载成功", "success")

    def load_config(self) -> AppConfig | None:
        """加载配置"""
        try:
            return load_config()
        except Exception as e:
            self.write_log("error", f"配置加载失败: {e}")
            self.write_log(
                "info", "请参考[b $accent-lighten-3 @click=app.open_example_config]示例配置文件[/]修改你的配置", "accent", markup=True)

    def build_monitor_service(self) -> MonitorService:
        """创建监控服务实例"""
        return MonitorService(
            post_message=self.post_message,
            bell=self.bell,
        )

    def start_monitor_service(self) -> None:
        """在配置准备完成后启动监控服务"""
        assert self.monitor_service is not None

        config = self.load_config()
        if config is None:
            return

        self.monitor_service.set_config(config)
        self.monitor_service.start()

    def action_open_config(self) -> None:
        """打开配置文件"""
        config_file_path = get_or_create_config_file()
        try:
            os.startfile(config_file_path)
        except OSError as e:
            self.write_log("error", f"打开配置文件失败: {e}")

    def action_open_example_config(self) -> None:
        """打开示例配置文件"""
        example_config_file_path = get_example_config_file_path()
        try:
            os.startfile(example_config_file_path)
        except OSError as e:
            self.write_log("error", f"打开示例配置文件失败: {e}")

    def action_reload_config(self) -> None:
        """停止当前监控并重新加载配置"""
        self.write_log("info", "开始重新加载配置")

        assert self.monitor_service is not None
        self.monitor_service.stop()

        self.update_overview(False, "")
        self.update_available_profiles([])
        self.start_monitor_service()

    async def on_mount(self) -> None:
        await self.switch_mode("dashboard")
        self.monitor_service = self.build_monitor_service()
        self.start_monitor_service()

    def on_unmount(self) -> None:
        if self.monitor_service is not None:
            self.monitor_service.stop()
