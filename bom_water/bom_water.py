import requests
import iso8601
import pytz
import json
import xmltodict
import os
from pathlib import Path
import re
import pandas as pd
import xml.etree.ElementTree as ET
import appdirs as ad
from bom_water.spatial_util import spatail_utilty

_APPNAME = "pybomwater"
_APPAUTHOR = "csiro"
_U_DATA_DIR = ad.user_data_dir(_APPNAME, _APPAUTHOR)
_U_CACHE_DIR = ad.user_cache_dir(_APPNAME, _APPAUTHOR)
if not os.path.exists(_U_CACHE_DIR):
    os.makedirs(_U_CACHE_DIR, mode = 0o700, exist_ok = True)

_U_CACHE_GET_CAP = os.path.join(_U_CACHE_DIR, 'waterML_GetCapabilities.json') 

def xml_to_json(self, xml_text, file):
    data_dict = dict(xmltodict.parse(xml_text))
    with open(file, 'w+') as json_file:
        json.dump(data_dict, json_file, indent=4, sort_keys=True)

    with open(file) as json_file:
        return json.load(json_file)

class Builder_Property():
    def __init__(self):
        pass

    def set_value(self, varname, value):
        self.__dict__[varname] = value


class Action:
    def __init__(self):
        pass

    # GetDescribeSensor = 'http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=DescribeSensor'
    GetCapabilities = 'http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=GetCapabilities'
    # GetDataAvailability = "http://www.opengis.net/def/serviceOperation/sos/daRetrieval/2.0/GetDataAvailability"
    # GetObservation = "http://www.opengis.net/def/serviceOperation/sos/core/2.0/GetObservation"
    # GetFeatureOfInterest = "http://www.opengis.net/def/serviceOperation/sos/foiRetrieval/2.0/GetFeatureOfInterest"
    GetDataAvailability = "http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=GetDataAvailability"
    GetObservation = "http://www.opengis.net/def/serviceOperation/sos/core/2.0/GetObservation"
    GetFeatureOfInterest = "http://www.opengis.net/def/serviceOperation/sos/foiRetrieval/2.0/GetFeatureOfInterest"


class Feature(Builder_Property):
    def __init__(self):
        pass

class Property(Builder_Property):
    def __init__(self):
        pass

    def set_value(self, varname, value):
        prop_name = varname.replace(' ', '_')
        self.__dict__[prop_name] = value


class Procedure(Builder_Property):
    def __init__(self):
        pass


