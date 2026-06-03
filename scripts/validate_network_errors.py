# -*- coding: utf-8 -*-
"""ERR の link_len 定数と Qneat3NetworkErrors の参照を検証（QGIS 不要）。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from QNEAT3.Qneat3Strings import ERR  # noqa: E402

REQUIRED_ERR = (
    "LINK_LEN_HEADER",
    "LINK_LEN_FIELD_EMPTY",
    "LINK_LEN_FIELD_MISSING",
    "LINK_LEN_VALUE_NULL",
    "LINK_LEN_VALUE_NOT_NUMERIC",
    "LINK_LEN_VALUE_NOT_POSITIVE",
    "LINK_LEN_TRUNCATED",
    "DEFAULT_SPEED_INVALID",
)

ERR_IN_TIME_STRATEGY = ("EDGE_SPEED_INVALID",)

errors = []
for name in REQUIRED_ERR:
    if not hasattr(ERR, name):
        errors.append("ERR.{} missing".format(name))
    else:
        val = getattr(ERR, name)
        if not val or not str(val).strip():
            errors.append("ERR.{} is empty".format(name))

net_err = ROOT / "Qneat3NetworkErrors.py"
text = net_err.read_text(encoding="utf-8")
for err_name in REQUIRED_ERR:
    if "ERR.{}".format(err_name) not in text:
        errors.append("Qneat3NetworkErrors.py does not reference ERR.{}".format(err_name))

if "DEFAULT_SPEED_INVALID" not in text:
    errors.append("require_positive_default_speed must use ERR.DEFAULT_SPEED_INVALID")

for err_name in ERR_IN_TIME_STRATEGY:
    if not hasattr(ERR, err_name):
        errors.append("ERR.{} missing".format(err_name))
time_strat = ROOT / "Qneat3LinkLengthTimeStrategy.py"
if time_strat.exists():
    ts = time_strat.read_text(encoding="utf-8")
    for err_name in ERR_IN_TIME_STRATEGY:
        if "ERR.{}".format(err_name) not in ts:
            errors.append(
                "Qneat3LinkLengthTimeStrategy must use ERR.{}".format(err_name)
            )

if errors:
    print("FAIL:", len(errors))
    for line in errors:
        print(" ", line)
    sys.exit(1)

print("OK: network error templates (ERR x{})".format(len(REQUIRED_ERR)))
