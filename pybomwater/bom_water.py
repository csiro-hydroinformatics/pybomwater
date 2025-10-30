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
import xarray as xr
from pybomwater.spatial_util import spatail_utilty
import math
import random
from statistics import mean


class Builder_Property():
    def __init__(self):
        pass

    def set_value(self, varname, value):
        self.__dict__[varname] = value


class Action:
    def __init__(self):
        pass

    # GetDescribeSensor = 'https://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=DescribeSensor'
    GetCapabilities = 'https://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request=GetCapabilities'
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


class BomWater():

    def __init__(self):
        # self._module_dir = os.path.dirname(__file__)
        self.actions = Action()
        self.features = Feature()
        self.properties = Property()
        self.procedures = Procedure()

        self.cache = os.path.join(str(os.path.expanduser("~")), 'pybomwater', 'cache')
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
            proc = re.sub(r'\W+', '_', proc)
            self.procedures.set_value(proc, proc)

        '''Features'''
        getfeature_json = ''
        with open(self.stations) as json_file:
            getfeature_json = json.load(json_file)
        # features = getfeature_json['longName']
        for index in range(len(getfeature_json['features'])):
            long_statioId = getfeature_json['features'][index]['properties']['long_name']

            name =  getfeature_json['features'][index]['properties']['name']
            name = re.sub(r'\W+', '_', name)
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

    # def feature_of_interest(self, station_id):
    #     return f"<sos:featureOfInterest>{station_id}</sos:featureOfInterest>"
    def feature_of_interest(self, station_id):
        if type(station_id) is list:
            feature_list = ''
            for stat_id in station_id:
                print(stat_id)
                feature_list += f"<sos:featureOfInterest>{stat_id}</sos:featureOfInterest>"
            return feature_list
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

    # def request(self, action, feature=None, prop=None, proced=None, begin=None, end=None, lower_corner=None,
    #             upper_corner=None):
    #     endpoint = f"https://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request={os.path.basename(action)}"
    #     payload = self.build_payload(action, feature, prop, proced, begin, end, lower_corner, upper_corner)
    #     if action == Action.GetCapabilities:
    #         return requests.get(action)
    #     return requests.post(endpoint, payload)

    def request(self, action, feature=None, prop=None, proced=None, begin=None, end=None, lower_corner=None, upper_corner=None):
        try:
            endpoint = f"https://www.bom.gov.au/waterdata/services?service=SOS&version=2.0&request={os.path.basename(action)}"
            payload = self.build_payload(action, feature, prop, proced, begin, end, lower_corner, upper_corner)
            if action == Action.GetCapabilities:
                response = requests.get(action)
                if response.ok:
                    return response
                else:
                    raise requests.exceptions.RequestException()
            response = requests.post(endpoint, payload)
            if response.ok:
                return response
            else:
                res_content = response.content
                raise requests.exceptions.RequestException(request=requests, response=response) 
        except requests.exceptions.RequestException as e:
            raise e


    def _parse_float(self, x):
        try:
            if x is None:
                return float('nan')
            return float(x)
        except:
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
    
    def divide_chunks(self, l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i:i + n]
   

    def define_request_chunking_size(self, features, property, procedure, start_date, end_date ):
        """
        This is a rough stab at determining a chunk size.
        Trying to balance between making too many requests and a response size which is too large
        """
        request_values_limit = 500000#BoM have a Constraint of 2000000 values specified however this does not seem real as the request fails if we try to get close to this value.
        size = 2
        feat_count = len(features)

        if feat_count > size:
            sample_indexes = random.sample(range(0, feat_count), max(2,math.floor(feat_count*0.05)))
            sample_sizes = []
            for s_indx in sample_indexes:
                feature = features[s_indx]
                response = self.request_observations( feature, property=property, procedure=procedure, t_begin=start_date, t_end=end_date)
                values_count = self.values_count(response)
                # size = request_values_limit/(values_count)#*len(features)
                sample_sizes.append(values_count)
            if max(sample_sizes) > 0:
                return math.floor((request_values_limit/max(sample_sizes)*0.9)/2)
            else:
                return 3
        return size
    
    def get_spatially_filtered_observations(self, features, spatial_path, bbox, property, procedure, t_begin, t_end):
        #Get feature details based on bounding box
        response = self.request(self.actions.GetFeatureOfInterest, features, property, procedure, t_begin, t_end, bbox[0], bbox[1]  )
        response_json = self.xml_to_json(response.text)
        feature_list = self.create_feature_list(response_json, None )
        #Filter based on shape file
        su = spatail_utilty()
        filtered_features = su.filter_feature_list(feature_list, spatial_path, None)
        #Segment into chunks for requests

        return self.batch_request_observations(property, procedure, t_begin, t_end, filtered_features)

    def batch_request_observations(self, property, procedure, t_begin, t_end, filtered_features):
        station_no = []
        for site in filtered_features['features']:
            station_no.append(site['properties']['long_name'])
        datasets = []
        chunk_size = self.define_request_chunking_size( station_no, property, procedure, t_begin, t_end )
        station_chunkes = list(self.divide_chunks(station_no, chunk_size))

        for chunk in station_chunkes:
            response = self.request_observations( chunk, property=property, procedure=procedure, t_begin=t_begin, t_end=t_end, )
            data = self.parse_data(response, filtered_features)
            datasets.append(data)

        return datasets

    def get_observations(self, features, property, procedure, t_begin, t_end, bbox):
        response = self.request(self.actions.GetFeatureOfInterest, features, property, procedure, t_begin, t_end, bbox[0], bbox[1]  )
        response_json = self.xml_to_json(response.text)
        feature_list = self.create_feature_list(response_json, None )
        # station_no = []
        # for site in feature_list['features']:
        #     station_no.append(site['properties']['long_name'])
        # datasets = []
        # chunkes = self.define_request_chunking_size( features, property, procedure, t_begin, t_end )
        # station_chunkes = list(self.divide_chunks(station_no, chunkes))

        # for chunk in station_chunkes:
        #     response = self.request_observations( chunk, property=property, procedure=procedure, t_begin=t_begin, t_end=t_end, )
        #     data = self.parse_data(response, feature_list)
        #     datasets.append(data)

        # return datasets
        return self.batch_request_observations(property, procedure, t_begin, t_end, feature_list)

    # def get_observations(self, features, property, procedure, t_begin, t_end, bbox):
    #     response = self.request(self.actions.GetFeatureOfInterest, features, property, procedure, t_begin, t_end, bbox[0], bbox[1]  )
    #     response_json = self.xml_to_json(response.text)
    #     feature_list = self.create_feature_list(response_json, None )
    #     response = self.request_observations(features, property, procedure, t_begin, t_end)

    #     dataframes = self.parse_data(response, feature_list)
    #     return dataframes

    def request_observations(self, features, property, procedure, t_begin, t_end):
        try:
            response = self.request( self.actions.GetObservation, features,
                                   property, procedure, t_begin, t_end)
        except requests.RequestException as e:
            assert False, f"GetObservation failed requestException: {e}"
        return response


    def parse_node_attributes(self, node):
        attribs = {}
        for element in node[0].attrib:
            attribs[element] = node[0].attrib[element]    
        return attribs

    def values_count(self, response):
        root = ET.fromstring(response.text)
        value_nodes = []
        # Unit and default quality code
        prefix = './/{http://www.opengis.net/waterml/2.0}'
        sos_prefix = './/{http://www.opengis.net/sos/2.0}'
        # Parse time series data
        query_observationData = f'{sos_prefix}observationData'
        query_measurement = f'{prefix}MeasurementTVP'
        for obs in root.findall(query_observationData):
        #Measurement values and associated metadata
            value_nodes = obs[0].findall(query_measurement)
            break
        return len(value_nodes)
    
    def parse_data(self, response, stations=None):
        root = ET.fromstring(response.text)

        # Unit and default quality code
        prefix = './/{http://www.opengis.net/waterml/2.0}'
        sos_prefix = './/{http://www.opengis.net/sos/2.0}'
        om_prefix = './/{http://www.opengis.net/om/2.0}'
        xlink_prefix = '{http://www.w3.org/1999/xlink}'
        # Parse time series data
        query_observationData = f'{sos_prefix}observationData'
        query_measurement = f'{prefix}MeasurementTVP'
        q_prop = f'{om_prefix}observedProperty'
        q_foi = f'{om_prefix}featureOfInterest'
        q_proc = f'{om_prefix}procedure'
        q_gen_date = f'{prefix}generationDate'
        
        ds = {}
        gen_date = root.findall(q_gen_date)[0].text

        for ob in root.findall(query_observationData):
            data = []
            #Observation Meta data
            default_node = ob.findall(f'{prefix}defaultPointMetadata')
            default_properties = self._parse_default_node(default_node)
            unit = default_properties["unit"]
            qdefault = default_properties["quality_code"]
            idefault = default_properties["interpolation"]

            proc_href = self.parse_node_attributes(ob.findall(q_proc))[f'{xlink_prefix}href']
            prop_href = self.parse_node_attributes(ob.findall(q_prop))[f'{xlink_prefix}href']
            foi_href = self.parse_node_attributes(ob.findall(q_foi))[f'{xlink_prefix}href']
            proc_val = self.parse_node_attributes(ob.findall(q_proc))[f'{xlink_prefix}title']
            prop_val = self.parse_node_attributes(ob.findall(q_prop))[f'{xlink_prefix}title']
            foi_val = self.parse_node_attributes(ob.findall(q_foi))[f'{xlink_prefix}title']
            #Measurement values and associated metadata
            for e in ob.findall(query_measurement):
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
            values_name = f'{prop_val} [{unit}]'
            pd_df = pd.DataFrame(data, columns=('time', values_name, 'Quality', 'Interpolation'))
            pd_df = pd_df.set_index('time')
            da = pd_df.to_xarray()
            description = f'Property: {prop_val} [{unit}], Procedure: {proc_val} for Feature: {foi_val}'
            if stations != None:
                coordinates = spatail_utilty.find_station_coordinates_from(os.path.basename(foi_href), stations, None)
            else:
                coordinates = ''
            da = da.assign_attrs(
                units=unit, 
                description=description,
                procedure = os.path.basename(proc_href),
                property = prop_val,
                generated_date = f'{gen_date}',
                station_no = f'{foi_href}',
                coordinates = coordinates,
                long_name=f'{foi_val}:{prop_val}', 
                missing_data_value = 'nan')

            ds[f'{foi_href}'] = da
 
        return ds

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
        if len(features) > 1:
            for feat in features:
                self.extract_feature(su, geojson_feature, feat)
        else:
            self.extract_feature(su, geojson_feature, features)
        if not path == None:
            su.write_features(geojson_feature, path)

        return su.get_feature_collection(geojson_feature)

    def extract_feature(self, su, geojson_feature, feat):
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

        # with open('stations.json', 'w') as fout:
        #     json.dump(feature_list, fout)

    # def find_all_keys(self, dictionary):
    #     for key, value in dictionary.items():
    #         if type(value) is dict:
    #             yield key
    #             yield from self.find_all_keys(value)
    #         if type(value) is list:
    #             yield key
    #             yield from self.find_keys_in_list(value)
    #         else:
    #             yield key

    # def find_keys_in_list(self, list):
    #     for item in list:
    #         if type(item) is dict:
    #             yield from self.find_all_keys(item)
    #         if type(item) is list:
    #             yield from self.find_keys_in_list(item)
    #         else:
    #             yield item

    # def find_keys(self, j_response):
    #     dummy_item = "dummy"
    #     keys = {dummy_item}
    #     for key in self.find_all_keys(j_response):
    #         if type(key) is dict:
    #             k = key.keys()
    #             for i in k:
    #                 keys.add(i)
    #         else:
    #             keys.add(key)

    #     keys.remove(dummy_item)
    #     return keys

    # def parse_data(self, response):
    #     json_response = self.xml_to_json(response.text)
    #     df = []
    #     neededKeys = []
    #     keys = {"soap12:Envelope", "soap12:Body", "sos:GetObservationResponse", "sos:observationData", "om:OM_Observation", "om:result", "wml2:MeasurementTimeseries", "wml2:point"}
       
    #     if self.find_keys(json_response) >= keys:
    #         print('Goodo')
    #         data_list = json_response['soap12:Envelope']['soap12:Body']['sos:GetObservationResponse']['sos:observationData']
    #         if type(data_list) is list:
    #             for data_point in data_list:
    #                 ts_data = data_point['om:OM_Observation']['om:result']['wml2:MeasurementTimeseries']['wml2:point']
    #                 self.get_data_values_as_dataframe(data_point, df, ts_data)
    #         else:
    #             ts_data = data_list['om:OM_Observation']['om:result']['wml2:MeasurementTimeseries']['wml2:point']
    #             self.get_data_values_as_dataframe(data_list, df, ts_data)
    #     return df

    # def get_data_values_as_dataframe(self, data_point, df, ts_data):
    #     time = []
    #     values = []
    #     for step in ts_data:
    #         time.append(self._parse_time(step['wml2:MeasurementTVP']['wml2:time']))
    #         values.append(self._parse_float(step['wml2:MeasurementTVP']['wml2:value']))
    #     # ts = list(zip(time, values))
    #     prop = data_point['om:OM_Observation']['om:observedProperty']['@xlink:title']
    #     current_dataframe = pd.DataFrame(values, index=time, columns=[prop])
    #     current_dataframe.attrs['meta_data'] = {}
    #     self.create_meta_data(data_point, current_dataframe.attrs['meta_data'])
    #     current_dataframe.attrs['feature_id'] = os.path.basename(
    #         data_point['om:OM_Observation']['om:featureOfInterest']['@xlink:href'])
    #     df.append(current_dataframe)

    # def create_meta_data(self, record_bundle, meta_data):
    #     meta_data['om:phenomenonTime'] = record_bundle['om:OM_Observation']['om:phenomenonTime']
    #     meta_data['om:resultTime'] = record_bundle['om:OM_Observation']['om:resultTime']
    #     meta_data['om:procedure'] = record_bundle['om:OM_Observation']['om:procedure']
    #     meta_data['om:observedProperty'] = record_bundle['om:OM_Observation']['om:observedProperty']
    #     meta_data['om:featureOfInterest'] = record_bundle['om:OM_Observation']['om:featureOfInterest']
    #     meta_data['@gml:id'] = record_bundle['om:OM_Observation']['om:result']['wml2:MeasurementTimeseries']['@gml:id']
    #     meta_data['wml2:defaultPointMetadata'] = record_bundle['om:OM_Observation']['om:result']['wml2:MeasurementTimeseries']['wml2:defaultPointMetadata']
