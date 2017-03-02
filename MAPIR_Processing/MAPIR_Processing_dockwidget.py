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
import hid
import struct

modpath = os.path.dirname(os.path.realpath(__file__))

if sys.platform == "win32":  # Windows OS
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

elif sys.platform == "darwin":
    if not os.path.exists(r'/usr/local/bin/brew'):
        subprocess.call([r'/usr/bin/ruby', r'-e',
                         r'"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"', r'<',
                         r'/dev/null'])
        subprocess.call([r'/usr/local/bin/brew', r'tap', r'homebrew/science'])
    if not os.path.exists(r'/usr/local/bin/dcraw'):
        subprocess.call([r'/usr/local/bin/brew', r'install', r'dcraw'])

    if not os.path.exists(r'/usr/local/bin/exiftool'):
        subprocess.call([r'/usr/local/bin/brew', r'install', r'exiftool'])

    if not os.path.exists(r'/usr/local/bin/opencv'):
        subprocess.call([r'/usr/local/bin/brew', r'install', r'opencv'])
    sys.path.append(r'/usr/local/bin')
    sys.path.append(r'/usr/local/bin/dcraw')
    sys.path.append(r'/usr/local/bin/exiftool')
    sys.path.append(r'/usr/local/bin/opencv')

from osgeo import gdal
import cv2
import glob

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
# if sys.platform == "win32":
#       import exiftool
#       exiftool.executable = modpath + os.sep + "exiftool.exe"
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_base.ui'))
MODAL_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'MAPIR_Processing_dockwidget_modal.ui'))


