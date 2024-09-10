# BoM Water
A python tool for requesting data from BoM Sensor Observation Service (SOS2, as WaterML 2.0 format)

![website](https://img.shields.io/website?url=http%3A%2F%2Fwww.bom.gov.au%2Fwaterdata%2F)
![license](http://img.shields.io/badge/license-MIT-blue.svg) ![status](https://img.shields.io/badge/status-alpha-blue.svg) [![CI](https://github.com/csiro-hydroinformatics/pybomwater/actions/workflows/main.yml/badge.svg)](https://github.com/csiro-hydroinformatics/pybomwater/actions/workflows/main.yml) ![pypi](https://img.shields.io/pypi/v/pybomwater.svg?logo=python&logoColor=white) 
[![codecov](https://codecov.io/gh/csiro-hydroinformatics/pybomwater/branch/main/graph/badge.svg?token=uj1VUQu7dT)](https://codecov.io/gh/csiro-hydroinformatics/pybomwater)


This package has been developed to access to the BoM Water Data Sensor Observation Service (SOS) with a goal to easily and efficiently integrate data into scientific workflows  

## License
MIT-derived (see [License.txt](LICENSE))

## Installation
From pypi:

`pip install pybomwater`

From source:
- Using [`poetry`](https://python-poetry.org/docs/)
  - I like to keep the `.venv` in my project directory so I use `poetry config --local virtualenvs.in-project true`
  - `poetry install` which will install the dependencies listed in the `poetry.lock`
  - `poetry shell` which is initialize the environment within your running application (eg cmd), or in VS Code `Cmd+Shift+p` and then type `Python Interpreter` and select the environment you just built.

## Usage
see [Jupyter Notebook example](https://github.com/csiro-hydroinformatics/bomwater-notebook)

---
**NOTE**

The first time a BomWater object is instantiated (bm = bom_water.BomWater()) a cache of data is created.  This process obtains data from the BoM service and will take a little while to complete.  Once cached this process is not repeated and performance will return to normal.

---

## Documentation
Bureau of Meteorology (BoM) documentation on using their SOS service is available at the following links:
* [BoM Water Data service ](http://www.bom.gov.au/waterdata/services)
* [BoM Notes](http://www.bom.gov.au/metadata/catalogue/19115/ANZCW0503900528)
* [BoM Guide to Sensor Observation Services (SOS2)](https://github.com/csiro-hydroinformatics/bom_water/blob/main/doc/Guide_to_Sensor_Observation_Services_(SOS2)_for_Water_Data_Online_v1.0.1.pdf)

### [The following cells implement requests that access the BoM SOS2 service.](https://github.com/csiro-hydroinformatics/bom_water/blob/main/doc/Guide_to_Sensor_Observation_Services_(SOS2)_for_Water_Data_Online_v1.0.1.pdf#page=14) 
### GetCapabilties
Lists services available and the filters that can be used to select data output by those services. It also provides an overview of parameters, time series types and geographic area covered by the services.
### GetFeatureOfInterest
Provides details about a set of geographical features or locations at which observations are measured. They can be selected according to the parameter measured, type of time series available, and area or point location.
### GetDataAvailability
Lists the type of data available for a ‘feature of interest’ and its coverage. This includes a list of parameters, the time series types available for each of the parameters, and the observed period of record for each time series type.
### GetObservation
Returns observations of a specified ‘feature of interest’ and parameter, within a specific time series type. Each observation has a datetime, value, quality and interpolation type.

### [Parameter currently available via SOS2](https://github.com/csiro-hydroinformatics/bom_water/blob/main/doc/Guide_to_Sensor_Observation_Services_(SOS2)_for_Water_Data_Online_v1.0.1.pdf#page=13)
|Parameter | Water regulation Data Subcategory |
|:--- |:--- |
|Dry Air Temperature  |  4f  |
|Electrical Conductivity @ 25C  | 9a  |
|Evaporation  | 4c  |
|Ground Water Level  | 2a  |
|Rainfall  | 4a  |
|Relative Humidity  | 4h  |
|Storage Level  | 3a  |
|Storage Volume  | 3b  |
|Turbidity  | 9d  |
|Water Course Discharge (standard time series types)  | 1b  |
|Water Course Discharge (flood warning time series types)  | 11b  |
|Water Course Level (standard time series types)  | 1a  |
|Water Course Level (flood warning time series types)   | 11a  |
|Water pH  | 9g  |
|Water Temperature  | 9h  |
|Wind Direction  | 4  |
### [Timeseries pattern and aggreated available](https://github.com/csiro-hydroinformatics/bom_water/blob/main/doc/Guide_to_Sensor_Observation_Services_(SOS2)_for_Water_Data_Online_v1.0.1.pdf#page=37)
|Time series name | Procedure | Identifier Time series description |
|:---|:---|:---|
|DMQaQc.Merged.DailyMean.24HR| Pat1_C_B_1_DailyMean or Pat9_C_B_1_DailyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily means, reported from midnight to midnight. |
|DMQaQc.Merged.DailyMax.24HR | Pat1_C_B_1_DailyMax or Pat9_C_B_1_DailyMax | Maximum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight |
|DMQaQc.Merged.DailyMin.24HR | Pat1_C_B_1_DailyMin or Pat9_C_B_1_DailyMin | Minimum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.  |
|DMQaQc.Merged.MonthlyMean.CalMonth| Pat1_C_B_1_MonthlyMean or Pat9_C_B_1_MonthlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to monthly means. |
|DMQaQc.Merged.YearlyMean.CalYear | Pat1_C_B_1_YearlyMean or Pat9_C_B_1_YearlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to yearly means. |
|DMQaQc.Merged.DailyTotal.09HR | Pat2_C_B_1_DailyTot09 | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily totals, reported from 9am to 9am. |
|DMQaQc.Merged.DailyTotal.24HR|Pat2_C_B_1_DailyTot24 | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily totals,reported from midnight to midnight.|
|DMQaQc.Merged.MonthlyTotal.CalMonth|Pat2_C_B_1_MonthlyTot24 | DMQaQc.Merged.AsStored.1 timeseries aggregated to monthly totals.|
|DMQaQc.Merged.YearlyTotal.CalYear|Pat2_C_B_1_YearlyTot24 | DMQaQc.Merged.AsStored.1 timeseries aggregated to yearly totals.|
|DMQaQc.Merged.HourlyMean.HR|Pat3_C_B_1_HourlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to hourly means.|
|DMQaQc.Merged.DailyMean.24HR|Pat3_C_B_1_DailyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily means, reported from midnight to midnight.|
|DMQaQc.Merged.DailyMax.24HR |Pat3_C_B_1_DailyMax | Maximum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.DailyMin.24HR|Pat3_C_B_1_DailyMin | Minimum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.MonthlyMean.CalMonth|Pat3_C_B_1_MonthlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to monthly means.|
|DMQaQc.Merged.YearlyMean.CalYear|Pat3_C_B_1_YearlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to yearly means.|
|DMQaQc.Merged.HourlyMean.HR|Pat4_C_B_1_HourlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to hourly means.|
|DMQaQc.Merged.DailyMean.09HR| Pat4_C_B_1_DailyMean09 | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily means, reported from 9am to 9am.|
|DMQaQc.Merged.DailyMax.24HR|Pat4_C_B_1_DailyMax | Maximum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.DailyMin.24HR|Pat4_C_B_1_DailyMin | Minimum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.DailyMean.24HR|Pat4_C_B_1_DailyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to daily means, reported from midnight to midnight.|
|DMQaQc.Merged.MonthlyMean.CalMonth|Pat4_C_B_1_MonthlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to monthly means.|
|DMQaQc.Merged.YearlyMean.CalYear|Pat4_C_B_1_YearlyMean| DMQaQc.Merged.AsStored.1 timeseries aggregated to yearly means.|
|DMQaQc.Merged.HourlyMean.HR|Pat6_C_B_1_HourlyMean or Pat7_C_B_1_HourlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to hourly means.|
|DMQaQc.Merged.DailyMean.24HR|Pat6_C_B_1_DailyMean or Pat7_C_B_1_DailyMean|DMQaQc.Merged.AsStored.1 timeseries aggregated to daily means, reported from midnight to midnight.|
|DMQaQc.Merged.DailyMax.24HR|Pat6_C_B_1_DailyMax or Pat7_C_B_1_DailyMax | Maximum of values in theDMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.DailyMin.24HR|Pat6_C_B_1_DailyMin or Pat7_C_B_1_DailyMin | Minimum of values in the DMQaQc.Merged.AsStored.1 timeseries - from midnight to midnight.|
|DMQaQc.Merged.MonthlyMean.CalMonth|Pat6_C_B_1_MonthlyMean or Pat7_C_B_1_MonthlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to monthly means.|
|DMQaQc.Merged.YearlyMean.CalYear |Pat6_C_B_1_YearlyMean or Pat7_C_B_1_YearlyMean | DMQaQc.Merged.AsStored.1 timeseries aggregated to yearly means.|

## [Task list](https://github.com/csiro-hydroinformatics/bom_water/blob/main/tasklist.md)
