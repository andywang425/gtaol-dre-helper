from typing import Literal, NamedTuple, TypedDict


ProfileTypes = Literal["ceo", "single"]


class RegionDict(TypedDict):
    left: int
    top: int
    width: int
    height: int


class ColorTuple(NamedTuple):
    r: int
    g: int
    b: int
