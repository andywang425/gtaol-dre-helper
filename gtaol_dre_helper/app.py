from pathlib import Path
from typing import cast

from textual.app import App
from textual.content import Content
from gtaol_dre_helper.models.config import RuntimeProfile
from gtaol_dre_helper.screens.dashboard import DashboardScreen
from gtaol_dre_helper.services.monitor import MonitorService, MonitorService
from gtaol_dre_helper.utils.logging import build_log_content


class DreHelperApp(App):
    TITLE = "GTAOL Dre Helper"

    CSS_PATH = Path(__file__).with_name("style.scss")

    BINDINGS = [
        # ("d", "switch_mode('dashboard')", "Dashboard"),
        # ("c", "switch_mode('config')", "Config Editor"),
    ]

    SCREENS = {
        "dashboard_screen": DashboardScreen,
    }

    MODES = {
        "dashboard": "dashboard_screen",
        # "config": "dashboard_screen",  # TODO: 实现配置编辑器
    }

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

    def write_log(self, message: Content) -> None:
        """写入 RichLog 日志"""
        self.dashboard.write_log(message)

    def on_monitor_service_logged(self, message: MonitorService.Logged) -> None:
        """处理日志消息"""
        content = build_log_content(
            message.level, message.message, message.style, message.markup)
        self.log(content)
        self.write_log(content)

    def on_monitor_service_overview_changed(self, message: MonitorService.OverviewChanged):
        """处理监控概览改变"""
        self.update_overview(
            message.monitoring,
            message.active_profile.name if message.active_profile else ""
        )

    def on_monitor_service_profiles_loaded(self, message: MonitorService.ProfilesLoaded):
        """处理监控方案加载完成消息"""
        self.update_available_profiles(message.profiles)

    async def on_mount(self) -> None:
        await self.switch_mode("dashboard")

        self.monitor_service = MonitorService(
            post_message=self.post_message,
            bell=self.bell,
        )
        self.monitor_service.start()

    def on_unmount(self) -> None:
        self.monitor_service.stop()
