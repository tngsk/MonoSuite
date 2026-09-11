"""Build a dependency-free browser integration test; open output HTML in a browser."""
import json
from pathlib import Path
base = Path(__file__).resolve().parent.parent
payload = json.dumps((base/'presentation.html').read_text(encoding='utf-8')).replace('<', '\\u003c')
script = (base/'tests/browser.js').read_text(encoding='utf-8')
page = '<!doctype html><meta charset="utf-8"><title>Mono Space browser regression</title><style>iframe{width:1200px;height:800px;border:1px solid #ccc}pre{white-space:pre-wrap}</style><pre id="result">Running…</pre><iframe title="test presentation"></iframe><script>const source='+payload+';'+script+'</script>'
(base/'tests/browser.html').write_text(page,encoding='utf-8')
print(base/'tests/browser.html')
