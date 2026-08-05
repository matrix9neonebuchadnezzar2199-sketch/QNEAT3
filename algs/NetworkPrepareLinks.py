# -*- coding: utf-8 -*-
"""
NetworkPrepareLinks.py
----------------------

架空道路・手描きリンクを既存ネットワークに接続する前処理。
- 他リンクの途中に突き当たる端点で既存リンクを分割（ノード挿入）
- 端点のズレをスナップ
- 未入力・不正な link_len を実測長で補完（任意）
- 分割したリンクの link_len を実測長比率で按分
出力レイヤをルーティング系アルゴリズムのネットワーク入力に使う。
"""

import os

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsGeometry,
                       QgsField,
                       QgsFields,
                       QgsDistanceArea,
                       QgsPointXY,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString)

from QNEAT3.Qneat3NetworkErrors import (
    DEFAULT_LINK_LENGTH_FIELD,
    parse_positive_link_length,
)
from QNEAT3.Qneat3NetworkPrep import (
    apply_plan,
    connected_components,
    plan_endpoint_attachments,
    prorate_value,
)
from QNEAT3.Qneat3Utilities import feature_geometry_part_tuples
from QNEAT3.Qneat3Strings import (
    UIS,
    LOG,
    ERR,
    ja,
    NEO_PREFIX,
    log_msg,
)
from QNEAT3.Qneat3HelpJa import help_network_prepare_links
from QNEAT3.Qneat3Paths import icon_path
from QNEAT3.Qneat3BuildInfo import push_build_banner
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm

# 主成分に属さないリンクのログ表示上限
MAX_REPORTED_ISOLATED = 10


