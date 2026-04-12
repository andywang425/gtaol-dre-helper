from __future__ import annotations
from textual.content import Content
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Header, Footer, Label, Static, RichLog
from textual.reactive import reactive

from gtaol_dre_helper.models.config import RuntimeProfile


class ActiveProfileText(Static):
    """当前方案文本"""

    value = reactive("")

    text = reactive("无")

    def compute_text(self) -> str:
        return f"[bold cyan]{self.value}[/bold cyan]" if self.value else "无"

    def render(self) -> str:
        return self.text


class MonitorStatusText(Static):
    """监控状态文本"""

    value = reactive(False)

    text = reactive("关闭")

    def compute_text(self) -> str:
        return "[bold green]开启[/bold green]" if self.value else "关闭"

    def render(self) -> str:
        return self.text


class OverviewPanel(Widget):
    """概览面板"""
    # 监控状态
    monitor_status = reactive(False)
    # 当前方案
    active_profile = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="item"):
            yield Label("监控状态: ")
            yield MonitorStatusText(classes="text", id="monitor_status").data_bind(value=OverviewPanel.monitor_status)

        with Horizontal(classes="item"):
            yield Label("当前方案: ")
            yield ActiveProfileText(classes="text", id="active_profile").data_bind(value=OverviewPanel.active_profile)


class AvailableProfilesPanel(Widget):
    """可用方案面板"""
    TABLE_COLUMNS = ("方案名称", "类型", "快捷键", "动作序列")

    profiles: reactive[list[RuntimeProfile]] = reactive([])

    def compose(self) -> ComposeResult:
        yield DataTable(show_cursor=False)

    @property
    def dataTable(self) -> DataTable:
        return self.query_one(DataTable)

    def on_mount(self) -> None:
        self.dataTable.add_columns(*self.TABLE_COLUMNS)

    def watch_profiles(self, old_profiles: list[RuntimeProfile], new_profiles: list[RuntimeProfile]) -> None:
        """监听可用方案列表变化"""
        if not new_profiles:
            return

        table = self.dataTable
        table.clear()

        for profile in new_profiles:
            action_keys = [
                ("+".join(action.keys), action.times)
                for action in profile.sequence
            ]

            table.add_row(
                profile.name,
                profile.type,
                profile.toggle_key,
                ", ".join([(f"{key} × {times}" if times > 1 else key)
                          for key, times in action_keys]) or "-",
                key=profile.toggle_key
            )


class LogPanel(Widget):
    def compose(self) -> ComposeResult:
        yield RichLog(id="log", markup=True)

    @property
    def richLog(self) -> RichLog:
        return self.query_one(RichLog)

    def clear_logs(self) -> None:
        """清除日志"""
        self.richLog.clear()

    def write_log(self, message: Content) -> None:
        """写入日志"""
        self.richLog.write(message)


class DashboardScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="dashboard"):
            overview_panel = OverviewPanel()
            overview_panel.border_title = "概览"
            yield overview_panel

            available_profiles_panel = AvailableProfilesPanel()
            available_profiles_panel.border_title = "可用方案"
            yield available_profiles_panel

            log_panel = LogPanel()
            log_panel.border_title = "日志"
            yield log_panel

        yield Footer()

    @property
    def overviewPanel(self) -> OverviewPanel:
        return self.query_one(OverviewPanel)

    @property
    def availableProfilesPanel(self) -> AvailableProfilesPanel:
        return self.query_one(AvailableProfilesPanel)

    @property
    def logPanel(self) -> LogPanel:
        return self.query_one(LogPanel)

    def set_overview(self, enabled: bool, active_profile_name: str = "") -> None:
        """设置概览信息（监控状态和当前方案）"""
        overview = self.overviewPanel
        overview.monitor_status = enabled
        overview.active_profile = active_profile_name

    def set_available_profiles(self, profiles: list[RuntimeProfile]) -> None:
        """设置可用方案"""
        self.availableProfilesPanel.profiles = profiles

    def clear_logs(self) -> None:
        """清除日志"""
        self.logPanel.clear_logs()

    def write_log(self, message: Content) -> None:
        """写入日志"""
        self.logPanel.write_log(message)
