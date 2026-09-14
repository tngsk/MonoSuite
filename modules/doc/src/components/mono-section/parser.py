import re
import html
from src.processors.base_parser import BaseComponentParser

class Parser(BaseComponentParser):
    @property
    def block_level_tags(self) -> list[str]:
        return ["mono-section"]

    def process(self, markdown_content: str) -> str:
        if "section" not in markdown_content:
            return markdown_content

        pattern = re.compile(
            r'(?sm)^[ \t]*(?P<fence>:{3,})[ \t]*section(?:\s+(?P<meta>[^\n{(]*))?(?:\((?P<args>[^)\n]*)\))?(?:\s*\{(?P<attrs>[^}\n]*)\})?\n'
            r'(?P<inner>(?:(?!^[ \t]*(?P=fence)[ \t]*section).)*?)\n'
            r'[ \t]*(?P=fence)(?:[ \t]*(?:end|/section)|[ \t]*)?(?=\n|$)'
        )

        def replacer(match: re.Match) -> str:
            meta_str = (match.group('meta') or "").strip()
            args_str = match.group('args') or ""
            attr_str = match.group('attrs') or ""
            inner_content = match.group('inner') or ""

            args = {}
            classes = []
            title = ""

            if meta_str:
                if "[" in meta_str and "]" in meta_str:
                    s = meta_str.find("[")
                    e = meta_str.rfind("]")
                    l, s_args = self.parse_bracket_content(meta_str[s+1:e])
                    if l:
                        title = l
                    args.update(s_args)
                    meta_str = (meta_str[:s] + meta_str[e+1:]).strip()
                for token in meta_str.split():
                    if token.startswith('.'):
                        classes.append(token[1:])
                    else:
                        classes.append(token)

            if args_str:
                args.update(self.parse_key_value_args(args_str))
            if attr_str:
                args.update(self.parse_attr_list(attr_str))

            if classes:
                existing_cls = args.get('class', '')
                all_cls = " ".join([c for c in [existing_cls] + classes if c]).strip()
                if all_cls:
                    args['class'] = all_cls

            if 'title' in args:
                title = args['title']

            attrs = ['markdown="1"']

            for prop in ('image', 'mode', 'bg-color', 'text-color', 'height', 'width'):
                if prop in args:
                    val = str(args[prop]).strip("'\"")
                    attrs.append(f'{prop}="{html.escape(val)}"')

            attrs_str = " ".join(attrs)
            common_attrs = self.get_common_attributes(args)

            result = f'<mono-section {attrs_str}{common_attrs}>\n'
            if title and title.strip():
                safe_title = html.escape(title.strip())
                result += f'<h2>{safe_title}</h2>\n'

            result += inner_content.strip() + "\n</mono-section>"
            return result

        prev_content = None
        max_depth = 20
        depth = 0
        while prev_content != markdown_content and depth < max_depth:
            prev_content = markdown_content
            markdown_content = pattern.sub(replacer, markdown_content)
            depth += 1

        return markdown_content
