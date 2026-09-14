"""Build a dependency-free browser integration test; open output HTML in a browser."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
base = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='mono-space-browser-') as directory:
    output = Path(directory) / 'presentation.html'
    subprocess.run([sys.executable, str(base/'build.py'),
                    str(base/'tests/fixtures/browser.md'), '-o', str(output),
                    '--offline'], check=True)
    payload = json.dumps(output.read_text(encoding='utf-8')).replace('<', '\\u003c')
script = (base/'tests/browser.js').read_text(encoding='utf-8')
page = '<!doctype html><meta charset="utf-8"><title>Mono Space browser regression</title><style>iframe{width:1200px;height:800px;border:1px solid #ccc}pre{white-space:pre-wrap}</style><pre id="result">Running…</pre><iframe title="test presentation"></iframe><script>const source='+payload+';'+script+'</script>'
output = base/'dist/tests/browser.html'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(page, encoding='utf-8')
print(output)
