"""Explicit, lossy Mono import. Never executes component attributes or changes input."""
import re
from .markdown_syntax import fence_open, fence_close, image_line

COMPONENT = re.compile(r'@\[([^\]]+)\](?:\((?:"[^"\n]*"|[^)"\n])*\))?')


def convert_mono(source):
    output, changes = [], []
    fence = None
    level = 1
    flow = None
    pending = []

    def report(line, kind, message):
        changes.append(dict(line=line, kind=kind, message=message))

    def component(match, number):
        name = match[1].split(':', 1)[0]
        if name == 'textfield':
            placeholder = re.search(r'placeholder:\s*"([^"]*)"', match[0])
            report(number, 'loss', '入力欄を表示用テキストに変換。入力・保存機能はありません。')
            return '［'+(placeholder[1] if placeholder else '記入欄')+'］'
        if name == 'badge':
            label = re.search(r'badge:\s*"([^"]*)"', match[1])
            report(number, 'loss', 'バッジをラベル文字列に変換。')
            return label[1] if label else match[0]
        report(number, 'unsupported', '未対応のMono記法を文字列として保持: '+match[0])
        return match[0]

    for number, line in enumerate(source.splitlines(), 1):
        delimiter = fence_open(line)
        if fence:
            output.append(line)
            if fence_close(line, fence):
                fence = None
            continue
        if delimiter:
            fence = delimiter[1]
            output.append(line)
            continue
        if re.fullmatch(r'\s*@\[(?:/)?section\](?:\(.*\))?\s*', line):
            report(number, 'loss', 'sectionの囲み・背景・幅指定を除去し、内容を保持。')
            continue
        if re.match(r'^\s*@\[flow\]', line):
            if level >= 5:
                raise ValueError(f'{number}行: flowを変換する見出し階層が不足しています')
            flow = level + 1
            vertical = bool(re.search(r'orientation:\s*"vertical"', line))
            output.extend(['#'*flow+' 工程', '::layout '+('stack' if vertical else 'flow'), '::focus subtree'])
            report(number, 'change', 'flowを子見出しと'+('縦配置' if vertical else '工程配置')+'へ変換。')
            continue
        if line.strip() == '@[/flow]':
            flow = None
            continue
        if flow is not None:
            for step in line.split('->'):
                if step.strip():
                    output.append('#'*(flow+1)+' '+step.strip())
            continue
        if re.fullmatch(r'\s*(?:---+|\*\*\*+|___+)\s*', line):
            report(number, 'loss', '水平線を除去。')
            continue
        heading = re.match(r'^(#{1,6})\s+', line)
        if heading:
            level = len(heading[1])
        # Inline code is literal; Mono-looking text inside it must remain unchanged.
        chunks = re.split(r'(`+[^`]*`+)', line)
        for i in range(0, len(chunks), 2):
            chunks[i] = COMPONENT.sub(lambda m: component(m, number), chunks[i])
            chunks[i] = re.sub(r'<br\s*/?>', ' — ' if heading else '\n\n', chunks[i], flags=re.I)
        converted = ''.join(chunks)
        if '<br' in line.lower() and converted != line:
            report(number, 'change', 'brを見出しの区切り／本文の段落へ変換。')
        # Decorations before the title become text after the first heading.
        if not output and not heading:
            if converted.strip(): pending.append(converted)
            continue
        output.append(converted)
        if heading:
            output.extend(pending);pending.clear()
    if flow is not None:
        raise ValueError('Mono flowの閉じ記法 @[/flow] がありません')
    if pending:
        raise ValueError('見出しが必要です')
    return '\n'.join(output)+'\n', changes


def import_document(source, output):
    """Convert and save a Mono document without modifying its source."""
    import json
    import os
    from pathlib import Path
    source, output = Path(source), Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    converted, changes = convert_mono(source.read_text(encoding='utf-8'))
    converted_path = output.with_suffix('.space.md')
    report_path = output.with_suffix('.conversion.json')
    if source.resolve() in (converted_path.resolve(), report_path.resolve(), output.resolve()):
        raise ValueError('出力先は元Markdownと異なるパスにしてください')
    # Relocate local image references, preserving code fences and inline code.
    # Resolve original paths during rendering; the saved copy uses relocated paths.
    data_source = source.parent
    fence = None
    saved = []
    for line in converted.splitlines(keepends=True):
        delimiter = fence_open(line)
        if delimiter:
            if fence is None: fence = delimiter[1]
            elif fence_close(line, fence): fence = None
            saved.append(line)
            continue
        if fence:
            saved.append(line)
            continue
        chunks = re.split(r'(`+[^`]*`+)', line)
        for i in range(0,len(chunks),2):
            chunks[i] = re.sub(r'(!\[[^\]]*\]\()([^)]+)(\))', lambda m: m[1]+os.path.relpath((data_source/m[2]).resolve(), converted_path.parent.resolve())+m[3], chunks[i])
        saved.append(''.join(chunks))
    converted_path.write_text(''.join(saved), encoding='utf-8')
    report_path.write_text(json.dumps(dict(source=str(source.resolve()), changes=changes), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return converted_path
