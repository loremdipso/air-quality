import sys
import geopandas
import csv
import statistics
from shapely.geometry import Polygon


def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == "--convert":
            convert()
            return
        elif sys.argv[1] == "--slow":
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
    bbox = (
        # Rough square around washington to limit our search space
        # TODO: button this up
        -130,
        50,
        -115, 
        45,
    )

    # Performance: you might want to build a spatial index:
    # https://geopandas.org/en/stable/docs/reference/sindex.html

    # I downloaded the GeoPackage file from https://hub.arcgis.com/datasets/d795eaa6ee7a40bdb2efeb2d001bf823_0/about
    # It says it was published in 2021 and updated in 2025, so I'm hopeful that this is pretty up to date.
    # gdf = geopandas.read_file("./data/census_blocks/census_blocks.gpkg", bbox=bbox)
    # gdf = geopandas.read_file("./data/census_blocks/census_blocks.gpkg")
    gdf = geopandas.read_file("./data/census_blocks/census_blocks.gpkg")

    # Change the coordinate reference system to something more standard.
    # This one is long/lat with 2M accuracy, which should be more than fine.
    print("Converting to a reasonable format")
    gdf.to_crs(epsg=4326, inplace=True)
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
    # key is zip code, value is array of air quality measurements
    mapping = {}
    census_blocks = load_census_blocks()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    print("Running through out air quality boxes...")
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
            result = census_blocks.cx[min_x:max_x, min_y:max_y]
            for block_id in result["BLOCK"]:
                mapping.setdefault(block_id, []).append(air_quality)
    return mapping


# NOTE: I haven't actually verified if this is correct.
def get_weighted_mapping():
    # key is zip code, value is array of tuples of (value, weight)
    mapping = {}
    census_blocks = load_census_blocks()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    print("Running through out air quality boxes...")
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

            zips_gdf = census_blocks.cx[min_x:max_x, min_y:max_y]
            aq_gdf = geopandas.GeoDataFrame(data={
              'geometry':[
                  Polygon([(min_x,min_y),(min_x,max_y),(max_x,max_y),(max_x,min_y)]),
              ]}, geometry='geometry')
            for index, row in zips_gdf.iterrows():
                # Make a new datafrom just from this row. Which is probably
                # not the right way to do this but I don't really know geopandas
                zip_gdf = geopandas.GeoDataFrame([row])

                # Find the intersection dataframe
                gdf_joined = geopandas.overlay(zip_gdf, aq_gdf, how='intersection')

                intersected_area = gdf_joined.area[0]
                zipcode_area = zip_gdf.area[0]
                weight = intersected_area / zipcode_area
                zip = zip_gdf["GEOID20"][0]
                mapping.setdefault(zip, []).append((air_quality, weight))
    return mapping


main()
