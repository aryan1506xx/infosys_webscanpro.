# tests/test_reporting.py
from scanners.reporting import score_finding, aggregate_findings
import json
import os

def test_score_finding_known():
    f = {"type": "xss"}
    s = score_finding(f)
    assert s["severity"] == "High"

def test_aggregate_empty(tmp_path):
    p = tmp_path / "p.json"
    a = tmp_path / "a.json"
    p.write_text("{}", encoding="utf-8")
    a.write_text("[]", encoding="utf-8")
    agg = aggregate_findings(str(p), str(a))
    assert "findings" in agg
    assert isinstance(agg["findings"], list)
