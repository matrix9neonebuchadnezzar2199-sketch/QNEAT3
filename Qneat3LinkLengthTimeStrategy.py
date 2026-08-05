# -*- coding: utf-8 -*-
"""
link_len 属性と速度からエッジ所要時間 [s] を返す QgsNetworkStrategy。
グラフ構築前に link_len 全件検証・デフォルト速度検証済みを前提とする。

重要: QGIS の QgsVectorLayerDirector はポリラインをセグメント
（頂点→頂点）ごとの辺に分割して cost() を呼ぶ。link_len は
フィーチャ全体の長さなので、distance（セグメント実測長）/
フィーチャ全長 で按分してから速度で割る。
"""

from qgis.analysis import QgsNetworkStrategy
from qgis.core import (
    QgsCoordinateTransformContext,
    QgsDistanceArea,
    QgsProcessingException,
)

from QNEAT3.Qneat3NetworkErrors import (
    parse_positive_link_length,
    parse_speed_kmh,
    raise_processing_exception,
)
from QNEAT3.Qneat3Strings import ERR

# km/h → m/s（QgsNetworkSpeedStrategy と同じ換算係数）
KMH_TO_MPS = 1000.0 / 3600.0


class Qneat3LinkLengthTimeStrategy(QgsNetworkStrategy):
    """時間最適化: link_len をセグメント按分し、÷ 速度でコスト [s] にする。"""

    def __init__(
        self,
        link_field_index,
        link_field_name,
        speed_field_index,
        default_speed_kmh,
        analysis_crs,
    ):
        super(Qneat3LinkLengthTimeStrategy, self).__init__()
        self.link_field_index = link_field_index
        self.link_field_name = link_field_name
        self.speed_field_index = speed_field_index
        self.default_speed_kmh = float(default_speed_kmh)
        # 距離戦略と同じく、全長計測はビルダと同条件（ソース CRS + WGS84）
        self._measure = QgsDistanceArea()
        self._measure.setSourceCrs(analysis_crs, QgsCoordinateTransformContext())
        self._measure.setEllipsoid("WGS84")
        self._total_length_cache = {}

    def _feature_total_length(self, feature):
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

        total = self._feature_total_length(feature)
        if total <= 0:
            segment_len = link_len
        else:
            segment_len = link_len * (distance / total)

        speed_mps = speed_kmh * KMH_TO_MPS
        return segment_len / speed_mps

    def requiredAttributes(self):
        #Qt6/SIP6 系では set は QSet<int> に変換できないため list で返す
        attrs = {self.link_field_index}
        if self.speed_field_index >= 0:
            attrs.add(self.speed_field_index)
        return sorted(attrs)
