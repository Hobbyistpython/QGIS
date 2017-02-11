# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MAPIR_ProcessingDockWidget
                                 A QGIS plugin
 Widget for processing images captured by MAPIR cameras
                             -------------------
        begin                : 2016-09-26
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Peau Productions
        email                : ethan@peauproductions.com
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

import os
os.umask(0)
import sys
import shutil
from zipfile import ZipFile
from PyQt4 import uic, QtGui
from PyQt4.Qt import *
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import *
# from qgis.core import QgsMessageLog

from scipy import stats
import numpy as np
import subprocess


modpath = os.path.dirname(os.path.realpath(__file__))

if sys.platform == "win32": #Windows OS
        sys.path.insert(1, modpath)
      # pypath = os.path.split(os.path.split(sys.executable)[0])[0] + os.sep + "apps" + os.sep + "Python27"
      # if not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "exiftool.exe")\
      #        or not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "dcraw.exe")\
      #        or not os.path.exists(pypath + os.sep + "Scripts" + os.sep + "cygwin1.dll")\
      #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "exiftool.py")\
      #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "exiftool.pyc")\
      #        or not os.path.exists(pypath + os.sep + "Lib" + os.sep + "site-packages" + os.sep + "cv2.pyd"):
      #    os.chmod(pypath,0777)
      #    shutil.copy(modpath + os.sep + "exiftool.exe", pypath + os.sep + "Scripts")
      #    shutil.copy(modpath + os.sep + "dcraw.exe", pypath + os.sep + "Scripts")
      #    shutil.copy(modpath + os.sep + "cygwin1.dll", pypath + os.sep + "Scripts")
      #    shutil.copy(modpath + os.sep + "exiftool.py", pypath + os.sep + "Lib" + os.sep + "site-packages")
      #    shutil.copy(modpath + os.sep + "exiftool.pyc", pypath + os.sep + "Lib" + os.sep + "site-packages")
      #    shutil.copy(modpath + os.sep + "cv2.pyd", pypath + os.sep + "Lib" + os.sep + "site-packages")

elif sys.platform == "darwin": #Mac OS
      if not os.path.exists(r'/usr/local/bin/brew'):
            subprocess.call([r'/usr/bin/ruby', r'-e', r'"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'])
            subprocess.call([r'/usr/local/bin/brew',r'tap',r'homebrew/science'])
      if not os.path.exists(r'/usr/local/bin/dcraw'):
            subprocess.call([r'/usr/local/bin/brew',r'install',r'dcraw'])

      if not os.path.exists(r'/usr/local/bin/exiftool'):
            subprocess.call([r'/usr/local/bin/brew',r'install',r'exiftool'])

      if not os.path.exists(r'/usr/local/bin/opencv'):
            subprocess.call([r'/usr/local/bin/brew',r'install',r'opencv'])
      sys.path.append(r'/usr/local/bin')
      sys.path.append(r'/usr/local/bin/dcraw')
      sys.path.append(r'/usr/local/bin/exiftool')
      sys.path.append(r'/usr/local/bin/opencv')
      
from osgeo import gdal
import cv2
import glob

if sys.platform == "win32":
      import exiftool
      exiftool.executable = modpath + os.sep + "exiftool.exe"

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_base.ui'))
# MODAL_CLASS, _ = uic.loadUiType(os.path.join(
#     os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_modal.ui'))


