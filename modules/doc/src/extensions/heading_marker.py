"""
Heading Marker Markdown Extension
=================================
見出しマーカー（.marker, .marker-ai, .marker-warning 等）を持つ見出し要素内部の
テキストを自動的に <span class="heading-marker-text">...</span> で包み、
CSS Grid環境下でもマーカー下線が画面全幅に広がることなく、テキスト幅のみに正確に収まるようにする。
"""

import re
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor


class HeadingMarkerPostprocessor(Postprocessor):
    HEADING_MARKER_PATTERN = re.compile(
        r'(<h[1-6][^>]*class="[^"]*?\b(?:marker|heading-marker|marker-[a-z0-9-]+|heading-marker-[a-z0-9-]+)\b[^"]*?"[^>]*>)(.*?)(</h[1-6]>)',
        re.IGNORECASE | re.DOTALL,
    )

    def run(self, text: str) -> str:
        def wrap_heading_text(m: re.Match) -> str:
            start_tag = m.group(1)
            content = m.group(2)
            end_tag = m.group(3)
            # すでにheading-highlightまたはheading-marker-textで包まれている場合は二重ラップを回避
            if 'class="heading-highlight"' in content or 'class="heading-marker-text"' in content:
                return m.group(0)
            return f'{start_tag}<span class="heading-highlight">{content}</span>{end_tag}'

        return self.HEADING_MARKER_PATTERN.sub(wrap_heading_text, text)


class HeadingMarkerExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(HeadingMarkerPostprocessor(md), "mono_heading_marker", 25)


def makeExtension(**kwargs):
    return HeadingMarkerExtension(**kwargs)
