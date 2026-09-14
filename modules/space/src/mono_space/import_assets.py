"""Local asset packaging shared by document importers."""
import hashlib
from pathlib import Path
from urllib.parse import unquote, urlsplit


class ImportAssets:
    def __init__(self, root, output):
        self.root = Path(root).resolve()
        self.output = Path(output).resolve()
        self.files = {}

    def image(self, reference):
        url = urlsplit(reference)
        if url.scheme or url.netloc:
            raise ValueError('外部画像は未対応です: ' + reference)
        path = (self.root / unquote(url.path)).resolve()
        if self.root not in path.parents:
            raise ValueError('画像が入力フォルダー外を参照しています: ' + reference)
        if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
            raise ValueError('未対応の画像形式: ' + reference)
        raw = path.read_bytes()
        name = hashlib.sha256(raw).hexdigest() + path.suffix.lower()
        self.files[name] = raw
        return self.output.stem + '.assets/' + name

    def write(self):
        if self.files:
            folder = self.output.parent / (self.output.stem + '.assets')
            folder.mkdir(parents=True, exist_ok=True)
            for name, raw in self.files.items():
                (folder / name).write_bytes(raw)
