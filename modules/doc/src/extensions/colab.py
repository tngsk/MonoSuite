from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from src.constants import (
    GITHUB_BASE_URL,
    COLAB_GITHUB_BASE_URL,
    COLAB_BADGE_URL,
)

class ColabLinkTreeprocessor(Treeprocessor):
    def run(self, root):
        for el in root.iter("a"):
            href = el.get("href")
            if href and href.lower().endswith(".ipynb"):
                url = href
                colab_url = url
                if url.startswith(GITHUB_BASE_URL):
                    colab_url = url.replace(GITHUB_BASE_URL, COLAB_GITHUB_BASE_URL)

                el.set("href", colab_url)
                el.set("target", "_blank")
                el.set("rel", "noopener noreferrer")

                classes = el.get("class", "")
                if "colab-link" not in classes:
                    el.set("class", (classes + " colab-link").strip())

                from xml.etree import ElementTree as etree
                img = etree.Element("img")
                img.set("src", COLAB_BADGE_URL)
                img.set("alt", "Open In Colab")
                img.set("class", "colab-badge")

                if el.text:
                    img.tail = el.text
                    el.text = None

                el.insert(0, img)

class ColabExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(ColabLinkTreeprocessor(md), 'colab_link', 10)

def makeExtension(**kwargs):
    return ColabExtension(**kwargs)
