# -*- coding: utf-8 -*-

"""
/***************************************************************************
  LineVectorLayer
                                 A QGIS plugin
 This software will be able to design the best route of one transmission line on a map.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-02-08
        copyright            : (C) 2020 by Ander Gutiérrez
        email                : angutiu@unirioja.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Ander Gutiérrez'
__date__ = '2020-02-08'
__copyright__ = '(C) 2020 by Ander Gutiérrez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *

import processing
from math import floor, sqrt
import queue
#********************************************************************************************
#********************************************************************************************
class LineVectorLayer:
    
    @staticmethod
    def ConvertPoint2RowCol(PointX, PointY, Raster):                        # Convierte una Coordenada en un Tuple con la Fila y Columna
        X_perPixel = Raster.rasterUnitsPerPixelX()                          # Se obtiene las Unidades X en una Columna o Píxel Vertical
        Y_perPixel = Raster.rasterUnitsPerPixelY()                          # Se obtiene las Unidades Y en una Fila o Pixel Horizontal
        Extent = Raster.dataProvider().extent()                             # Se obtiene la extensión del raster
                                                                                    
        Col = floor((PointX - Extent.xMinimum()) / X_perPixel)              # Se obtiene la columna del Raster en el que esta la Coord X
        Fil = floor((Extent.yMaximum() - PointY) / Y_perPixel)              # Se obtiene la fila del Raster en el que esta la Coord Y
        
        Fil_Col_List = []
        Fil_Col_List.append((Fil,Col))                                      # En esta lista se guarda la Fila Y Columna obtenida

        return Fil_Col_List
#****************************************************************************
    @staticmethod
    def GetBlocksRaster(Raster):                                            # Consigue y devuelve el bloque con los datos del Raster
        X_perPixel = Raster.rasterUnitsPerPixelX()                          # Se obtiene las Unidades X en una Columna o Píxel Vertical
        Y_perPixel = Raster.rasterUnitsPerPixelY()                          # Se obtiene las Unidades Y en una Fila o Pixel Horizontal
        
        ProviderRaster = Raster.dataProvider()
        Extent = ProviderRaster.extent()                                    # Se obtiene la extensión del raster
        
        Width = floor((Extent.xMaximum() - Extent.xMinimum()) / X_perPixel) # Columnas del Raster
        Height = floor((Extent.yMaximum() - Extent.yMinimum()) / Y_perPixel)# Filas del Raster

        Blocks = ProviderRaster.block(1, Extent, Width, Height)             # Se guarda en la variable los datos del Raster
        return Blocks
#****************************************************************************
    @staticmethod
    def ConvertBlock2Matriz(Bloque, feedback):                                        # Convierte el Bloque con datos del Raster en una Matriz
                                                                            
        BlockNegative = False
        Matriz = []
                                                                            # Bucle para hacer la matriz
        for i in range(Bloque.height()):                                    # Para las filas
            Matriz.append([])
            for j in range(Bloque.width()):                                 # Para las columnas
                if Bloque.isNoData(i, j) != True:
                    Matriz[i].append(Bloque.value(i, j))
                    if Bloque.value(i,j) < 0:                               # El método también avisa si hay algún valor negativo para que ...
                        BlockNegative = True                                # ... cancele el programa y dé Error
                else:
                    Matriz[i].append(None)                                  # Si no hay dato en el pixel, se rellena con None en la matriz
                if feedback.isCanceled():                                   # Si el proceso se cancela, se para la ejecución
                    return None, None

        return Matriz, BlockNegative
#****************************************************************************
    @staticmethod
    def ConvertPath2Points(Raster, MinPath, PointStart, PointEnd):          # Convierte el camino de Filas y Columnas en un Camino de Coords

        PathPoints = []
        for i in range(len(MinPath)):                                       # En este bucle se recorre toda la lista con la Filas y Columnas
            PathPoints.append(LineVectorLayer.ConvertRowCol2Point(MinPath[i], Raster))  # Y cada uno lo transforma en Coordenadas
        
        PathPoints[0].setX(PointStart.x())                                  # Se modifica Punto X e Y de Origen y Final del tramo correspondiente ..
        PathPoints[0].setY(PointStart.y())                                  # .. por temas de precisión.
        PathPoints[-1].setX(PointEnd.x())
        PathPoints[-1].setY(PointEnd.y())
        return PathPoints
#****************************************************************************
    @staticmethod
    def ConvertRowCol2Point(RowCol, Raster):                                # Método que se llama en el anterior. Se convierte la fila y columna ..
                                                                            # .. en Coordenadas
        X_perPixel = Raster.rasterUnitsPerPixelX()                          # Se obtiene las Unidades X en una Columna o Píxel Vertical                   
        Y_perPixel = Raster.rasterUnitsPerPixelY()                          # Se obtiene las Unidades Y en una Fila o Pixel Horizontal
        Extent = Raster.dataProvider().extent()                             # Se obtiene la extensión del raster

        X = (RowCol[1] + 0.5) * X_perPixel + Extent.xMinimum()              # Se convierte la columna en Coordenada X
        Y = Extent.yMaximum() - (RowCol[0] + 0.5) * Y_perPixel              # Se convierte la fila en Coordenada Y

        Coord = QgsPoint(X, Y)                                              # Se guardan las Coordenadas como tipo QgsPoint ( Para QGIS)
        return Coord
#********************************************************************************************
    def LeastPath (self, Matriz, FromRowCol, ToRowCol, End_RowCol, feedback = None ):
        Sqrt2 = sqrt(2)
        self.Matriz2 = Matriz
        CostAcc = {}                                                        # CostAcc es la variable Diccionario que almacenará todos los..
        CostAcc[FromRowCol] = 0                                            # .. costes acumulados según la ubicación (Fila Columna)
        Procedencia = {}                                                    # Procedenca es la variable Diccionario que almacenará la ..
        Procedencia[FromRowCol] = None                                     # ..procedencia de mínimo valor de cada ubicación (Fila Columna)

        if not LineVectorLayer.Valid_RowCol (self, FromRowCol):            # Se comprueba si la Fila Columna de partida es válido

            return None

        if not LineVectorLayer.Valid_RowCol (self, ToRowCol):              # Se comprueba si la Fila Columna de destino es válido

            return None

        if FromRowCol in ToRowCol:                                        # Se comprueba que la Fila Columna de partida y destino no sean el mismo

            return None
        
        StackFifo = queue.PriorityQueue()                                   # Se crea una pila FIFO donde se irá almacenando las Fila Columnas en..
        StackFifo.put((CostAcc[FromRowCol], FromRowCol))                  # .. los que se realizará la Matriz Transición
    
        Min_Difference = LineVectorLayer.Diff_Start2End(FromRowCol, End_RowCol)    # Estas tres líneas son para inicializar el progreso ..
        Total_Difference = Min_Difference                                                       # ..de la barra del Plugin en porcentaje
        feedback.setProgress((1 - Min_Difference / Total_Difference) * 100)                     # Siempre se compara contra el Fila Columna final del..
                                                                                                # .. recorrido total, no del tramo del momento

                                            # En el siguiente bucle es donde se busca el recorrido mínimo entre..
                                            # .. las Filas Columnas de Inicio y Destino
        while not StackFifo.empty():        # Mientras la pila no se quede vacía (ocurriría si se recorriese toda la Matriz)
            
            CurrentCost, CurrentRowCol = StackFifo.get()    # Se extrae de la pila, del tuple interesa la Fila Columna con la..
                                                            # .. que trabajará en dicha iteración
                                            # Este IF es para cancelar la ejecución si se pide Cancelación en el Plugin
                                            # Y si no se cancela, se calcula el progreso de la barra en porcentaje
            if feedback:                        
                if feedback.isCanceled():
                    return None 
                Current_Difference = LineVectorLayer.Diff_Start2End(CurrentRowCol, End_RowCol)  
                if Current_Difference < Min_Difference:                                                     
                    Min_Difference = Current_Difference
                    feedback.setProgress((1 - Min_Difference / Total_Difference) * 100)

            if CurrentRowCol == ToRowCol:                      # El bucle terminará, cuando el recorrido mínimo esté..
                break                                           # .. terminado y eso será cuando Fila Columna Actual..
                                                                # .. de la iteración y Final coincidan.
                                                            # Se realiza la Matriz Transición de la Fila Columna Actual.
                                                            # La Matriz Transición consiste en crear una matriz..
                                                            # .. con las celdas de alrededor de la Fila Columna Actual..
                                                            # .. y que además sean ubicaciones válidas dentro del Raster.

            Transition = LineVectorLayer.TransitionMatriz(self, CurrentRowCol)          
                                                                                        
                            # En este bucle For se recorre cada celda de la Matriz Transición para comprobar para..
                            # .. ir obteniendo posibles caminos mínimos. El posible camino que antes llegue al punto final..
                            # .. será el recorrido mínimo que se pretendía obtener para la resolución del método.                                    

                            # En el siguiente 'If Else' se pretende obtener la suma que supone recorrer desde el centro..
                            # .. de la ubicación actual hasta el centro del siguiente, en recto o en diagonal.
                            # Después, se calcula cuál es el Siguiente Coste Acumulado formado por el CostAcc hasta..
                            # .. la ubicación Actual en todo el recorrido, más el Nuevo Coste previamente calculado.

                            # En el último 'If Else' del bucle For, se compara lo siguiente, Si el Next Fila Columna ..
                            # ..que procede de la Matriz Transición NO se encuentra en CostAcc se entra. Se entra para..
                            # .. guardarlo. En caso de existir y dar Falso, la siguiente opción para entrar,
                            # Si el Next Coste Acumulado reciéntemente calculado, es inferior al Coste Acumulado que hay..
                            # .. hasta dicho Next Fila Columna, se entra. Esto último se hace porque, si NextCostAcc es ..
                            # .. inferior, quiere decir que existe un recorrido más mínimo que el guardado y hay que entrar..
                            # para guardarlo. Si no se entra significa que el ya guardado es más mínimo.

            for NextRowCol in Transition:                                                                   
                if NextRowCol[0] == CurrentRowCol[0] or NextRowCol[1] == CurrentRowCol[1]:
                   NewCost_Sumando = (Matriz[NextRowCol[0]][NextRowCol[1]] + Matriz[CurrentRowCol[0]][CurrentRowCol[1]])/2 
                else:
                    NewCost_Sumando = Sqrt2 * (Matriz[NextRowCol[0]][NextRowCol[1]] + Matriz[CurrentRowCol[0]][CurrentRowCol[1]])/2 
             
                NewCostAcc = CostAcc[CurrentRowCol] + NewCost_Sumando
                if NextRowCol not in CostAcc or NewCostAcc < CostAcc[NextRowCol]:   # Si se entra es porque existe un nuevo mínimo posible cammino y..
                    CostAcc[NextRowCol] = NewCostAcc                                # .. se guarda el nuevo CostAcc hasta el Next Fila Columna 
                    Procedencia[NextRowCol] = CurrentRowCol                         # .. de donde procede ese Next Fila Columna
                    StackFifo.put((CostAcc[NextRowCol], NextRowCol))                # .. se mete dicho CostAcc y Next Fila Columna en la pila FIFO

                                        # Al salir del bucle While, se ha encontrado ya el minimo recorrido hasta la Fila Columna final.
                                        # Entonces en el siguiente 'If Else' se formará en la lista MinPath dicho camino, que se encuentra..
                                        # .. almacenado en el diccionario Procedencia en una gran cantidad de posibles mínimos..
                                        # .. caminos que no llegaron hasta la Fila Columna final.

        if CurrentRowCol == ToRowCol:
            MinPath = []

            while CurrentRowCol != None:            
                MinPath.append(CurrentRowCol)
                CurrentRowCol = Procedencia[CurrentRowCol]

            MinPath.reverse()
            return MinPath
        else:
            return None
#****************************************************************************
    def Valid_RowCol (self, RowCol):     # Método para Validar una Fila Columna
        Row = RowCol[0]
        Col = RowCol[1]

        Height = len(self.Matriz2)
        Width = len (self.Matriz2[0])
                                        # Se valida si se cumplen estos todos métodos
        return ((LineVectorLayer.RowCol_InMatriz(Row, Col, Height, Width)) and (LineVectorLayer.ValueNoNone(self, Row, Col)))
#****************************************************************************       
    def RowCol_InMatriz (Row, Col, H, W):# En este método se comprueba que la Fila Columna..
                                         #  ..en cuestión se encuentra entre los límites..
                                         # .. del raster. Entre 0 y su máxima Fila y Columna.   

        return ((0 <= Row < H ) and (0 <= Col < W))
#****************************************************************************
    def ValueNoNone (self, Row, Col):   # Aquí se comprueba que dentro de la matriz,
                                        # la celda de dicha Ficha y Columna no..
                                        # .. contiene un valor No Data, vacío.

        if self.Matriz2[Row][Col] != None:
            return True
        else:
            return False
#****************************************************************************
    def TransitionMatriz(self, RowCol):# Función para conseguir la Matriz Transición
        Row = RowCol[0]
        Col = RowCol[1]
                                    # Matriz Transición
        PossibleTransition = [(Row + 1, Col), (Row, Col - 1), (Row - 1, Col), (Row, Col + 1),
                       (Row + 1, Col - 1), (Row + 1, Col + 1), (Row - 1, Col - 1), (Row - 1, Col + 1)]

        It = 0
        It_Matriz = 0
        DefinitiveTransition = []
                                    # Bucle While para comprobar que cada celda de..
                                    # .. la Matriz Transición es Válida.
                                    # Y si lo es, guardar dicha celda para..
                                    # .. su estudio en el mínimo recorrido.
        while It != 8:
            if LineVectorLayer.Valid_RowCol(self, PossibleTransition[It_Matriz]):
                DefinitiveTransition.append(PossibleTransition[It_Matriz])
            It_Matriz = It_Matriz + 1
            It = It + 1

        return DefinitiveTransition
#****************************************************************************    
    def Diff_Start2End (Current_RowCol, EndRowCol): # Método para conseguir la diferencia entre..
                                                    # .. la Fila Columna Actual y la Destino.        
        return (abs(Current_RowCol[0] - EndRowCol[0]) + abs(Current_RowCol[1] - EndRowCol[1]))
#*************************************************************************************************************
