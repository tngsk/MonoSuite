"""Mono Space section and block parsing. No rendering or asset fetching."""
import re
from .markdown_syntax import fence_open, fence_close, image_line
from .links import validate_url


def table_cells(line):
    """Split pipe rows; escaped pipes stay inside their cell."""
    value = line.strip()
    cells, current = [], []
    i = 0
    while i < len(value):
        if value[i:i+2] == r'\|':
            current.append('|')
            i += 2
            continue
        if value[i] == '|':
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(value[i])
        i += 1
    cells.append(''.join(current).strip())
    if value.startswith('|'):
        cells.pop(0)
    if value.endswith('|') and not value.endswith(r'\|'):
        cells.pop()
    return cells


def parse_blocks(lines):
    """Turn collected section input into typed blocks, without file or network IO."""
    blocks, i = [], 0
    while i < len(lines):
        line = lines[i]
        if isinstance(line, dict):
            if line['kind'] == 'code':
                blocks.append(dict(kind='code', language=line['language'], text=''.join(line['lines'])))
            else:
                blocks.append(dict(line))
            i += 1
            continue
        if not line:
            i += 1
            continue
        if image_line(line):
            images = []
            while i < len(lines) and isinstance(lines[i], str):
                if image_line(lines[i]):
                    images.append(image_line(lines[i])); i += 1
                elif not lines[i].strip():
                    i += 1
                else:
                    break
            blocks.append(dict(kind='images', images=images))
            continue
        quote = re.match(r'^ *> ?(.*)$', line)
        item = re.match(r'^( *)([-+*]|[0-9]+[.)]) +(.+)$', line)
        local_heading = re.match(r'^#{1,6} +(.+)$', line)
        if quote:
            content = []
            while i < len(lines) and isinstance(lines[i], str):
                q = re.match(r'^ *> ?(.*)$', lines[i])
                if q:
                    content.append(q[1]); i += 1
                elif not lines[i].strip():
                    content.append(''); i += 1
                else:
                    break
            blocks.append(dict(kind='quote', blocks=parse_blocks(content)))
            continue
        if item:
            ordered = item[2][0].isdigit()
            indent = len(item[1])
            items = []
            start = int(re.match(r'[0-9]+', item[2])[0]) if ordered else 1
            while i < len(lines) and isinstance(lines[i], str):
                m = re.match(r'^( *)([-+*]|[0-9]+[.)]) +(.+)$', lines[i])
                if not m or len(m[1]) != indent or m[2][0].isdigit() != ordered:
                    break
                content = [m[3]]; i += 1
                while i < len(lines) and isinstance(lines[i], str):
                    current = lines[i]
                    if not current.strip():
                        content.append(''); i += 1; continue
                    depth = len(current)-len(current.lstrip(' '))
                    if depth <= indent: break
                    content.append(current[min(depth, indent+4):]); i += 1
                items.append(parse_blocks(content))
            blocks.append(dict(kind='list', ordered=ordered, start=start, items=items))
            continue
        if local_heading:
            blocks.append(dict(kind='local_heading', text=local_heading[1])); i += 1
            continue
        header = table_cells(line)
        separators = table_cells(lines[i+1]) if i+1 < len(lines) and isinstance(lines[i+1], str) else []
        if separators and len(header) == len(separators) and all(re.fullmatch(r':?-{3,}:?', cell) for cell in separators):
            align = ['center' if cell.startswith(':') and cell.endswith(':') else 'right' if cell.endswith(':') else 'left' for cell in separators]
            rows = []
            i += 2
            while i < len(lines) and isinstance(lines[i], str) and lines[i].strip() and '|' in lines[i]:
                rows.append((table_cells(lines[i]) + [''] * len(header))[:len(header)])
                i += 1
            blocks.append(dict(kind='table', header=header, align=align, rows=rows))
        else:
            if blocks and blocks[-1]['kind'] == 'paragraph' and i > 0 and isinstance(lines[i-1], str) and lines[i-1].strip():
                blocks[-1]['text'] += '\n' + line.strip()
            else:
                blocks.append(dict(kind='paragraph', text=line))
            i += 1
    return blocks


