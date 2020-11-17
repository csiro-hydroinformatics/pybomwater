from geojson import Feature, FeatureCollection, Point

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
        with open(f'{path}_geofeature.json', "w") as f:
            f.write('%s' % collection)