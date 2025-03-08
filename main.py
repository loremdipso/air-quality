import geopandas
import csv

# Lets you load common datasets
# from geodatasets import get_path
# path_to_data = get_path("nybb")

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

    # print(gdf.total_bounds)
    # print(gdf.cx[slice(50, -124), slice(47, -116)])

    # print(gdf)
    # print(gdf.columns)
    # for index, row in gdf.iterrows():
        # print(row["GEOID20"]) # zip code
    # def main():
    #     print("Hello from air-quality!")
    return gdf


def load_points():
    with open('./data/8hour_44201_2024.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        # Skip the first one
        next(csvreader)
        return [next(csvreader) for _ in range(10)]

points = load_points()
point = points[0]

lat = float(point[5])
lon = float(point[6])
# print(lon, lat)

# this is just made up
air_quality = float(point[19])

# We have the points, we have the shapes. We just want to see which points exist
# in each shape. So... n^2, just loop through everything?
shapes = load_shapes()
print(shapes.total_bounds)
print(shapes.cx[ -119.243743:-119.343743, 46.204582:46.304582 ])
