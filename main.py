import geopandas
import csv
import statistics


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


def get_mapping():
    # key is zip code, value is array of air quality measurements
    mapping = {}
    shapes = load_shapes()
    # This assumes your dataset is just a csv and each row is a bounding box
    # and then the air quality, i.e.
    # min_x, max_x, min_y, max_y, air quality
    with open('./data/boxes.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for point in csvreader:
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


for key, values in get_mapping().items():
    # Basic, unweighted mean
    avg = statistics.mean(values)
    print(key, avg)
