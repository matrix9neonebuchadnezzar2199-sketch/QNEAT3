# -*- coding: utf-8 -*-
"""
QNEAT3 パッケージ内のシンボル参照整合チェック（QGIS 不要）。

- UIS.* / LOG.* / ERR.* → Qneat3Strings
- help_*() → Qneat3HelpJa
- Provider: addAlgorithm(Class()) のみ（Module.Class() 禁止）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from QNEAT3 import Qneat3HelpJa  # noqa: E402
from QNEAT3.Qneat3Strings import ERR, LOG, UIS  # noqa: E402

UIS_NAMES = {k for k in vars(UIS) if k.isupper()}
LOG_NAMES = {k for k in vars(LOG) if k.isupper()}
ERR_NAMES = {k for k in vars(ERR) if k.isupper()}
HELP_FUNCS = {
    k
    for k in dir(Qneat3HelpJa)
    if k.startswith("help_") and callable(getattr(Qneat3HelpJa, k))
}

SKIP_DIRS = {"scripts", "__pycache__", "dist"}
PATTERNS = [
    ("UIS", re.compile(r"\bUIS\.([A-Z][A-Z0-9_]*)\b"), UIS_NAMES),
    ("LOG", re.compile(r"\bLOG\.([A-Z][A-Z0-9_]*)\b"), LOG_NAMES),
    ("ERR", re.compile(r"\bERR\.([A-Z][A-Z0-9_]*)\b"), ERR_NAMES),
]
HELP_PATTERN = re.compile(r"\b(help_[a-z_]+)\s*\(")

errors = []
warnings = []

for path in sorted(ROOT.rglob("*.py")):
    if any(part in SKIP_DIRS for part in path.parts):
        continue
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    for kind, pattern, names in PATTERNS:
        for sym in pattern.findall(text):
            if sym not in names:
                errors.append(f"{rel}: {kind}.{sym} undefined")
    for fn in HELP_PATTERN.findall(text):
        if fn not in HELP_FUNCS:
            errors.append(f"{rel}: {fn}() undefined in Qneat3HelpJa")

provider = ROOT / "Qneat3Provider.py"
if provider.is_file():
    pt = provider.read_text(encoding="utf-8")
    for mod, cls in re.findall(
        r"addAlgorithm\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        pt,
    ):
        if mod == cls:
            errors.append(f"Qneat3Provider.py: legacy addAlgorithm({mod}.{cls}())")

# 意味的ラベル不一致（静的ルール）
poly_layer = ROOT / "algs" / "IsoAreaAsPolygonsFromLayer.py"
if poly_layer.is_file():
    t = poly_layer.read_text(encoding="utf-8")
    if "self.STRATEGY" in t and "ja(UIS.PATH_TYPE)" in t:
        warnings.append(
            "IsoAreaAsPolygonsFromLayer.py: STRATEGY param uses UIS.PATH_TYPE "
            "(should be UIS.OPTIMIZATION_CRITERION)"
        )

if errors:
    print("FAIL:", len(errors))
    for line in errors:
        print(" ", line)
    sys.exit(1)

print(
    "OK: UIS={} LOG={} ERR={} help={}".format(
        len(UIS_NAMES), len(LOG_NAMES), len(ERR_NAMES), len(HELP_FUNCS)
    )
)
if warnings:
    print("WARN:", len(warnings))
    for line in warnings:
        print(" ", line)
    sys.exit(2)
