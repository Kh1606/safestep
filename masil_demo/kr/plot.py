import geopandas as gpd

gdf = gpd.read_file("RDL_ETCT_AS_4326.geojson")
print(gdf["FTR_CDE"].value_counts())
