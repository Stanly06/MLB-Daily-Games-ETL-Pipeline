"""Build the static web platform: inject the Gold export into the template.

    python web/build.py path/to/mlb_web_data.json   ->   web/dist/index.html

The page is one self-contained file (data embedded), so it can be hosted on GitHub Pages or
published as-is. Chart.js and Google Fonts load from public CDNs.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
data_path = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "data" / "mlb_web_data.json")
data = json.loads(data_path.read_text(encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
html = (HERE / "template.html").read_text(encoding="utf-8").replace("__MLB_DATA__", payload)
out = HERE / "dist" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
print(f"{out} ({out.stat().st_size / 1e6:.1f} MB) · data through {data['meta']['last_game_date']}")
