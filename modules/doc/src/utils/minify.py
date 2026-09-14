import re

def minify_css(css: str) -> str:
    """CSSを簡易的に圧縮する"""
    if not css:
        return ""
    # コメント削除
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    # 構造文字の周りの空白を削除
    css = re.sub(r'\s*([\{\}\:\;\,\>])\s*', r'\1', css)
    # 改行とタブを削除
    css = re.sub(r'[\n\r\t]', '', css)
    # 連続する空白を1つに
    css = re.sub(r'\s+', ' ', css)
    return css.strip()

def minify_html(html: str) -> str:
    """HTMLを簡易的に圧縮する"""
    if not html:
        return ""
    # <!-- --> 形式のコメントを削除
    html = re.sub(r'<!--(.*?)-->', '', html, flags=re.DOTALL)
    # タグ間の空白を削除
    html = re.sub(r'>\s+<', '><', html)
    # 行頭・行末の空白を削除し、改行を取り除く
    html = re.sub(r'^\s+|\s+$', '', html, flags=re.MULTILINE)
    html = html.replace('\n', '')
    return html.strip()

def minify_js(js: str) -> str:
    """JSを簡易的に圧縮する"""
    if not js:
        return ""
    # 複数行コメント削除 (安全な範囲で)
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
    lines = []
    for line in js.splitlines():
        line = line.strip()
        if not line:
            continue
        # 行全体がコメントの場合はスキップ
        if line.startswith('//'):
            continue
        lines.append(line)
    return '\n'.join(lines)