def normalize_headings(nodes, layouts, directives):
    """Resolve spatial roles before validating references and rendering blocks."""
    kept, owners = [], {}
    for node in nodes:
        parent = node['parent']
        if node['level'] >= 4 and parent not in layouts and parent is not None:
            if directives.get(node['id']):
                number, name = directives[node['id']][0]
                raise ValueError(f'{number}行: 本文内見出しに ::{name} は指定できません。話題見出しに移してください')
            owner = owners[parent]
            owner['body'].extend(['', '#' * node['level'] + ' ' + node['title'], '', *node['body']])
            owners[node['id']] = owner
        else:
            if parent: node['parent'] = owners[parent]['id']
            kept.append(node)
            owners[node['id']] = node
    return kept


def _format_comment_preview(comment: str, max_length: int = 80) -> str:
    """HTMLコメントを標準出力向けに1行に正規化し、長すぎる場合は省略する"""
    normalized = " ".join(comment.strip().split())
    if len(normalized) > max_length:
        return f"{normalized[:max_length]}..."
    return normalized


def strip_html_comments(source: str) -> str:
    blocks = {}
    counter = 0

    def replace_block(match: re.Match) -> str:
        nonlocal counter
        placeholder = f"@@SPACE_CODE_BLOCK_{counter}@@"
        blocks[placeholder] = match.group(0)
        counter += 1
        return placeholder

    fenced_pattern = re.compile(
        r"(?s)(^[ \t]*(?P<f>`{3,}|~{3,})[^\n]*.*?\n[ \t]*(?P=f)[ \t]*(?=\n|$))",
        re.MULTILINE,
    )
    processed = fenced_pattern.sub(replace_block, source)

    # CommonMark仕様に準拠し、空行を跨ぐマッチはインラインコードとみなさない
    inline_pattern = re.compile(
        r"(?s)(?<!`)(?P<ticks>`+)(?!`)(?:(?!\n[ \t]*\n).)*?(?<!`)(?P=ticks)(?!`)"
    )
    processed = inline_pattern.sub(replace_block, processed)

    def comment_replacer(match: re.Match) -> str:
        preview = _format_comment_preview(match.group(0))
        print(f"HTMLコメント無視: {preview}")
        return "\n" * match.group(0).count("\n")

    processed = re.sub(r"<!--.*?-->", comment_replacer, processed, flags=re.DOTALL)

    if blocks:
        pattern = re.compile(r"@@SPACE_CODE_BLOCK_\d+@@")
        processed = pattern.sub(lambda m: blocks.get(m.group(0), m.group(0)), processed)

    return processed


