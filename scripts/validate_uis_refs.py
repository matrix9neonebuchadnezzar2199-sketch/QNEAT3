# -*- coding: utf-8 -*-
"""algs 内の UIS.* 参照が Qneat3Strings.UIS に存在するか検証（QGIS 不要）。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from QNEAT3.Qneat3Strings import UIS  # noqa: E402

UIS_NAMES = {k for k in vars(UIS) if k.isupper() and not k.startswith("_")}
PATTERN = re.compile(r"\bUIS\.([A-Z][A-Z0-9_]*)\b")

errors = []
for path in sorted((ROOT / "algs").glob("*.py")):
    text = path.read_text(encoding="utf-8")
    for name in PATTERN.findall(text):
        if name not in UIS_NAMES:
            errors.append(f"{path.name}: UIS.{name}")

if errors:
    print("FAIL: undefined UIS attributes")
    for line in errors:
        print(" ", line)
    sys.exit(1)

print(f"OK: {len(UIS_NAMES)} UIS constants; all algs references resolve")
