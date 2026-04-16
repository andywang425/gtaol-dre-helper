from typing import Literal, NamedTuple, TypedDict


type ProfileTypes = Literal["ceo", "single"]


class RegionDict(TypedDict):
    left: int
    top: int
    width: int
    height: int


class ColorTuple(NamedTuple):
    r: int
    g: int
    b: int


class Resolution(NamedTuple):
    width: int
    height: int
