import geopandas as gpd

gdf = gpd.read_file("RDL_ETCT_AS.shp")

# convert Korea projected CRS -> WGS84 lat/lon for web maps
gdf_wgs84 = gdf.to_crs(epsg=4326)

# optional: keep only a few useful columns to reduce file size
keep = ["FTR_CDE", "FTR_IDN", "BJD_CDE", "SHT_NUM", "geometry"]
cols = [c for c in keep if c in gdf_wgs84.columns]
gdf_wgs84[cols].to_file("RDL_ETCT_AS_4326.geojson", driver="GeoJSON")
print("Saved: RDL_ETCT_AS_4326.geojson")