class KernelModal(QtGui.QDialog, MODAL_CLASS):
    parent = None

    def __init__(self, parent=None):
        """Constructor."""
        super(KernelModal, self).__init__(parent=parent)
        self.parent = parent
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def on_ModalSaveButton_released(self):
        seconds = int(self.SecondsLine.text())
        minutes = int(self.MinutesLine.text())
        hours = int(self.HoursLine.text())
        days = int(self.DaysLine.text())
        weeks = int(self.WeeksLine.text())
        if (seconds / 60) > 1:
            minutes += int(seconds / 60)
            seconds = seconds % 60
        if (minutes / 60) > 1:
            hours += int(minutes / 60)
            minutes = minutes % 60
        if (hours / 24) > 1:
            days += int(hours / 24)
            hours = hours % 24
        if (days / 7) > 1:
            weeks += int(days / 7)
            days = days % 7
        self.parent.seconds = seconds
        self.parent.minutes = minutes
        self.parent.hours = hours
        self.parent.days = days
        self.parent.weeks = weeks
        self.parent.writeToIntervalLine()

        # weeks /= 604800
        # days /= 86400
        # hours /= 3600
        # minutes /= 60
        # seconds += minutes + hours + days + weeks
        #
        # MAPIR_ProcessingDockWidget.interval = int(seconds)
        self.close()

    def on_ModalCancelButton_released(self):
        self.close()


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
    BASE_COEFF_SURVEY2_NDVI_TIF = [3.21946584661, 1.06087488594, 0.0, 0.0, -43.6505776052, 1.46482226805]
    BASE_COEFF_SURVEY2_NIR_TIF = [-2.24216724, 0.12962333, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_DJIX3_NDVI_JPG = [-0.34430543, 4.63184993, 0.0, 0.0, -0.49413940, 16.36429964]
    BASE_COEFF_DJIX3_NDVI_TIF = [-0.74925346, 0.01350319, 0.0, 0.0, -0.77810008, 0.03478272]
    BASE_COEFF_DJIPHANTOM4_NDVI_JPG = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM4_NDVI_TIF = [-1.17016961, 0.03333209, 0.0, 0.0, -0.99455214, 0.05373502]
    BASE_COEFF_DJIPHANTOM3_NDVI_JPG = [-1.54494979, 3.44708472, 0.0, 0.0, -1.40606832, 6.35407929]
    BASE_COEFF_DJIPHANTOM3_NDVI_TIF = [-1.37495554, 0.01752340, 0.0, 0.0, -1.41073753, 0.03700812]
    BASE_COEFF_KERNEL_F644 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F405 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F450 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F520 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F550 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F632 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F650 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F725 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F808 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F850 = [0.0, 0.0]
    BASE_COEFF_KERNEL_F395_870 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F475_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F550_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F660_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F475_550_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    BASE_COEFF_KERNEL_F550_660_850 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

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
    qrcoeffs = []  # Red Intercept, Red Slope,  Green Intercept, Green Slope, Blue Intercept, Blue Slope
    refvalues = {
        "660/850": [[87.032549, 52.135779, 23.664799], [0, 0, 0], [84.63514, 51.950608, 22.795518]],
        "446/800": [[84.19608509, 52.0440145, 23.0113958], [0, 0, 0], [86.45652801, 50.37779363, 23.59041624]],
        "850": [[84.63514, 51.950608, 22.795518], [0, 0, 0], [0, 0, 0]],
        "808": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        "650": [[87.032549, 52.135779, 23.664799], [0, 0, 0], [0, 0, 0]],
        "548": [[0, 0, 0], [87.415089, 51.734381, 24.032515], [0, 0, 0]],
        "450": [[0, 0, 0], [0, 0, 0], [86.469794, 50.392915, 23.565447]],
        "Mono450": [86.34818638, 50.24087105, 23.51860396],
        "Mono550": [87.40616379, 51.73070235, 24.02423818],
        "Mono650": [87.05783136, 52.12290524, 23.66437854],
        "Mono725": [86.06071247, 52.1474266, 23.37744252],
        "Mono808": [84.06184266, 52.03405498, 22.97701185],
        "Mono850": [84.81919553, 51.9491643, 22.78713071],
        "Mono405": [85.56905469, 49.21243183, 23.09899254],
        "Mono520": [87.29814889, 51.51370187, 24.04729692],
        "Mono632": [87.24034645, 52.09649915, 23.74529161],
        "Mono660": [87.04202831, 52.12214688, 23.65919358],
        "Mono590": [87.47043911, 51.95596573, 23.92049856]
    }

    pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                     "greenmax": 0.0, "greenmin": 65535.0,
                     "bluemax": 0.0, "bluemin": 65535.0}
    weeks = 0
    days = 0
    hours = 0
    minutes = 0
    seconds = 1
    modalwindow = None

    def __init__(self, parent=None):
        """Constructor."""
        super(MAPIR_ProcessingDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def on_KernelExposureMode_currentIndexChanged(self, int):
        if self.KernelExposureMode.currentIndex() == 0:
            self.KernelISO.setEnabled(False)
            self.KernelShutterSpeed.setEnabled(False)
        else:
            self.KernelISO.setEnabled(True)
            self.KernelShutterSpeed.setEnabled(True)

    def on_KernelUpdate_released(self):
        self.writeToKernel()

    def on_KernelCaptureButton_released(self):
        camera = hid.device(0x525, 0xa4ac)
        if camera <= 0:
            return 9
        camera.open(0x525, 0xa4ac)
        if self.KernelPhotoMode.currentIndex() == 0:
            buf = [0] * 512

            buf[0] = 3
            buf[1] = 13
            buf[2] = 0
            camera.write(buf)
        elif self.KernelPhotoMode.currentIndex() == 2:
            buf = [0] * 512

            buf[0] = 3
            buf[1] = 14
            if self.capturing == False:
                buf[2] = 1
                self.capturing = True
            else:
                buf[2] = 0
                self.capturing == False
            camera.write(buf)
        else:

            buf = [0] * 512

            buf[0] = 3
            buf[1] = 15
            if self.capturing == False:
                buf[2] = 1
                self.capturing = True
            else:
                buf[2] = 0
                self.capturing == False
            camera.write(buf)

    def writeToKernel(self):
        for d in hid.enumerate(0, 0):
            keys = d.keys()
            keys.sort()
            for key in keys:
                self.PreProcessLog.append(str(key) + ', ' + str(d[key]))
        buf = [0] * 512
        buf[0] = 5
        buf[1] = 143  # ISO Register
        temp = int(self.KernelISO.currentText())
        buf[2] = temp / 100

        camera = hid.device(0x525, 0xa4ac)
        if camera <= 0:
            return 9
        camera.open(0x525, 0xa4ac)
        # if camera <= 0:
        #     return 9
        # if sys.platform == "linux2":
        #     res = camera.write(buf, 220)
        # else:
        camera.write(buf)
        buf = [0] * 512

        buf[0] = 5
        buf[1] = 111  # Shutter Speed Register
        buf[2] = (self.KernelShutterSpeed.currentIndex() + 1)
        camera.write(buf)

        buf = [0] * 512

        buf[0] = 5
        buf[1] = 22  # Time Lapse Interval Register
        buf[2] = (self.seconds)
        camera.write(buf)
        if self.KernelVideoOut.currentIndex() == 0:  # No Output
            buf = [0] * 512

            buf[0] = 5
            buf[1] = 121  # DAC Register
            buf[2] = 0
            camera.write(buf)

            buf = [0] * 512

            buf[0] = 5
            buf[1] = 122  # HDMI Register
            buf[2] = 0
            camera.write(buf)
        elif self.KernelVideoOut.currentIndex() == 1:  # HDMI
            buf = [0] * 512

            buf[0] = 5
            buf[1] = 122  # HDMI Register
            buf[2] = 0
            camera.write(buf)
        elif self.KernelVideoOut.currentIndex() == 2:  # SD( DAC )
            buf = [0] * 512

            buf[0] = 5
            buf[1] = 121  # DAC Register
            buf[2] = 0
            camera.write(buf)
        else:  # Both outputs
            buf = [0] * 512

            buf[0] = 5
            buf[1] = 121  # DAC Register
            buf[2] = 1
            camera.write(buf)

            buf = [0] * 512

            buf[0] = 5
            buf[1] = 122  # HDMI Register
            buf[2] = 1
            camera.write(buf)
        camera.close()

    def on_KernelIntervalButton_released(self):
        self.modalwindow = KernelModal(self)
        self.modalwindow.setGeometry(QRect(100, 100, 400, 200))
        self.modalwindow.show()

        num = self.seconds % 168
        if num == 0:
            num = 1
        self.seconds = num

    def writeToIntervalLine(self):
        self.KernelIntervalLine.clear()
        self.KernelIntervalLine.setText(
            str(self.weeks) + 'w, ' + str(self.days) + 'd, ' + str(self.hours) + 'h, ' + str(self.minutes) + 'm,' + str(
                self.seconds) + 's')

    #########Pre-Process Steps: Start#################
    def on_PreProcessCameraModel_currentIndexChanged(self, int):
        if self.PreProcessCameraModel.currentIndex() == 0:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.PreProcessFilter.setEnabled(True)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 1:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Blue + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 2:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 3:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 4:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        elif self.PreProcessCameraModel.currentIndex() == 5:
            self.PreProcessFilter.clear()
            self.PreProcessFilter.addItems(["Red + NIR (NDVI)"])
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.addItems(["3.97mm"])
            self.PreProcessLens.setEnabled(False)
        else:
            self.PreProcessLens.clear()
            self.PreProcessFilter.setEnabled(False)
            self.PreProcessLens.clear()
            self.PreProcessLens.setEnabled(False)

    def on_CalibrationCameraModel_currentIndexChanged(self, int):
        if self.CalibrationCameraModel.currentIndex() == 0:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)", "NIR", "Red", "Green", "Blue", "RGB"])
            self.CalibrationFilter.setEnabled(True)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 1:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Blue + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 2:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 3:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 4:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        elif self.CalibrationCameraModel.currentIndex() == 5:
            self.CalibrationFilter.clear()
            self.CalibrationFilter.addItems(["Red + NIR (NDVI)"])
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.addItems(["3.97mm"])
            self.CalibrationLens.setEnabled(False)
        else:
            self.CalibrationLens.clear()
            self.CalibrationFilter.setEnabled(False)
            self.CalibrationLens.clear()
            self.CalibrationLens.setEnabled(False)

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
            # self.PreProcessLog.append(r'Extracting vignette corection data')


            infolder = self.PreProcessInFolder.text()
            outdir = self.PreProcessOutFolder.text()

            foldercount = 1
            endloop = False
            while endloop is False:
                outfolder = outdir + os.sep + "Processed_" + str(foldercount)
                if os.path.exists(outfolder):
                    foldercount += 1
                else:
                    os.mkdir(outfolder)
                    endloop = True

            self.PreProcessLog.append("Input folder: " + infolder)
            self.PreProcessLog.append("Output folder: " + outfolder)
            self.preProcessHelper(infolder, outfolder)
            self.PreProcessLog.append("Finished Processing Images.")
            # if os.path.exists(modpath + os.sep + 'Vig'):
            #     shutil.rmtree(modpath + os.sep + 'Vig')

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
            # self.CalibrationLog.append("Files to calibrate[0]: " + files_to_calibrate[0])
            pixel_min_max = {"redmax": 0.0, "redmin": 65535.0,
                             "greenmax": 0.0, "greenmin": 65535.0,
                             "bluemax": 0.0, "bluemin": 65535.0}
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
                if self.CalibrationCameraModel.currentIndex() > 3:
                    for calpixel in files_to_calibrate:

                        img = cv2.imread(calpixel, -1)
                        # imsize = np.shape(img)
                        # if imsize[0] > self.imcols or imsize[1] > self.imrows:
                        #     if "tif" or "TIF" in calpixel:
                        #         tempimg = np.memmap(calpixel, dtype=np.uint16, shape=(imsize))
                        #         refimg = None
                        #         refimg = tempimg
                        #     else:
                        #         tempimg = np.memmap(calpixel, dtype=np.uint8, shape=(imsize))
                        #         refimg = None
                        #         refimg = tempimg

                        if self.CalibrationCameraModel.currentIndex() == 1:  # Survey1_NDVI
                            # img = img.astype('float')

                            img[:, :, 0] = img[:, :, 0] - ((img[:, :, 2] / 5) * 4)
                        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 0 \
                                or self.CalibrationCameraModel.currentIndex() > 1:  # Survey2 NDVI, DJI NDVI cameras
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
                        if self.CalibrationCameraModel.currentIndex() == 1:  # Survey1_NDVI
                            if "tif" or "TIF" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_SURVEY1_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_SURVEY1_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_SURVEY1_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY1_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_SURVEY1_NDVI_TIF[2]
                            elif "jpg" or "JPG" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_SURVEY1_NDVI_JPG[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY1_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_SURVEY1_NDVI_JPG[2]
                        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 0:
                            if "tif" or "TIF" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_SURVEY2_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_SURVEY2_NDVI_TIF[2]
                            elif "jpg" or "JPG" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_SURVEY2_NDVI_JPG[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_SURVEY2_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_SURVEY2_NDVI_JPG[2]
                        elif self.CalibrationCameraModel.currentIndex() == 5:
                            if "tif" or "TIF" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIX3_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_TIF[3]) \
                                                           + self.BASE_COEFF_DJIX3_NDVI_TIF[2]
                            elif "jpg" or "JPG" in calpixel:
                                pixel_min_max["redmax"] = (pixel_min_max["redmax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                                pixel_min_max["redmin"] = (pixel_min_max["redmin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_DJIX3_NDVI_JPG[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIX3_NDVI_JPG[3]) \
                                                           + self.BASE_COEFF_DJIX3_NDVI_JPG[2]
                        elif self.CalibrationCameraModel.currentIndex() == 2:
                            if "tif" or "TIF" in calpixel:
                                pixel_min_max["redmax"] = (
                                                          pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (
                                                          pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF[2]
                            elif "jpg" or "JPG" in calpixel:
                                pixel_min_max["redmax"] = (
                                                          pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                                pixel_min_max["redmin"] = (
                                                          pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG[2]
                        elif self.CalibrationCameraModel.currentIndex() == 3 or self.CalibrationCameraModel.currentIndex() == 4:
                            if "tif" or "TIF" in calpixel:
                                pixel_min_max["redmax"] = (
                                                          pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (
                                                          pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                            elif "jpg" or "JPG" in calpixel:
                                pixel_min_max["redmax"] = (
                                                          pixel_min_max["redmax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                pixel_min_max["redmin"] = (
                                                          pixel_min_max["redmin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[1]) \
                                                          + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[0]
                                pixel_min_max["bluemin"] = (pixel_min_max["bluemin"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]
                                pixel_min_max["bluemax"] = (pixel_min_max["bluemax"] * self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[
                                    3]) \
                                                           + self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF[2]

                    for calfile in files_to_calibrate:

                        cameramodel = self.CalibrationCameraModel.currentIndex()
                        if self.useqr is True:
                            # self.CalibrationLog.append("Using QR")
                            self.CalibratePhotos(calfile, self.qrcoeffs, pixel_min_max, outdir)
                        else:
                            # self.CalibrationLog.append("NOT Using QR")
                            if cameramodel == 0 and self.CalibrationFilter.currentIndex() == 0:  # Survey2 NDVI
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NDVI_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NDVI_JPG, pixel_min_max, outdir)
                            elif cameramodel == 0 and self.CalibrationFilter.currentIndex() == 1:  # Survey2 NIR
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NIR_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_NIR_JPG, pixel_min_max, outdir)
                            elif cameramodel == 0 and self.CalibrationFilter.currentIndex() == 2:  # Survey2 RED
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_RED_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_RED_JPG, pixel_min_max, outdir)
                            elif cameramodel == 0 and self.CalibrationFilter.currentIndex() == 3:  # Survey2 GREEN
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_GREEN_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_GREEN_JPG, pixel_min_max, outdir)
                            elif cameramodel == 0 and self.CalibrationFilter.currentIndex() == 4:  # Survey2 BLUE
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_BLUE_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY2_BLUE_JPG, pixel_min_max, outdir)
                            elif cameramodel == 1:  # Survey1 NDVI
                                if "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_SURVEY1_NDVI_JPG, pixel_min_max, outdir)
                            elif cameramodel == 5:  # DJI X3 NDVI
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIX3_NDVI_TIF, pixel_min_max, outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIX3_NDVI_JPG, pixel_min_max, outdir)
                            elif cameramodel == 2:  # DJI Phantom4 NDVI
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM4_NDVI_TIF, pixel_min_max,
                                                         outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM4_NDVI_JPG, pixel_min_max,
                                                         outdir)
                            elif cameramodel == 3 or cameramodel == 4:  # DJI PHANTOM3 NDVI
                                if "TIF" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM3_NDVI_TIF, pixel_min_max,
                                                         outdir)
                                elif "JPG" in calfile.split('.')[2].upper():
                                    self.CalibratePhotos(calfile, self.BASE_COEFF_DJIPHANTOM3_NDVI_JPG, pixel_min_max,
                                                         outdir)
                            else:
                                self.CalibrationLog.append(
                                    "No default calibration data for selected camera model. Please please supply a MAPIR Reflectance Target to proceed.\n")
                                break

                self.CalibrationLog.append("Finished Calibrating " + str(len(files_to_calibrate)) + " images\n")
    def CalibrateMono(self, photo, coeffs, output_directory):
        refimg = cv2.imread(photo, -1)
        refimg = (refimg * coeffs[1]) + coeffs[0]
        refimg[refimg > 65535] = 65535
        refimg[refimg < 0] = 0
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
    def CalibratePhotos(self, photo, coeffs, minmaxes, output_directory):
        refimg = cv2.imread(photo, -1)
        # imsize = np.shape(refimg)
        # if imsize[0] > self.imcols or imsize[1] > self.imrows:
        #     if "tif" or "TIF" in photo:
        #             tempimg = np.memmap(photo, dtype=np.uint16, shape=(imsize))
        #             refimg = None
        #             refimg = tempimg
        #     else:
        #             tempimg = np.memmap(photo, dtype=np.uint8, shape=(imsize))
        #             refimg = None
        #             refimg = tempimg

        ### split channels (using cv2.split caused too much overhead and made the host program crash)
        blue = refimg[:, :, 0]
        green = refimg[:, :, 1]
        red = refimg[:, :, 2]
        if refimg.shape[2] > 3:
            alpha = refimg[:, :, 3]
            refimg = refimg[:, :, :3]

        ### find the maximum and minimum pixel values over the entire directory.
        if self.CalibrationCameraModel.currentIndex() == 1:  ###Survey1 NDVI
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            blue = refimg[:, :, 0] - (refimg[:, :, 2] * 0.80)  # Subtract the NIR bleed over from the blue channel
        elif (self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 1) \
                or (self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 2):
            ### red and NIR
            maxpixel = minmaxes["redmax"]
            minpixel = minmaxes["redmin"]
        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 3:
            ### green
            maxpixel = minmaxes["greenmax"]
            minpixel = minmaxes["greenmin"]
        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 4:
            ### blue
            maxpixel = minmaxes["bluemax"]
            minpixel = minmaxes["bluemin"]
        else:  ###Survey2 NDVI or any DJI ndvi
            maxpixel = minmaxes["redmax"] if minmaxes["redmax"] > minmaxes["bluemax"] else minmaxes["bluemax"]
            minpixel = minmaxes["redmin"] if minmaxes["redmin"] < minmaxes["bluemin"] else minmaxes["bluemin"]
            red = refimg[:, :, 2] - (refimg[:, :, 0] * 0.80)  # Subtract the NIR bleed over from the red channel



            ### Calibrate pixels based on the default reflectance values (or the values gathered from the MAPIR reflectance target)
        red = (red * coeffs[1]) + coeffs[0]
        green = (green * coeffs[3]) + coeffs[2]
        blue = (blue * coeffs[5]) + coeffs[4]

        ### Scale calibrated values back down to a useable range (Adding 1 to avaoid 0 value pixels, as they will cause a
        #### devide by zero case when creating an index image.
        if photo.split('.')[2].upper() == "JPG" or photo.split('.')[
            2].upper() == "JPEG" or self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Entering JPG")
            red = (((red - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
            green = (((green - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
            blue = (((blue - minpixel + 1) / (maxpixel - minpixel + 1)) * 255)
        else:
            red = (((red - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)
            green = (((green - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)
            blue = (((blue - minpixel + 1) / (maxpixel - minpixel + 1)) * 65535)

        if photo.split('.')[2].upper() == "JPG":  # Remove the gamma correction that is automaticall applied to JPGs
            self.CalibrationLog.append("Removing Gamma")
            red = np.power(red, 1 / 2.2)
            green = np.power(green, 1 / 2.2)
            blue = np.power(blue, 1 / 2.2)

            ### Merge the channels back into a single image
        refimg = cv2.merge((blue, green, red))
        if refimg.shape[2] > 3:
            white_background_image = np.ones_like(refimg, dtype=np.uint8) * 255
            a_factor = alpha[:, :, np.newaxis].astype(np.float32) / 255.0
            a_factor = np.concatenate((a_factor, a_factor, a_factor), axis=2)
            base = refimg.astype(np.float32) * a_factor
            white = white_background_image.astype(np.float32) * (1 - a_factor)
            refimg = base + white
            ### If the image is a .tiff then change it to a 16 bit color image
        if "TIF" in photo.split('.')[2].upper() and not self.Tiff2JpgBox.checkState() > 0:
            refimg = refimg.astype("uint16")

        if (self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 0) \
                or self.CalibrationCameraModel.currentIndex() >= 4:
            ### Remove green information if NDVI camera
            refimg[:, :, 1] = 1
        elif (self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 1) \
                or self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 2:
            ### Remove blue and green information if NIR or Red camera
            refimg[:, :, 0] = 1
            refimg[:, :, 1] = 1
        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 3:
            ### Remove blue and red information if GREEN camera
            refimg[:, :, 0] = 1
            refimg[:, :, 2] = 1
        elif self.CalibrationCameraModel.currentIndex() == 0 and self.CalibrationFilter.currentIndex() == 4:
            ### Remove red and green information if BLUE camera
            refimg[:, :, 1] = 1
            refimg[:, :, 2] = 1

        if self.Tiff2JpgBox.checkState() > 0:
            self.CalibrationLog.append("Making JPG")
            cv2.imencode(".jpg", refimg)
            cv2.imwrite(output_directory + photo.split('.')[1] + "_CALIBRATED.JPG", refimg,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            self.copyExif(photo, output_directory + photo.split('.')[1] + "_CALIBRATED.JPG")
            # if self.IndexBox.checkState() > 0:
            #     indeximg = (blue - red) / (blue + red)
            #     indeximg = indeximg.astype("float32")
            #     cv2.imwrite(output_directory + photo.split('.')[1] + "_Indexed.JPG", indeximg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            #     self.copyExif(photo, output_directory + photo.split('.')[1] + "_Indexed.JPG")
            # todo See if JPG can store geotiff metadata
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
        if self.CalibrationCameraModel.currentIndex() > 2:
            im = cv2.imread(image)
            grayscale = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl1 = clahe.apply(grayscale)
        else:
            im = cv2.imread(image, 0)
            clahe2 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl1 = clahe2.apply(im)
        denoised = cv2.fastNlMeansDenoising(cl1, None, 14, 7, 21)

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

        line1 = np.sqrt(np.power((coords[0][0] - coords[1][0]), 2) + np.power((coords[0][1] - coords[1][1]),
                                                                              2))  # Getting the distance between each centroid
        line2 = np.sqrt(np.power((coords[1][0] - coords[2][0]), 2) + np.power((coords[1][1] - coords[2][1]), 2))
        line3 = np.sqrt(np.power((coords[2][0] - coords[0][0]), 2) + np.power((coords[2][1] - coords[0][1]), 2))

        hypotenuse = line1 if line1 > line2 else line2
        hypotenuse = line3 if line3 > hypotenuse else hypotenuse

        if hypotenuse == line1:

            slope = (coords[1][1] - coords[0][1]) / (coords[1][0] - coords[0][0])
            dist = coords[2][1] - (slope * coords[2][0]) + ((slope * coords[1][0]) - coords[1][1])
            dist /= np.sqrt(np.power(slope, 2) + 1)
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
        pixelinch = guidelength / self.SQ_TO_SQ

        rad = (pixelinch * self.SQ_TO_TARG)
        vx = center[0] - bottom[0]
        vy = center[1] - bottom[1]
        newlen = np.sqrt(vx * vx + vy * vy)
        targ1x = (rad * (vx / newlen)) + center[0]
        targ1y = (rad * (vy / newlen)) + center[1]
        targ3x = (rad * (vx / newlen)) + right[0]
        targ3y = (rad * (vy / newlen)) + right[1]

        target1 = (int(targ1x), int(targ1y))
        target3 = (int(targ3x), int(targ3y))
        target2 = ((np.abs(target1[0] + target3[0])) / 2, np.abs((target1[1] + target3[1])) / 2)

        im2 = cv2.imread(image, -1)
        if len(im2.shape) > 2:
            blue = im2[:, :, 0]
            green = im2[:, :, 1]
            red = im2[:, :, 2] - ((im2[:, :, 0] / 5) * 4)

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

            t1redmean = np.mean(targ1values[:, :, 2]) / 100
            t1greenmean = np.mean(targ1values[:, :, 1]) / 100
            t1bluemean = np.mean(targ1values[:, :, 0]) / 100
            t2redmean = np.mean(targ2values[:, :, 2]) / 100
            t2greenmean = np.mean(targ2values[:, :, 1]) / 100
            t2bluemean = np.mean(targ2values[:, :, 0]) / 100
            t3redmean = np.mean(targ3values[:, :, 2]) / 100
            t3greenmean = np.mean(targ3values[:, :, 1]) / 100
            t3bluemean = np.mean(targ3values[:, :, 0]) / 100

            yred = [0.87, 0.51, 0.23]
            yblue = [0.87, 0.51, 0.23]
            ygreen = [0.87, 0.51, 0.23]
            if self.CalibrationCameraModel.currentIndex() == 0 and 1 <= self.CalibrationFilter.currentIndex() <= 4:
                if self.CalibrationFilter.currentIndex() == 1:
                    yred = self.refvalues["850"][0]
                    ygreen = self.refvalues["850"][1]
                    yblue = self.refvalues["850"][2]
                elif self.CalibrationFilter.currentIndex() == 2:
                    yred = self.refvalues["650"][0]
                    ygreen = self.refvalues["650"][1]
                    yblue = self.refvalues["650"][2]
                elif self.CalibrationFilter.currentIndex() == 3:
                    yred = self.refvalues["548"][0]
                    ygreen = self.refvalues["548"][1]
                    yblue = self.refvalues["548"][2]
                elif self.CalibrationFilter.currentIndex() == 4:
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

            # self.CalibrationLog.append("Red Slope: " + str(redslope))
            # self.CalibrationLog.append("Red Intcpt: " + str(redintcpt))
            # self.CalibrationLog.append("Green Slope: " + str(greenslope))
            # self.CalibrationLog.append("Green Intcpt: " + str(greenintcpt))
            # self.CalibrationLog.append("Blue Slope: " + str(blueslope))
            # self.CalibrationLog.append("Blue Intcpt: " + str(blueintcpt))
            self.CalibrationLog.append("Found QR Target, please proceed with calibration.")

            return [redintcpt, redslope, greenintcpt, greenslope, blueintcpt, blueslope]

    # Calibration Steps: End


    # Helper functions
    def preProcessHelper(self, infolder, outfolder, customerdata=True):

        if self.PreProcessCameraModel.currentIndex() == 2 \
                or self.PreProcessCameraModel.currentIndex() == 3 \
                or self.PreProcessCameraModel.currentIndex() == 4 \
                or self.PreProcessCameraModel.currentIndex() == 5:
            infiles = []
            infiles.extend(glob.glob("." + os.sep + "*.[dD][nN][gG]"))
            counter = 0
            for input in infiles:
                self.PreProcessLog.append(
                    "processing image: " + str((counter) + 1) + " of " + str(len(infiles)) +
                    " " + input.split(os.sep)[1])
                QtGui.qApp.processEvents()
                self.openDNG(infolder + input.split('.')[1] + "." + input.split('.')[2], outfolder, customerdata)

                counter += 1
        # elif self.PreProcessCameraModel.currentIndex() == 0 \
        #          or self.PreProcessCameraModel.currentIndex() == 1 \
        #          or self.PreProcessCameraModel.currentIndex() == 2:
        #     os.chdir(infolder)
        #     infiles = []
        #     infiles.extend(glob.glob("." + os.sep + "*.[mM][aA][pP][iI][rR]"))
        #     infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF]"))
        #     infiles.extend(glob.glob("." + os.sep + "*.[tT][iI][fF][fF]"))
        #     counter = 0
        #     for input in infiles:
        #         self.PreProcessLog.append(
        #             "processing image: " + str((counter) + 1) + " of " + str(len(infiles)) +
        #             " " + input.split(os.sep)[1])
        #         QtGui.qApp.processEvents()
        #         filename = input.split('.')
        #         outputfilename = filename[1] + '.tiff'
        #
        #         self.openMapir(infolder + input.split('.')[1] + "." + input.split('.')[2], outfolder + outputfilename)
        #
        #
        #         counter += 1
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
                        QtGui.qApp.processEvents()
                    with open(input, "rb") as rawimage:
                        img = np.fromfile(rawimage, np.dtype('u2'), self.imsize).reshape((self.imrows, self.imcols))
                        color = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB)

                        filename = input.split('.')
                        outputfilename = filename[1] + '.tiff'
                        cv2.imencode(".tiff", color)
                        cv2.imwrite(outfolder + outputfilename, color)
                        if customerdata == True:
                            self.copyExif(infolder + infiles[counter + 1], outfolder + outputfilename)
                    counter += 2

            else:
                self.PreProcessLog.append(
                    "Incorrect file structure. Please arrange files in a RAW, JPG, RAW, JGP... format.")


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

    def openMapir(self, inphoto, outphoto):
        subprocess.call(
            [modpath + os.sep + r'"Mapir Converter.exe"', os.path.abspath(inphoto),
             os.path.abspath(outphoto)])

    def copyExif(self, inphoto, outphoto):
        if sys.platform == "win32":
            # with exiftool.ExifTool() as et:
            #     et.execute(r' -overwrite_original -tagsFromFile ' + os.path.abspath(inphoto) + ' ' + os.path.abspath(outphoto))

            subprocess.call(
                [modpath + os.sep + r'exiftool.exe', r'-overwrite_original', r'-addTagsFromFile',
                 os.path.abspath(inphoto),
                 r'-all:all<all:all',
                 os.path.abspath(outphoto)], startupinfo=si)
        elif sys.platform == "darwin":
            subprocess.call(
                [r'/usr/local/bin/exiftool', r'-overwrite_original', r'-addTagsFromFile', os.path.abspath(inphoto),
                 r'-all:all<all:all',
                 os.path.abspath(outphoto)])

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

