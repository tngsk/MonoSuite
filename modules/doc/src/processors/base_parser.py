import html
import logging

logger = logging.getLogger("markdown_converter")


class BaseComponentParser:
    """コンポーネント用Markdownパーサーの基底クラス"""

    def __init__(self):
        self.counter = 0

    @property
    def block_level_tags(self) -> list[str]:
        """
        このパーサーが生成するブロックレベル要素のタグ名リストを返す。
        Markdown変換時に <p> タグで囲まれるのを防ぐために使用される。
        サブクラスで必要に応じてオーバーライドする。
        """
        return []

    def get_next_id(self, prefix: str) -> str:
        """ユニークなIDを生成して返す"""
        self.counter += 1
        return f"{prefix}-{self.counter}"

    @staticmethod
    def escape_html(text: str) -> str:
        """HTML特殊文字をエスケープする"""
        if text is None:
            return ""
        return html.escape(text.strip())

    @staticmethod
    def parse_attr_list(attr_str: str) -> dict[str, str]:
        """
        Parse Markdown standard attr_list string inside `{...}` or `{: ...}`.
        Supports:
        - Classes: `.class-name`
        - ID: `#element-id`
        - Key-value pairs: `key="value"`, `key='value'`, `key=value`, `key: "value"`
        Returns dict of attributes, e.g. {'class': 'gap-md center', 'id': 'main'}
        """
        if not attr_str:
            return {}

        content = attr_str.strip()
        if content.startswith('{') and content.endswith('}'):
            content = content[1:-1].strip()
        if content.startswith(':'):
            content = content[1:].strip()

        if not content:
            return {}

        classes = []
        elem_id = None
        attrs = {}

        has_quote = '"' in content or "'" in content
        tokens = []
        if not has_quote:
            tokens = [t for t in content.split() if t]
        else:
            import shlex
            try:
                tokens = shlex.split(content)
            except ValueError:
                tokens = [t for t in content.split() if t]

        for token in tokens:
            if token.startswith('.'):
                cls = token[1:].strip()
                if cls:
                    classes.append(cls)
            elif token.startswith('#'):
                elem_id = token[1:].strip()
            elif '=' in token:
                k, v = token.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                attrs[k] = v
            elif ':' in token:
                k, v = token.split(':', 1)
                k = k.strip()
                v = v.strip().strip('"\'')
                attrs[k] = v

        if classes:
            attrs['class'] = ' '.join(classes)
        if elem_id:
            attrs['id'] = elem_id

        return attrs

    @classmethod
    def merge_trailing_attrs(cls, args: dict, attr_str: str) -> dict:
        """
        後置属性文字列（例: {.class #id}）をパースし、既存の args とマージする。
        - クラスは重複除去して結合
        - IDは後置属性を優先
        - その他の属性も後置属性を優先
        """
        if not attr_str:
            return args

        trailing_attrs = cls.parse_attr_list(attr_str)
        if not trailing_attrs:
            return args

        merged = dict(args)
        # クラスのマージ
        orig_class = merged.get('class', '').strip()
        new_class = trailing_attrs.get('class', '').strip()
        if orig_class and new_class:
            orig_tokens = orig_class.split()
            new_tokens = new_class.split()
            combined_tokens = list(dict.fromkeys(orig_tokens + new_tokens))
            merged['class'] = ' '.join(combined_tokens)
        elif new_class:
            merged['class'] = new_class

        # IDのマージ（後置属性を優先）
        if 'id' in trailing_attrs:
            merged['id'] = trailing_attrs['id']

        # その他の属性
        for k, v in trailing_attrs.items():
            if k not in ('class', 'id'):
                merged[k] = v

        return merged

    @staticmethod
    def parse_bracket_content(content: str) -> tuple[str, dict]:
        """
        Parse the content inside `[]` which can be:
        - Label only: `"My Label"` or `My Label`
        - Label and args: `"My Label", id: "123"`
        - Args only: `id: "123"`
        Returns (label_str, args_dict)
        """
        if not content:
            return "", {}

        content = content.strip()

        has_paren = '(' in content
        has_quote = '"' in content or "'" in content

        parts = []

        # Fast path for simple cases without nested parens or quotes
        if not has_paren and not has_quote:
            parts = [p.strip() for p in content.split(',') if p.strip()]
        else:
            paren_depth = 0
            in_quote = None
            start_idx = 0

            if not has_paren:
                raw_parts = content.split(',')
                current_part = ""
                in_quote = None

                for p in raw_parts:
                    if current_part:
                        current_part += "," + p
                    else:
                        current_part = p

                    if not in_quote and "'" not in p:
                        if p.count('"') % 2 == 0:
                            parts.append(current_part.strip())
                            current_part = ""
                            continue
                    elif not in_quote and '"' not in p:
                        if p.count("'") % 2 == 0:
                            parts.append(current_part.strip())
                            current_part = ""
                            continue

                    search_start = 0
                    while True:
                        if in_quote:
                            idx = p.find(in_quote, search_start)
                            if idx == -1:
                                break
                            in_quote = None
                            search_start = idx + 1
                        else:
                            idx_q1 = p.find('"', search_start)
                            idx_q2 = p.find("'", search_start)

                            if idx_q1 == -1 and idx_q2 == -1:
                                break
                            elif idx_q1 != -1 and idx_q2 != -1:
                                m = idx_q1 if idx_q1 < idx_q2 else idx_q2
                            else:
                                m = idx_q1 if idx_q1 != -1 else idx_q2

                            in_quote = p[m]
                            search_start = m + 1

                    if not in_quote:
                        parts.append(current_part.strip())
                        current_part = ""

                start_idx = len(content)
                if current_part:
                    parts.append(current_part.strip())
            else:
                for i, char in enumerate(content):
                    if in_quote:
                        if char == in_quote:
                            in_quote = None
                    elif char in "\"'":
                        in_quote = char
                    elif char == '(':
                        paren_depth += 1
                    elif char == ')':
                        paren_depth -= 1
                    elif char == ',' and paren_depth == 0 and not in_quote:
                        parts.append(content[start_idx:i].strip())
                        start_idx = i + 1

            if start_idx < len(content):
                parts.append(content[start_idx:].strip())

        label = ""
        args_dict = {}

        if parts:
            first_part = parts[0]
            has_kv_separator = False

            if ':' in first_part:
                in_q = None
                for i, char in enumerate(first_part):
                    if in_q:
                        if char == in_q:
                            in_q = None
                    elif char in "\"'":
                        in_q = char
                    elif char == ':':
                        if i + 2 < len(first_part) and first_part[i+1:i+3] == '//':
                            continue
                        has_kv_separator = True
                        break

            if not has_kv_separator:
                label = first_part
                if len(label) >= 2 and label[0] == label[-1] and label[0] in "\"'":
                    label = label[1:-1]
                parts = parts[1:]

        for part in parts:
            if not part or ':' not in part:
                continue

            search_start = 0
            split_idx = -1
            while True:
                idx_colon = part.find(':', search_start)
                if idx_colon == -1:
                    break
                if idx_colon + 2 < len(part) and part[idx_colon+1:idx_colon+3] == '//':
                    search_start = idx_colon + 1
                    continue
                split_idx = idx_colon
                break

            if split_idx == -1:
                continue

            k = part[:split_idx].strip()
            v = part[split_idx+1:].strip()
            if len(v) >= 2 and v[0] == v[-1] and (v[0] == '"' or v[0] == "'"):
                v = v[1:-1]
            args_dict[k] = v

        return label, args_dict

    @staticmethod
    def parse_key_value_args(args_str: str) -> dict:
        if not args_str:
            return {}

        args_str_stripped = args_str.strip()
        if args_str_stripped.startswith('{') and args_str_stripped.endswith('}'):
            return BaseComponentParser.parse_attr_list(args_str_stripped)

        if ':' not in args_str:
            if '.' in args_str or '#' in args_str:
                return BaseComponentParser.parse_attr_list(args_str)
            return {}

        result = {}

        has_paren = '(' in args_str
        has_quote = '"' in args_str or "'" in args_str

        # Fast path for simple cases without nested parens or quotes
        if not has_paren and not has_quote:
            for part in args_str.split(','):
                part = part.strip()
                if not part or ':' not in part:
                    continue

                search_start = 0
                split_idx = -1
                while True:
                    idx_colon = part.find(':', search_start)
                    if idx_colon == -1:
                        break
                    if idx_colon + 2 < len(part) and part[idx_colon+1:idx_colon+3] == '//':
                        search_start = idx_colon + 1
                        continue
                    split_idx = idx_colon
                    break

                if split_idx != -1:
                    result[part[:split_idx].strip()] = part[split_idx+1:].strip()
            return result

        parts = []
        paren_depth = 0
        in_quote = None
        start_idx = 0

        if not has_paren:
            raw_parts = args_str.split(',')
            current_part = ""
            in_quote = None

            for p in raw_parts:
                if current_part:
                    current_part += "," + p
                else:
                    current_part = p

                if not in_quote and "'" not in p:
                    if p.count('"') % 2 == 0:
                        parts.append(current_part.strip())
                        current_part = ""
                        continue
                elif not in_quote and '"' not in p:
                    if p.count("'") % 2 == 0:
                        parts.append(current_part.strip())
                        current_part = ""
                        continue

                search_start = 0
                while True:
                    if in_quote:
                        idx = p.find(in_quote, search_start)
                        if idx == -1:
                            break
                        in_quote = None
                        search_start = idx + 1
                    else:
                        idx_q1 = p.find('"', search_start)
                        idx_q2 = p.find("'", search_start)

                        if idx_q1 == -1 and idx_q2 == -1:
                            break
                        elif idx_q1 != -1 and idx_q2 != -1:
                            m = idx_q1 if idx_q1 < idx_q2 else idx_q2
                        else:
                            m = idx_q1 if idx_q1 != -1 else idx_q2

                        in_quote = p[m]
                        search_start = m + 1

                if not in_quote:
                    parts.append(current_part.strip())
                    current_part = ""

            start_idx = len(args_str)
            if current_part:
                parts.append(current_part.strip())
        else:
            for i, char in enumerate(args_str):
                if in_quote:
                    if char == in_quote:
                        in_quote = None
                elif char in "\"'":
                    in_quote = char
                elif char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                elif char == ',' and paren_depth == 0 and not in_quote:
                    parts.append(args_str[start_idx:i].strip())
                    start_idx = i + 1

        if start_idx < len(args_str):
            parts.append(args_str[start_idx:].strip())

        for part in parts:
            if not part or ':' not in part:
                continue

            search_start = 0
            split_idx = -1
            while True:
                idx_colon = part.find(':', search_start)
                if idx_colon == -1:
                    break
                if idx_colon + 2 < len(part) and part[idx_colon+1:idx_colon+3] == '//':
                    search_start = idx_colon + 1
                    continue
                split_idx = idx_colon
                break

            if split_idx == -1:
                continue

            k = part[:split_idx].strip()
            v = part[split_idx+1:].strip()
            if len(v) >= 2 and v[0] == v[-1] and (v[0] == '"' or v[0] == "'"):
                v = v[1:-1]
            result[k] = v
        return result

    def get_common_attributes(self, args: dict) -> str:
        """
        全コンポーネント共通の属性（例: padding）を抽出し、HTML属性文字列として返す。
        """
        attrs = []
        if 'class' in args:
            attrs.append(f'class="{self.escape_html(args["class"])}"')
        if 'id' in args:
            attrs.append(f'id="{self.escape_html(args["id"])}"')
        if 'padding' in args:
            attrs.append(f'padding="{self.escape_html(args["padding"])}"')
        if 'padding-x' in args:
            attrs.append(f'padding-x="{self.escape_html(args["padding-x"])}"')
        if 'padding-y' in args:
            attrs.append(f'padding-y="{self.escape_html(args["padding-y"])}"')

        return " " + " ".join(attrs) if attrs else ""


    def resolve_url_and_label(self, label: str, args: dict, url_keys: list[str], label_key: str) -> tuple[str, str]:
        """
        Resolves the primary URL and label/alt text for components.
        If any of the `url_keys` are present in `args`, we use that as the URL and `label` as the label text.
        If no `url_keys` are present, we assume `label` (bracket content) is the URL, and look for `label_key` in `args`.

        Returns:
            tuple: (url, text)
        """
        url = ""
        text = ""

        # Check if url is explicitly passed in args
        for key in url_keys:
            if key in args:
                url = args[key]
                break

        if url:
            # URL is in args, so bracket content is the text
            text = args.get(label_key, label)
        else:
            # URL is not in args, so bracket content is the URL
            url = label
            text = args.get(label_key, "")

        return url, text

    def process(self, markdown_content: str) -> str:
        """
        Markdownテキストを受け取り、コンポーネント固有の前処理（置換）を行った結果を返す。
        サブクラスで必ずオーバーライドすること。
        """
        raise NotImplementedError("Subclasses must implement process()")
