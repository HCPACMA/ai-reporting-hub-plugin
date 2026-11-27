"""
refresh_dashboard_json.py

Re-embeds a fresh alfaihaa_inventory_audit.json into an already-built
dashboard.html (the full tab/JS structure is assumed already present — this
only swaps the embedded data, it does not add tabs or JS).

Usage:
    python3 refresh_dashboard_json.py <path_to_current_dashboard.html> <path_to_fresh_json> <output_path>

If output_path is omitted, overwrites the input HTML in place.
"""
import json
import sys


def refresh(html_path, json_path, out_path=None):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    start_tag = '<script id="audit-data" type="application/json">'
    end_tag = '</script>\n<script>'
    start_i = html.index(start_tag) + len(start_tag)
    end_i = html.index(end_tag, start_i)
    new_json_text = json.dumps(data, ensure_ascii=False, indent=2)
    html = html[:start_i] + new_json_text + html[end_i:]

    out_path = out_path or html_path
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Re-embedded {json_path} into {out_path} (new size: {len(html)} bytes)")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    html_path = sys.argv[1]
    json_path = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else None
    refresh(html_path, json_path, out_path)
