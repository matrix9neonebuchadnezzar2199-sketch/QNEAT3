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


def reconstruct_shortest_path_polyline(
    network,
    tree,
    start_vertex_id,
    end_vertex_id,
    start_point_geom,
    end_point_geom,
):
    """
    Dijkstra 木から始点→終点の折れ線（QgsPointXY のリスト）を構築する。

    Returns:
        list[QgsPointXY]: start_point_geom から end_point_geom へ。到達不能時は None。
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

    