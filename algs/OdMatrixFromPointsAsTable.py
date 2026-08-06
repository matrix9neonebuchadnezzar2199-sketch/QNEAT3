# -*- coding: utf-8 -*-
"""
***************************************************************************
    OdMatrixFromPointsAsTable.py
    ---------------------
        
    Partially based on QGIS3 network analysis algorithms. 
    Copyright 2016 Alexander Bruy    
    
    Date                 : February 2018
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

__author__ = 'Clemens Raffler'
__date__ = 'February 2018'
__copyright__ = '(C) 2018, Clemens Raffler'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from collections import OrderedDict

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition)

from qgis.analysis import (QgsVectorLayerDirector)

from QNEAT3.Qneat3Framework import Qneat3Network, Qneat3AnalysisPoint
from QNEAT3.Qneat3Utilities import getFeaturesFromQgsIterable, getFieldDatatype, log_far_tie_summary

from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX, log_msg, log_od_run_footer
from QNEAT3.Qneat3HelpJa import help_od_matrix_points_table
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class OdMatrixFromPointsAsTable(QgisAlgorithm):

    INPUT = 'INPUT'
    POINTS = 'POINTS'
    ID_FIELD = 'ID_FIELD'    
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
        return QIcon(icon_path('icon_matrix.svg'))

    def group(self):
        return ja(NEO_PREFIX + UIS.DISTANCE_MATRICES)

    def groupId(self):
        return 'networkbaseddistancematrices'
    
    def name(self):
        return 'OdMatrixFromPointsAsTable'

    def displayName(self):
        return ja(NEO_PREFIX + 'OD 行列（ポイント・表 n:n）')

    def shortHelpString(self):
        return help_od_matrix_points_table()

    
    def print_typestring(self, var):
        return "Type:"+str(type(var))+" repr: "+var.__str__()

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        self.DIRECTIONS = OrderedDict([
            (ja(UIS.DIR_FORWARD), QgsVectorLayerDirector.DirectionForward),
            (ja(UIS.DIR_BACKWARD), QgsVectorLayerDirector.DirectionBackward),
            (ja(UIS.DIR_BOTH), QgsVectorLayerDirector.DirectionBoth)])

        self.STRATEGIES = strategy_labels()

        self.ENTRY_COST_CALCULATION_METHODS = entry_cost_labels(include_ellipsoidal=True)


        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
                                                              ja(UIS.NETWORK_LAYER),
                                                              [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINTS,
                                                              ja(UIS.POINT_LAYER),
                                                              [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterField(self.ID_FIELD,
                                                       ja(UIS.UNIQUE_POINT_ID),
                                                       None,
                                                       self.POINTS,
                                                       optional=False))
        self.addParameter(QgsProcessingParameterEnum(self.STRATEGY,
                                                     ja(UIS.OPTIMIZATION_CRITERION),
                                                     self.STRATEGIES,
                                                     defaultValue=0))

        add_advanced_network_params(self, self.INPUT)

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, ja(UIS.OUTPUT_OD_MATRIX), QgsProcessing.TypeVectorLine), True)

    def processAlgorithm(self, parameters, context, feedback):
        log_msg(feedback, LOG.ALG_START, name=self.displayName())
        network = self.parameterAsSource(parameters, self.INPUT, context) #QgsProcessingFeatureSource
        points = self.parameterAsSource(parameters, self.POINTS, context) #QgsProcessingFeatureSource
        id_field = self.parameterAsString(parameters, self.ID_FIELD, context) #str
        strategy = self.parameterAsEnum(parameters, self.STRATEGY, context) #int
        
        entry_cost_calc_method = self.parameterAsEnum(parameters, self.ENTRY_COST_CALCULATION_METHOD, context) #int
        directionFieldName = self.parameterAsString(parameters, self.DIRECTION_FIELD, context) #str (empty if no field given)
        forwardValue = self.parameterAsString(parameters, self.VALUE_FORWARD, context) #str
        backwardValue = self.parameterAsString(parameters, self.VALUE_BACKWARD, context) #str
        bothValue = self.parameterAsString(parameters, self.VALUE_BOTH, context) #str
        defaultDirection = self.parameterAsEnum(parameters, self.DEFAULT_DIRECTION, context) #int
        speedFieldName = self.parameterAsString(parameters, self.SPEED_FIELD, context) #str
        defaultSpeed = self.parameterAsDouble(parameters, self.DEFAULT_SPEED, context) #float
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        link_length_field = self.parameterAsString(parameters, self.LINK_LENGTH_FIELD, context)
        
        analysisCrs = network.sourceCrs()
        
        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        net = Qneat3Network(network, points, strategy, directionFieldName, forwardValue, backwardValue, bothValue, defaultDirection, analysisCrs, speedFieldName, defaultSpeed, tolerance, link_length_field, feedback)
        
        list_analysis_points = [Qneat3AnalysisPoint("point", feature, id_field, net, net.list_tiedPoints[i], entry_cost_calc_method, feedback) for i, feature in enumerate(getFeaturesFromQgsIterable(net.input_points))]
        
        feat = QgsFeature()
        fields = QgsFields()
        output_id_field_data_type = getFieldDatatype(points, id_field)
        fields.append(QgsField('origin_id', output_id_field_data_type, '', 254, 0))
        fields.append(QgsField('destination_id', output_id_field_data_type, '', 254, 0))
        fields.append(QgsField('entry_cost', QVariant.Double, '', 20,7))
        fields.append(QgsField('network_cost', QVariant.Double, '', 20, 7))
        fields.append(QgsField('exit_cost', QVariant.Double, '', 20,7))
        fields.append(QgsField('total_cost', QVariant.Double, '', 20,7))
        feat.setFields(fields)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.NoGeometry, network.sourceCrs())

        log_far_tie_summary(list_analysis_points, feedback)

        total_workload = float(pow(len(list_analysis_points),2))
        log_msg(feedback, LOG.OD_WORKLOAD, n=int(total_workload))
        
        
        current_workstep_number = 0
        pairs_ok = 0

        for start_point in list_analysis_points:
            #optimize in case of undirected (not necessary to call calcDijkstra as it has already been calculated - can be replaced by reading from list)
            dijkstra_query = net.calcDijkstra(start_point.network_vertex_id, 0)
            for query_point in list_analysis_points:
                if (current_workstep_number%1000)==0:
                    log_msg(feedback, LOG.OD_PROGRESS, n=current_workstep_number)
                if query_point.point_id == start_point.point_id:
                    pairs_ok += 1
                    feat['origin_id'] = start_point.point_id
                    feat['destination_id'] = query_point.point_id
                    feat['entry_cost'] = 0.0
                    feat['network_cost'] = 0.0
                    feat['exit_cost'] = 0.0
                    feat['total_cost'] = 0.0
                    sink.addFeature(feat, QgsFeatureSink.FastInsert)
                elif query_point.network_vertex_id == start_point.network_vertex_id:
                    # 別点が同一頂点に結線: 到達不能ではなく graph コスト 0 + entry/exit
                    pairs_ok += 1
                    feat['origin_id'] = start_point.point_id
                    feat['destination_id'] = query_point.point_id
                    feat['entry_cost'] = start_point.entry_cost
                    feat['network_cost'] = 0.0
                    feat['exit_cost'] = query_point.entry_cost
                    feat['total_cost'] = start_point.entry_cost + query_point.entry_cost
                    sink.addFeature(feat, QgsFeatureSink.FastInsert)
                elif dijkstra_query[0][query_point.network_vertex_id] == -1:
                    feat['origin_id'] = start_point.point_id
                    feat['destination_id'] = query_point.point_id
                    feat['entry_cost'] = None
                    feat['network_cost'] = None
                    feat['exit_cost'] = None
                    feat['total_cost'] = None
                    sink.addFeature(feat, QgsFeatureSink.FastInsert)
                else:
                    pairs_ok += 1
                    network_cost = dijkstra_query[1][query_point.network_vertex_id]
                    feat['origin_id'] = start_point.point_id
                    feat['destination_id'] = query_point.point_id
                    feat['entry_cost'] = start_point.entry_cost
                    feat['network_cost'] = network_cost
                    feat['exit_cost'] = query_point.entry_cost
                    feat['total_cost'] = start_point.entry_cost + network_cost + query_point.entry_cost
                    sink.addFeature(feat, QgsFeatureSink.FastInsert)  
                current_workstep_number=current_workstep_number+1
                feedback.setProgress(current_workstep_number/total_workload)
                    
        log_msg(feedback, LOG.OD_TOTAL, n=current_workstep_number)
        log_od_run_footer(
            feedback, net.strategy_int, pairs_ok, int(total_workload)
        )

        log_msg(feedback, LOG.ALG_END)

        results = {}
        results[self.OUTPUT] = dest_id
        return results

