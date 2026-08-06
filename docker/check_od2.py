# -*- coding: utf-8 -*-
"""Smoke check: OD row network_cost and total_cost for a given pair."""
import json
import sys

path = sys.argv[1]
origin = sys.argv[2]
dest = sys.argv[3]
expected_net = float(sys.argv[4])
expected_total = float(sys.argv[5])

with open(path, encoding="utf-8") as handle:
    data = json.load(handle)

rows = [
    f for f in data["features"]
    if f["properties"]["origin_id"] == origin
    and f["properties"]["destination_id"] == dest
]
if len(rows) != 1:
    raise SystemExit("FAIL: OD row {} -> {} found {} time(s)".format(origin, dest, len(rows)))

props = rows[0]["properties"]
net = props["network_cost"]
total = props["total_cost"]
if net is None or abs(net - expected_net) > 0.6:
    raise SystemExit("FAIL: network_cost {} -> {} = {} (!= {})".format(origin, dest, net, expected_net))
if total is None or abs(total - expected_total) > 0.6:
    raise SystemExit("FAIL: total_cost {} -> {} = {} (!= {})".format(origin, dest, total, expected_total))

print("check_od2 OK: {} -> {} network_cost={} total_cost={}".format(origin, dest, net, total))
