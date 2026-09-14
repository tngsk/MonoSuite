import re
import urllib.request
import urllib.parse
import base64
import hashlib
import json
import logging
import os
import time
from html.parser import HTMLParser
from pathlib import Path
from src.processors.base_parser import BaseComponentParser

logger = logging.getLogger(__name__)

class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "meta":
            key = attrs_dict.get("property", attrs_dict.get("name", "")).lower().strip()
            if key and "content" in attrs_dict:
                self.values.setdefault(key, attrs_dict["content"])
        elif tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value

class Parser(BaseComponentParser):
    DEFAULT_CACHE_TTL = 7 * 86400  # 7 days in seconds
    _memory_cache = {}

    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-link"]

    def get_cache_ttl(self) -> float:
        """Get cache TTL in seconds from MONO_CACHE_TTL environment variable or default"""
        env_val = os.environ.get("MONO_CACHE_TTL")
        if env_val:
            try:
                return float(env_val)
            except ValueError:
                pass
        return float(self.DEFAULT_CACHE_TTL)

    def safe_encode_url(self, url: str) -> str:
        """Encode URL properly handling non-ASCII characters without double encoding"""
        try:
            url.encode('ascii')
            return url
        except UnicodeEncodeError:
            from urllib.parse import urlsplit, urlunsplit, quote, unquote
            scheme, netloc, path, query, fragment = urlsplit(url)
            path = quote(unquote(path))
            query = quote(unquote(query), safe='=&')
            fragment = quote(unquote(fragment))
            return urlunsplit((scheme, netloc, path, query, fragment))

    def _get_cache_dir(self) -> Path:
        cache_dir = Path.cwd() / ".mono-cache"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return cache_dir

    def download_resource(self, url: str, limit: int, timeout: int = 8) -> tuple[bytes, str, str, str]:
        parts = urllib.parse.urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname or any(ord(c) < 33 for c in url):
            raise ValueError(f"不正なURL形式です: {url}")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MonoDoc/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            final_url = response.url
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("プレビュー取得サイズが上限を超過しました")
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
            return data, content_type, charset, final_url

    def fetch_og_data(self, url: str) -> dict:
        """Fetch OpenGraph metadata and image from URL with caching and size limits"""
        data = {
            "title": "",
            "desc": "",
            "image": ""
        }

        if not url.startswith("http://") and not url.startswith("https://"):
            return data

        ttl = self.get_cache_ttl()
        now = time.time()

        # インメモリキャッシュのTTL検証
        if url in self._memory_cache:
            mem_data = self._memory_cache[url]
            mem_cached_at = mem_data.get("cached_at")
            if mem_cached_at is not None and (now - float(mem_cached_at) < ttl):
                return mem_data

        cache_dir = self._get_cache_dir()
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        cache_file = cache_dir / f"{url_hash}.json"

        cached_data = None
        is_cache_valid = False

        if cache_file.is_file():
            try:
                cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                cached_at = cached_data.get("cached_at")
                if cached_at is None:
                    cached_at = cache_file.stat().st_mtime
                if now - float(cached_at) < ttl:
                    is_cache_valid = True
            except (OSError, ValueError):
                cached_data = None

        if is_cache_valid and cached_data:
            self._memory_cache[url] = cached_data
            return cached_data

        try:
            safe_url = self.safe_encode_url(url)
            raw_html, content_type, charset, final_url = self.download_resource(safe_url, limit=2_000_000)
            if content_type not in ("text/html", "application/xhtml+xml"):
                return cached_data or data

            html_text = raw_html.decode(charset, errors="replace")
            meta_parser = MetadataParser()
            meta_parser.feed(html_text)

            title = meta_parser.values.get("og:title") or meta_parser.title.strip()
            desc = meta_parser.values.get("og:description") or meta_parser.values.get("description", "")
            data["title"] = title.strip()
            data["desc"] = desc.replace("\n", " ").strip()

            img_url = meta_parser.values.get("og:image")
            if img_url:
                absolute_img_url = urllib.parse.urljoin(final_url, img_url.strip())
                try:
                    img_data, img_mime, _, _ = self.download_resource(absolute_img_url, limit=8_000_000)
                    if img_mime in ("image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml"):
                        b64 = base64.b64encode(img_data).decode("utf-8")
                        data["image"] = f"data:{img_mime};base64,{b64}"
                except Exception as img_err:
                    logger.debug(f"OGP画像の取得をスキップしました ({absolute_img_url}): {img_err}")

            data["cached_at"] = now
            if cache_dir.exists():
                try:
                    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                except OSError:
                    pass

        except Exception as e:
            logger.warning(f"Failed to fetch OpenGraph data for {url}: {e}")
            if cached_data:
                self._memory_cache[url] = cached_data
                return cached_data

        self._memory_cache[url] = data
        return data

    def process(self, markdown_content: str) -> str:
        if "::link" not in markdown_content:
            return markdown_content

        lines = markdown_content.split("\n")
        output = []
        i = 0
        n = len(lines)

        link_re = re.compile(r'^[ \t]*::link\s+([^\s]+)(?:\s+(square|full|small|card))?[ \t]*$', re.IGNORECASE)
        prop_re = re.compile(r'^[ \t]*::link-([a-z]+)\s+(.+?)[ \t]*$', re.IGNORECASE)

        while i < n:
            line = lines[i]
            m = link_re.match(line)
            if not m:
                output.append(line)
                i += 1
                continue

            url = m.group(1).strip('\'"')
            style = m.group(2) or "full"
            overrides = {}
            i += 1

            while i < n:
                next_line = lines[i]
                pm = prop_re.match(next_line)
                if pm:
                    prop_name = pm.group(1).lower()
                    prop_val = pm.group(2).strip()
                    overrides[prop_name] = prop_val
                    i += 1
                else:
                    break

            og_data = self.fetch_og_data(url)

            title = overrides.get("title") or og_data.get("title") or url
            desc = overrides.get("description") or overrides.get("desc") or og_data.get("desc") or ""
            img = overrides.get("image") or og_data.get("image") or ""

            safe_url = self.escape_html(url)
            safe_title = self.escape_html(title)
            safe_desc = self.escape_html(desc)
            safe_img = self.escape_html(img)
            safe_style = self.escape_html(style)

            output.append(
                f'<mono-link url="{safe_url}" title="{safe_title}" desc="{safe_desc}" '
                f'image="{safe_img}" card-style="{safe_style}"></mono-link>'
            )

        return "\n".join(output)
