# -*- coding: utf-8 -*-
"""
***************************************************************************
    OdMatrixFromLayersAsTable.py
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
from QNEAT3.Qneat3Utilities import getFeaturesFromQgsIterable, getFieldDatatype, getListOfPoints

from QNEAT3.Qneat3Strings import UIS, LOG, ja, NEO_PREFIX, log_msg, log_od_run_footer
from QNEAT3.Qneat3HelpJa import help_od_matrix_layers_table
from QNEAT3.Qneat3ProcessingParams import add_advanced_network_params, strategy_labels, entry_cost_labels

from QNEAT3.Qneat3Paths import icon_path
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm


class OdMatrixFromLayersAsTable(QgisAlgorithm):

    INPUT = 'INPUT'
    FROM_POINT_LAYER = 'FROM_POINT_LAYER'
    FROM_ID_FIELD = 'FROM_ID_FIELD'
    TO_POINT_LAYER = 'TO_POINT_LAYER'
    TO_ID_FIELD = 'TO_ID_FIELD'    
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
        return 'OdMatrixFromLayersAsTable'

    def displayName(self):
        return ja(NEO_PREFIX + 'OD 行列（レイヤ間・表 m:n）')

    def shortHelpString(self):
        return help_od_matrix_layers_table()

    
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
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.FROM_POINT_LAYER,
                                                              ja(UIS.FROM_POINT_LAYER),
                                                              [QgsProcessing.TypeVectorPoint]))
        
        self.addParameter(QgsProcessingParameterField(self.FROM_ID_FIELD,
                                                       ja(UIS.FROM_POINT_ID_FIELD),
                                                       None,
                                                       self.FROM_POINT_LAYER,
                                                       optional=False))
        
        self.addParameter(QgsProcessingParameterFeatureSource(self.TO_POINT_LAYER,
                                                      ja(UIS.TO_POINT_LAYER),
                                                      [QgsProcessing.TypeVectorPoint]))
        
        self.addParameter(QgsProcessingParameterField(self.TO_ID_FIELD,
                                                     ja(UIS.TO_POINT_ID_FIELD),
                                                     None,
                                                     self.TO_POINT_LAYER,
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
        from_points = self.parameterAsSource(parameters, self.FROM_POINT_LAYER, context) #QgsProcessingFeatureSource
        from_id_field = self.parameterAsString(parameters, self.FROM_ID_FIELD, context) #str
        to_points = self.parameterAsSource(parameters, self.TO_POINT_LAYER, context)
        to_id_field = self.parameterAsString(parameters, self.TO_ID_FIELD, context)
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
        
        #Points of both layers have to be merged into one layer --> then tied to the Qneat3Network
        #get point list of from layer
        from_coord_list = getListOfPoints(from_points)
        from_coord_list_length = len(from_coord_list)
        to_coord_list = getListOfPoints(to_points)

        merged_coords = from_coord_list + to_coord_list
        
        log_msg(feedback, LOG.ALG_BUILD_GRAPH)
        net = Qneat3Network(network, merged_coords, strategy, directionFieldName, forwardValue, backwardValue, bothValue, defaultDirection, analysisCrs, speedFieldName, defaultSpeed, tolerance, link_length_field, feedback)
        
        #read the merged point-list seperately for the two layers --> index at the first element of the second layer begins at len(firstLayer) and gets added the index of the current point of layer b.
        list_from_apoints = [Qneat3AnalysisPoint("from", feature, from_id_field, net, net.list_tiedPoints[i], entry_cost_calc_method, feedback) for i, feature in enumerate(getFeaturesFromQgsIterable(from_points))]
        list_to_apoints = [Qneat3AnalysisPoint("to", feature, to_id_field, net, net.list_tiedPoints[from_coord_list_length+i], entry_cost_calc_method, feedback) for i, feature in enumerate(getFeaturesFromQgsIterable(to_points))]
        
        feat = QgsFeature()
        fields = QgsFields()
        orig_id_field_data_type = getFieldDatatype(from_points, from_id_field)
        dest_id_field_data_type = getFieldDatatype(to_points, to_id_field)
        fields.append(QgsField('origin_id', orig_id_field_data_type, '', 254, 0))
        fields.append(QgsField('destination_id', dest_id_field_data_type, '', 254, 0))
        fields.append(QgsField('entry_cost', QVariant.Double, '', 20,7))
        fields.append(QgsField('network_cost', QVariant.Double, '', 20, 7))
        fields.append(QgsField('exit_cost', QVariant.Double, '', 20,7))
        fields.append(QgsField('total_cost', QVariant.Double, '', 20,7))
        feat.setFields(fields)
        
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.NoGeometry, network.sourceCrs())

        
        total_workload = float(len(from_coord_list)*len(to_coord_list))
        log_msg(feedback, LOG.OD_WORKLOAD, n=int(total_workload))
        
        
        current_workstep_number = 0
        pairs_ok = 0

        for start_point in list_from_apoints:
            #optimize in case of undirected (not necessary to call calcDijkstra as it has already been calculated - can be replaced by reading from list)
            dijkstra_query = net.calcDijkstra(start_point.network_vertex_id, 0)
            for query_point in list_to_apoints:
                if (current_workstep_number%1000)==0:
                    log_msg(feedback, LOG.OD_PROGRESS, n=current_workstep_number)
                if dijkstra_query[0][query_point.network_vertex_id] == -1:
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
                    feat['total_cost'] = network_cost + start_point.entry_cost + query_point.entry_cost
                    sink.addFeature(feat, QgsFeatureSink.FastInsert)  
                current_workstep_number=current_workstep_number+1
                feedback.setProgress((current_workstep_number/total_workload)*100)
                    
        log_msg(feedback, LOG.OD_TOTAL, n=current_workstep_number)
        log_od_run_footer(
            feedback, net.strategy_int, pairs_ok, int(total_workload)
        )

        log_msg(feedback, LOG.ALG_END)

        results = {}
        results[self.OUTPUT] = dest_id
        return results

