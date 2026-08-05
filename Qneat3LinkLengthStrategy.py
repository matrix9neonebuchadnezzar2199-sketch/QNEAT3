# -*- coding: utf-8 -*-
"""
属性フィールドに格納したリンク長をエッジコストとする QgsNetworkStrategy。
グラフ構築前に Qneat3NetworkErrors で全件検証済みであることを前提とする。

重要: QGIS の QgsVectorLayerDirector はポリラインをセグメント
（頂点→頂点）ごとの辺に分割して cost() を呼ぶ。link_len は
フィーチャ全体の長さなので、そのまま返すとセグメント数だけ重複課金
される。distance（セグメントの実測長）/ フィーチャ全長 で按分する。
"""

from qgis.analysis import QgsNetworkStrategy
from qgis.core import QgsDistanceArea, QgsCoordinateTransformContext

from QNEAT3.Qneat3NetworkErrors import (
  parse_positive_link_length,
  raise_processing_exception,
)


class Qneat3LinkLengthStrategy(QgsNetworkStrategy):
  """距離最適化: link_len をセグメント辺に按分してコストにする。"""

  def __init__(self, field_index, field_name, analysis_crs):
    super(Qneat3LinkLengthStrategy, self).__init__()
    self.field_index = field_index
    self.field_name = field_name
    # フィーチャ全長の計測はビルダと同じ条件（ソース CRS + WGS84 楕円体）
    # に揃える。揃えないと distance 合計と全長が食い違い link_len 合計が
    # わずかに狂う
    self._measure = QgsDistanceArea()
    self._measure.setSourceCrs(analysis_crs, QgsCoordinateTransformContext())
    self._measure.setEllipsoid("WGS84")
    # フィーチャ全長キャッシュ（セグメント辺のたびに計測すると遅い）
    self._total_length_cache = {}

  def _feature_total_length(self, feature):
    """ビルダの distance 合計と一致するフィーチャ全長（マルチパート対応）。"""
    fid = feature.id()
    total = self._total_length_cache.get(fid)
    if total is None:
      geom = feature.geometry()
      if geom.isMultipart():
        parts = geom.asMultiPolyline()
      else:
        parts = [geom.asPolyline()]
      total = 0.0
      for part in parts:
        total += self._measure.measureLine(part)
      self._total_length_cache[fid] = total
    return total

  def cost(self, distance, feature):
    """QGIS がセグメント辺ごとに呼ぶ。distance はセグメントの実測長。"""
    raw = feature.attribute(self.field_index)
    length, issue = parse_positive_link_length(
      raw, feature.id(), self.field_name
    )
    if issue:
      raise_processing_exception([issue])

    total = self._feature_total_length(feature)
    if total <= 0:
      # 退化ジオメトリ: 按分不能のため全額を返す（理論上到達しない）
      return length
    return length * (distance / total)

  def requiredAttributes(self):
    #Qt6/SIP6 系では set は QSet<int> に変換できないため list で返す
    return [self.field_index]
