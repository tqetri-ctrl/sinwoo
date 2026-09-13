"""
텍스트 및 이모지 정제 유틸리티 (services/text_utils.py)
- 유니코드 이모지 연속 중복 제거 (예: '⚡ ⚡' -> '⚡', '🔍 🔍' -> '🔍')
- 선행 이모지 감지 및 제거 (카드, 박스, 차트 헤더의 중복 이모지 방지)
- 플레이스홀더 및 제목 서식 정제
"""

import re

# SMP 이모지, 딩뱃, 기술기호, 기호/화살표, 변형선택자, ZWJ 등 포괄
EMOJI_CHAR_CLASS = (
    r'[\U00010000-\U0010ffff'  # Emoticons, Pictographs, Transport, etc.
    r'\u2600-\u27bf'            # Misc Symbols & Dingbats
    r'\u2300-\u23ff'            # Misc Technical
    r'\u2b50\u2b55'             # Star, Heavy Large Circle
    r'\u2900-\u2bfa]'           # Supplemental Arrows and Symbols
)
EMOJI_TOKEN = rf'(?:{EMOJI_CHAR_CLASS}(?:[\ufe00-\ufe0f]|\u200d{EMOJI_CHAR_CLASS})*)'

RE_DUP_EMOJI = re.compile(rf'({EMOJI_TOKEN})(?:\s*\1)+')
RE_LEADING_EMOJIS = re.compile(rf'^(?:\s*{EMOJI_TOKEN})+\s*')


def deduplicate_consecutive_emojis(text: str) -> str:
    """
    동일한 이모지가 연속으로 반복되는 경우 1개로 축약
    예: '## ⚡ ⚡ 신통기획' -> '## ⚡ 신통기획'
        '🔍  🔍 핵심' -> '🔍 핵심'
        '😊😊 안녕하세요' -> '😊 안녕하세요'
        '🏢 🏢 신우부동산' -> '🏢 신우부동산'
    """
    if not text:
        return ""
    return RE_DUP_EMOJI.sub(r'\1', text)


def has_leading_emoji(text: str) -> bool:
    """텍스트가 이모지로 시작하는지 여부 확인"""
    if not text:
        return False
    return bool(RE_LEADING_EMOJIS.match(text.strip()))


def strip_leading_emojis(text: str) -> str:
    """텍스트 시작 부분의 모든 이모지 및 뒤따르는 공백 제거"""
    if not text:
        return ""
    return RE_LEADING_EMOJIS.sub('', text.strip()).strip()
