import argparse
import json
from scanners.passive import passive_scan
from utils.logger import get_logger

logger = get_logger("passive-runner")

def main():
    parser = argparse.ArgumentParser(description="Run passive scan")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--out", default="outputs/passive_output.json")
    args = parser.parse_args()

    logger.info(f"Starting passive scan on {args.url}")
    results = passive_scan(args.url)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Passive scan completed. Output saved to {args.out}")

if __name__ == "__main__":
    main()
