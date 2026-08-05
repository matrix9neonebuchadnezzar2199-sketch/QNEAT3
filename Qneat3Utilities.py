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

from qgis.core import QgsWkbTypes, QgsMessageLog, QgsVectorLayer, QgsFeature, QgsGeometry, QgsFields, QgsField, QgsFeatureRequest

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
    geom_index=None,
):
    """
    Dijkstra 木から始点→終点の経路（QgsPointXY のリスト）を構築する。

    geom_index（EdgeGeometryIndex）があれば各グラフ辺を元リンク形状でなぞる。
    見つからない辺は従来通り頂点間の直線にフォールバックする。
    entry/exit（点↔最寄り頂点）は設計通り直線のまま。

    Returns:
        tuple: (list[QgsPointXY] | None, int) — (経路, 直線フォールバックした辺数)。
        到達不能時は (None, 0)。
    """
    if tree[end_vertex_id] == -1:
        return None, 0
    if start_vertex_id == end_vertex_id:
        return [start_point_geom, end_point_geom], 0

    # 終点→始点へ木を遡り、(edge_id, from_vid, to_vid) を始点→終点順に並べる
    hops = []
    current = end_vertex_id
    max_hops = network.vertexCount() + 2
    for _ in range(max_hops):
        if current == start_vertex_id:
            break
        edge_id = tree[current]
        if edge_id < 0:
            return None, 0
        previous = predecessor_vertex_on_tree(network, edge_id, current)
        if previous < 0:
            return None, 0
        hops.append((edge_id, previous, current))
        current = previous
    else:
        return None, 0
    hops.reverse()

    points = [start_point_geom]
    fallback_count = 0
    for edge_id, from_vid, to_vid in hops:
        a = network.vertex(from_vid).point()
        b = network.vertex(to_vid).point()
        seg = None
        if geom_index is not None:
            seg = geom_index.lookup(
                (a.x(), a.y()), (b.x(), b.y()), network.edge(edge_id).cost(0)
            )
        if seg is None:
            if geom_index is not None:
                fallback_count += 1
            seg = [(a.x(), a.y()), (b.x(), b.y())]
        else:
            # 継ぎ目の連続性を保証するため両端はグラフ頂点座標に合わせる
            seg[0] = (a.x(), a.y())
            seg[-1] = (b.x(), b.y())
        points.extend(QgsPointXY(x, y) for x, y in seg[1:])
    points.append(end_point_geom)
    return points, fallback_count
        
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

    