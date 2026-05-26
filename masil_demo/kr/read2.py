import geopandas as gpd

gdf = gpd.read_file("RDL_ETCT_AS.shp")   # needs .shp/.shx/.dbf in same folder
print(gdf.crs)
print(gdf.head())

# quick plot
gdf.plot()

# For web maps (lat/lon)
gdf_4326 = gdf.to_crs(epsg=4326)
gdf_4326.to_file("RDL_ETCT_AS.geojson", driver="GeoJSON")
