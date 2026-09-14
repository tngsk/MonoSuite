from markdown.inlinepatterns import InlineProcessor
from markdown.extensions import Extension

class NowrapInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        from xml.etree import ElementTree as etree
        el = etree.Element("span")
        el.set("class", "nowrap")
        el.text = m.group(1)
        return el, m.start(0), m.end(0)

class NowrapExtension(Extension):
    def extendMarkdown(self, md):
        NOWRAP_PATTERN = r"\{\{(.*?)\}\}"
        md.inlinePatterns.register(NowrapInlineProcessor(NOWRAP_PATTERN, md), 'nowrap', 175)

def makeExtension(**kwargs):
    return NowrapExtension(**kwargs)
