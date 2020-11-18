import unittest
import requests
import bom_water.bom_water as bm
import os
import shapely
from bom_water.spatial_util import spatail_utilty

class test_core(unittest.TestCase):

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

    def test_get_data_availability(self):
        '''Get Data availability test'''
        _bm = bm.BomWater()

    def test_get_observation(self):
        '''Get Observation test'''
        _bm = bm.BomWater()

    def test_create_feature_geojson_list(self):
        _bom = bm.BomWater()
        response = _bom.request(_bom.actions.GetFeatureOfInterest, None, None, None, None, None, "-37.505032 140.999283", "-28.157021 153.638824"  )
        response_json = _bom.xml_to_json(response.text)
        folder = f'C:\\Users\\fre171\\Documents\\pyBOMwater_dummyData\\test_stations.json'
        _bom.create_feature_list(response_json, folder )
