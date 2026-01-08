# debug_active.py
import json
import time
import requests
from scanners.active import analyze_form_submission

# load crawler output (adjust filename if different)
path = "outputs/scan_results_localhost_3000.json"

try:
    d = json.load(open(path, "r", encoding="utf-8"))
except Exception as e:
    print(f"Failed to load {path}: {e}")
    raise SystemExit(1)

s = requests.Session()
s.headers.update({"User-Agent": "WebScanProActive/1.0"})

for url, page in d.items():
    forms = page.get("forms", [])
    if not forms:
        print(f"[NO FORMS] URL: {url}")
    for i, f in enumerate(forms):
        input_names = [inp.get("name") for inp in f.get("inputs", [])]
        print(f"Testing form {i+1} on {url}")
        print("  action:", f.get("action"))
        print("  method:", f.get("method"))
        print("  inputs:", input_names)
        res = analyze_form_submission(url, f, s, delay=1.0)
        print("  Findings:", res.get("findings"))
        print("-" * 60)
        # polite delay between forms
        time.sleep(1)