class NetworkPrepareLinks(QgisAlgorithm):

    INPUT = 'INPUT'
    LINK_LENGTH_FIELD = 'LINK_LENGTH_FIELD'
    SNAP_TOLERANCE = 'SNAP_TOLERANCE'
    FILL_LENGTH = 'FILL_LENGTH'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(icon_path('icon_network_prepare.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.NETWORK_PREP)

    def groupId(self):
        return 'networkprep'

    def name(self):
        return 'networkpreparelinks'

    def displayName(self):
        return ja(NEO_PREFIX + 'ネットワーク前処理（接続・link_len）')

    def shortHelpString(self):
        return help_network_prepare_links()

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT,
            ja(UIS.NETWORK_LAYER),
            [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterString(
            self.LINK_LENGTH_FIELD,
            ja(UIS.PREP_LINK_FIELD),
            defaultValue=DEFAULT_LINK_LENGTH_FIELD))
        self.addParameter(QgsProcessingParameterNumber(
            self.SNAP_TOLERANCE,
            ja(UIS.PREP_SNAP_TOLERANCE),
            QgsProcessingParameterNumber.Double,
            1.0,
            False,
            0,
            99999999.99))
        self.addParameter(QgsProcessingParameterBoolean(
            self.FILL_LENGTH,
            ja(UIS.PREP_FILL_LENGTH),
            defaultValue=True))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            ja(UIS.OUTPUT_PREPARED_NETWORK),
            QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        push_build_banner(feedback)

        source = self.parameterAsSource(parameters, self.INPUT, context)
        field_name = self.parameterAsString(
            parameters, self.LINK_LENGTH_FIELD, context).strip()
        if not field_name:
            field_name = DEFAULT_LINK_LENGTH_FIELD
        tolerance = self.parameterAsDouble(parameters, self.SNAP_TOLERANCE, context)
        fill_length = self.parameterAsBool(parameters, self.FILL_LENGTH, context)

        crs = source.sourceCrs()
        source_fields = source.fields()
        link_field_index = source_fields.lookupField(field_name)

        # link_len 補完用の実測長（楕円体。得られなければ CRS 平面）
        measure = QgsDistanceArea()
        measure.setSourceCrs(crs, context.transformContext())
        ellipsoid = crs.ellipsoidAcronym()
        if ellipsoid:
            measure.setEllipsoid(ellipsoid)

        # フィーチャ → パート（マルチパートは分解。QGIS グラフもパート単位で辺を作る）
        lines = []
        part_attrs = []
        part_fids = []
        part_measured = []
        feature_count = 0
        for feature in source.getFeatures():
            feature_count += 1
            attrs = feature.attributes()
            for pts in feature_geometry_part_tuples(feature):
                lines.append(pts)
                part_attrs.append(attrs)
                part_fids.append(feature.id())
                part_measured.append(
                    measure.measureLine([QgsPointXY(x, y) for x, y in pts])
                )
        log_msg(
            feedback, LOG.PREP_READ,
            features=feature_count, parts=len(lines),
        )
        feedback.setProgress(20)

        # link_len の確定（未入力・不正は任意で実測長に補完。0 以下は受理しない）
        values = []
        filled_count = 0
        for k, attrs in enumerate(part_attrs):
            raw = None
            if 0 <= link_field_index < len(attrs):
                raw = attrs[link_field_index]
            length, issue = parse_positive_link_length(raw, part_fids[k], field_name)
            if issue:
                if not fill_length or part_measured[k] <= 0:
                    raise QgsProcessingException(
                        ja(ERR.PREP_LINK_LEN_INVALID).format(
                            fid=part_fids[k], value=raw
                        )
                    )
                length = part_measured[k]
                filled_count += 1
            values.append(length)
        if filled_count:
            log_msg(feedback, LOG.PREP_FILLED, count=filled_count)
        feedback.setProgress(40)

        # 接続計画 → 適用（スナップ → 分割）
        cuts, snaps, stats = plan_endpoint_attachments(lines, tolerance)
        parts_per_line, snapped_lines = apply_plan(lines, cuts, snaps)
        log_msg(
            feedback, LOG.PREP_SNAP_SPLIT,
            snaps=stats["snaps"],
            links=stats["split_links"],
            events=stats["split_events"],
        )
        feedback.setProgress(60)

        # フラット化 + link_len 按分
        out_lines = []
        out_attrs = []
        out_values = []
        for i, parts in enumerate(parts_per_line):
            prorated = prorate_value(values[i], snapped_lines[i], parts)
            for part, value in zip(parts, prorated):
                out_lines.append(part)
                out_attrs.append(part_attrs[i])
                out_values.append(value)

        # 連結成分レポート（孤立リンク＝経路計算で到達不能）
        comps = connected_components(out_lines, tolerance)
        comps.sort(key=len, reverse=True)
        if comps:
            log_msg(
                feedback, LOG.PREP_COMPONENTS,
                count=len(comps), largest=len(comps[0]),
            )
            isolated = [idx for comp in comps[1:] for idx in comp]
            if isolated:
                shown = isolated[:MAX_REPORTED_ISOLATED]
                suffix = " ..." if len(isolated) > MAX_REPORTED_ISOLATED else ""
                log_msg(
                    feedback, LOG.PREP_ISOLATED,
                    indices=", ".join(str(i) for i in shown) + suffix,
                )
        feedback.setProgress(80)

        # 出力フィールド（link_len フィールドが無ければ追加）
        out_fields = QgsFields(source_fields)
        if link_field_index < 0:
            out_fields.append(QgsField(field_name, QVariant.Double, '', 20, 7))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, out_fields,
            QgsWkbTypes.LineString, crs)

        for part, attrs, value in zip(out_lines, out_attrs, out_values):
            feat = QgsFeature(out_fields)
            feat.setGeometry(
                QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in part])
            )
            for idx, field in enumerate(source_fields):
                feat[field.name()] = attrs[idx] if idx < len(attrs) else None
            feat[field_name] = value
            sink.addFeature(feat, QgsFeatureSink.FastInsert)

        log_msg(
            feedback, LOG.PREP_DONE,
            count=len(out_lines), total=sum(out_values),
        )
        log_msg(feedback, LOG.ALG_END)
        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}
