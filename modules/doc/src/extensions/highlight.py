import re
from xml.etree import ElementTree as etree
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor

VALID_COLORS = {"yellow", "pink", "green", "cyan", "orange", "ai", "warning"}
COLOR_ALIASES = {
    "blue": "cyan",
    "sky": "cyan",
    "red": "pink",
    "normal": "yellow",
    "purple": "ai",
}


def resolve_color(raw_arg: str | None) -> str:
    """波括弧内の引数から安全に色名を解決する（未指定または不明な場合はyellow）"""
    if not raw_arg:
        return "yellow"
    arg = raw_arg.strip().strip("{}").strip()
    match = re.search(r"(?:color\s*[:=]\s*['\"]?|\.)?([a-zA-Z]+)", arg)
    if not match:
        return "yellow"
    color = match.group(1).lower()
    color = COLOR_ALIASES.get(color, color)
    return color if color in VALID_COLORS else "yellow"


class MarkerInlineProcessor(InlineProcessor):
    """==テキスト== または ==テキスト=={color} 記法を <mark> タグへ変換するプロセッサ"""

    def handleMatch(self, m, data):
        text = m.group(1)
        raw_color = m.group(2) if len(m.groups()) >= 2 else None
        color = resolve_color(raw_color)

        el = etree.Element("mark")
        el.set("class", f"mono-marker mono-marker-{color}")
        el.text = text
        return el, m.start(0), m.end(0)


class UnderlineInlineProcessor(InlineProcessor):
    """++テキスト++ または ++テキスト++{color} 記法を <span> タグへ変換するプロセッサ"""

    def handleMatch(self, m, data):
        text = m.group(1)
        raw_color = m.group(2) if len(m.groups()) >= 2 else None
        color = resolve_color(raw_color)

        el = etree.Element("span")
        el.set("class", f"mono-underline mono-underline-{color}")
        el.text = text
        return el, m.start(0), m.end(0)


class HighlightExtension(Extension):
    """蛍光マーカーおよびアンダーライン用Markdown拡張"""

    def extendMarkdown(self, md):
        # ==テキスト== および ==テキスト=={color}
        MARKER_PATTERN = r"==(?!\s)(.+?)(?<!\s)==(?:\{([a-zA-Z0-9_.:=\s\"'-]+)\})?"
        # ++テキスト++ および ++テキスト++{color}
        UNDERLINE_PATTERN = r"\+\+(?!\s)(.+?)(?<!\s)\+\+(?:\{([a-zA-Z0-9_.:=\s\"'-]+)\})?"

        # Python-Markdown標準のhtml保護プロセッサ（priority 90）より低い優先度に設定することで、
        # HTMLタグ属性値（Base64やURLクエリ等）内部の記号に対する誤マッチを防止し、安全にstash保護させる
        md.inlinePatterns.register(MarkerInlineProcessor(MARKER_PATTERN, md), "mono_marker", 85)
        md.inlinePatterns.register(UnderlineInlineProcessor(UNDERLINE_PATTERN, md), "mono_underline", 84)


def makeExtension(**kwargs):
    return HighlightExtension(**kwargs)
