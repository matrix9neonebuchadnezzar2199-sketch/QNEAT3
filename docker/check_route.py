# -*- coding: utf-8 -*-
"""Smoke check: shortest path goes through the fictional road (cost assertion)."""
import json
import sys

path = sys.argv[1]
expected = float(sys.argv[2])
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)

features = data["features"]
if len(features) != 1:
    raise SystemExit("FAIL: expected 1 route feature, got {}".format(len(features)))

props = features[0]["properties"]
total = props["total_cost"]
graph = props["cost_on_graph"]
if abs(graph - expected) > 0.5:
    raise SystemExit("FAIL: cost_on_graph {} != {}".format(graph, expected))
if abs(total - expected) > 0.5:
    raise SystemExit("FAIL: total_cost {} != {}".format(total, expected))

print("check_route OK: cost_on_graph = total_cost = {}".format(total))
