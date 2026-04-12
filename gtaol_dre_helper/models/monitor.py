
from __future__ import annotations
from collections.abc import Sequence, Callable
from dataclasses import dataclass, field
from typing import Optional

from gtaol_dre_helper.models.config import AppConfig, ProfileTypes, RuntimeActionStep, RuntimeProfile

from gtaol_dre_helper.utils.config import load_config
from gtaol_dre_helper.utils.screen import get_screen_region_average_color, check_screen_region_color
from gtaol_dre_helper.utils.ocr import ocr_screen_region, setup_tesseract
from gtaol_dre_helper.utils.input import execute_sequence
from gtaol_dre_helper.utils.text_parser import parse_player_count
from gtaol_dre_helper.utils.hotkey import is_vk_pressed
from gtaol_dre_helper.types import RegionTuple, ColorTuple


@dataclass(slots=True)
class MonitorDependencies:
    load_config: Callable[[], AppConfig] = load_config
    setup_tesseract: Callable[[], None] = setup_tesseract
    ocr_screen_region: Callable[[RegionTuple], str] = ocr_screen_region
    get_screen_region_average_color: Callable[[
        RegionTuple], ColorTuple] = get_screen_region_average_color
    check_screen_region_color: Callable[[
        RegionTuple, ColorTuple], bool] = check_screen_region_color
    parse_player_count: Callable[[str], Optional[int]] = parse_player_count
    execute_sequence: Callable[[
        Sequence[RuntimeActionStep]], None] = execute_sequence
    is_vk_pressed: Callable[[int], bool] = is_vk_pressed


@dataclass(slots=True)
class MonitorState:
    profiles: dict[str, RuntimeProfile] = field(default_factory=dict)
    pressed_states: dict[str, bool] = field(default_factory=dict)
    regions: dict[ProfileTypes, RegionTuple] = field(default_factory=dict)
    monitoring: bool = False
    active_profile_key: Optional[str] = None
    menu_color: Optional[ColorTuple] = None
    next_check_at: float = 0.0

    @property
    def active_profile(self) -> Optional[RuntimeProfile]:
        """当前监控方案"""
        if self.active_profile_key is None:
            return None
        return self.profiles.get(self.active_profile_key)

    def configure(
        self,
        *,
        profiles: dict[str, RuntimeProfile],
        regions: dict[ProfileTypes, RegionTuple],
    ) -> None:
        """配置监控状态"""
        self.profiles = profiles
        self.pressed_states = {
            key: False
            for key in profiles
        }
        self.regions = regions
        self.deactivate()
        self.next_check_at = 0.0

    def activate(self, profile_key: str) -> RuntimeProfile:
        """开启监控，激活监控方案"""
        profile = self.profiles[profile_key]
        self.monitoring = True
        self.active_profile_key = profile_key
        self.menu_color = None
        self.next_check_at = 0.0
        return profile

    def deactivate(self) -> None:
        """关闭监控"""
        self.monitoring = False
        self.active_profile_key = None
        self.menu_color = None

    def region_for(self, profile_type: ProfileTypes) -> RegionTuple:
        """获取指定类型的区域配置"""
        return self.regions[profile_type]

    def set_pressed(self, profile_key: str, is_pressed: bool) -> None:
        """设置指定监控方案的快捷键按键状态"""
        self.pressed_states[profile_key] = is_pressed

    def set_menu_color(self, color: Optional[ColorTuple]) -> None:
        """设置游戏内任务准备页面的菜单颜色"""
        self.menu_color = color

    def schedule_next_check(self, next_check_at: float) -> None:
        """设置下一次检查时间"""
        self.next_check_at = next_check_at
