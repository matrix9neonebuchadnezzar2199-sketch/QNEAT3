# -*- coding: utf-8 -*-
"""metadata.txt が QGIS ConfigParser で読めるか簡易検証。"""
import configparser
import sys
from pathlib import Path

meta_path = Path(__file__).resolve().parents[1] / "metadata.txt"
cp = configparser.ConfigParser()
cp.read(meta_path, encoding="utf-8")
g = cp["general"]
required = ("name", "description", "version", "qgisMinimumVersion", "author", "email")
missing = [k for k in required if not g.get(k, "").strip()]
print("metadata:", meta_path)
print("version:", g.get("version"))
print("name:", g.get("name"))
if missing:
    print("MISSING:", missing)
    sys.exit(1)
tags = g.get("tags", "")
if ", " in tags:
    print("WARN: tags must not use comma+space (use comma only)")
    sys.exit(1)
print("OK")
