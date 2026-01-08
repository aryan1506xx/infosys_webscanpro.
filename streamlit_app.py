# streamlit_app.py
import streamlit as st
import time
import os
import json
from pathlib import Path
from scanners import ui_helpers

# --- CONFIG ---
PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_PASSIVE = OUTPUT_DIR / "scan_results_localhost_3000.json"
DEFAULT_ACTIVE = OUTPUT_DIR / "active_results_localhost_3000.json"
DEFAULT_REPORT_HTML = OUTPUT_DIR / "report.html"
DEFAULT_REPORT_CSV = OUTPUT_DIR / "findings.csv"

st.set_page_config(page_title="WebScanPro Dashboard", layout="wide")

st.title("WebScanPro — Scan & Report Dashboard")

# Sidebar controls
with st.sidebar:
    st.header("Scan Controls")
    target_url = st.text_input("Target base URL", value="http://localhost:3000")
    run_passive = st.button("Run Passive Scan")
    run_active = st.button("Run Active Scan (requires passive)")
    run_report = st.button("Generate Report (CSV + HTML)")
    st.markdown("---")
    st.header("Paths / Files")
    passive_path = st.text_input("Passive JSON path", value=str(DEFAULT_PASSIVE))
    active_path = st.text_input("Active JSON path", value=str(DEFAULT_ACTIVE))
    html_path = st.text_input("Report HTML path", value=str(DEFAULT_REPORT_HTML))
    csv_path = st.text_input("Report CSV path", value=str(DEFAULT_REPORT_CSV))
    st.markdown("---")
    st.caption("Use the buttons above to run scans. Logs will appear below. Do not run against systems you don't own.")

# helper to display live output lines
def stream_command(cmd_list, cwd=None):
    log_win = st.empty()
    lines = []
    pbar = st.progress(0.0)
    idx = 0
    for line, ret in ui_helpers.run_command_live(cmd_list, cwd=cwd):
        if line.startswith("__RETURN_CODE__:"):
            code = int(line.split(":",1)[1])
            lines.append(f"[PROCESS_RETURNED]{code}")
            pbar.progress(1.0)
            break
        lines.append(line)
        # update UI
        # show only last 200 lines to keep UI responsive
        display = "\n".join(lines[-200:])
        log_win.text_area("Live logs", display, height=400)
        idx += 1
        # simple progress heuristic (not accurate): show some motion
        pbar.progress(min(0.9, idx/50 if idx<50 else 0.9))
    return lines

# Run passive scan
if run_passive:
    st.info(f"Running passive scan for {target_url}")
    # Command: reuse passive_runner.py which accepts URL
    cmd = ["python", "passive_runner.py", target_url]
    logs = stream_command(cmd, cwd=str(PROJECT_ROOT))
    st.success("Passive scan finished.")
    # attempt to save output to chosen passive_path if process printed JSON
    # if the logger saved to file, we will trust that. Otherwise, parse last JSON block from logs.
    out_text = "\n".join(logs)
    # try to extract last JSON object (quick heuristic: find first '{' from last line)
    try:
        # find the first '{' in the combined lines and load JSON from there
        sidx = out_text.rfind("{")
        if sidx != -1:
            candidate = out_text[sidx:]
            parsed = json.loads(candidate)
            os.makedirs(os.path.dirname(passive_path), exist_ok=True)
            with open(passive_path, "w", encoding="utf-8") as fh:
                # expected format from passive_runner is a single object per run; but crawler format differs.
                # To keep UI consistent, save as a dict with url->passive_analysis
                # If parsed is the single result object, we wrap it
                wrapped = { parsed.get("url","unknown"): {"passive_analysis": parsed} }
                json.dump(wrapped, fh, indent=2)
            st.success(f"Saved passive result to {passive_path}")
    except Exception as e:
        st.error(f"Could not parse passive output JSON: {e}")

# Run active scan
if run_active:
    st.info("Running active scan. This will try to use the passive file for forms if present; otherwise it will fetch the page.")
    # Prefer using crawler/passive json if it exists and contains forms; otherwise call active_runner.py with URL
    if os.path.exists(passive_path):
        cmd = ["python", "active_runner.py", "--from-file", passive_path, "--delay", "1.0", "--output", str(active_path)]
    else:
        cmd = ["python", "active_runner.py", target_url, "--delay", "1.0", "--output", str(active_path)]
    logs = stream_command(cmd, cwd=str(PROJECT_ROOT))
    st.success("Active scan finished.")
    st.info(f"Active results saved (if runner wrote output) to {active_path}")

# Generate report
if run_report:
    st.info("Generating aggregated report (CSV + HTML)...")
    # call report_runner.py with paths
    cmd = ["python", "report_runner.py", "--passive", passive_path, "--active", active_path, "--out-html", html_path, "--out-csv", csv_path, "--title", "WebScanPro Report", "--target", target_url]
    logs = stream_command(cmd, cwd=str(PROJECT_ROOT))
    st.success("Report generation finished.")
    st.write(f"HTML: {html_path}")
    st.write(f"CSV: {csv_path}")
# Display last passive and active outputs (if present)
st.markdown("---")
st.header("Latest Results")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Passive (latest)")
    lp = ui_helpers.latest_file_in_dir(OUTPUT_DIR, ".json")
    if lp:
        st.write("Latest JSON in outputs:", lp)
    else:
        st.write("No output JSON files found in outputs/")
    if os.path.exists(passive_path):
        data = ui_helpers.safe_load_json(passive_path)
        if data:
            st.json(data)
        else:
            st.write("Passive file exists but could not parse.")

with col2:
    st.subheader("Active (latest)")
    if os.path.exists(active_path):
        data = ui_helpers.safe_load_json(active_path)
        if data:
            st.json(data)
        else:
            st.write("Active file exists but could not parse.")
    else:
        st.write("No active results found at", active_path)

st.markdown("---")
st.header("Quick Actions")
colA, colB, colC = st.columns(3)
with colA:
    if st.button("Open Report (HTML)"):
        if os.path.exists(html_path):
            st.markdown(f"[Open report HTML]({html_path})")
        else:
            st.warning("Report HTML not found. Generate it first.")
with colB:
    if st.button("Download CSV"):
        if os.path.exists(csv_path):
            st.download_button("Download findings CSV", Path(csv_path).read_bytes(), file_name=os.path.basename(csv_path))
        else:
            st.warning("CSV not found. Generate it first.")
with colC:
    if st.button("Show Last Logs (outputs/log.txt)"):
        log_file = OUTPUT_DIR / "log.txt"
        if log_file.exists():
            st.text_area("Log file", log_file.read_text())
        else:
            st.info("No log file found in outputs/")
