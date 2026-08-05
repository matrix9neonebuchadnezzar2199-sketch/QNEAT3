# -*- coding: utf-8 -*-
"""
属性フィールドに格納したリンク長をエッジコストとする QgsNetworkStrategy。
グラフ構築前に Qneat3NetworkErrors で全件検証済みであることを前提とする。
"""

from qgis.analysis import QgsNetworkStrategy

from QNEAT3.Qneat3NetworkErrors import (
  parse_positive_link_length,
  raise_processing_exception,
)


class Qneat3LinkLengthStrategy(QgsNetworkStrategy):
  """距離最適化: 形状長ではなく link_len 等の属性値をコストにする。"""

  def __init__(self, field_index, field_name):
    super(Qneat3LinkLengthStrategy, self).__init__()
    self.field_index = field_index
    self.field_name = field_name

  def cost(self, distance, feature):
    """QGIS がグラフ構築時に呼ぶ。distance（形状長）は使用しない。"""
    raw = feature.attribute(self.field_index)
    length, issue = parse_positive_link_length(
      raw, feature.id(), self.field_name
    )
    if issue:
      raise_processing_exception([issue])
    return length

  def requiredAttributes(self):
    #Qt6/SIP6 系では set は QSet<int> に変換できないため list で返す
    return [self.field_index]
