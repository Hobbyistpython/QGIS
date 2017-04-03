This directory contains the download link to a pre-packeged version of the plugin.

Windows Users: Please run QGIS as the administrator the first time you install our plugin. The next times you do not need to run as administrator.

## Attention: We've found a fatal flaw in trying to run the plugin on MacOS, Mac support will be discontinued until further notice

## Latest Version 1.0.9
#### [QGIS package](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_04032017.zip)

### [1.0.9] - 2017-04-03
#### Fixed
-Issue locating QR taget when supplied with a JPG.
-Issue processing images from Survey1 camera.

### [1.0.8] - 2017-03-07
#### Fixed
-Issue with Calibration step and inproper indexing of camera models.

### [1.0.7] - 2017-03-02
#### Changed
-Removed the Vignette correction and color normalization due to a critical flaw in the design. 
-Modified the UI to support lens and filter options for future use.

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

#### FIXED
- Plugin now warns when trying to overwrite tiffs created when preprocessing DNG images instead of throwing an exception.

### [0.0.3] - 2016-12-6
#### FIXED
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

## Previous Versions

#### [Version 1.0.8](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_03072017.zip)

#### [Version 1.0.7](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_03022017.zip)

#### [Version 1.0.6](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_02102017.zip)

#### [Version 1.0.5](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_02072017.zip)

#### [Version 1.0.4](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_01312017.zip)

#### [Version 1.0.3](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12192016.zip)

#### [Version 1.0.2](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12152016.zip)

#### [Version 1.0.1](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12142016.zip)

#### [Version 1.0.0](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12132016.zip)

#### [Version 0.0.3](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12062016.zip)

#### [Version 0.0.2](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12022016.zip)

#### [Version 0.0.1](http://www.docs.peauproductions.com/qgis/MAPIR_Processing_12012016.zip)