class BomWater():

    def __init__(self):
        # self._module_dir = os.path.dirname(__file__)
        self.actions = Action()
        self.features = Feature()
        self.properties = Property()
        self.procedures = Procedure()

        self.cache = os.path.join(str(os.path.expanduser("~")), 'bom_water', 'cache')
        self.waterML_GetCapabilities = os.path.join(self.cache, 'waterML_GetCapabilities.json')
        self.stations = os.path.join(self.cache, 'stations.json')
        self.check_cache_status()#This should move to user space not be in module space
        self.init_properties()

    def check_cache_status(self):
        if os.path.exists(self.waterML_GetCapabilities):
            return
        else:
            print(f'one time creating cache directory and files, this will take a little time please wait.')
            if not os.path.exists(self.cache):
                os.makedirs(self.cache)

            response = self.request(self.actions.GetCapabilities)
            self.xml_to_json_via_file(response.text, self.waterML_GetCapabilities)
            response = self.request(self.actions.GetFeatureOfInterest)

            self.create_feature_list(self.xml_to_json(response.text), self.stations)
            # self.xml_to_json_via_file(response.text, os.path.join(self._module_dir, 'cache/stations.json'))
            print(f'finished creating cache directory and files')

    def init_properties(self):
        getCap_json = ''
        with open(self.waterML_GetCapabilities) as json_file:
            getCap_json = json.load(json_file)

        '''actions'''
        #         operations = getCap_json['sos:Capabilities']['ows:OperationsMetadata']['ows:Operation']
        #         for ops in operations:
        #         #     water_ml_b.actions.set_value(ops['@name'],ops['@name'])

        '''Properties'''
        properties = getCap_json['sos:Capabilities']['sos:contents']['sos:Contents']['swes:observableProperty']
        for prop in properties:
            p = os.path.basename(prop)
            self.properties.set_value(p, p)

        '''Procedures'''
        offerings = getCap_json['sos:Capabilities']['sos:contents']['sos:Contents']['swes:offering']
        for off in offerings:
            proc = os.path.basename(off['sos:ObservationOffering']['swes:procedure'])
            proc = re.sub('\W+', '_', proc)
            self.procedures.set_value(proc, proc)

        '''Features'''
        getfeature_json = ''
        with open(self.stations) as json_file:
            getfeature_json = json.load(json_file)
        # features = getfeature_json['longName']
        for index in range(len(getfeature_json['features'])):
            long_statioId = getfeature_json['features'][index]['properties']['long_name']

            name =  getfeature_json['features'][index]['properties']['name']
            name = re.sub('\W+', '_', name)
            # stationId = getfeature_json['stationID']stationID
            self.features.set_value(name, long_statioId)

    def xml(self):
        ''' XML payload builder'''
        return '''<?xml version="1.0" encoding="UTF-8"?>'''

    def envelope_head(self):
        return """<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" xmlns:sos="http://www.opengis.net/sos/2.0" xmlns:wsa="http://www.w3.org/2005/08/addressing" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:fes="http://www.opengis.net/fes/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:swes="http://www.opengis.net/swes/2.0" xsi:schemaLocation="http://www.w3.org/2003/05/soap-envelope http://www.w3.org/2003/05/soap-envelope/soap-envelope.xsd http://www.opengis.net/sos/2.0 http://schemas.opengis.net/sos/2.0/sos.xsd">"""

    def envelope_tail(self):
        return "</soap12:Envelope>"

    def header_action(self, action):
        return f"<soap12:Header><wsa:To>http://www.ogc.org/SOS</wsa:To><wsa:Action>{action}</wsa:Action><wsa:ReplyTo><wsa:Address>http://www.w3.org/2005/08/addressing/anonymous</wsa:Address></wsa:ReplyTo><wsa:MessageID>0</wsa:MessageID></soap12:Header>"

    def body(self, action, feature, prop, proced, begin, end, lower_corner, upper_corner):

        act = os.path.basename(action)

        proc = ''
        if not proced == None:
            proc = self.procedure(proced)
        obs = ''
        if not prop == None:
            obs = self.observed_property(prop)
        feat = ''  # feature_of_interest(feature)
        if not feature == None:
            feat = self.feature_of_interest(feature)
        temp_f = ''
        if not begin == None and not end == None:
            temp_f = self.temp_filter(begin, end)

        spatial_filter = ''
        if not lower_corner == None and not upper_corner == None:
            spatial_filter = self.spatial(action, lower_corner, upper_corner)

        return f"<soap12:Body><sos:{act} service=\"SOS\" version=\"2.0.0\">{proc}{obs}{spatial_filter}{feat}{temp_f}</sos:{act}></soap12:Body>"

    def temp_filter(self, begin, end):
        temporal_filter = f"<sos:temporalFilter>"
        during = f"<fes:During>"

        value_ref = f"<fes:ValueReference>om:phenomenonTime</fes:ValueReference>"

        t_period = f"<gml:TimePeriod gml:id=\"tp1\">"
        begin_pos = f"<gml:beginPosition>{begin}</gml:beginPosition>"
        end_pos = f"<gml:endPosition>{end}</gml:endPosition>"
        time_per_close = f"</gml:TimePeriod>"

        during_close = f"</fes:During>"
        temp_filter_close = f"</sos:temporalFilter>"

        return temporal_filter + during + value_ref + t_period + begin_pos + end_pos + time_per_close + during_close + temp_filter_close

    def feature_of_interest(self, station_id):
        return f"<sos:featureOfInterest>{station_id}</sos:featureOfInterest>"

    def observed_property(self, prop):
        return f"<sos:observedProperty>http://bom.gov.au/waterdata/services/parameters/{prop}</sos:observedProperty>"

    def procedure(self, proc):
        return f"<sos:procedure>http://bom.gov.au/waterdata/services/tstypes/{proc}</sos:procedure>"

    def spatial(self, action, lower_corner, upper_corner):
        # corner string is made up of lat long values eg -37.505032 140.999283
        spatial_filter = f"<sos:spatialFilter>"
        contains = f"<fes:Contains>"

        value_ref = f"<fes:ValueReference>om:{action}/*/sams:shape</fes:ValueReference>"
        envelope = f"<gml:Envelope srsName=\"http://www.opengis.net/def/crs/EPSG/0/4326\">"
        l_corner = f"<gml:lowerCorner>{lower_corner}</gml:lowerCorner>"
        u_corner = f"<gml:upperCorner>{upper_corner}</gml:upperCorner>"
        envelope_end = f"</gml:Envelope>"
        contains_end = f"</fes:Contains>"
        spatial_filter_end = f"</sos:spatialFilter>"

        return spatial_filter + contains + value_ref + envelope + l_corner + u_corner + envelope_end + contains_end + spatial_filter_end

    def bom_url_KVP_builder(self, action, query):
        '''KVP URL builder'''
        endpoint = f'http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request={action}'
        return f"{endpoint}&{query}"

    def build_payload(self, action, feature=None, prop=None, proced=None, begin=None, end=None, lower_corner=None,
                      upper_corner=None):
        '''
        Payload builder

        Note that only action is required.

        However if you need another arg you still need to keep the correct order.
        eg water_ml_builder( GetAction, None, 'Water Course Level', None)
        '''
        return self.xml() + self.envelope_head() + self.header_action(action) + self.body(action, feature, prop, proced,
                                                                                          begin, end, lower_corner,
                                                                                          upper_corner) + self.envelope_tail()

    def request(self, action, feature=None, prop=None, proced=None, begin=None, end=None, lower_corner=None,
                upper_corner=None):
        if action == Action.GetCapabilities:
            return requests.get(action)
        else:
            endpoint = f"http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request={os.path.basename(action)}"
            payload = self.build_payload(action, feature, prop, proced, begin, end, lower_corner, upper_corner)
            return requests.post(endpoint, payload)

    def _parse_float(self, x):
        if x is None:
            return float('nan')
        try:
            return float(x)
        except ValueError:
            return float('nan')

    def _parse_time(self, x):
        t = iso8601.parse_date(x).astimezone(pytz.utc)
        return t.replace(tzinfo=None)

    def _parse_quality_code(self, node, qdefault=-1, idefault=""):
        qcodes = [qdefault, idefault]
        if len(node) == 0:
            return qcodes

        if len(node[0]) == 0:
            return qcodes

        for nd in node[0]:
            for key, field in nd.items():
                value = re.sub(".*/", "", field)
                if re.search("interpolation", field):
                    # Found interpolation field
                    qcodes[1] = value
                    break
                elif re.search("qualifier", field):
                    # Found qualifier field
                    qcodes[0] = int(value)
                    break

        return qcodes

    def _parse_default_node(self, default_node):
        default_props = {\
            "quality_code": -1, \
            "unit": "", \
            "interpolation": ""
        }
        if len(default_node)>0:
            if len(default_node[0])>0:
                for nd in default_node[0][0]:
                    for key, field in nd.items():
                        value = re.sub(".*/", "", field)
                        if re.search("interpolation", field):
                            # Found interpolation field
                            default_props["interpolation"] = value
                            break
                        elif re.search("qualifier", field):
                            # Found qualifier field
                            default_props["quality_code"] = int(value)
                            break
                        elif key == 'code':
                            default_props["unit"] = value

        return default_props


    def parse_get_data(self, response, raw=False):
        root = ET.fromstring(response.text)

        # Unit and default quality code
        prefix = './/{http://www.opengis.net/waterml/2.0}'
        default_node = root.findall(f'{prefix}defaultPointMetadata')
        default_properties = self._parse_default_node(default_node)
        unit = default_properties["unit"]

        # Parse time series data
        query_measurement = f'{prefix}MeasurementTVP'
        data = []
        qdefault = default_properties["quality_code"]
        idefault = default_properties["interpolation"]

        for e in root.findall(query_measurement):
            info = [None, float('nan'), qdefault, idefault]
            for node in e:
                if node.tag.endswith("time"):
                    info[0] = self._parse_time(node.text)
                elif node.tag.endswith("value"):
                    info[1] = self._parse_float(node.text)
                elif node.tag.endswith("metadata"):
                    qcodes = self._parse_quality_code(node, \
                                        qdefault, idefault)
                    info[2] = qcodes[0]
                    info[3] = qcodes[1]
            data.append(info)

        if raw:
            return data

        df = pd.DataFrame(data, columns=('Timestamp[UTC]', f'Value[{unit}]', 'Quality', 'Interpolation'))
        df = df.set_index('Timestamp[UTC]')

        return df

    def xml_to_json(self, xml_text):
        return dict(xmltodict.parse(xml_text))


    def xml_to_json_via_file(self, xml_text, file):
        data_dict = dict(xmltodict.parse(xml_text))
        with open(file, 'w+') as json_file:
            json.dump(data_dict, json_file, indent=4, sort_keys=True)

        with open(file) as json_file:
            return json.load(json_file)

    def create_feature_list(self, bom_response_foi, path):
        '''This is used to create a feature list for reuse'''

        # feature_list = []
        # with open('all_GetFeatureOfInterest.json', 'r') as fin:
        #     getfeature_json = json.load(fin)
        su = spatail_utilty()
        features = bom_response_foi['soap12:Envelope']['soap12:Body']['sos:GetFeatureOfInterestResponse']['sos:featureMember']
        geojson_feature = []
        lat = ''
        long = ''
        pos = ''
        for feat in features:
            long_station_no = feat['wml2:MonitoringPoint']['gml:identifier']['#text']
            if '#text' in feat['wml2:MonitoringPoint']['sams:shape']['gml:Point']['gml:pos']:
                pos = feat['wml2:MonitoringPoint']['sams:shape']['gml:Point']['gml:pos']['#text']
            else:
                lat = ''
                long = ''
                pos = ''
            if not pos == '':
                lat = pos.split(' ')[0]
                long = pos.split(' ')[1]

            name = feat['wml2:MonitoringPoint']['gml:name'].replace(' ', '_').replace('-', '_')
            station_no = os.path.basename(long_station_no)
            stat = {'stationID': station_no, 'name': name, 'longName': long_station_no, 'coords': pos}
            # feature_list.append(stat)
            geojson_feature.append(su.create_geojson_feature(lat, long, station_no, None, name, long_station_no))
        if not path == None:
            su.write_features(geojson_feature, path)

        return su.get_feature_collection(geojson_feature)

        # with open('stations.json', 'w') as fout:
        #     json.dump(feature_list, fout)

