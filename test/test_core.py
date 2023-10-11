import unittest
import types
import requests
import bom_water.bom_water as bm
import os
from pathlib import Path
import shapely
from bom_water.spatial_util import spatail_utilty

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
        response = _bm.request(_bm.actions.GetFeatureOfInterest,
                                   "http://bom.gov.au/waterdata/services/stations/GW036501.2.2")
        test_json = _bm.xml_to_json(response.text)#, f'test_GetFeatureOfInterest.json')
        features = test_json['soap12:Envelope']['soap12:Body']['sos:GetFeatureOfInterestResponse'][
            'sos:featureMember']
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
        ts = _bm.parse_get_data(response)

        assert ts.shape[1] == 3
        assert ts.columns[0] == 'Value[cumec]'
        assert (ts.Interpolation == "Continuous").all()

        qual = ts.Quality.value_counts()
        assert qual[90] == 1075
        assert qual[10] == 295
        assert qual[110] == 172


    def test_get_data_availability(self):
        '''Get Data availability test'''
        _bm = bm.BomWater()


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
        df = _bm.get_observations(features, prop, proced, t_begin, t_end)
        assert len(df) > 0, "No observational data found"

    def test_get_obs_diff(self):
        '''Get Observation test'''
        _bm = bm.BomWater()
        t_begin = "2016-01-01T00:00:00+10"
        t_end = "2019-12-31T00:00:00+10"

        features = []
        features.append(_bm.features.West_of_Dellapool)
        features.append(_bm.features.LK_VIC)
        
        prop = _bm.properties.Ground_Water_Level
        proced = _bm.procedures.Pat9_C_B_1
        try:
            response = _bm.request( _bm.actions.GetObservation, features,
                                   prop, proced, t_begin, t_end)
        except Exception as e:
            assert False, f"Test GetObservation failed requestException: {e}"
        df_1 = _bm.parse_get_data(response)
        # df_2 = _bm.get_observations(features, prop, proced, t_begin, t_end)
        for feature in features:
            da_1 = df_1[feature]

            assert df_1['values'].equals(df_2['values'])
   
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

if __name__ == '__main__':
    unittest.main()
