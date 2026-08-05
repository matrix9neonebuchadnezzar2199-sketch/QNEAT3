# -*- coding: utf-8 -*-
"""
***************************************************************************
    ShortestPathPointToPoint.py
    ---------------------

    Partially based on QGIS3 network analysis algorithms.
    Copyright 2016 Alexander Bruy

    Date                 : February 2018
    Copyright            : (C) 2018 by Clemens Raffler
    Email                : clemens dot raffler at gmail dot com
***************************************************************************
"""

__author__ = 'Clemens Raffler'
__date__ = 'February 2018'
__copyright__ = '(C) 2018, Clemens Raffler'

__revision__ = '$Format:%H$'

import os
from collections import OrderedDict

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsGeometry,
                       QgsFields,
                       QgsField,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterPoint,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)

from QNEAT3.Qneat3Framework import Qneat3Network, Qneat3AnalysisPoint
from QNEAT3.Qneat3Utilities import getFeatureFromPointParameter, reconstruct_path_geometry
from QNEAT3.Qneat3Strings import (
    UIS,
    LOG,
    ja,
    NEO_PREFIX,
    ERR,
    log_msg,
    log_path_cost_breakdown,
)
from QNEAT3.Qneat3HelpJa import help_shortest_path_point_to_point
from QNEAT3.Qneat3ProcessingParams import (
    add_advanced_network_params,
    strategy_labels,
)

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class ShortestPathBetweenPoints(QgisAlgorithm):

    INPUT = 'INPUT'
    START_POINT = 'START_POINT'
    END_POINT = 'END_POINT'
    STRATEGY = 'STRATEGY'
    ENTRY_COST_CALCULATION_METHOD = 'ENTRY_COST_CALCULATION_METHOD'
    DIRECTION_FIELD = 'DIRECTION_FIELD'
    VALUE_FORWARD = 'VALUE_FORWARD'
    VALUE_BACKWARD = 'VALUE_BACKWARD'
    VALUE_BOTH = 'VALUE_BOTH'
    DEFAULT_DIRECTION = 'DEFAULT_DIRECTION'
    SPEED_FIELD = 'SPEED_FIELD'
    DEFAULT_SPEED = 'DEFAULT_SPEED'
    TOLERANCE = 'TOLERANCE'
    LINK_LENGTH_FIELD = 'LINK_LENGTH_FIELD'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(icon_path('icon_dijkstra_onetoone.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.ROUTING)

    def groupId(self):
        return 'networkanalysis'

    def name(self):
        return 'shortestpathpointtopoint'

    def displayName(self):
        return ja(NEO_PREFIX + '最短経路（点間）')

    def shortHelpString(self):
        return help_shortest_path_point_to_point()

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT,
            ja(UIS.NETWORK_LAYER),
            [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterPoint(
            self.START_POINT, ja(UIS.START_POINT)))
        self.addParameter(QgsProcessingParameterPoint(
            self.END_POINT, ja(UIS.END_POINT)))
        self.addParameter(QgsProcessingParameterEnum(
            self.STRATEGY,
            ja(UIS.OPTIMIZATION_CRITERION),
            strategy_labels(),
            defaultValue=0))

        add_advanced_network_params(self, self.INPUT)

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT,
            ja(UIS.OUTPUT_SHORTEST_PATH),
            QgsProcessing.TypeVectorLine))

    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        log_msg(feedback, LOG.ALG_INIT)

        network = self.parameterAsSource(parameters, self.INPUT, context)
        startPoint = self.parameterAsPoint(
            parameters, self.START_POINT, context, network.sourceCrs())
        endPoint = self.parameterAsPoint(
            parameters, self.END_POINT, context, network.sourceCrs())
        strategy = self.parameterAsEnum(parameters, self.STRATEGY, context)

        entry_cost_calc_method = self.parameterAsEnum(
            parameters, self.ENTRY_COST_CALCULATION_METHOD, context)
        directionFieldName = self.parameterAsString(
            parameters, self.DIRECTION_FIELD, context)
        forwardValue = self.parameterAsString(parameters, self.VALUE_FORWARD, context)
        backwardValue = self.parameterAsString(parameters, self.VALUE_BACKWARD, context)
        bothValue = self.parameterAsString(parameters, self.VALUE_BOTH, context)
        defaultDirection = self.parameterAsEnum(
            parameters, self.DEFAULT_DIRECTION, context)
        speedFieldName = self.parameterAsString(parameters, self.SPEED_FIELD, context)
        defaultSpeed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context)
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)

        analysisCrs = network.sourceCrs()

        input_qgspointxy_list = [startPoint, endPoint]
        input_points = [
            getFeatureFromPointParameter(startPoint, "始点"),
            getFeatureFromPointParameter(endPoint, "終点"),
        ]

        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        feedback.setProgress(10)
        net = Qneat3Network(
            network, input_qgspointxy_list, strategy,
            directionFieldName, forwardValue, backwardValue, bothValue,
            defaultDirection, analysisCrs, speedFieldName, defaultSpeed,
            tolerance, link_length_field, feedback)
        feedback.setProgress(40)

        list_analysis_points = [
            Qneat3AnalysisPoint(
                "point", feature, "point_id", net, net.list_tiedPoints[i],
                entry_cost_calc_method, feedback)
            for i, feature in enumerate(input_points)
        ]

        start_vertex_idx = list_analysis_points[0].network_vertex_id
        end_vertex_idx = list_analysis_points[1].network_vertex_id

        log_msg(feedback, LOG.PATH_CALC)
        feedback.setProgress(50)

        dijkstra_query = net.calcDijkstra(start_vertex_idx, 0)

        if dijkstra_query[0][end_vertex_idx] == -1:
            raise QgsProcessingException(ja(ERR.NO_PATH))

        path_elements = reconstruct_path_geometry(
            net.network,
            dijkstra_query[0],
            start_vertex_idx,
            end_vertex_idx,
            list_analysis_points[0].point_geom,
            list_analysis_points[1].point_geom,
        )
        if path_elements is None:
            raise QgsProcessingException(ja(ERR.NO_PATH))
        log_msg(feedback, LOG.PATH_TOTAL_NODES, count=len(path_elements))

        start_entry_cost = list_analysis_points[0].entry_cost
        end_exit_cost = list_analysis_points[1].entry_cost
        cost_on_graph = dijkstra_query[1][end_vertex_idx]
        total_cost = start_entry_cost + cost_on_graph + end_exit_cost
        log_path_cost_breakdown(
            feedback,
            net.strategy_int,
            start_entry_cost,
            cost_on_graph,
            end_exit_cost,
            total_cost,
        )

        log_msg(feedback, LOG.PATH_WRITE)
        feedback.setProgress(80)
        feat = QgsFeature()

        fields = QgsFields()
        fields.append(QgsField('start_id', QVariant.String, '', 254, 0))
        fields.append(QgsField('start_coordinates', QVariant.String, '', 254, 0))
        fields.append(QgsField('start_entry_cost', QVariant.Double, '', 20, 7))
        fields.append(QgsField('end_id', QVariant.String, '', 254, 0))
        fields.append(QgsField('end_coordinates', QVariant.String, '', 254, 0))
        fields.append(QgsField('end_exit_cost', QVariant.Double, '', 20, 7))
        fields.append(QgsField('cost_on_graph', QVariant.Double, '', 20, 7))
        fields.append(QgsField('total_cost', QVariant.Double, '', 20, 7))
        feat.setFields(fields)

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields,
            QgsWkbTypes.LineString, network.sourceCrs())

        feat['start_id'] = "A"
        feat['start_coordinates'] = startPoint.toString()
        feat['start_entry_cost'] = start_entry_cost
        feat['end_id'] = "B"
        feat['end_coordinates'] = endPoint.toString()
        feat['end_exit_cost'] = end_exit_cost
        feat['cost_on_graph'] = cost_on_graph
        feat['total_cost'] = total_cost
        geom = QgsGeometry.fromPolylineXY(path_elements)
        feat.setGeometry(geom)

        sink.addFeature(feat, QgsFeatureSink.FastInsert)
        log_msg(feedback, LOG.ALG_END)
        feedback.setProgress(100)
        results = {self.OUTPUT: dest_id}
        return results
