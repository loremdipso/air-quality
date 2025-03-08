import geopandas
import csv
import statistics

# Performance: build a spatial index instead???

# Lets you load common datasets
# from geodatasets import get_path
# path_to_data = get_path("nybb")
# print(shapes.total_bounds)

# print(gdf.total_bounds)
# print(gdf.cx[slice(50, -124), slice(47, -116)])

# print(gdf)
# print(gdf.columns)
# for index, row in gdf.iterrows():
    # print(row["GEOID20"]) # zip code
# def main():
#     print("Hello from air-quality!")

def load_shapes():
    bbox = (
        # Rough approximation of washington
        -130,
        50,
        -115, 
        45,
    )

    # gdf = geopandas.read_file("./data/tl_2020_us_zcta520/tl_2020_us_zcta520.shp", rows=slice(0,10), bbox=bbox)
    gdf = geopandas.read_file("./data/tl_2020_us_zcta520/tl_2020_us_zcta520.shp", bbox=bbox)
    return gdf


def doit():
    rv = {}
    shapes = load_shapes()
    with open('./data/8hour_44201_2024.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip the title row one
        next(csvreader)
        for point in csvreader:
            lat = float(point[5])
            lon = float(point[6])

            # this is just made up
            air_quality = float(point[19])

            # Maybe use https://geopandas.org/en/stable/docs/reference/api/geopandas.sindex.SpatialIndex.intersection.html#geopandas.sindex.SpatialIndex.intersection
            # instead of this thing
            lilbit = 0.00000000001
            result = shapes.cx[lon:lon+lilbit, lat:lat+lilbit]
            for zip in result["GEOID20"]:
                rv.setdefault(zip, []).append(air_quality)
    return rv

data = doit()
for key, values in data.items():
    avg = statistics.mean(values)
    print(key, avg)

print("done")
