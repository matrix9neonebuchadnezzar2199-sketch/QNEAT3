#!/usr/bin/env bash
# QGIS検証スモークランナー（コンテナ内で実行）
# 1) Provider 登録確認 2) ネットワーク前処理 3) 出力検証
# 4) 最短経路（距離） 5) 最短経路（時間・速度フィールド） 6) OD 行列（ライン）
set -euo pipefail
export QT_QPA_PLATFORM=offscreen

TESTDATA=/opt/qneat3-test/testdata
CHECKS=/opt/qneat3-test
OUT=/out
mkdir -p "$OUT"

echo "== [1/6] provider registration =="
qgis_process plugins enable QNEAT3 >/dev/null 2>&1 || true
if qgis_process list | grep -q "qneat3:networkpreparelinks"; then
  echo "OK: qneat3 provider registered"
else
  echo "FAIL: qneat3:networkpreparelinks not found in qgis_process list"
  qgis_process list | grep -i "qneat" || true
  exit 1
fi

echo "== [2/6] run networkpreparelinks =="
qgis_process run qneat3:networkpreparelinks \
  --INPUT="$TESTDATA/network.geojson" \
  --LINK_LENGTH_FIELD=link_len \
  --SNAP_TOLERANCE=5 \
  --FILL_LENGTH=true \
  --OUTPUT="$OUT/prepared.geojson"

echo "== [3/6] check prepared output =="
python3 "$CHECKS/check_prepared.py" "$OUT/prepared.geojson"

echo "== [4/6] run shortestpathpointtopoint (distance, via fictional road) =="
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

echo "== [5/6] run shortestpathpointtopoint (time, speed field) =="
# fictional 300 m @5km/h = 216 s + base半分 2500 m @100km/h = 90 s → 306 s
qgis_process run qneat3:shortestpathpointtopoint \
  --INPUT="$OUT/prepared.geojson" \
  --START_POINT="500,1000 [EPSG:3857]" \
  --END_POINT="0,0 [EPSG:3857]" \
  --STRATEGY=1 \
  --ENTRY_COST_CALCULATION_METHOD=0 \
  --DEFAULT_DIRECTION=2 \
  --SPEED_FIELD=speed \
  --DEFAULT_SPEED=5 \
  --TOLERANCE=0 \
  --LINK_LENGTH_FIELD=link_len \
  --OUTPUT="$OUT/route_time.geojson"
python3 "$CHECKS/check_route.py" "$OUT/route_time.geojson" 306

echo "== [6/6] run OdMatrixFromPointsAsLines (route geometry) =="
qgis_process run qneat3:OdMatrixFromPointsAsLines \
  --INPUT="$OUT/prepared.geojson" \
  --POINTS="$TESTDATA/points.geojson" \
  --ID_FIELD=pid \
  --STRATEGY=0 \
  --MATRIX_GEOMETRY_TYPE=1 \
  --ENTRY_COST_CALCULATION_METHOD=0 \
  --DEFAULT_DIRECTION=2 \
  --DEFAULT_SPEED=5 \
  --TOLERANCE=0 \
  --LINK_LENGTH_FIELD=link_len \
  --OUTPUT="$OUT/od.geojson"
python3 "$CHECKS/check_od.py" "$OUT/od.geojson" A B 2800

echo "SMOKE PASS"
