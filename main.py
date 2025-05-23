import sys
import geopandas
import csv
import statistics
import time
from shapely.geometry import Polygon
from pyproj import Transformer


def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == "--slow":
            num_rows = slow_and_precise()
            print(f"Done writing {num_rows} rows to output.csv")
            return
        elif sys.argv[1] == "--fast":
            num_rows = fast_and_imprecise()
            print(f"Done writing {num_rows} rows to output.csv")
            return
    print("Usage: ./main.py [--slow|--fast]")


def load_census_blocks():
    print("Loading census blocks...")
    # Try to load from cache. If not found we'll build the cache next.
    try:
        gdf = geopandas.read_file("./washington.gpkg")
        print("Loaded from cache...")
        return gdf
    except: pass

    # I refuse to look this up because EPSG:4326 is dumb and makes no sense
    # So let's just work in lat/long and convert at runtime
    trans = Transformer.from_crs(
        "EPSG:4326", # lat/long
        "EPSG:3857", # world
        always_xy=True,
    )

    bbox = (
        # Rough square around washington to limit our search space
        # TODO: button this up
        *trans.transform(-130, 50),
        *trans.transform(-115, 45)
    )

    # Performance: you might want to build a spatial index:
    # https://geopandas.org/en/stable/docs/reference/sindex.html

    # I downloaded the GeoPackage file from https://hub.arcgis.com/datasets/d795eaa6ee7a40bdb2efeb2d001bf823_0/about
    # It says it was published in 2021 and updated in 2025, so I'm hopeful that this is pretty up to date.
    gdf = geopandas.read_file("./data/census_blocks/census_blocks.gpkg", bbox=bbox)

    # Change the coordinate reference system to something more standard.
    # This one is long/lat with 2M accuracy, which should be more than fine.
    print("Converting to a reasonable format")
    gdf.to_crs(epsg=4326, inplace=True)

    # Cache
    print("Writing to cache...")
    gdf.to_file("washington.gpkg", driver="GPKG")
    return gdf


# Faster, less precise
def fast_and_imprecise():
    num_rows = 0
    with open("output.csv", "w") as output_file:
        output_file.write("Block ID,Average Air Quality\n")
        for key, values in get_unweighted_mapping().items():
            avg = statistics.mean(values)
            output_file.write(f"{key},{avg}\n")
            num_rows += 1
    return num_rows


# Slower, more precise
def slow_and_precise():
    num_rows = 0
    with open("output.csv", "w") as output_file:
        output_file.write("Block ID,Average Air Quality\n")
        for key, values in get_weighted_mapping().items():
            weighted_sum = sum(value * weight for value, weight in values)
            total_weight = sum(weight for _, weight in values)

            # Weighted mean
            avg = weighted_sum / total_weight
            output_file.write(f"{key},{avg}\n")
            num_rows += 1
    return num_rows


def get_unweighted_mapping():
    # key is block id, value is array of air quality measurements
    mapping = {}
    census_blocks = load_census_blocks()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    print("Running through the air quality boxes...")
    with open('./data/air_quality_boxes.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for air_quality_rect in csvreader:
            count += 1
            if count % 100 == 0: print(f"Finished {count} rows")
            min_x = float(air_quality_rect[0])
            max_x = float(air_quality_rect[1])
            min_y = float(air_quality_rect[2])
            max_y = float(air_quality_rect[3])

            # I'm not sure what this number actually is
            air_quality = float(air_quality_rect[4])

            # This finds all overlapping ZCTAs. If you want more precision you
            # could check a bunch of points and see how many overlap.
            results = census_blocks.cx[min_x:max_x, min_y:max_y]
            for block_id in results["BLOCK"]:
                mapping.setdefault(block_id, []).append(air_quality)
    return mapping


# NOTE: I haven't actually verified if this is correct.
def get_weighted_mapping():
    # key is block id, value is array of tuples of (value, weight)
    mapping = {}
    times = {
        "cx": 0,
        "area": 0,
        "overlay": 0,
        "aq_gdf": 0,
        "bgdf": 0,
    }
    census_blocks = load_census_blocks()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    print("Running through our air quality boxes...")
    with open('./data/air_quality_boxes.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        count = 0
        for air_quality_rect in csvreader:
            # print(times)
            count += 1
            if count % 100 == 0: print(f"Finished {count} rows")
            min_x = float(air_quality_rect[0])
            max_x = float(air_quality_rect[1])
            min_y = float(air_quality_rect[2])
            max_y = float(air_quality_rect[3])

            # I'm not sure what this number actually is
            air_quality = float(air_quality_rect[4])

            t = time.perf_counter()
            blocks_gdf = census_blocks.cx[min_x:max_x, min_y:max_y]
            times["cx"] += (time.perf_counter() - t)

            t = time.perf_counter()
            aq_gdf = geopandas.GeoDataFrame(data={
              'geometry':[
                  Polygon([(min_x,min_y),(min_x,max_y),(max_x,max_y),(max_x,min_y)]),
              ]}, geometry='geometry')
            times["aq_gdf"] += (time.perf_counter() - t)

            for index, row in blocks_gdf.iterrows():
                # Make a new datafrom just from this row. Which is probably
                # not the right way to do this but I don't really know geopandas
                t = time.perf_counter()
                block_gdf = geopandas.GeoDataFrame([row])
                times["bgdf"] += (time.perf_counter() - t)

                # Find the intersection dataframe
                t = time.perf_counter()
                gdf_joined = geopandas.overlay(block_gdf, aq_gdf, how='intersection')
                times["overlay"] += (time.perf_counter() - t)

                t = time.perf_counter()
                intersected_area = list(gdf_joined.area)[0]
                block_area = list(block_gdf.area)[0]
                weight = intersected_area / block_area
                block = list(block_gdf["BLOCK"])[0]
                times["area"] += (time.perf_counter() - t)
                mapping.setdefault(block, []).append((air_quality, weight))
    return mapping


main()
