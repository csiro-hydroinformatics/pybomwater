import requests
import iso8601
import pytz
import json5
import xmltodict
import os
import pandas as pd
import xml.etree.ElementTree as ET

class Builder_Property():
    def __init__(self):
        pass

    def set_value(self, varname, value):
        self.__dict__[varname] = value


class Action():
    def __init__(self):
        pass

    GetDescribeSensor = 'http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=DescribeSensor'
    GetCapabilities = 'http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=GetCapabilities'
    GetDataAvailability = "http://www.opengis.net/def/serviceOperation/sos/daRetrieval/2.0/GetDataAvailability"
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


class Bom_Water():

    def __init__(self):
        self.actions = Action()
        self.features = Feature()
        self.properties = Property()
        self.procedures = Procedure()
        self.init_properties()

    def init_properties(self):
        getCap_json = ''
        with open('waterML_GetCapabilities.json') as json_file:
            getCap_json = json5.load(json_file)

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
            self.procedures.set_value(proc, proc)

        '''Features'''
        getfeature_json = ''
        with open('bomWater_all_foi.json') as json_file:
            getfeature_json = json5.load(json_file)
        features = getfeature_json['soap12:Envelope']['soap12:Body']['sos:GetFeatureOfInterestResponse'][
            'sos:featureMember']
        for feat in features:
            long_statioId = feat['wml2:MonitoringPoint']['gml:identifier']['#text']
            name = feat['wml2:MonitoringPoint']['gml:name'].replace(' ', '_').replace('-', '_')
            #             stationId = os.path.basename(long_statioId)
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
        endpoint = f"http://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request={os.path.basename(action)}"
        payload = self.build_payload(action, feature, prop, proced, begin, end, lower_corner, upper_corner)
        if action == Action.GetCapabilities:
            return requests.get(action)
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

    def parse_get_data(self, response, raw=False):

        root = ET.fromstring(response.text)

        data = [[e.text for e in root.findall('.//{http://www.opengis.net/waterml/2.0}' + t)]
                for t in ['time', 'value']]

        dd = [(self._parse_time(t),
               self._parse_float(v))
              for t, v in zip(*data)]

        if raw:
            return dd

        return pd.DataFrame(dd, columns=('Timestamp', 'Value')).set_index('Timestamp')

    def xml_to_json(self, xml_text, file):
        data_dict = dict(xmltodict.parse(xml_text))
        with open(file, 'w+') as json_file:
            json5.dump(data_dict, json_file, indent=4, sort_keys=True)

        with open(file) as json_file:
            return json5.load(json_file)