import re
from markdown.extensions import Extension
from markdown.postprocessors import Postprocessor


class TopicRailPostprocessor(Postprocessor):
    """
    1. HTML内に class="topic" または class="section" を持つ見出しが存在する場合、
       自動的に <mono-topic-rail></mono-topic-rail> を先頭に注入する。
    2. 見出しマーカー（class="marker..."）を持つ見出しの内部テキストを
       <span class="heading-marker-text">...</span> で包み、
       テキスト幅のみにマーカー下線が正確に収まるようにする。
    """

    TOPIC_PATTERN = re.compile(
        r'<h[1-6][^>]*class="[^"]*?\b(?:topic|section)\b[^"]*?"',
        re.IGNORECASE,
    )

    HEADING_MARKER_PATTERN = re.compile(
        r'(<h[1-6][^>]*class="[^"]*?\b(?:marker|heading-marker|marker-[a-z0-9-]+|heading-marker-[a-z0-9-]+)\b[^"]*?"[^>]*>)(.*?)(</h[1-6]>)',
        re.IGNORECASE | re.DOTALL,
    )

    def run(self, text: str) -> str:
        # 明示的な構文 @[topic-rail] の置換
        if "@[topic-rail" in text:
            text = re.sub(
                r"@\[topic-rail(?:(?:\:\s*)?([^\]]*))\](?:\(((?:[^()]*|\([^()]*\))*)\))?(?:\{([^}]*)\})?",
                "<mono-topic-rail></mono-topic-rail>",
                text,
            )

        # 見出しに .topic または .section クラスが存在し、まだタグがない場合、先頭に注入
        if "<mono-topic-rail>" not in text and self.TOPIC_PATTERN.search(text):
            text = "<mono-topic-rail></mono-topic-rail>\n" + text

        # 見出しマーカーのテキスト幅対応（内部spanラップ）
        def wrap_heading_text(m: re.Match) -> str:
            start_tag = m.group(1)
            content = m.group(2)
            end_tag = m.group(3)
            # すでにheading-marker-textで包まれている場合はスキップ
            if 'class="heading-marker-text"' in content:
                return m.group(0)
            return f'{start_tag}<span class="heading-marker-text">{content}</span>{end_tag}'

        text = self.HEADING_MARKER_PATTERN.sub(wrap_heading_text, text)

        return text


class TopicRailExtension(Extension):
    def extendMarkdown(self, md):
        md.postprocessors.register(TopicRailPostprocessor(md), "mono_topic_rail", 25)


def makeExtension(**kwargs):
    return TopicRailExtension(**kwargs)
