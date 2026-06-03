# -*- coding: utf-8 -*-
"""
link_len 属性と速度からエッジ所要時間 [s] を返す QgsNetworkStrategy。
グラフ構築前に link_len 全件検証・デフォルト速度検証済みを前提とする。
"""

from qgis.analysis import QgsNetworkStrategy
from qgis.core import QgsProcessingException

from QNEAT3.Qneat3NetworkErrors import (
    parse_positive_link_length,
    parse_speed_kmh,
    raise_processing_exception,
)
from QNEAT3.Qneat3Strings import ERR

# km/h → m/s（QgsNetworkSpeedStrategy と同じ換算係数）
KMH_TO_MPS = 1000.0 / 3600.0


class Qneat3LinkLengthTimeStrategy(QgsNetworkStrategy):
    """時間最適化: 形状長ではなく link_len / 速度 でコスト [s] を算出する。"""

    def __init__(
        self,
        link_field_index,
        link_field_name,
        speed_field_index,
        default_speed_kmh,
    ):
        super(Qneat3LinkLengthTimeStrategy, self).__init__()
        self.link_field_index = link_field_index
        self.link_field_name = link_field_name
        self.speed_field_index = speed_field_index
        self.default_speed_kmh = float(default_speed_kmh)

    def cost(self, distance, feature):
        """QGIS がグラフ構築時に呼ぶ。distance（形状長）は使用しない。"""
        raw_len = feature.attribute(self.link_field_index)
        link_len, issue = parse_positive_link_length(
            raw_len, feature.id(), self.link_field_name
        )
        if issue:
            raise_processing_exception([issue])

        speed_kmh = parse_speed_kmh(
            feature,
            self.speed_field_index,
            self.default_speed_kmh,
            feature.id(),
        )
        if speed_kmh is None:
            raise QgsProcessingException(
                ERR.EDGE_SPEED_INVALID.format(fid=feature.id())
            )

        speed_mps = speed_kmh * KMH_TO_MPS
        return link_len / speed_mps

    def requiredAttributes(self):
        attrs = {self.link_field_index}
        if self.speed_field_index >= 0:
            attrs.add(self.speed_field_index)
        return attrs
