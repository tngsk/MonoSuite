"""Craft TextBundle importer. No Mono components or runtime dependencies."""
import json
import re
from markdown_syntax import fence_open, fence_close, image_line
from pathlib import Path
from import_assets import ImportAssets


def import_bundle(bundle, output):
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    if output == bundle or bundle in output.parents:
        raise ValueError('出力先は元TextBundleの外にしてください')
    info = json.loads((bundle/'info.json').read_text(encoding='utf-8'))
    if info.get('type') != 'net.daringfireball.markdown':
        raise ValueError('Markdown形式のTextBundleのみ対応しています')
    source = bundle/'text.markdown'
    if not source.is_file():
        source = bundle/'text.md'
    text = source.read_text(encoding='utf-8')
    lines, notices = [], []
    assets = ImportAssets(bundle, output)
    stack, fence, started = [], None, False
    def note(number, message):
        notices.append(dict(line=number, message=message))
    for number, line in enumerate(text.splitlines(), 1):
        delimiter = fence_open(line)
        if fence:
            lines.append(line)
            if fence_close(line, fence): fence=None
            continue
        if delimiter:
            fence=delimiter[1];lines.append(line);continue
        heading = re.match(r'^(#{1,6})\s+(.+)$',line)
        if heading:
            original=len(heading[1])
            if not started:
                lines.append('# '+heading[2]);started=True
                stack=[(original,1)]
                continue
            while stack and stack[-1][0]>=original:stack.pop()
            level=min(6,(stack[-1][1]+1) if stack else 2)
            stack.append((original,level))
            lines.append('#'*level+' '+heading[2])
            if level!=original:note(number,'見出し階層を単一キャンバス内へ整理')
            continue
        if not started and line.strip():
            lines.append('# '+bundle.stem);started=True
        if re.fullmatch(r'\s*---+\s*',line):
            note(number,'水平線を余白へ変換');lines.append('');continue
        image = re.fullmatch(r'\s*!\[([^\]]*)\]\((.*)\)\s*',line)
        if image:
            path = assets.image(image[2])
            lines.append(f'![{image[1]}]({path})')
            continue
        if '![' in line:raise ValueError(f'{number}行: 試験版では画像は単独行にしてください')
        lines.append(line)
    if not started:raise ValueError('本文がありません')
    output.parent.mkdir(parents=True,exist_ok=True)
    assets.write()
    md=output.with_suffix('.space.md');md.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    output.with_suffix('.conversion.json').write_text(json.dumps(dict(importer='craft',source=str(bundle),images=len(assets.files),changes=notices),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return md
