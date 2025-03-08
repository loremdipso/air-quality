import geopandas
import csv
import statistics
from shapely.geometry import Polygon


def load_shapes():
    bbox = (
        # Rough square around washington
        -130,
        50,
        -115, 
        45,
    )

    # Performance: you might want to build a spatial index:
    # https://geopandas.org/en/stable/docs/reference/sindex.html
    gdf = geopandas.read_file("./data/tl_2020_us_zcta520/tl_2020_us_zcta520.shp", bbox=bbox)
    return gdf


def get_unweighted_mapping():
    # key is zip code, value is array of air quality measurements
    mapping = {}
    shapes = load_shapes()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    with open('./data/boxes.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for point in csvreader:
            count += 1
            if count % 100 == 0: print(f"Finished {count} rows")
            min_x = float(point[0])
            max_x = float(point[1])
            min_y = float(point[2])
            max_y = float(point[3])

            # I'm not sure what this number actually is
            air_quality = float(point[4])

            result = shapes.cx[min_x:max_x, min_y:max_y]

            # This finds all overlapping ZCTAs. If you want more precision you
            # could check a bunch of points and see how many overlap.
            for zip in result["GEOID20"]:
                mapping.setdefault(zip, []).append(air_quality)
    return mapping

# NOTE: I haven't actually verified if this is correct.
def get_weighted_mapping():
    # key is zip code, value is array of tuples of (value, weight)
    mapping = {}
    shapes = load_shapes()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    with open('./data/boxes.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for point in csvreader:
            count += 1
            if count % 100 == 0: print(f"Finished {count} rows")
            min_x = float(point[0])
            max_x = float(point[1])
            min_y = float(point[2])
            max_y = float(point[3])

            # I'm not sure what this number actually is
            air_quality = float(point[4])

            zips_gdf = shapes.cx[min_x:max_x, min_y:max_y]
            aq_gdf = geopandas.GeoDataFrame(data={
              'geometry':[
                  Polygon([(min_x,min_y),(min_x,max_y),(max_x,max_y),(max_x,min_y)]),
              ]}, geometry='geometry')
            for index, row in zips_gdf.iterrows():
                zip_gdf = geopandas.GeoDataFrame([row])
                gdf_joined = geopandas.overlay(zip_gdf, aq_gdf, how='intersection')
                intersected_area = gdf_joined.area[0]
                zipcode_area = zip_gdf.area[0]
                weight = intersected_area / zipcode_area
                zip = zip_gdf["GEOID20"][0]
                mapping.setdefault(zip, []).append((air_quality, weight))
    return mapping

# Faster, less precise
def fast_and_imprecise():
    for key, values in get_unweighted_mapping().items():
        avg = statistics.mean(values)
        print(f"{key},{avg}")

# Slower, more precise
def slow_and_precise():
    for key, values in get_weighted_mapping().items():
        weighted_sum = sum(value * weight for value, weight in values)
        total_weight = sum(weight for _, weight in values)

        # Weighted mean
        avg = weighted_sum / total_weight
        print(f"{key},{avg}")

fast_and_imprecise()
# slow_and_precise()
