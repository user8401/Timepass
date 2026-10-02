"""Fetch gold rates from Chandukaka Saraf and PNG Jewellers and write rates.json.

Run by the GitHub Actions workflow (.github/workflows/rates.yml).
"""
import json
import re
import sys
from datetime import datetime, timezone

import requests

SITES = {
    "chandukaka": {
        "url": "https://chandukakasaraf.in/todays-gold-rate/",
        "rate": r"(\d{2})\s*KT\s*Gold\s*₹\s*([\d,]+)",
        "updated": r"Updated\s*On:?\s*([\d\-]+\s[\d:]+)",
    },
    "png": {
        "url": "https://www.pngjewellers.com/pages/metal-rates",
        "rate": r"(\d{1,2})\s*K\s*Gold\s*₹\s*([\d,]+)",
        "updated": r"Updated on\s*([A-Za-z]+,\s*[A-Za-z]+ \d{1,2}, \d{4} at \d{1,2}:\d{2} [AP]M)",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def strip_tags(html):
    text = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#8377;", "₹").replace("&#x20B9;", "₹")
    return re.sub(r"\s+", " ", text)


def parse(text, cfg):
    rates = {}
    for karat, amount in re.findall(cfg["rate"], text):
        rates.setdefault(int(karat), int(amount.replace(",", "")))
    m = re.search(cfg["updated"], text, flags=re.I)
    return rates, (m.group(1) if m else "time not shown on page")


def main():
    try:
        with open("rates.json", encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        old = {}

    out = {"fetchedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    ok = 0
    for key, cfg in SITES.items():
        try:
            r = requests.get(cfg["url"], headers=HEADERS, timeout=30)
            r.raise_for_status()
            rates, updated = parse(strip_tags(r.text), cfg)
            if not rates:
                raise ValueError("page loaded but no rates found (layout may have changed)")
            out[key] = {"rates": rates, "updated": updated}
            ok += 1
            print(f"{key}: {rates} ({updated})")
        except Exception as e:
            prev = old.get(key, {})
            out[key] = {
                "rates": prev.get("rates", {}),
                "updated": prev.get("updated", "unknown"),
                "error": str(e)[:150],
            }
            print(f"{key}: FAILED - {e}")

    with open("rates.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