class MAPIR_ProcessingDockWidget(QtGui.QDockWidget, FORM_CLASS):
    BASE_COEFF_SURVEY2_RED_JPG = [-2.55421832, 16.01240929, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY2_GREEN_JPG = [0.0, 0.0, -0.60437250, 4.82869470, 0.0, 0.0]
    BASE_COEFF_SURVEY2_BLUE_JPG = [0.0, 0.0, 0.0, 0.0, -0.39268985, 2.67916884]
    BASE_COEFF_SURVEY2_NDVI_JPG = [-0.29870245, 6.51199915, 0.0, 0.0, -0.65112026, 10.30416005]
    BASE_COEFF_SURVEY2_NIR_JPG = [-0.46967653, 7.13619139, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY1_NDVI_JPG = [-6.33770486888, 331.759383023, 0.0, 0.0, -0.6931339436, 51.3264675118]
    BASE_COEFF_SURVEY2_RED_TIF = [-5.09645820, 0.24177528, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_SURVEY2_GREEN_TIF = [0.0, 0.0, -1.39528479, 0.07640011, 0.0, 0.0]
    BASE_COEFF_SURVEY2_BLUE_TIF = [0.0, 0.0, 0.0, 0.0, -0.67299134, 0.03943339]
    BASE_COEFF_SURVEY2_NDVI_TIF = [-0.60138990, 0.14454211, 0.0, 0.0, -3.51691589, 0.21536524]
    BASE_COEFF_SURVEY2_NIR_TIF = [-2.24216724, 0.12962333, 0.0, 0.0, 0.0, 0.0 ]
    BASE_COEFF_DJIX3_NDVI_JPG = [-0.34430543, 4.63184993, 0.0, 0.0, -0.49413940, 16.36429964]
    BASE_COEFF_DJIX3_NDVI_TIF = [-0.74925346, 0.01350319, 0.0, 0.0, -0.77810008, 0.03478272]
    BASE_COEFF_DJIPHANTOM4_NDVI_JPG = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM4_NDVI_TIF = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM3_NDVI_JPG = [-1.54494979, 3.44708472, 0.0, 0.0, -1.40606832, 6.35407929]
    BASE_COEFF_DJIPHANTOM3_NDVI_TIF = [-1.37495554, 0.01752340, 0.0, 0.0, -1.41073753, 0.03700812]

    capturing = False
    SQ_TO_TARG = 2.1875
    SQ_TO_SQ = 5.0
    TARGET_LENGTH = 2.0
    TARG_TO_TARG = 2.6
    dialog = None
    imcols = 4608
    imrows = 3456
    imsize = imcols * imrows
    closingPlugin = pyqtSignal()
    firstpass = True
    useqr = False
    qrcoeffs = [] #  Red Intercept, Red Slope,  Green Intercept, Green Slope, Blue Intercept, Blue Slope
    refvalues = {
        "660/850":[[87.032549, 52.135779, 23.664799],[0, 0, 0],[84.63514, 51.950608, 22.795518]],
        "446/800":[[84.19608509,52.0440145,23.0113958],[0,0,0],[86.45652801,50.37779363,23.59041624]],
        "850":[[84.63514, 51.950608, 22.795518], [0, 0, 0],[0, 0, 0]],
        "808":[[0,0,0],[0,0,0],[0,0,0]],
        "650":[[87.032549, 52.135779, 23.664799],[0, 0, 0],[0, 0, 0]],
        "548":[[0, 0, 0],[87.415089, 51.734381, 24.032515],[0, 0, 0]],
        "450":[[0, 0, 0],[0, 0, 0],[86.469794, 50.392915, 23.565447]]
    }

    pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                     "greenmax": 0.0, "greenmin": 65535.0,
                     "bluemax": 0.0, "bluemin": 65535.0}

    def __init__(self, parent=None):
        """Constructor."""
        super(MAPIR_ProcessingDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)



    #########Pre-Process Steps: Start#################
    def on_PreProcessInButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.PreProcessInFolder.setText(QtGui.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.PreProcessInFolder.text())
    def on_PreProcessOutButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.PreProcessOutFolder.setText(QtGui.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.PreProcessOutFolder.text())
    def on_PreProcessButton_released(self):
        if self.PreProcessCameraModel.currentIndex() == -1:
            self.PreProcessLog.append("Attention! Please select a camera model.\n")
        else:
            pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                             "greenmax": 0.0, "greenmin": 65535.0,
                             "bluemax": 0.0, "bluemin": 65535.0}

                # self.PreProcessLog.append(r'Extracting vignette corection data')
            if not os.path.exists(modpath + os.sep + r'Vig'):
                os.mkdir(modpath + os.sep + r'Vig')
            vigfolder = modpath + os.sep + r'Vig'
            with ZipFile(modpath + os.sep + r'Vig.zip') as vigzip:
                vigzip.extractall(vigfolder)
            DCfolder = vigfolder + os.sep + r'DC'
            FFfolder = vigfolder + os.sep + r'FF'
            if not os.path.exists(DCfolder + os.sep + r'Proc'):
                os.mkdir(DCfolder + os.sep + r'Proc')
            if not os.path.exists(FFfolder + os.sep + r'Proc'):
                os.mkdir(FFfolder + os.sep + r'Proc')

            if self.PreProcessCameraModel.currentIndex() == 0:
                self.preProcessHelper(DCfolder + os.sep + r'ndvi', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'ndvi', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 1:
                self.preProcessHelper(DCfolder + os.sep + r'rgb', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'rgb', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 2:
                self.preProcessHelper(DCfolder + os.sep + r'nir', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'nir', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 3:
                self.preProcessHelper(DCfolder + os.sep + r'red', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'red', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 4:
                self.preProcessHelper(DCfolder + os.sep + r'green', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'green', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 5:
                self.preProcessHelper(DCfolder + os.sep + r'blue', DCfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
                pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                                 "greenmax": 0.0, "greenmin": 65535.0,
                                 "bluemax": 0.0, "bluemin": 65535.0}

                self.preProcessHelper(FFfolder + os.sep + r'blue', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 7:
                # self.preProcessHelper(DCfolder + r'FC350', DCfolder + os.sep + 'Proc', pixel_min_max,
                #                       customerdata=False)
                self.preProcessHelper(FFfolder + os.sep + r'FC350', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 8:
                # self.preProcessHelper(DCfolder + r'FC330', DCfolder + os.sep + 'Proc', pixel_min_max,
                #                       customerdata=False)
                self.preProcessHelper(FFfolder + os.sep + r'FC330', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 9:
                # self.preProcessHelper(DCfolder + r'FC300X', DCfolder + os.sep + 'Proc', pixel_min_max,
                #                       customerdata=False)
                self.preProcessHelper(FFfolder + os.sep + r'FC300X', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            elif self.PreProcessCameraModel.currentIndex() == 10:
                # self.preProcessHelper(DCfolder + r'FC300S', DCfolder + os.sep + 'Proc', pixel_min_max,
                #                       customerdata=False)
                self.preProcessHelper(FFfolder + os.sep + r'FC300S', FFfolder + os.sep + r'Proc', pixel_min_max,
                                      customerdata=False)
            else:
                self.PreProcessLog.append(r'Vignette correction not yet available for selected camera model.')

            pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                             "greenmax": 0.0, "greenmin": 65535.0,
                             "bluemax": 0.0, "bluemin": 65535.0}

            infolder = self.PreProcessInFolder.text()
            outfolder = self.PreProcessOutFolder.text()

            self.PreProcessLog.append("Input folder: " + infolder)
            self.PreProcessLog.append("Output folder: " + outfolder)
            self.preProcessHelper(infolder, outfolder, pixel_min_max)
            self.PreProcessLog.append("Finished Processing Images.")
            if os.path.exists(modpath + os.sep + 'Vig'):
                shutil.rmtree(modpath + os.sep + 'Vig')

# Pre-Process Steps: End

# Calibration Steps: Start
    def on_CalibrationInButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationInFolder.setText(QtGui.QFileDialog.getExistingDirectory(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationInFolder.text())
    def on_CalibrationQRButton_released(self):
        with open(modpath + os.sep + "instring.txt", "r+") as instring:
            self.CalibrationQRFile.setText(QtGui.QFileDialog.getOpenFileName(directory=instring.read()))
            instring.truncate(0)
            instring.seek(0)
            instring.write(self.CalibrationQRFile.text())
    def on_CalibrationGenButton_released(self):
        if self.CalibrationCameraModel.currentIndex() == -1:
            self.CalibrationLog.append("Attention! Please select a camera model.\n")
        elif len(self.CalibrationQRFile.text()) > 0:
            self.qrcoeffs = self.findQR(self.CalibrationQRFile.text())
            self.useqr = True
        else:
            self.CalibrationLog.append("Attention! Please select a target image.\n")
    def on_CalibrateButton_released(self):
        if self.CalibrationCameraModel.currentIndex() == -1:
            self.CalibrationLog.append("Attention! Please select a camera model.\n")
        elif len(self.CalibrationInFolder.text()) <= 0:
            self.CalibrationLog.append("Attention! Please select a calibration folder.\n")
        else:
            self.firstpass = True
            # self.CalibrationLog.append("CSV Input: \n" + str(self.refvalues))
            # self.CalibrationLog.append("Calibration button pressed.\n")
            calfolder = self.CalibrationInFolder.text()
            # self.CalibrationLog.append("Calibration target folder is: " + calfolder + "\n")
            files_to_calibrate = []
            os.chdir(calfolder)
            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
            files_to_calibrate.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
            #self.CalibrationLog.append("Files to calibrate[0]: " + files_to_calibrate[0])
            pixel_min_max = {"redmax" : 0.0, "redmin" : 65535.0,
                             "greenmax" : 0.0, "greenmin" : 65535.0,
                             "bluemax" : 0.0, "bluemin" : 65535.0}
            if "tif" or "TIF" or "jpg" or "JPG" in files_to_calibrate[0]:
                # self.CalibrationLog.append("Found files to Calibrate.\n")
                foldercount = 1
                endloop = False
                while endloop is False:
                    outdir = calfolder + os.sep + "Calibrated_" + str(foldercount)
                    if os.path.exists(outdir):
                        foldercount += 1
                    else:
                        os.mkdir(outdir)
                        endloop = True

                for calpixel in files_to_calibrate:

                    img = cv2.imread(calpixel, -1)


                    if self.CalibrationCameraModel.currentIndex() == 5: #Survey1_NDVI
                        # img = img.astype('float')

                        img[:, :, 0] = img[:, :, 0] - ((img[:, :, 2] / 5) * 4)
                    elif self.CalibrationCameraModel.currentIndex() == 0 or self.CalibrationCameraModel.currentIndex() > 9: #Survey2 NDVI, DJI NDVI cameras
                        # img = img.astype('float')

                        img[:, :, 2] = img[:, :, 2] - ((img[:, :, 0] / 5) * 4)
                    # these are a little confusing, but the check to find the highest and lowest pixel value
                    # in each channel in each image and keep the highest/lowest value found.
                    pixel_min_max["redmax"] = max(img[:, :, 2].max(), pixel_min_max["redmax"])
                    pixel_min_max["redmin"] = min(img[:, :, 2].min(), pixel_min_max["redmin"])
                    pixel_min_max["greenmax"] = max(img[:, :, 1].max(), pixel_min_max["greenmax"])
                    pixel_min_max["greenmin"] = min(img[:, :, 1].min(), pixel_min_max["greenmin"])
                    pixel_min_max["bluemax"] = max(img[:, :, 0].max(), pixel_min_max["bluemax"])
                    pixel_min_max["bluemin"] = min(img[:, :, 0].min(), pixel_min_max["bluemin"])


                if self.useqr == True:
                    pixel_min_max["redmax"] = pixel_min_max["redmax"] * self.qrcoeffs[1] + self.qrcoeffs[0]
                    pixel_min_max["redmin"] = pixel_min_max["redmin"] * self.qrcoeffs[1] + self.qrcoeffs[0]
                    pixel_min_max["greenmax"] = pixel_min_max["greenmax"] * self.qrcoeffs[3] + self.qrcoeffs[2]
                    pixel_min_max["greenmin"] = pixel_min_max["greenmin"] * self.qrcoeffs[3] + self.qrcoeffs[2]
                    pixel_min_max["bluemax"] = pixel_min_max["bluemax"] * self.qrcoeffs[5] + self.qrcoeffs[4]
                    pixel_min_max["bluemin"] = pixel_min_max["bluemin"] * self.qrcoeffs[5] + self.qrcoeffs[4]

                else:
                    if self.CalibrationCameraModel.currentIndex() == 5:  # Survey1_NDVI
                        if "tif" or "TIF" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[1])\
                                + self.BASE_COEFF_SURVEY1_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[1])\
                                + self.BASE_COEFF_SURVEY1_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[3])\
                                + self.BASE_COEFF_SURVEY1_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[3])\
                                + self.BASE_COEFF_SURVEY1_NDVI_TIF[2]
                        elif "jpg" or "JPG" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1])\
                                + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1])\
                                + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3])\
                                + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3])\
                                + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                    elif self.CalibrationCameraModel.currentIndex() == 0:
                        if "tif" or "TIF" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1])\
                                + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1])\
                                + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3])\
                                + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3])\
                                + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                        elif "jpg" or "JPG" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1])\
                                + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1])\
                                + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3])\
                                + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3])\
                                + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                    elif self.CalibrationCameraModel.currentIndex() == 10:
                        if "tif" or "TIF" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                        elif "jpg" or "JPG" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1])\
                                + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1])\
                                + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3])\
                                + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3])\
                                + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                    elif self.CalibrationCameraModel.currentIndex() == 11:
                        if "tif" or "TIF" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                        elif "jpg" or "JPG" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[3])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[3])\
                                + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                    elif self.CalibrationCameraModel.currentIndex() == 12:
                        if "tif" or "TIF" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                        elif "jpg" or "JPG" in calpixel:
                            pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                            pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                            pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                            pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[3])\
                                + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]

                for calfile in files_to_calibrate:
                    
                    cameramodel = self.CalibrationCameraModel.currentIndex()
                    if self.useqr is True:
                        # self.CalibrationLog.append("Using QR")
                        self.CalibratePhotos(calfile, self.qrcoeffs, pixel_min_max, outdir)
                    else:
                        # self.CalibrationLog.append("NOT Using QR")
                        if cameramodel == 0: # Survey2 NDVI
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_SURVEY2_NDVI_TIF, pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NDVI_JPG, pixel_min_max, outdir)
                        elif cameramodel == 1:# Survey2 NIR
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_SURVEY2_NIR_TIF, pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NIR_JPG, pixel_min_max, outdir)
                        elif cameramodel == 2:# Survey2 RED
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_SURVEY2_RED_TIF, pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_RED_JPG, pixel_min_max, outdir)
                        elif cameramodel == 3:# Survey2 GREEN
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_SURVEY2_GREEN_TIF, pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_GREEN_JPG, pixel_min_max, outdir)
                        elif cameramodel == 4:# Survey2 BLUE
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_SURVEY2_BLUE_TIF,pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_BLUE_JPG, pixel_min_max, outdir)
                        elif cameramodel == 5:# Survey1 NDVI
                            if "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY1_NDVI_JPG, pixel_min_max, outdir)
                        elif cameramodel == 10:# DJI X3 NDVI
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_DJIX3_NDVI_TIF,pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_DJIX3_NDVI_JPG, pixel_min_max, outdir)
                        elif cameramodel == 11:# DJI Phantom3 NDVI
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF,pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG, pixel_min_max, outdir)
                        elif cameramodel == 12:# DJI PHANTOM4 NDVI
                            if "TIF" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile,self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF,pixel_min_max, outdir)
                            elif "JPG" in calfile.split('.')[2].upper():
                                self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM3_NDVI_JPG, pixel_min_max, outdir)
                        else:
                            self.CalibrationLog.append("No default calibration data for selected camera model. Please please supply a MAPIR Reflectance Target to proceed.\n")
                            break
                self.CalibrationLog.append("Finished Calibrating " + str(len(files_to_calibrate)) + " images\n")

    def CalibratePhotos(self, photo, coeffs, minmaxes, output_directory):
        refimg = cv2.imread(photo, -1)

        ### split channels (using cv2.split caused too much overhead and made the host program crash)
        blue = refimg[:, :, 0]
        green = refimg[:, :, 1]
        red = refimg[:, :, 2]


        ### find the maximum and minimum pixel values over the entire directory.
        if self.CalibrationCameraModel.currentIndex() == 5: ###Survey1 NDVI
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            blue = refimg[:, :, 0] - (refimg[:, :, 2] * 0.80)# Subtract the NIR bleed over from the blue channel
        elif self.CalibrationCameraModel.currentIndex() == 1 \
                or self.CalibrationCameraModel.currentIndex() == 2 \
                or self.CalibrationCameraModel.currentIndex() == 6 \
                or self.CalibrationCameraModel.currentIndex() == 7:
            ### red and NIR
            maxpixel = minmaxes["redmax"]
            minpixel = minmaxes["redmin"]
        elif self.CalibrationCameraModel.currentIndex() == 3 or self.CalibrationCameraModel.currentIndex() == 8:
            ### green
            maxpixel = minmaxes["greenmax"]
            minpixel = minmaxes["greenmin"]
        elif self.CalibrationCameraModel.currentIndex() == 4 or self.CalibrationCameraModel.currentIndex() == 9:
            ### blue
            maxpixel = minmaxes["bluemax"]
            minpixel = minmaxes["bluemin"]
        else: ###Survey2 NDVI or any DJI ndvi
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            red = refimg[:, :, 2] - (refimg[:, :, 0] * 0.80)# Subtract the NIR bleed over from the red channel



    ### Calibrate pixels based on the default reflectance values (or the values gathered from the MAPIR reflectance target)
        red = (red * coeffs[1]) + coeffs[0]
        green = (green * coeffs[3]) + coeffs[2]
        blue = (blue * coeffs[5]) + coeffs[4]

    ### Scale calibrated values back down to a useable range (Adding 1 to avaoid 0 value pixels, as they will cause a
    #### devide by zero case when creating an index image.
        if photo.split('.')[2].upper() == "JPG" or photo.split('.')[2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Entering JPG")
            red = (((red - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
            green = (((green - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
            blue = (((blue - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
        else:
            red = (((red - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)
            green = (((green - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)
            blue = (((blue - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)


        if photo.split('.')[2].upper() == "JPG": #Remove the gamma correction that is automaticall applied to JPGs
            self.CalibrationLog.append("Removing Gamma")
            red = np.power(red, 1/2.2)
            green = np.power(green, 1/2.2)
            blue = np.power(blue, 1/2.2)

    ### Merge the channels back into a single image
        refimg = cv2.merge((blue, green, red))

    ### If the image is a .tiff then change it to a 16 bit color image
        if "TIF" in photo.split('.')[2].upper() and not self.Tiff2JpgBox.checkState() > 0:
            refimg = refimg.astype("uint16")


        if self.CalibrationCameraModel.currentIndex() == 0 \
                or self.CalibrationCameraModel.currentIndex() == 5 \
                or self.CalibrationCameraModel.currentIndex() >= 10:
            ### Remove green information if NDVI camera
            refimg[:, :, 1] = 1
        elif self.CalibrationCameraModel.currentIndex() == 1 \
                or self.CalibrationCameraModel.currentIndex() == 2 \
                or self.CalibrationCameraModel.currentIndex() == 6 \
                or self.CalibrationCameraModel.currentIndex() == 7:
            ### Remove blue and green information if NIR or Red camera
            refimg[:, :, 0] = 1
            refimg[:, :, 1] = 1
        elif self.CalibrationCameraModel.currentIndex() == 3 or self.CalibrationCameraModel.currentIndex() == 8:
            ### Remove blue and red information if GREEN camera
            refimg[:, :, 0] = 1
            refimg[:, :, 2] = 1
        elif self.CalibrationCameraModel.currentIndex() == 4 or self.CalibrationCameraModel.currentIndex() == 9:
            ### Remove red and green information if BLUE camera
            refimg[:, :, 1] = 1
            refimg[:, :, 2] = 1


        if self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Making JPG")
            cv2.imencode(".jpg", refimg)
            cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED.JPG", refimg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED.JPG", refimg)

            self.copyExif(photo, output_directory + photo.split('.')[1] + "_CALIBRATED.JPG")
            # if self.IndexBox.checkState() > 0:
            #     indeximg = (blue - red) / (blue + red)
            #     indeximg = indeximg.astype("float32")
            #     cv2.imwrite(output_directory + photo.split('.')[1] + "_Indexed.JPG", indeximg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            #     self.copyExif(photo, output_directory + photo.split('.')[1] + "_Indexed.JPG")
            #todo See if JPG can store geotiff metadata
        else:
            newimg = output_directory + photo.split('.')[1] + "_CALIBRATED." + photo.split('.')[2]
            if 'tif' in photo.split('.')[2].lower():
                cv2.imencode(".tiff", refimg)
                cv2.imwrite(newimg, refimg)
                srin = gdal.Open(photo)
                inproj = srin.GetProjection()
                transform = srin.GetGeoTransform()
                gcpcount = srin.GetGCPs()
                srout = gdal.Open(newimg, gdal.GA_Update)
                srout.SetProjection(inproj)
                srout.SetGeoTransform(transform)
                srout.SetGCPs(gcpcount, srin.GetGCPProjection())
                srout = None
                srin = None
            else:
                cv2.imwrite(newimg, refimg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            self.copyExif(photo, newimg)
            # if self.IndexBox.checkState() > 0:
            #     indeximg = (blue - red) / (blue + red)
            #     cv2.imwrite(output_directory + photo.split('.')[1] + "_Indexed." + photo.split('.')[2], indeximg)
            #     self.copyExif(photo, output_directory + photo.split('.')[1] + "_Indexed" + photo.split('.')[2])


####Function for finding he QR target and calculating the calibration coeficients
    def findQR(self, image):
        im = cv2.imread(image)
        grayscale = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl1 = clahe.apply(grayscale)

        denoised = cv2.fastNlMeansDenoising(cl1,None,14,7,21)

        threshcounter = 0
        while threshcounter <= 255:
            ret, thresh = cv2.threshold(denoised, threshcounter, 255, 0)
            if os.name == "nt":
                placeholder, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            else:
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            coords = []
            count = 0

            for i in hierarchy[0]:

                self.traverseHierarchy(hierarchy, contours, count, im, 0, coords)

                count += 1
            if len(coords) == 3:
                break
            else:
                threshcounter += 5


        if len(coords) is not 3:
            self.CalibrationLog.append("Could not find MAPIR ground target.")
            return

        line1 = np.sqrt(np.power((coords[0][0] - coords[1][0]), 2) + np.power((coords[0][1] - coords[1][1]), 2))  # Getting the distance between each centroid
        line2 = np.sqrt(np.power((coords[1][0] - coords[2][0]), 2) + np.power((coords[1][1] - coords[2][1]), 2))
        line3 = np.sqrt(np.power((coords[2][0] - coords[0][0]), 2) + np.power((coords[2][1] - coords[0][1]), 2))

        hypotenuse = line1 if line1 > line2 else line2
        hypotenuse = line3 if line3 > hypotenuse else hypotenuse

        if hypotenuse == line1:

            slope = (coords[1][1] - coords[0][1])/(coords[1][0] - coords[0][0])
            dist = coords[2][1] - (slope * coords[2][0]) + ((slope * coords[1][0]) - coords[1][1])
            dist /= np.sqrt(np.power(slope,2) + 1)
            center = coords[2]
            if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                bottom = coords[0]
                right = coords[1]
            else:

                bottom = coords[1]
                right = coords[0]
        elif hypotenuse == line2:

            slope = (coords[2][1] - coords[1][1]) / (coords[2][0] - coords[1][0])
            dist = coords[0][1] - (slope * coords[0][0]) + ((slope * coords[2][0]) - coords[2][1])
            dist /= np.sqrt(np.power(slope, 2) + 1)
            center = coords[0]
            if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):

                bottom = coords[1]
                right = coords[2]
            else:

                bottom = coords[2]
                right = coords[1]
        else:

            slope = (coords[0][1] - coords[2][1]) / (coords[0][0] - coords[2][0])
            dist = coords[1][1] - (slope * coords[1][0]) + ((slope * coords[0][0]) - coords[0][1])
            dist /= np.sqrt(np.power(slope, 2) + 1)
            center = coords[1]
            if (slope < 0 and dist < 0) or (slope >= 0 and dist >= 0):
                # self.CalibrationLog.append("slope and dist share sign")
                bottom = coords[0]
                right = coords[2]
            else:

                bottom = coords[2]
                right = coords[0]




        guidelength = np.sqrt(np.power((center[0] - bottom[0]), 2) + np.power((center[1] - bottom[1]), 2))
        pixelinch = guidelength/self.SQ_TO_SQ

        rad = (pixelinch * self.SQ_TO_TARG)
        vx = center[0] - bottom[0]
        vy = center[1] - bottom[1]
        newlen = np.sqrt(vx*vx + vy*vy)
        targ1x = (rad * (vx / newlen)) + center[0]
        targ1y = (rad * (vy / newlen)) + center[1]
        targ3x = (rad * (vx / newlen)) + right[0]
        targ3y = (rad * (vy / newlen)) + right[1]


        target1 = (int(targ1x),int(targ1y))
        target3 = (int(targ3x),int(targ3y))
        target2 = ((np.abs(target1[0] + target3[0])) / 2, np.abs((target1[1] + target3[1])) / 2)


        im2 = cv2.imread(image, -1)
        # im2 = im2.astype('float')
        blue = im2[:, :, 0]
        green = im2[:, :, 1]
        red = im2[:, :, 2] - ((im2[:, :, 0]/5) * 4)

        red = np.floor(red)
        if "TIF" in image.split('.')[1].upper():
            red = red.astype("uint16")
            blue = blue.astype("uint16")
            green = green.astype("uint16")
        im2 = cv2.merge((blue, green, red))



        targ1values = im2[(target1[1] - ((pixelinch * 0.75) / 2)):(target1[1] + ((pixelinch * 0.75) / 2)),
                      (target1[0] - ((pixelinch * 0.75) / 2)):(target1[0] + ((pixelinch * 0.75) / 2))]
        targ2values = im2[(target2[1] - ((pixelinch * 0.75) / 2)):(target2[1] + ((pixelinch * 0.75) / 2)),
                      (target2[0] - ((pixelinch * 0.75) / 2)):(target2[0] + ((pixelinch * 0.75) / 2))]
        targ3values = im2[(target3[1] - ((pixelinch * 0.75) / 2)):(target3[1] + ((pixelinch * 0.75) / 2)),
                      (target3[0] - ((pixelinch * 0.75) / 2)):(target3[0] + ((pixelinch * 0.75) / 2))]


        t1redmean = np.mean(targ1values[:, :, 2])/100
        t1greenmean = np.mean(targ1values[:, :, 1])/100
        t1bluemean = np.mean(targ1values[:, :, 0])/100
        t2redmean = np.mean(targ2values[:, :, 2])/100
        t2greenmean = np.mean(targ2values[:, :, 1])/100
        t2bluemean = np.mean(targ2values[:, :, 0])/100
        t3redmean = np.mean(targ3values[:, :, 2])/100
        t3greenmean = np.mean(targ3values[:, :, 1])/100
        t3bluemean = np.mean(targ3values[:, :, 0])/100


        yred = [0.87, 0.51, 0.23]
        yblue = [0.87, 0.51, 0.23]
        ygreen = [0.87, 0.51, 0.23]
        if 1 <= self.CalibrationCameraModel.currentIndex() <= 4:
            if self.CalibrationCameraModel.currentIndex() == 1:
                yred = self.refvalues["850"][0]
                ygreen = self.refvalues["850"][1]
                yblue = self.refvalues["850"][2]
            elif self.CalibrationCameraModel.currentIndex() == 2:
                yred = self.refvalues["650"][0]
                ygreen = self.refvalues["650"][1]
                yblue = self.refvalues["650"][2]
            elif self.CalibrationCameraModel.currentIndex() == 3:
                yred = self.refvalues["548"][0]
                ygreen = self.refvalues["548"][1]
                yblue = self.refvalues["548"][2]
            elif self.CalibrationCameraModel.currentIndex() == 4:
                yred = self.refvalues["450"][0]
                ygreen = self.refvalues["450"][1]
                yblue = self.refvalues["450"][2]
        else:
            yred = self.refvalues["660/850"][0]
            ygreen = self.refvalues["660/850"][1]
            yblue = self.refvalues["660/850"][2]

        xred = [t1redmean, t2redmean, t3redmean]
        xgreen = [t1greenmean, t2greenmean, t3greenmean]
        xblue = [t1bluemean, t2bluemean, t3bluemean]


        redslope, redintcpt, r_value, p_value, std_err = stats.linregress(xred, yred)

        greenslope, greenintcpt, r_value, p_value, std_err = stats.linregress(xgreen, ygreen)

        blueslope, blueintcpt, r_value, p_value, std_err = stats.linregress(xblue, yblue)


        self.CalibrationLog.append("Found QR Target, please proceed with calibration.")


        return [redintcpt, redslope, greenintcpt, greenslope, blueintcpt, blueslope]






# Calibration Steps: End


# Helper functions
    def preProcessHelper(self, infolder, outfolder, pixel_min_max, customerdata=True):

        if "DJI" in self.PreProcessCameraModel.currentText():
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[dD][nN][gG]"))
            counter = 0
            for input in infiles:
                self.PreProcessLog.append(
                    "processing image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    " " + input.split(os.sep)[1])
                self.openDNG(infolder + input.split('.')[1] + "." + input.split('.')[2], outfolder, customerdata)

                counter += 1
        else:
            os.chdir(infolder)
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[rR][aA][wW]"))
            infiles.extend(glob.glob("." + os.sep + "*.[jJ][pP][gG]"))
            infiles.extend(glob.glob("." + os.sep + "*.[jJ][pP][eE][gG]"))
            infiles.sort()

            if ("RAW" in infiles[0].upper()) and ("JPG" in infiles[1].upper()):
                counter = 0
                for input in infiles[::2]:
                    if customerdata == True:
                        self.PreProcessLog.append(
                            "processing image: " + str((counter / 2) + 1) + " of " + str(len(infiles) / 2) +
                            " " + input.split(os.sep)[1])
                    with open(input, "rb") as rawimage:
                        img = np.fromfile(rawimage, np.dtype('u2'), self.imsize).reshape((self.imrows, self.imcols))
                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)

                        filename = input.split('.')
                        outputfilename = filename[1] + '.tiff'
                        cv2.imencode(".tiff", color)
                        cv2.imwrite(outfolder + outputfilename, color)
                        if self.PreProcessCameraModel.currentIndex() == 1 and customerdata:
                            # if self.PreProcessCameraModel.currentIndex() == 1:
                                rgb = cv2.imread(outfolder + outputfilename, -1)


                                pixel_min_max["redmax"] = max(np.percentile(rgb[:, :, 2], 80), pixel_min_max["redmax"])
                                pixel_min_max["redmin"] = min(rgb[:, :, 2].min(), pixel_min_max["redmin"])
                                pixel_min_max["greenmax"] = max(np.percentile(rgb[:, :, 1], 80),
                                                                pixel_min_max["greenmax"])
                                pixel_min_max["greenmin"] = min(rgb[:, :, 1].min(), pixel_min_max["greenmin"])
                                pixel_min_max["bluemax"] = max(np.percentile(rgb[:, :, 0], 80),
                                                               pixel_min_max["bluemax"])
                                pixel_min_max["bluemin"] = min(rgb[:, :, 0].min(), pixel_min_max["bluemin"])


                        if customerdata == True:
                            self.copyExif(infolder + infiles[counter + 1], outfolder + outputfilename)
                    counter += 2

            else:
                self.PreProcessLog.append(
                    "Incorrect file structure. Please arrange files in a RAW, JPG, RAW, JGP... format.")
            if self.PreProcessCameraModel.currentIndex() == 1 and self.RgbBox.checkState() > 0 and customerdata:
                if self.PreProcessCameraModel.currentIndex() == 1:
                    os.chdir(outfolder)
                    outfiles = []
                    outfiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                    outfiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                    counter = 0
                    for input in outfiles:
                        rgb = cv2.imread(input, -1)
                        if self.VignetteBox.checkState() > 0:
                            rgb = self.removeVignette(rgb, pixel_min_max)

                        red = rgb[:, :, 2]
                        green = rgb[:, :, 1]
                        blue = rgb[:, :, 0]


                        red[red > pixel_min_max["redmax"]] = pixel_min_max["redmax"]
                        green[green > pixel_min_max["greenmax"]] = pixel_min_max["greenmax"]
                        blue[blue > pixel_min_max["bluemax"]] = pixel_min_max["bluemax"]

                        # maxval = max(max(pixel_min_max["redmax"], pixel_min_max["greenmax"]), pixel_min_max["bluemax"])
                        # minval = min(min(pixel_min_max["redmin"], pixel_min_max["greenmin"]), pixel_min_max["bluemin"])

                        red = (((red - pixel_min_max["redmin"]) / (pixel_min_max["redmax"] - pixel_min_max["redmin"])) * 65535)
                        green = (((green - pixel_min_max["greenmin"]) / (pixel_min_max["greenmax"] - pixel_min_max["greenmin"])) * 65535)
                        blue = (((blue - pixel_min_max["bluemin"]) / (pixel_min_max["bluemax"] - pixel_min_max["bluemin"])) * 65535)

                        # red[green == 65535] = 65535
                        # # red[blue == 65535] = 65535
                        # # green[red == 65535] = 65535
                        # # green[blue == 65535] = 65535
                        # blue[green == 65535] = 65535
                        # # blue[red == 65535] = 65535
                        rgb = cv2.merge((blue, green, red))

                        rgb = rgb.astype('uint16')

                        filename = input.split('.')
                        outputfilename = filename[1] + '.tiff'
                        cv2.imencode(".tiff", rgb)

                        cv2.imwrite(outfolder + outputfilename, rgb)
                        if customerdata == True:

                            self.copyExif(infolder + infiles[counter + 1], outfolder + outputfilename)
                        counter += 2

                # else:
                #     self.PreProcessLog.append("Normalization for RGB camera models only")
            elif self.VignetteBox.checkState() > 0 and customerdata:
                os.chdir(outfolder)
                outfiles = []
                outfiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
                outfiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
                counter = 0
                for input in outfiles:
                    photo = cv2.imread(input, -1)

                    # blue = photo[:, :, 2]
                    # green = photo[:, :, 1]
                    # red = photo[:, :, 0]
                    #
                    #
                    #
                    #
                    #
                    # photo = cv2.merge((blue, green, red))

                    outphoto = self.removeVignette(photo, pixel_min_max)



                    filename = input.split('.')
                    outputfilename = filename[1] + '.tiff'
                    cv2.imencode(".tiff", outphoto)
                    cv2.imwrite(outfolder + outputfilename, outphoto)
                    if customerdata == True:

                        self.copyExif( infolder + infiles[counter + 1], outfolder + outputfilename)
                    counter += 2
    def traverseHierarchy(self, tier, cont, index, image, depth, coords):

        if tier[0][index][2] != -1:
            self.traverseHierarchy(tier, cont, tier[0][index][2], image, depth + 1, coords)
            return
        elif depth >= 2:
            c = cont[index]
            moment = cv2.moments(c)
            if int(moment['m00']) != 0:
                x = int(moment['m10'] / moment['m00'])
                y = int(moment['m01'] / moment['m00'])
                coords.append([x, y])
            return
    def openDNG(self, inphoto, outfolder, customerdata=True):
        inphoto = str(inphoto)
        newfile = inphoto.split(".")[0] + ".tiff"
        if not os.path.exists(outfolder + os.sep + newfile.rsplit(os.sep, 1)[1]):
              if sys.platform == "win32":
                    subprocess.call([modpath + os.sep + 'dcraw.exe', '-6', '-T', inphoto])
              elif sys.platform == "darwin":
                    subprocess.call([r'/usr/local/bin/dcraw', '-6', '-T', inphoto])
              if customerdata == True:
                    self.copyExif(os.path.abspath(inphoto), newfile)
              shutil.move(newfile, outfolder)
        else:
              self.PreProcessLog.append("Attention!: " + str(newfile) + " already exists.")
    def removeVignette(self, photo, pixel_min_max):
        if self.PreProcessCameraModel.currentIndex() == 0:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'ndvi.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'ndvi.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 1:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'rgb.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'rgb.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'nir.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'nir.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 3:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'red.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'red.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 4:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'green.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'green.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 5:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'blue.tiff', 0)
            dc = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'DC' + os.sep + 'Proc' + os.sep + 'blue.tiff', 0)
        elif self.PreProcessCameraModel.currentIndex() == 7:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'FC350.tiff', 0)
            dc = ff * 0
        elif self.PreProcessCameraModel.currentIndex() == 8:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'FC330.tiff', 0)
            dc = ff * 0
        elif self.PreProcessCameraModel.currentIndex() == 9:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'FC300X.tiff', 0)
            dc = ff * 0
        elif self.PreProcessCameraModel.currentIndex() == 10:
            ff = cv2.imread(modpath + os.sep + 'Vig' + os.sep + 'FF' + os.sep + 'Proc' + os.sep + 'FC300S.tiff', 0)
            dc = ff * 0
        else:
            self.PreProcessLog.append(r'Vignette correction not yet available for selected camera model.')
            return photo


        ffblur = cv2.medianBlur(ff, 5)
        dcblur = cv2.medianBlur(dc, 5)
        ffblur = ffblur.max() / (ffblur)

        # ffred = cv2.medianBlur(ff[:, :, 2].astype('uint8'),10)
        # ffgreen = cv2.medianBlur(ff[:, :, 1].astype('uint8'),10)
        # ffblue = cv2.medianBlur(ff[:, :, 0].astype('uint8'),10)
        #
        # ffred = np.max(ffred) / ffred
        # ffgreen = np.max(ffgreen) / ffgreen
        # ffblue = np.max(ffblue) / ffblue

        # sred = ffred - dc[:, :, 2]
        # sgreen = ffgreen - dc[:, :, 1]
        # sblue = ffblue - dc[:, :, 0]
        # height, width = ffred.shape
        # mred = np.mean(cv2.circle(ffred, [height/2, width/2], 10))
        # mgreen = np.mean(cv2.circle(ffgreen, [height / 2, width / 2], 10))
        # mblue = np.mean(cv2.circle(ffblue, [height / 2, width / 2], 10))



        red = photo[:, :, 2]
        green = photo[:, :, 1]
        blue = photo[:, :, 0]

        red = (red - dcblur) * (ffblur)
        green = (green - dcblur) * (ffblur)
        blue = (blue - dcblur) * (ffblur)

        # red = (red) * Gred
        # green = (green) * Ggreen
        # blue = (blue) * Gblue

        # red[red < 0] = 0
        # red[red > 65535] = 65535
        # green[green < 0] = 0
        # green[green > 65535] = 65535
        # blue[blue < 0] = 0
        # blue[blue > 65535] = 65535

        # photo = cv2.merge((blue, green, red))
        # photo = photo.astype('uint16')

        # maxval = max(max(pixel_min_max["redmax"], pixel_min_max["greenmax"]), pixel_min_max["bluemax"])
        # minval = min(min(pixel_min_max["redmin"], pixel_min_max["greenmin"]), pixel_min_max["bluemin"])

        # red[red > pixel_min_max["redmax"]] = pixel_min_max["redmax"]
        # green[green > pixel_min_max["greenmax"]] = pixel_min_max["greenmax"]
        # blue[blue > pixel_min_max["bluemax"]] = pixel_min_max["bluemax"]


        # red = (((red - minval) / (maxval - minval)) * 65535)
        # green = (((green - minval) / (maxval - minval)) * 65535)
        # blue = (((blue - minval) / (maxval - minval)) * 65535)

        # red[red > np.percentile(red, 80)] = np.percentile(red, 80)
        # green[green > np.percentile(green, 80)] = np.percentile(green, 80)
        # blue[blue > np.percentile(blue, 80)] = np.percentile(blue, 80)

        # photo[:, :, 0][photo[:, :, 1] == 65535] = 65535
        # photo[:, :, 0][photo[:, :, 2] == 65535] = 65535
        # photo[:, :, 1][photo[:, :, 0] == 65535] = 65535
        # photo[:, :, 1][photo[:, :, 2] == 65535] = 65535
        # photo[:, :, 2][photo[:, :, 0] == 65535] = 65535
        # photo[:, :, 2][photo[:, :, 2] == 65535] = 65535
        photo = cv2.merge((blue, green, red))
        photo = photo.astype('uint16')
        #
        # photo = cv2.merge((photo[:, :, 0], photo[:, :, 1], photo[:, :, 2]))

        return photo

    def copyExif(self, inphoto, outphoto):
        if sys.platform == "win32":
              # with exiftool.ExifTool() as et:
              #     et.execute(r' -overwrite_original -tagsFromFile ' + os.path.abspath(inphoto) + ' ' + os.path.abspath(outphoto))
              subprocess.call(
                  [modpath + os.sep + r'exiftool.exe', r'-overwrite_original', r'-addTagsFromFile', os.path.abspath(inphoto), r'-all:all<all:all',
                   os.path.abspath(outphoto)])
        elif sys.platform == "darwin":
              subprocess.call([r'/usr/local/bin/exiftool', r'-overwrite_original', r'-addTagsFromFile', os.path.abspath(inphoto), r'-all:all<all:all',
                   os.path.abspath(outphoto)])
 
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

