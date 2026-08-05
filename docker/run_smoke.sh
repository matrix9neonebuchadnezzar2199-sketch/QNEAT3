#!/usr/bin/env bash
# QGIS検証スモークランナー（コンテナ内で実行）
# 1) Provider 登録確認 2) ネットワーク前処理 3) 出力検証 4) 最短経路コスト検証
set -euo pipefail
export QT_QPA_PLATFORM=offscreen

TESTDATA=/opt/qneat3-test/testdata
CHECKS=/opt/qneat3-test
OUT=/out
mkdir -p "$OUT"

echo "== [1/4] provider registration =="
qgis_process plugins enable QNEAT3 >/dev/null 2>&1 || true
if qgis_process list | grep -q "qneat3:networkpreparelinks"; then
  echo "OK: qneat3 provider registered"
else
  echo "FAIL: qneat3:networkpreparelinks not found in qgis_process list"
  qgis_process list | grep -i "qneat" || true
  exit 1
fi

echo "== [2/4] run networkpreparelinks =="
qgis_process run qneat3:networkpreparelinks \
  --INPUT="$TESTDATA/network.geojson" \
  --LINK_LENGTH_FIELD=link_len \
  --SNAP_TOLERANCE=5 \
  --FILL_LENGTH=true \
  --OUTPUT="$OUT/prepared.geojson"

echo "== [3/4] check prepared output =="
python3 "$CHECKS/check_prepared.py" "$OUT/prepared.geojson"

echo "== [4/4] run shortestpathpointtopoint (via fictional road) =="
qgis_process run qneat3:shortestpathpointtopoint \
  --INPUT="$OUT/prepared.geojson" \
  --START_POINT="500,1000 [EPSG:3857]" \
  --END_POINT="0,0 [EPSG:3857]" \
  --STRATEGY=0 \
  --ENTRY_COST_CALCULATION_METHOD=0 \
  --DEFAULT_DIRECTION=2 \
  --DEFAULT_SPEED=5 \
  --TOLERANCE=0 \
  --LINK_LENGTH_FIELD=link_len \
  --OUTPUT="$OUT/route.geojson"
python3 "$CHECKS/check_route.py" "$OUT/route.geojson" 2800

echo "SMOKE PASS"
