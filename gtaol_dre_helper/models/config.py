from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from gtaol_dre_helper.utils.hotkey import (
    CompiledSendInputKey,
    compile_action_keys,
    get_virtual_key_code,
    is_sendinput_supported_key,
    parse_key_combo,
)
from gtaol_dre_helper.types import ProfileTypes


ACTION_DEFAULT_DELAY = 0.1
ACTION_DEFAULT_HOLD = 0.05
ACTION_DEFAULT_INTERVAL = 0.05
ACTION_DEFAULT_TIMES = 1


class ActionStep(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    key: str
    interval: float = Field(default=ACTION_DEFAULT_INTERVAL, ge=0)
    hold: float = Field(default=ACTION_DEFAULT_HOLD, gt=0)
    delay: float = Field(default=ACTION_DEFAULT_DELAY, ge=0)
    times: int = Field(default=ACTION_DEFAULT_TIMES, ge=1)

    @field_validator("key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        normalized_keys = parse_key_combo(value, field_name="动作按键")
        for key in normalized_keys:
            if not is_sendinput_supported_key(key):
                raise ValueError(f"不支持的动作按键: {value}")
        return "+".join(normalized_keys)

    def to_runtime_action_step(self) -> RuntimeActionStep:
        normalized_keys = parse_key_combo(self.key, field_name="动作按键")

        return RuntimeActionStep(
            keys=normalized_keys,
            interval=self.interval,
            hold=self.hold,
            delay=self.delay,
            times=self.times,
            compiled_keys=compile_action_keys(normalized_keys),
        )


class ProfileConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str
    type: ProfileTypes = Field(default="ceo")
    toggle_key: str
    sequence: list[ActionStep] = Field(min_length=1)

    @field_validator("toggle_key")
    @classmethod
    def validate_toggle_key(cls, value: str) -> str:
        normalized_keys = parse_key_combo(value, field_name="监控开关键")
        if len(set(normalized_keys)) != len(normalized_keys):
            raise ValueError(f"监控开关键不能包含重复按键: {value}")
        for key in normalized_keys:
            if get_virtual_key_code(key) is None:
                raise ValueError(f"不支持的监控开关键: {value}")
        return "+".join(normalized_keys)

    @cached_property
    def toggle_keys(self) -> tuple[str, ...]:
        return parse_key_combo(self.toggle_key, field_name="监控开关键")

    @property
    def toggle_vk_codes(self) -> tuple[int, ...]:
        vk_codes: list[int] = []
        for key in self.toggle_keys:
            vk_code = get_virtual_key_code(key)
            if vk_code is None:
                raise ValueError(f"不支持的监控开关键: {self.toggle_key}")
            vk_codes.append(vk_code)
        return tuple(vk_codes)

    def to_runtime_profile(self) -> RuntimeProfile:
        return RuntimeProfile(
            name=self.name,
            type=self.type,
            toggle_key=self.toggle_key,
            sequence=[step.to_runtime_action_step() for step in self.sequence],
            toggle_vk_codes=self.toggle_vk_codes,
        )


@dataclass(slots=True, frozen=True)
class RuntimeProfile:
    name: str
    type: ProfileTypes
    toggle_key: str
    sequence: list[RuntimeActionStep]
    toggle_vk_codes: tuple[int, ...]


@dataclass(slots=True, frozen=True)
class RuntimeActionStep:
    keys: tuple[str, ...]
    interval: float
    hold: float
    delay: float
    times: int
    compiled_keys: tuple[CompiledSendInputKey, ...] = field(
        default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.compiled_keys:
            object.__setattr__(self, "compiled_keys",
                               compile_action_keys(self.keys))


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: int
    y: int
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


class RegionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ceo: Region
    single: Region


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region: RegionConfig
    profiles: list[ProfileConfig] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_toggle_keys(self) -> Self:
        used_keys: set[tuple[str, ...]] = set()
        for profile in self.profiles:
            normalized_key = tuple(sorted(profile.toggle_keys))
            if normalized_key in used_keys:
                raise ValueError(f"监控开关键重复: {'+'.join(normalized_key)}")
            used_keys.add(normalized_key)
        return self
