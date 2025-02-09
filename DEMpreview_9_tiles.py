import datetime
import time
import numpy
import os
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import earthpy as et
import earthpy.spatial as es
import earthpy.plot as ep
import sys
import rasterio
from matplotlib.patches import Patch


def lat_lon(tail):
    t_lat=tail[0:3]
    t_lon=tail[3:7]
    lat=(0-int(t_lat[1:3])) if t_lat[0]=="S" else int(t_lat[1:3])
    lon=(0-int(t_lon[1:4])) if t_lon[0]=="W" else int(t_lon[1:4])    
    return (lat,lon)

def hem_latlon(lat, lon):
    hemisphere = "N" if lat >= 0 else "S"
    greenwichside = "E" if lon >= 0 else "W"
    return (
        hemisphere
        + "{:.0f}".format(abs(lat)).zfill(2)
        + greenwichside
        + "{:.0f}".format(abs(lon)).zfill(3))

def tile(lat,lon,rest):   
    
    file_name="./"+hem_latlon(lat, lon)+rest
    return file_name
    

def preview(file) :   
    wall_time = time.perf_counter()   
    histogram=True
    scatter_plot=False 
    try:  
      head, tail = os.path.split(file)
      rest=tail[7:len(tail)]
      print(f"Processing: {tail}")
      with rasterio.open(file) as dataset:
            alt_dem= dataset.read(1).astype(numpy.float32)
            (nxdem, nydem) =(dataset.width, dataset.height)
            nodata=dataset.nodata
    except Exception as e:
      print(e)
      print("error_msg")
      sys.exit(1)           
    
    lat,lon=lat_lon(tail)
    
    nw=tile(lat+1,lon-1,rest)
    n=tile(lat+1,lon,rest)
    ne=tile(lat+1,lon+1,rest)
    w=tile(lat,lon-1,rest)
    e=tile(lat,lon+1,rest)
    sw=tile(lat-1,lon-1,rest)
    s=tile(lat-1,lon,rest)
    se=tile(lat-1,lon+1,rest)

    file_names = [nw, n, ne, w, e, sw, s, se]

    tiles_around = []
    for file in file_names:
      try: 
        with rasterio.open(file) as src:
            array=src.read(1).astype(numpy.float32)
      except:
            array=np.full((nxdem,nydem),nodata, dtype=np.float32)
            
      tiles_around.append(array)
    
    all_tiles = [alt_dem] + tiles_around
    combined_data = np.block([
    [all_tiles[1], all_tiles[2], all_tiles[3]],
    [all_tiles[4], alt_dem, all_tiles[5]],
    [all_tiles[6], all_tiles[7], all_tiles[8]]
     ])
   
       
    
    combined_data[combined_data==nodata]=np.nan
    
    
    masked_dem_data = np.ma.masked_invalid(combined_data)
    
    hillshade = es.hillshade(masked_dem_data, altitude=30, azimuth=210)

    cmap = plt.get_cmap('terrain') 
    cmap.set_bad(color='white')
    
    
    # Plot the DEM and hillshade at the same time
    
    #masked_dem_data = np.ma.masked_invalid(alt_dem)
  
    # Plot the DEM and hillshade at the same time
    cmap = plt.get_cmap('terrain') 
    fig, ax = plt.subplots(figsize=(12, 8))
    ep.plot_bands(
       masked_dem_data,
       ax=ax,
       cmap=cmap,
       title=f"DEM file: {tail}",
       )
    ax.imshow(hillshade, cmap="Greys", alpha=0.5)

    plt.show()   

error_msg="\nError!\n\nSyntax: python DEMpreview /path to dem file\n\n\
or:\n\npython DEMpreview_9_tiles.py  - from a folder with multiple DEM files\n"

def main():
 if len(sys.argv)==1:
   n=0
   for f in os.listdir():
      if not f[-4:] in (".hgt",".tif"):
         continue
      n += 1
      
      preview(f)
   if n == 0:
      print(error_msg)      
 else:
   try:
       f = str(sys.argv[1])
   except Exception as e:
       print(e)
       print("error_msg")
       sys.exit(1)            
   
   preview(f)

if __name__ == "__main__":
    main()
