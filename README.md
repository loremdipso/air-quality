## The Data

I downloaded the GeoPackage version of the Census Block data from [here](https://hub.arcgis.com/datasets/d795eaa6ee7a40bdb2efeb2d001bf823_0/about)
to `./data/census_blocks/census_blocks.gpkg`.
It says it was published in 2021 and updated in 2025, so I'm hopeful that this is pretty up to date.

I also made a stab at what the format of the air quality boxes were in `./data/air_quality_boxes.csv`. You'll want to update the parsing in the `get_unweighted_mapping` and `get_weighted_mapping` functions.

## To Setup

I used `uv` to do python project management. If you don't then you'll want to
manually pip install the right packages:

```bash
pip3 install csv
pip3 install pyproj
pip3 install geopandas
pip3 install shapely
```

## To Run

For the slow (and more accurate) version:

`uv run main.py --slow`

For the slow (and less accurate) version, good for local testing:

`uv run main.py --fast`

Or, if you aren't using uv, you can just do:

`python3 main.py --fast`

## Caching

The biggest optimization here is caching the census blocks for just Washington. That way we don't have to load all the blocks (~13G) into memory, just relevant ~400MB or so.
