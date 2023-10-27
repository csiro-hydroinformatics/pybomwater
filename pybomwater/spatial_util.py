from geojson import Feature, FeatureCollection, Point
import geopandas as gpd
import json
import shapely
class spatail_utilty():

    def create_geojson_feature(self, lat, long, station_no=None, station_id=None, name=None, long_name=None):
            '''Create a geojson feature that can be append to a list'''
            try:
                coords = (float(long),float(lat))
                a_point = Point(coords)
            except ValueError as e:
                return Feature(
                    geometry = None,
                    properties = {
                        'stationNo': station_no,
                        'stationId': station_id,
                        'name': name,
                        'long_name': long_name
                    }
            )

            return Feature(
                    geometry = a_point,
                    properties = {
                        'stationNo': station_no,
                        'stationId': station_id,
                        'name': name,
                        'long_name': long_name
                    }
            )
    def get_feature_collection(self, features):
        return FeatureCollection(features)

    def write_features(self, features, path):
        collection = FeatureCollection(features)
        with open(path, "w") as f:
            f.write('%s' % collection)

    def find_station_coordinates_from( target:str, stations:FeatureCollection = None, path:str = None ):
        if path!=None and stations == None:
            with open(path) as json_file:
                stations =  json.load(json_file)
        if stations == None and path == None:
            raise Exception('Both stations and path are None')
        if target:
            for s in stations['features']:
                if s['properties']['stationNo'] == target:
                    return s['geometry']['coordinates']
        
        raise Exception('Target not in stations list')

    def filter_feature_list(self, feature_list, spatial_file_path, save_path=None):
        sites = []
        shape_file = spatial_file_path#'./test/test_data/Spatial/mdb_buffer_1km.shp'
        geometries = json.loads(gpd.read_file(shape_file).to_json())['features'][0]['geometry']
        coordinates = geometries['coordinates']
        poly = shapely.geometry.Polygon(coordinates[0])#coordinates is a multipolygon, so the 2nd index has the main poly of interest

        for f in feature_list['features']:
            point = shapely.geometry.Point(f['geometry']['coordinates'])
            if point.within(poly):
        #         print(f'Points X: {point.x}, Point Y: {point.y}')
                sites.append(f)
        if save_path:
            self.write_json_features(sites, save_path)#f'./test/test_data/mdb_Watertemp_stations.json')
        return FeatureCollection(sites)
    
    def write_json_features(self, features, file):
        collection = FeatureCollection(features)
        with open(file, "w") as f:
            f.write('%s' % collection)

