# -*- coding: utf-8 -*-
"""
***************************************************************************
    Qneat3Utilities.py
    ---------------------
    
    Date                 : January 2018
    Copyright            : (C) 2018 by Clemens Raffler
    Email                : clemens dot raffler at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.core import QgsWkbTypes, QgsMessageLog, QgsVectorLayer, QgsFeature, QgsGeometry, QgsFields, QgsField, QgsFeatureRequest, QgsPointXY, QgsProject, QgsCoordinateTransform

from qgis.PyQt.QtCore import QVariant
from QNEAT3.Qneat3Exceptions import Qneat3GeometryException

def AssignAnalysisCrs(vlayer):
    logPanel("Setting analysis CRS")
    AnalysisCrs = vlayer.crs()
    return AnalysisCrs

def logPanel(message):
    QgsMessageLog.logMessage(message, "QNEAT3")
    
def isGeometryType(vlayer, type_obj):
    geom_type = vlayer.geometryType()
    if geom_type == type_obj:
        return True
    else:
        return False

def buildQgsVectorLayer(string_geomtype, string_layername, crs, feature_list, list_qgsfield):
    
    #create new vector layer from self.crs
    vector_layer = QgsVectorLayer(string_geomtype, string_layername, "memory")
    
    #set crs from class
    vector_layer.setCrs(crs)
    
    #set fields
    provider = vector_layer.dataProvider()
    provider.addAttributes(list_qgsfield) #[QgsField('fid',QVariant.Int),QgsField("origin_point_id", QVariant.Double),QgsField("iso", QVariant.Int)]
    vector_layer.updateFields()
    
    #fill layer with geom and attrs
    vector_layer.startEditing()
    for feat in feature_list:
        vector_layer.addFeature(feat, True)
    vector_layer.commitChanges()

    return vector_layer

def getFeatureFromPointParameter(qgs_point_xy, point_label="ポイント"):
    feature = QgsFeature()
    fields = QgsFields()
    fields.append(QgsField('point_id', QVariant.String, '', 254, 0))
    feature.setFields(fields)
    feature.setGeometry(QgsGeometry.fromPointXY(qgs_point_xy))
    feature['point_id'] = point_label
    return feature

def getFeaturesFromQgsIterable(qgs_feature_storage):#qgs_feature_storage can be any vectorLayer/QgsProcessingParameterFeatureSource/etc
    fRequest = QgsFeatureRequest().setFilterFids(qgs_feature_storage.allFeatureIds())
    return qgs_feature_storage.getFeatures(fRequest)

def mergeFeaturesFromQgsIterable(qgs_feature_storage_list):
    result_feature_list = []
    for qgs_feature_storage in qgs_feature_storage_list:
        fRequest = QgsFeatureRequest().setFilterFids(qgs_feature_storage.allFeatureIds())
        result_feature_list.extend(qgs_feature_storage.getFeatures(fRequest))
    return result_feature_list
        
        
def getFieldIndexFromQgsProcessingFeatureSource(feature_source, field_name):
    if field_name != "":
        return feature_source.fields().lookupField(field_name)
    else:
        return -1
    
def iter_point_features(qgs_feature_storage):
    """
    ポイントレイヤを (feature, QgsPointXY) の順で返す。

    getListOfPoints と Qneat3AnalysisPoint のインデックスを一致させるため、
    マルチポイントは頂点ごとに同じ feature を繰り返す。
    """
    given_geom_type = qgs_feature_storage.wkbType()
    if QgsWkbTypes.geometryType(given_geom_type) != QgsWkbTypes.PointGeometry:
        raise Qneat3GeometryException(given_geom_type, QgsWkbTypes.PointGeometry)

    for feature in getFeaturesFromQgsIterable(qgs_feature_storage):
        geom = feature.geometry()
        if geom.isMultipart():
            for pt in geom.asMultiPoint():
                yield feature, pt
        else:
            yield feature, geom.asPoint()


def getListOfPoints(qgs_feature_storage):
    """ポイント / マルチポイントレイヤから QgsPointXY のリストを取得。"""
    return [pt for _, pt in iter_point_features(qgs_feature_storage)]


def transform_point_list(points, source_crs, target_crs):
    """
    座標リストを source_crs → target_crs に変換する。

    点レイヤはレイヤ自身が CRS を持つため、ネットワーク CRS と異なる場合は
    決定論的に変換できる（ヒューリスティックな「みなし」は不要）。
    CRS が同じ・無効な場合はそのまま返す。

    Returns:
        tuple: (変換後の点リスト, 変換したかどうかの真偽)
    """
    if (
        source_crs is None
        or not source_crs.isValid()
        or not target_crs.isValid()
        or source_crs == target_crs
    ):
        return list(points), False
    xform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
    return [xform.transform(pt) for pt in points], True


def reproject_rows_to_crs(rows, source_crs, target_crs, feedback):
    """
    (feature, pt) 行の座標を source_crs → target_crs に変換する。

    アルゴリズム側でレイヤをマージして渡す場合（FromLayers 系・FromPointsAsLines）
    は Framework の変換が効かないため、このヘルパーでレイヤごとに変換する。
    変換した場合は POINTS_REPROJECTED を 1 行ログ出力する。
    """
    pts, transformed = transform_point_list(
        [pt for _, pt in rows], source_crs, target_crs
    )
    if transformed:
        from QNEAT3.Qneat3Strings import LOG, log_msg

        log_msg(
            feedback, LOG.POINTS_REPROJECTED,
            src=source_crs.authid(), dst=target_crs.authid(), count=len(pts),
        )
    return [(feat, pt) for (feat, _), pt in zip(rows, pts)]


def log_far_tie_summary(analysis_points, feedback, threshold=100000.0):
    """
    ネットワークから threshold（投影 CRS のメートル想定）以上離れて結線した
    点の件数を 1 行で警告する。CRS 混在による全点誤結線の検出用。
    """
    from QNEAT3.Qneat3Strings import LOG, log_msg

    far_count = 0
    far_max = 0.0
    for analysis_point in analysis_points:
        tie_dist = analysis_point.calcEntryLinestring().length()
        if tie_dist > threshold:
            far_count += 1
            far_max = max(far_max, tie_dist)
    if far_count:
        log_msg(
            feedback, LOG.TIE_FAR_SUMMARY,
            count=far_count, total=len(analysis_points), dist=far_max,
        )


def predecessor_vertex_on_tree(network, edge_id, at_vertex):
    """
    最短経路木の辺 edge_id 上で、頂点 at_vertex の反対側の頂点を返す。

    無向グラフでは辺の向きが一定でないため fromVertex 固定は誤走査になる。
    """
    edge = network.edge(edge_id)
    if edge.toVertex() == at_vertex:
        return edge.fromVertex()
    if edge.fromVertex() == at_vertex:
        return edge.toVertex()
    return -1


def feature_geometry_part_tuples(feature):
    """
    フィーチャのラインジオメトリをパートごとの (x, y) タプル列に分解する。

    マルチパートは各パートを個別に返す（QGIS グラフもパート単位で辺を作る）。
    空・非ライン・2 点未満のパートは除外。

    Returns:
        list[list[tuple]]: パートごとの座標列。該当なしなら空リスト。
    """
    geom = feature.geometry()
    if geom is None or geom.isEmpty():
        return []
    if geom.isMultipart():
        raw_parts = geom.asMultiPolyline()
    else:
        raw_parts = [geom.asPolyline()]
    parts = []
    for part in raw_parts:
        pts = [(p.x(), p.y()) for p in part]
        if len(pts) >= 2:
            parts.append(pts)
    return parts


def reconstruct_path_geometry(
    network,
    tree,
    start_vertex_id,
    end_vertex_id,
    start_point_geom,
    end_point_geom,
):
    """
    Dijkstra 木から始点→終点の経路（QgsPointXY のリスト）を構築する。

    QGIS のグラフ辺はポリラインのセグメント（頂点→頂点）なので、
    辺を頂点順に継ぐだけで元リンクの形状と厳密に一致する。
    entry/exit（点↔最寄り頂点）は設計通り直線。

    Returns:
        list[QgsPointXY] | None: 到達不能時は None。
    """
    if tree[end_vertex_id] == -1:
        return None
    if start_vertex_id == end_vertex_id:
        return [start_point_geom, end_point_geom]

    path = [end_point_geom, network.vertex(end_vertex_id).point()]
    current = end_vertex_id
    max_hops = network.vertexCount() + 2

    for _ in range(max_hops):
        if current == start_vertex_id:
            break
        edge_id = tree[current]
        if edge_id < 0:
            return None
        previous = predecessor_vertex_on_tree(network, edge_id, current)
        if previous < 0:
            return None
        current = previous
        path.append(network.vertex(current).point())
    else:
        return None

    path.append(start_point_geom)
    path.reverse()
    return path
        
def getFieldDatatype(qgs_feature_storage, fieldname):
    fields_list = qgs_feature_storage.fields()
    qvariant_type = fields_list.field(fieldname).type()
    return qvariant_type

def getFieldDatatypeFromPythontype(pythonvar):
    if isinstance(pythonvar, str):
        return QVariant.String
    elif isinstance(pythonvar, int):
        return QVariant.Int
    elif isinstance(pythonvar, float):
        return QVariant.Double
    else: 
        return QVariant.String

    