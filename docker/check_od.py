# -*- coding: utf-8 -*-
"""Smoke check: OD matrix row for the fictional-road pair with route geometry."""
import json
import sys

path = sys.argv[1]
origin = sys.argv[2]
dest = sys.argv[3]
expected = float(sys.argv[4])

with open(path, encoding="utf-8") as handle:
    data = json.load(handle)


def find_row(o, d):
    rows = [
        f for f in data["features"]
        if f["properties"]["origin_id"] == o
        and f["properties"]["destination_id"] == d
    ]
    if len(rows) != 1:
        raise SystemExit(
            "FAIL: OD row {} -> {} found {} time(s)".format(o, d, len(rows))
        )
    return rows[0]


for o, d in ((origin, dest), (dest, origin)):
    row = find_row(o, d)
    cost = row["properties"]["network_cost"]
    if abs(cost - expected) > 0.5:
        raise SystemExit(
            "FAIL: network_cost {} -> {} = {} (!= {})".format(o, d, cost, expected)
        )
    if not row.get("geometry"):
        raise SystemExit("FAIL: route geometry empty for {} -> {}".format(o, d))

print("check_od OK: {} <-> {} network_cost = {}".format(origin, dest, expected))
