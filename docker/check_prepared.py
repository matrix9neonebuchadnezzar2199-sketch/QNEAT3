# -*- coding: utf-8 -*-
"""Smoke check: prepared network has split/filled link_len as expected."""
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)

features = data["features"]
lengths = sorted(round(f["properties"]["link_len"], 1) for f in features)

if len(features) != 4:
    raise SystemExit("FAIL: expected 4 links after prep, got {}".format(len(features)))
if any(v <= 0 for v in lengths):
    raise SystemExit("FAIL: non-positive link_len: {}".format(lengths))

# dangler filled (~100), fictional explicit 300, base split into 2 x 2500
if abs(lengths[0] - 100.0) > 5.0:
    raise SystemExit("FAIL: filled dangler length: {}".format(lengths))
if abs(lengths[1] - 300.0) > 0.5:
    raise SystemExit("FAIL: fictional link_len changed: {}".format(lengths))
if abs(lengths[2] - 2500.0) > 0.5 or abs(lengths[3] - 2500.0) > 0.5:
    raise SystemExit("FAIL: base split proration: {}".format(lengths))

print("check_prepared OK: link_len values = {}".format(lengths))
