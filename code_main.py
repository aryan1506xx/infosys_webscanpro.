import argparse
import subprocess
import os
from datetime import datetime

def run_ui():
    print("\n🚀 Launching WebScanPro UI...\n")
    subprocess.run(["streamlit", "run", "ui/app.py"], shell=True)


def run_scan(mode, urls):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    json_file = os.path.join(output_dir, f"results-{timestamp}.json")
    html_file = os.path.join(output_dir, f"report-{timestamp}.html")

    cmd = [
        "python", "report_runner.py",
        "--targets", *urls,
        "--out-json", json_file,
        "--out-html", html_file,
        "--mode", mode
    ]

    print(f"\n🔍 Running {mode.upper()} scan on:")
    for url in urls:
        print("  -", url)

    print("\n⌛ Processing...\n")
    result = subprocess.run(cmd, text=True, capture_output=True, shell=True)

    if result.returncode != 0:
        print("\n❌ Scan failed. Error:")
        print(result.stderr)
        return

    print("✅ Scan completed.")
    print(f"📄 JSON report saved to:  {json_file}")
    print(f"📑 HTML report saved to:  {html_file}")


def main():
    parser = argparse.ArgumentParser(description="WebScanPro Main Controller")

    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch Streamlit UI"
    )

    parser.add_argument(
        "--scan",
        choices=["passive", "active", "both"],
        help="Run scanners from CLI"
    )

    parser.add_argument(
        "--urls",
        nargs="+",
        help="Target URLs (space separated)"
    )

    args = parser.parse_args()

    # ---- UI Mode ----
    if args.ui:
        run_ui()
        return

    # ---- CLI Scan Mode ----
    if args.scan:
        if not args.urls:
            print("❌ Error: You must specify target URLs using --urls")
            print("Example: python main.py --scan both --urls http://localhost:3000")
            return

        run_scan(args.scan, args.urls)
        return

    # ---- If nothing provided ----
    print("""
⚠️ No command provided.

Use one of these:

▶ Launch UI:
    python main.py --ui

▶ Run Passive Scan:
    python main.py --scan passive --urls http://localhost:3000

▶ Run Both Scans:
    python main.py --scan both --urls http://localhost:3000 http://localhost:8080
""")


if __name__ == "__main__":
    main()
