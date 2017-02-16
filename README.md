# QGIS Distribution for MAPIR Cameras
This repository contains the QGIS distribution for use with MAPIR cameras. The distribution is in a beta stage while we work on getting it placed in the QGIS plugin repository.

Camera supported:
- MAPIR Survey2 (all filter models)
- DJI Inspire X3 with [PEAU 3.97mm NDVI (Red+NIR) lens](http://www.peauproductions.com/products/gp39728) installed
- DJI Phantom 4 & 3 with [PEAU 3.97mm NDVI (Red+NIR) lens](http://www.peauproductions.com/products/gp39728) installed

Functionality for above supported cameras includes:
- Convert Survey2 RAW to TIFF, converts DJI DNG to TIFF
- Calibrate directory of images using [MAPIR Reflectance Target](http://www.mapir.camera/collections/accessories/products/mapir-camera-calibration-ground-target-package) image taken before survey or uses built-in reflectance values if no target image supplied
- Converts TIFF to JPG after calibration if desired

Functionality still in the works:
- Creating index images

### Installation
- Download and install QGIS program [HERE](http://www.qgis.org/en/site/forusers/download.html)
- Download the [MAPIR_Processing folder](https://github.com/mapircamera/QGIS/tree/master/Packages), unzip it and add it to your .qgis2/python/plugins folder. In Windows, the .qgis2 folder is in C:\Users\(your computer user name).
- Start QGIS as an administrator (right mouse click, run as admin).
- In the top Plugin menu bar, choose the MAPIR plugin.

##Attention: We've found a fatal flaw in trying to run the plugin on MacOS, Mac support will be discontinued until further notice


### Using Plugin

- To pre-process images (convet RAW images to TIFFs):
-- Select the "Pre-Process" tab
-- Select a camera model
-- Select an input folder
-- Select an output folder
-- Press the "Pre-Process Images" button

- To Calibrate images
-- Select the "Calibrate" tab
-- Select a camera model
-- Select a MAPIR ground target image (optional)
-- Press the "Generate Calibration Values" button
-- Select a folder containing images to calibrate
-- Press the "Calibrate Images From Directory" button

### Credits
 - [Photomonitoring Plugin](https://github.com/nedhorning/PhotoMonitoringPlugin) by Ned Horning - American Museum of Natural History, Center for Biodiversity and Conservation

## Change Log
All notable changes to this project will be documented in this file.

### [1.0.6] - 2017-02-10
#### Changed
-Plugin now allows for users to trun vignette correction on/off

### [1.0.5] - 2017-02-07
#### Fixed
-EXIF information now properly copied, including geotagging information
-Program no longer tries to read GDAL projections from images other than GeoTIFFs

### [1.0.4] - 2017-01-31
#### Added
-Vignette correction

#### Changed
-Vignette correction and normalization are now always performed

#### Fixed
-Plugin now transfers projection data in preprocess and calibrate steps

### [1.0.3] - 2016-12-19
#### Added
- Normalization of RGB images in the Preprocess step.

### [1.0.2] - 2016-12-15
#### ADDED
- Transfer of GeoTIFF metadata.

#### CHANGED
- Application no longer requires administrator access to run on Windows.

#### FIXED
- Plugin no longer loads non image files with "tif" or "jpg" in the filepath.

### [1.0.1] - 2016-12-13
#### ADDED
- Legacy support for Survey1 camera models in Calibrate tab.

### [1.0.0] - 2016-12-13
#### ADDED
- MacOS X is now supported

#### Fixed
- Plugin now warns when trying to overwrite tiffs created when preprocessing DNG images instead of throwing an exception.

### [0.0.3] - 2016-12-6
#### Fixed
- Tiffs now properly convert to Jpegs when checking the "Convert calibrated tiffs to jpgs" box

#### TO DO
- Found issues when trying to install plugin on Mac OSX. Working on a solution.

### [0.0.2] - 2016-12-2
#### ADDED
- Now stores previously selected filepaths to make navigation easier

#### Changed
- Cleaned up UI layout

#### FIXED
- Missing default calibration for DKI camera models
- QR calibration percentage values

### [0.0.1] - 2016-12-1
#### FIXED
- Issue with merging channels in DJIx3 images


