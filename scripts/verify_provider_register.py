# -*- coding: utf-8 -*-
"""Provider の addAlgorithm(X()) パターンを検証（QGIS / qgis モジュール不要）。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
provider = ROOT / "Qneat3Provider.py"
text = provider.read_text(encoding="utf-8")

# 旧バグ: Module.Class() — クラス import 後は Class() のみ
bad = re.findall(
    r"addAlgorithm\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(",
    text,
)
errors = []
for mod, cls in bad:
    if mod == cls:
        errors.append(f"legacy Module.Class(): {mod}.{cls}()")

if "addAlgorithm(ShortestPathBetweenPoints())" not in text:
    errors.append("missing: addAlgorithm(ShortestPathBetweenPoints())")

if errors:
    print("FAIL")
    for item in errors:
        print(" ", item)
    sys.exit(1)

print("OK: Provider uses addAlgorithm(Class()); no Module.Class() pattern")
