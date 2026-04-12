import re
from typing import Optional


def parse_player_count(text: str) -> Optional[int]:
    """
    解析"已加入人数/人数上限"格式文本的已加入人数

    例如："2/4"会返回 2

    Args:
        text: OCR 识别得到的原始文本

    Returns:
        解析成功时返回当前加入人数，解析失败时返回 None
    """
    if not text:
        return None

    normalized = re.sub(r"\s+", "", text)
    match = re.search(r"(\d+)/(\d+)", normalized)
    return int(match.group(1)) if match else None
