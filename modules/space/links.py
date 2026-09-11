"""Build-time link previews; stdlib only, cached and embedded for offline viewing."""
import base64
import hashlib
import html
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from urllib.request import Request, urlopen


def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password or any(ord(c) < 33 for c in url):
        raise ValueError('リンクは http:// または https:// のURLを指定してください')
    return url


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property', attrs.get('name', '')).lower()
            self.values.setdefault(key, attrs.get('content', ''))
        if tag == 'title':
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value


def download(url, limit):
    validate_url(url)
    with urlopen(Request(url, headers={'User-Agent': 'MonoSpacePreview/1.0'}), timeout=8) as response:
        validate_url(response.url)
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('プレビューの取得サイズが上限を超えました')
        return data, response.headers.get_content_type(), response.headers.get_content_charset() or 'utf-8', response.url


class Previews:
    def __init__(self, cache, refresh=False, offline=False):
        self.cache, self.refresh, self.offline = Path(cache), refresh, offline
        self.memo = {}

    def get(self, url):
        if url in self.memo:
            return self.memo[url]
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache / (key + '.json')
        cached = {}
        try:
            cached = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
        if self.offline or (cached and not self.refresh):
            self.memo[url] = cached
            return cached
        try:
            raw, mime, charset, final = download(url, 2_000_000)
            if mime not in ('text/html', 'application/xhtml+xml'):
                raise ValueError('HTMLではありません')
            parser = Metadata()
            parser.feed(raw.decode(charset, errors='replace'))
            result = {'title': parser.values.get('og:title') or parser.title.strip(),
                      'description': parser.values.get('og:description') or parser.values.get('description', '')}
            image = parser.values.get('og:image')
            if image:
                try:
                    raw, mime, _, _ = download(urljoin(final, image), 8_000_000)
                    if mime in ('image/png', 'image/jpeg', 'image/webp', 'image/gif'):
                        result['image'] = f'data:{mime};base64,' + base64.b64encode(raw).decode()
                except Exception:
                    pass
            self.cache.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        except Exception:
            result = cached
        self.memo[url] = result
        return result


def render_link(link, root, assets, previews):
    url = validate_url(link['url'])
    meta = previews.get(url) if previews else {}
    title = link.get('title', meta.get('title') or url)
    description = link.get('description', meta.get('description', ''))
    image = meta.get('image', '')
    if 'image' in link:
        import mimetypes
        try:
            path = root / link['image']
            mime = mimetypes.guess_type(path.name)[0]
            if mime not in ('image/png', 'image/jpeg', 'image/webp', 'image/gif'):
                raise ValueError('画像形式が未対応です')
            image = f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()
        except (OSError, ValueError):
            image = ''
    picture = ''
    if image.startswith(('data:image/png;base64,', 'data:image/jpeg;base64,', 'data:image/webp;base64,', 'data:image/gif;base64,')):
        key = hashlib.sha256(base64.b64decode(image.split(',', 1)[1])).hexdigest()
        assets.setdefault(key, image)
        picture = f'<img alt="" data-asset="{key}">'
    esc = html.escape
    return (f'<a class="rich-link {link["shape"]}" href="{esc(url, quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{picture}<span class="link-copy"><span class="link-title">{esc(title)}</span>'
            f'<span class="link-description">{esc(description)}</span>'
            f'<span class="link-domain">{esc(urlsplit(url).netloc)}</span></span></a>')
