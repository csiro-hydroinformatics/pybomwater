import json
import unittest
from datetime import datetime
from dateutil import parser
import types
import pytest
import requests
import pybomwater.bom_water as bm
import os
from pathlib import Path
from pybomwater.spatial_util import spatail_utilty
from geojson import Feature, FeatureCollection, Point
import json
import xarray as xr
import shapely
import numpy as np

import requests
import xmltodict
import pandas as pd

FTEST = Path(__file__).resolve().parent

class test_core(unittest.TestCase):

    # def __init__(self):
    #     super(test_core, self).__init__(self)
    #     self.setUp()

    @classmethod
    def setUpClass(self):
        print('Dont do this for a moment')
        # remove_file = Path.home() / "bom_water" / "cache" / \
        #                     "waterML_GetCapabilities.json"
        # if remove_file.exists():
        #     remove_file.unlink()

    # def test_user_path(self):
    #     from pathlib import Path
    #     print(Path.home())



    def test_bom_service(self):
        '''Test that the service is up
        :rtype: None
        '''
        _bm = bm.BomWater()
        try:
            response = _bm.request(_bm.actions.GetCapabilities)
            if response.status_code == 200:
                assert True, "Test BoM service passed"
            else:
                assert False, f'Test BoM service failed with status_code: {response.status_code}'
        except requests.exceptions.RequestException as e:
            assert False, f'Test BoM service failed with RequestException: {e}'
        except requests.exceptions.ConnectionError as ece:
            assert False, f'Test BoM service failed with ConnectionError: {ece}'
        except requests.exceptions.Timeout as et:
            assert False, f'Test BoM service failed with Timeout: {et}'

    def test_get_capabilities(self):
        '''Get Capabilities test'''
        _bm = bm.BomWater()
        response = _bm.request(_bm.actions.GetCapabilities)
        test_json = _bm.xml_to_json(response.text)#, f'test_GetCapabilities.json')
        actions = test_json['sos:Capabilities']['ows:OperationsMetadata']['ows:Operation']
        for action in actions:
            for property, value in vars(_bm.actions).items():
                if not action['@name'] == 'DescribeSensor':
                    if property == action['@name']:
                        print(value)
                        assert True, f'Test GetCapabilities passed'
                        continue

                assert False, f'Test GetCapabilities, falied to get action: expected {action}'

    def test_get_feature_of_interest(self):
        '''Get Feature of interest test'''
        _bm = bm.BomWater()
        '''Todo: Need a small bounding box with known stations contained'''
        response = _bm.request(_bm.actions.GetFeatureOfInterest, "http://bom.gov.au/waterdata/services/stations/GW036501.2.2")
        test_json = _bm.xml_to_json(response.text)#, f'test_GetFeatureOfInterest.json')
        features = test_json['soap12:Envelope']['soap12:Body']['sos:GetFeatureOfInterestResponse']['sos:featureMember']
        long_statioId = features['wml2:MonitoringPoint']['gml:identifier']['#text']
        if os.path.basename(long_statioId) == 'GW036501.2.2':
            assert True, "Test GetFeatureOfInterest passed"
        else:
            assert False, "Test GetFeatureOfInterest falied"

    def test_parse_get_data(self):
        '''Test parsing time series'''
        # Generate fictive response object
        with (FTEST / "test_data" / "response.xml").open("r") as fo:
            resp_text = fo.read()
        response = types.SimpleNamespace()
        response.text = resp_text

        _bm = bm.BomWater()
        result = _bm.parse_data(response)
        ts = result['http://bom.gov.au/waterdata/services/stations/915011A']

        # assert ts.shape[1] == 3
        assert ts.data_vars.__contains__('Water Course Discharge [cumec]'), "Values not found"
        assert (ts.Interpolation == "Continuous").all(), "Interpolation not continuous"
        assert len(ts.dims) == 1

        qual = xr.CFTimeIndex.value_counts(ts.Quality.values)
        assert qual[90] == 1075
        assert qual[10] == 295
        assert qual[110] == 172


    def test_get_data_availability(self):
        '''Get Data availability test'''
        _bm = bm.BomWater()
        t_begin = "1930-01-01T00:00:00+10"
        t_end = "2024-12-31T00:00:00+10"

        features = []
        features.append('http://bom.gov.au/waterdata/services/stations/410061')
        procedure = _bm.procedures.Pat4_C_B_1_DailyMean
        prop = _bm.properties.Water_Course_Discharge

        response = _bm.request(_bm.actions.GetDataAvailability, features, prop=None, proced=None, begin=t_begin, end=t_end, lower_corner=None, upper_corner=None)
        #This needs a parser
        print(response.text)
        assert response.status_code == 200

    def test_get_observation(self):
        '''Get Observation test'''
        _bm = bm.BomWater()
        t_begin = "2016-01-01T00:00:00+10"
        t_end = "2019-12-31T00:00:00+10"

        features = []
        features.append(_bm.features.West_of_Dellapool)
        features.append(_bm.features.LK_VIC)
        prop = _bm.properties.Ground_Water_Level
        proced = _bm.procedures.Pat9_C_B_1
        bbox = [None, None]
        results = _bm.get_observations(features, prop, proced, t_begin, t_end, bbox)
        for result in results:
            assert len(result) > 0, "No observational data found"
            assert result[_bm.features.West_of_Dellapool].property == prop
            assert result[_bm.features.LK_VIC].procedure == proced

    def test_get_observation_check_daily(self):
        '''Get Observation test'''
        _bm = bm.BomWater()
        t_begin = "1800-01-01T00:00:00+10"
        t_end = "2030-12-31T00:00:00+10"

        features = []
        f= _bm.features.MOWAMBA___LYNWOOD#'http://bom.gov.au/waterdata/services/stations/222027'
        features.append(f)

        prop = _bm.properties.Water_Temperature
        proced = _bm.procedures.Pat1_C_B_1_DailyMean
        bbox = [None,None]
        results = _bm.get_observations(features, prop, proced, t_begin, t_end, bbox=bbox)
        for result in results:
            da = result[f]
            assert len(results) > 0, "No observational data found"
            assert da.property == prop
            assert da.procedure == proced
            assert len(np.unique(da.time)) == len(da.time), 'Multiple values for daily data, there should be unique daily values!'

        #test slicing
        t_begin = "2002-01-20"
        t_end = "2002-01-26"
        one_week = da.sel(time=slice(t_begin, t_end))
        df_week = _bm.get_observations(features, prop, proced, f'{t_begin}T00:00:00+10', f'{t_end}T00:00:00+10', bbox)
        da_week = df_week[0][f]
        assert one_week == da_week

        # data = xr.open_dataset('./test/test_data/mdb_water_temp/222027.nc')
        # assert data.equals( df['http://bom.gov.au/waterdata/services/stations/222027'])

    def test_create_feature_geojson_list(self):
        _bom = bm.BomWater()
        response = _bom.request(_bom.actions.GetFeatureOfInterest, None, None, None, None, None, "-37.505032 140.999283", "-28.157021 153.638824"  )
        response_json = _bom.xml_to_json(response.text)
        fsta = FTEST / "test_data" / "test_station.json"
        fsta.parent.mkdir(exist_ok=True)
        _bom.create_feature_list(response_json, str(fsta) )

    def test_list_features(self):
        _bom = bm.BomWater()
        all_features = _bom.features.__dict__
        assert len(all_features) > 0, "Not features found"
        for key in all_features:
            print(f'Key: {key}, Value: {all_features[key]}')


    def test_get_features_of_interest(self):
        _bm = bm.BomWater()
        procedure = _bm.procedures.Pat1_C_B_1_DailyMean
        prop = _bm.properties.Water_Temperature
        features = []
        features.append(_bm.features.Long_Gully_at_Philip)
        features.append(_bm.features.Loveday_Disposal_Basin_at_Cobdogla_Swamp)
        response = _bm.request(_bm.actions.GetFeatureOfInterest, features, None, None, None, None, None, None  )
        response_json = _bm.xml_to_json(response.text)
        '''bomwater creates a FeatureCollection which can be used for mapping'''
        feature_list = _bm.create_feature_list(response_json, None )
        su = spatail_utilty()
        mdb_sites = su.filter_feature_list(feature_list, './test/test_data/Spatial/mdb_buffer_1km.shp', False)

        for site in mdb_sites['features']:
            if features.__contains__(site['properties']['long_name']):
                assert True
            else:
                assert False, "Feature not found"

    def test_check_what_available(self):
        '''Get Data availability test'''
        _bm = bm.BomWater()
        t_begin = "1930-01-01T00:00:00+10"
        t_end = "2024-12-31T00:00:00+10"
        # Setup bounding box for BoM api spatial filter query
        low_left_lat = -37.505032
        low_left_long = 138.00
        upper_right_lat = -24.00
        upper_right_long = 154.00

        lower_left_coords = f'{low_left_lat} {low_left_long}'
        upper_right_coords = f'{upper_right_lat} {upper_right_long}'

        features = []
        feat = 'http://bom.gov.au/waterdata/services/stations/410061'
        features.append(feat)
        response =  _bm.request(_bm.actions.GetDataAvailability, features)
        # response = _bm.request(_bm.actions.GetDataAvailability, features, prop=None, proced=None, begin=t_begin, end=t_end, lower_corner=lower_left_coords, upper_corner=upper_right_coords)
        assert response.status_code == 200, "Response error"
        response_json = _bm.xml_to_json( response.text)
        features_availabilities = response_json['soap12:Envelope']['soap12:Body']['gda:GetDataAvailabilityResponse']['gda:dataAvailabilityMember']
        for feature in features_availabilities: 
            procedure_title = feature['gda:procedure']['@xlink:title']
            observation_property_title = feature['gda:observedProperty']['@xlink:title']
            feature_of_interest_title = feature['gda:featureOfInterest']['@xlink:title']
            feature_of_interest_href = feature['gda:featureOfInterest']['@xlink:href']
            if 'gml:TimePeriod' in feature['gda:phenomenonTime']:
                start_period = feature['gda:phenomenonTime']['gml:TimePeriod']['gml:beginPosition']
            else:
                start_period = '1900-01-01T00:00:00.000+10:00'
            if 'gml:TimePeriod' in feature['gda:phenomenonTime']:
                end_period = feature['gda:phenomenonTime']['gml:TimePeriod']['gml:endPosition']
            else:
                end_period = '1900-01-02T00:00:00.000+10:00'

            assert feature_of_interest_href == feat, 'Feature not found'
            assert procedure_title, 'Procedure is None'
            assert observation_property_title, 'Property is None'
            assert feature_of_interest_title, 'FOI is None'
            assert start_period, 'Start period is None'
            assert end_period, 'End period is None'
            assert self.is_positive_date_period(start_period, end_period), 'Date periods error' 
        
    def is_positive_date_period(self, start_period, end_period):
        # Convert string dates to datetime objects
        start = parser.parse(start_period)
        end = parser.parse(end_period)
        
        # Calculate the difference
        date_diff = end - start
        
        # Check if the difference is positive
        return date_diff.total_seconds() >= 0
       
    def dont_test_list_index_out_of_range(self):
        _bm = bm.BomWater()
        procedure = _bm.procedures.Pat1_C_B_1_DailyMean
        prop = _bm.properties.Water_Temperature

        # Setup bounding box for BoM api spatial filter query
        low_left_lat = -37.505032
        low_left_long = 138.00
        upper_right_lat = -24.00
        upper_right_long = 154.00

        lower_left_coords = f'{low_left_lat} {low_left_long}'
        upper_right_coords = f'{upper_right_lat} {upper_right_long}'
        coords = tuple((lower_left_coords, upper_right_coords))

        t_begin = "1800-01-01T00:00:00+10"
        t_end = "2030-12-31T00:00:00+10"

        spat_dir = r'.\\test\\test_data\\Spatial'
        spatial_path = os.path.join( spat_dir, 'mdb_buffer_1km.shp')#'./test/test_data/Spatial/mdb_buffer_1km.shp'#
        assert os.path.exists(spatial_path)

        results = _bm.get_spatially_filtered_observations( None, str(spatial_path), coords, prop, procedure, t_begin, t_end)
        assert len(results) > 0, 'No results found'

    def divide_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def test_coords(self):
        low_left_lat =  -35.413204
        low_left_long = 149.047814
        upper_right_lat = -35.406226
        upper_right_long = 149.064809

        lower_left_coords = f'{low_left_lat} {low_left_long}'
        upper_right_coords = f'{upper_right_lat} {upper_right_long}'
        coords = tuple((lower_left_coords, upper_right_coords))
        assert coords[0] == lower_left_coords
        assert coords[1] == upper_right_coords
    

    def test_duplicate_dates(self):
        _bm = bm.BomWater()
        procedure = _bm.procedures.Pat4_C_B_1_DailyMean
        prop = _bm.properties.Water_Course_Discharge
        low_left_lat = -37.505032
        low_left_long = 138.00
        upper_right_lat = -24.00
        upper_right_long = 154.00

        lower_left_coords = f'{low_left_lat} {low_left_long}'
        upper_right_coords = f'{upper_right_lat} {upper_right_long}'
        coords = tuple((lower_left_coords, upper_right_coords))
        t_begin = "2000-01-01T00:00:00+10"
        t_end = "2024-12-31T00:00:00+10"

        spatial_path = './test/test_data/Spatial/test_filter_layer.shp'#os.path.join(spatial_test_data_path, 'mdb_buffer_1km.shp')
        results = _bm.get_spatially_filtered_observations( None, spatial_path, coords, prop, procedure, t_begin, t_end)
        for r in results:
            for d in r:
                assert f'{len(np.unique(r[d].time)) == len(r[d].time)} {d}', f'Station: {d} does not have unique daily values, { xr.CFTimeIndex.value_counts(r[d].time)}'

    def test_single_feature_obs(self):
        '''Get Observation test'''
        _bm = bm.BomWater()
        t_begin = "1930-01-01T00:00:00+10"
        t_end = "2024-12-31T00:00:00+10"

        features = []
        features.append('http://bom.gov.au/waterdata/services/stations/410061')
        features.append('http://bom.gov.au/waterdata/services/stations/410733')
        features.append('http://bom.gov.au/waterdata/services/stations/410071')
        features.append('http://bom.gov.au/waterdata/services/stations/410700')
        features.append('http://bom.gov.au/waterdata/services/stations/410747')
        features.append('http://bom.gov.au/waterdata/services/stations/410752')
        features.append('http://bom.gov.au/waterdata/services/stations/410070')
        features.append('http://bom.gov.au/waterdata/services/stations/410750')
        features.append('http://bom.gov.au/waterdata/services/stations/410719')
        features.append('http://bom.gov.au/waterdata/services/stations/410038')
        features.append('http://bom.gov.au/waterdata/services/stations/410061')
        features.append('http://bom.gov.au/waterdata/services/stations/41000269')

        procedure = _bm.procedures.Pat4_C_B_1_DailyMean
        prop = _bm.properties.Water_Course_Discharge
        bbox = [None, None]
        results = _bm.get_observations(features, prop, procedure, t_begin, t_end, bbox)
        for r in results:
            for station in r:
                da = r[station]
                assert len(da) > 0, "No observational data found"
                assert da.property == prop, f'Station: {station} properties are incorrect'
                assert len(np.unique(da.time)) == len(da.time), f'Station: {station} does not have unique daily values, { xr.CFTimeIndex.value_counts(da.time)}'


    def test_filtered_get_observations(self):
        _bm = bm.BomWater()
        procedure = _bm.procedures.Pat1_C_B_1_DailyMean
        prop = _bm.properties.Water_Temperature
        #Single gauge 
        stationNo = "410779"
        coordinates = [ 149.057806, -35.406972]
        #Bounding for single station
        low_left_lat =  -35.413204
        low_left_long = 149.047814
        upper_right_lat = -35.406226
        upper_right_long = 149.064809
        #Whole of the MDB
        # low_left_lat = -37.505032
        # low_left_long = 138.00
        # upper_right_lat = -24.00
        # upper_right_long = 154.00

        lower_left_coords = f'{low_left_lat} {low_left_long}'
        upper_right_coords = f'{upper_right_lat} {upper_right_long}'
        coords = tuple((lower_left_coords, upper_right_coords))

        t_begin = "1930-01-01T00:00:00+10"
        t_end = "2024-12-31T00:00:00+10"

        spatial_path = './test/test_data/Spatial/test_filter_layer.shp'#./test/test_data/Spatial/mdb_buffer_1km.shp'
        results = _bm.get_spatially_filtered_observations( None, spatial_path, coords, prop, procedure, t_begin, t_end)
        
        # This test can be used on a local machine for writing to disk
        #a_path = ''
        # for r in results:
        #     paths = []
        #     for set in r:
        #         base_path = f'./test/test_data/mdb_water_temp'
        #         file_name = f'{os.path.basename(set)}.nc'
        #         paths.append(os.path.join(base_path, file_name))
        #     a_path = paths[0]
        #     xr.save_mfdataset(r.values(), paths, mode='w', format="NETCDF4", groups=None, engine=None, compute=True )

        data = results[0]['http://bom.gov.au/waterdata/services/stations/410779']#xr.open_dataset(a_path)
        #Correct coordinates and station found
        assert all([a == b for a, b in zip(data.coordinates, coordinates)]), "Not expected coordinates"
        assert stationNo == os.path.basename(data.station_no), "Not expected station"
        assert len(data.dims) == 1


    def load_nc_file(self):
        path = './test/test_data/mdb_water_temp/222027.nc'
        data = xr.open_dataset(path)
        assert data != None

    def test_list_bomWater_metadata(self):
        #Use this is debug mode to obtain print statements in the Debug console
        # _bm = bm.BomWater()
        # print(_bm.actions.__dict__)
        # print(_bm.properties.__dict__)
        # print(_bm.procedures.__dict__)
        # print(_bm.feature_of_interest.__dict__)
        # self.write_json_features(_bm.feature_of_interest.__dict__, './test_data/features.json')
        assert True

    def test_load_json_stations(self):
        # {'geometry': {'coordinates': [149.315944, -33.956499], 'type': 'Point'}, 'properties': {'long_name': 'http://bom.gov.au/waterdata/services/stations/41200209', 'name': 'ABERCROMBIE_@_ABER#2', 'stationId': None, 'stationNo': '41200209'}, 'type': 'Feature'}
        result = [149.057806, -35.406972]
        target = '410779'
        answer = spatail_utilty.find_station_coordinates_from(target, None, './test/test_data/mdb_Watertemp_stations.json')
        assert answer == result, 'Incorrect find'

        with open('./test/test_data/mdb_Watertemp_stations.json') as json_file:
            stations =  json.load(json_file)
        answer = spatail_utilty.find_station_coordinates_from(target, stations, None)
        assert answer == result, 'Incorrect find'

        target = '410779'
        with pytest.raises(Exception):
            answer = spatail_utilty.find_station_coordinates_from(target, None, None)

        target = 'not_in_list'
        with pytest.raises(Exception):
            answer = spatail_utilty.find_station_coordinates_from(target, stations=stations, path=None)


    def get_capabilities(self, url):
        response = requests.get(url)
        # Parse the XML response
        data = xmltodict.parse(response.content)

        # Extracting service metadata
        capabilities_info = data.get('sos:Capabilities', {})
        
        # Extracting service identification and provider details
        service_info = capabilities_info.get('ows:ServiceIdentification', {})
        provider_info = capabilities_info.get('ows:ServiceProvider', {})

        # Extracting available offerings (e.g., observations)
        offerings = capabilities_info.get('sos:contents', {}).get('sos:Contents', {}).get('swes:offering', {})# capabilities_info.get('sos:Contents', {}).get('swes:offering', {}).get('sos:ObservationOffering', [])

        # Convert offerings to a more user-friendly format (e.g., DataFrame)
        offerings_list = []
        for offering in offerings:
            offering_details = {
                'Offering ID': offering.get('@gml:id', 'N/A'),
                'Procedure': offering.get('sos:procedure', 'N/A'),
                'ObservableProperty': offering.get('sos:observableProperty', 'N/A'),
                'FeatureOfInterest': offering.get('sos:featureOfInterest', 'N/A'),
                'TimePeriod': offering.get('gml:timePeriod', {}).get('gml:beginPosition', 'N/A') + " to " +
                            offering.get('gml:timePeriod', {}).get('gml:endPosition', 'N/A')
            }
            offerings_list.append(offering_details)

        # Create DataFrame for offerings
        offerings_df = pd.DataFrame(offerings_list)

        # Service info as a summary
        service_summary = {
            'Title': service_info.get('ows:Title', 'N/A'),
            'Abstract': service_info.get('ows:Abstract', 'N/A'),
            'Provider Name': provider_info.get('ows:ProviderName', 'N/A'),
            'Service Type': service_info.get('ows:ServiceType', 'N/A'),
            'Service Version': capabilities_info.get('@version', 'N/A'),
        }

        return service_summary, offerings_df
    
    def future_test_get_cap(self):
        #TODO In the future the response text needs to be parsed into something usable.  Continue this test with intent to parse the xml into pandas tables
        url = "http://www.bom.gov.au/waterdata/services?service=SOS&request=GetCapabilities"
        service_summary, offerings_df = self.get_capabilities(url)
        print(service_summary)
        print(offerings_df)

    def future_test_get_feature_of_interest(self):
        #TODO In the future the response text needs to be parsed into something usable.  Continue this test with intent to parse the xml into pandas tables
        print("Results")

    def future_test_data_availability(self):
        #TODO In the future the response text needs to be parsed into something usable.  Continue this test with intent to parse the xml into pandas tables
        print("Results")

    def future_test_get_observation(self):
        #TODO In the future the response text needs to be parsed into something usable.  Continue this test with intent to parse the xml into pandas tables
        print("Results")

if __name__ == '__main__':
    unittest.main()