def parse_document(source):
    source = strip_html_comments(source)
    nodes, stack, edges, route = [], [], [], []
    layouts = set()
    directives = {}
    last_link = None
    fence = None
    math_block = None
    block = None
    for number, raw in enumerate(source.splitlines(keepends=True), 1):
        line = raw.rstrip('\r\n')
        if fence:
            if fence_close(line, fence):
                fence = None
            else:
                block['lines'].append(raw.replace('\r\n', '\n'))
            continue
        if math_block is not None:
            if line.strip() == '$$':
                math_block = None
            else:
                math_block['text'] += raw.replace('\r\n', '\n')
            continue
        if line.strip().startswith('$$'):
            if not stack:
                raise ValueError(f'{number}行: 数式の前に見出しを記述してください')
            single = re.fullmatch(r'\$\$(.*?)\$\$', line.strip())
            if single:
                stack[-1]['body'].append(dict(kind='math', text=single[1].strip(), line=number))
            elif line.strip() == '$$':
                math_block = dict(kind='math', text='', line=number)
                stack[-1]['body'].append(math_block)
            else:
                raise ValueError(f'{number}行: $$は独立した行、または $$式$$ と記述してください')
            last_link = None
            continue
        opening = fence_open(line)
        if opening:
            if not stack:
                raise ValueError(f'{number}行: コードの前に見出しを記述してください')
            fence = opening[1]
            block = dict(kind='code', language=opening[2].strip(), lines=[])
            stack[-1]['body'].append(block)
            last_link = None
            continue
        if not line.strip():
            if stack:
                stack[-1]['body'].append('')
            continue
        heading = re.fullmatch(r'(#{1,6})\s+(.+?)(?:\s+\{#([\w-]+)\})?', line)
        if heading:
            last_link = None
            level, title, key = len(heading[1]), heading[2], heading[3] or f'n{len(nodes)+1}'
            if any(n['id'] == key for n in nodes):
                raise ValueError(f'{number}行: ID重複 {key}')
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            node = dict(id=key, title=title, level=level, parent=stack[-1]['id'] if stack else None,
                        layout='row' if not stack else 'stack', tone='neutral', style='plain', focus='content', marker='auto', body=[])
            nodes.append(node)
            stack.append(node)
        elif line.startswith('::image-position '):
            position = line.split()[-1]
            body = stack[-1]['body'] if stack else []
            if position not in ('left', 'right') or not body or not isinstance(body[-1], str) or not image_line(body[-1]):
                raise ValueError(f'{number}行: 画像の直後にleft/rightを指定してください')
            body[-1] = dict(kind='images', images=[image_line(body[-1])], position=position)
        elif line.startswith('::link '):
            m = re.fullmatch(r'::link (\S+)(?: (square))?', line)
            if not m or not stack:
                raise ValueError(f'{number}行: リンク指定が不正です')
            last_link = dict(kind='link', url=validate_url(m[1]), shape=m[2] or 'wide')
            stack[-1]['body'].append(last_link)
        elif line.startswith('::link-'):
            m = re.fullmatch(r'::link-(title|description|image) (.+)', line)
            if not m or last_link is None:
                raise ValueError(f'{number}行: ::link の直後に指定してください')
            last_link[m[1]] = m[2]
        elif line.startswith('::connect '):
            m = re.fullmatch(r'::connect ([\w-]+) -> ([\w-]+)(?: \|(.*))?', line)
            if not m:
                raise ValueError(f'{number}行: 接続の構文が不正です')
            edges.append(dict(source=m[1], target=m[2], label=(m[3] or '').strip()))
        elif line.startswith('::route '):
            route = line[8:].split()
        elif line.startswith('::'):
            m = re.fullmatch(r'::(layout|tone|focus|marker|style) (\w+)', line)
            if not m or not stack:
                raise ValueError(f'{number}行: 不明なディレクティブ')
            allowed = dict(layout=('row', 'stack', 'compare', 'flow', 'slide'), tone=('neutral', 'primary', 'secondary', 'accent', 'info', 'success', 'warning', 'error', 'normal', 'ai', 'note'), style=('plain', 'note'), focus=('content', 'subtree', 'image'), marker=('on', 'off'))
            if m[2] not in allowed[m[1]]:
                raise ValueError(f'{number}行: 未対応の値 {m[2]}')
            directives.setdefault(stack[-1]['id'], []).append((number, m[1]))
            stack[-1][m[1]] = m[2]
            if m[1] == 'layout': layouts.add(stack[-1]['id'])
        elif stack:
            last_link = None
            stack[-1]['body'].append(line)
        else:
            raise ValueError(f'{number}行: 最初に見出しを記述してください')
    if math_block is not None:
        raise ValueError(f'{math_block["line"]}行: 数式の閉じ $$ がありません: {math_block["text"]!r}')
    if not nodes:
        raise ValueError('見出しが必要です')
    nodes = normalize_headings(nodes, layouts, directives)
    ids = {n['id'] for n in nodes}
    for key in route + [e[k] for e in edges for k in ('source', 'target')]:
        if key not in ids:
            raise ValueError(f'参照先がありません: {key}')
    for n in nodes:
        if n['tone'] == 'note':
            n['style'] = 'note'
            n['tone'] = 'warning'
        else:
            n['tone'] = {'normal': 'neutral', 'ai': 'primary'}.get(n['tone'], n['tone'])
        if n['layout'] == 'compare' and sum(c['parent'] == n['id'] for c in nodes) not in (2, 3):
            raise ValueError('compare は直下の子見出し2個または3個が必要です')
        n['blocks'] = parse_blocks(n.pop('body'))
    default_route = [n['id'] for n in nodes if n['level'] != 2 or n['blocks'] or not any(c['parent'] == n['id'] for c in nodes)]
    return dict(nodes=nodes, edges=edges, route=route or default_route)


