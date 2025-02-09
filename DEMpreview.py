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

def preview(file) :   
    
    histogram=False
    scatter_plot=False 
    try:  
      head, tail = os.path.split(file)
      print(f"Processing: {tail}")
      with rasterio.open(file) as dataset:
            alt_dem= dataset.read(1).astype(numpy.float32)
            (nxdem, nydem) =(dataset.width, dataset.height)
            nodata=dataset.nodata
    except Exception as e:
      print(e)
      print(error_msg)
      sys.exit(1)           
    
    zeros=np.count_nonzero(alt_dem==0)
    nodata_count=np.count_nonzero(alt_dem==nodata)
    nans=np.count_nonzero(np.isnan(alt_dem))
  
    if nans+nodata_count==nxdem*nydem:
       print(f"File: {tail} contains no data! Aborting")
       sys.exit(1)
    
    alt_dem_stat=np.copy(alt_dem)
    alt_dem_stat[alt_dem_stat==nodata]=0
    alt_dem_stat=numpy.nan_to_num(alt_dem_stat,nan=0)
    crs=dataset.crs
    epsg=crs.to_epsg()
    min_alt = np.min(alt_dem_stat)
    max_alt = np.max(alt_dem_stat)
    mean_alt = np.mean(alt_dem_stat)
    shape=alt_dem.shape
    dtype=alt_dem.dtype
    file_size=os.path.getsize(file)   
    alt_dem[alt_dem==nodata]=np.nan

    hillshade = es.hillshade(alt_dem, altitude=30, azimuth=210)

    # Plot the DEM and hillshade at the same time
    
    masked_dem_data = np.ma.masked_invalid(alt_dem)
    cmap = plt.get_cmap('terrain') 
    cmap.set_bad(color='black')
    
    max_value = np.max(masked_dem_data)
    max_loc = np.where(masked_dem_data == max_value) 
    max_row, max_col = max_loc[0][0], max_loc[1][0]
        
    # Flatten the masked array to create a 1D array of elevation values
    elevation_values = masked_dem_data.compressed()  # This will ignore masked values (NaNs)

    # Calculate Q1, Q3, and IQR
    Q1 = np.percentile(elevation_values, 1)
    Q3 = np.percentile(elevation_values, 99)
    IQR = Q3 - Q1

   # Define the bounds for outliers
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

   # Identify outliers
    outliers = elevation_values[(elevation_values < lower_bound) | (elevation_values > upper_bound)]
    outlier_mask = (alt_dem_stat < lower_bound) | (alt_dem_stat > upper_bound)
    print(f"Count of NoData: {nodata_count}")
    print(f"Count of NaN: {nans}")
    print(f"Number of outliers: {len(outliers)}")
    
    # Plot the DEM and hillshade at the same time
    fig, ax = plt.subplots(figsize=(12, 8))
    ep.plot_bands(
       masked_dem_data,
       ax=ax,
       cmap=cmap,
       title=f"DEM file: {tail}",
       )
    ax.imshow(hillshade, cmap="Greys", alpha=0.5)
    plt.figtext(0.02, 0.46, f"Raster dimensions: {shape}\n\
x*y= {nxdem*nydem}\n\n\
Data type: {dtype}\nNoData: {nodata}\n\n\
EPSG: {epsg}\n\n\
Min altitude: {min_alt:.2f}\n\
Mean altitude: {mean_alt:.2f}\n\
Max altitude: {max_alt:.2f}\n\n\
Count of NaN: {nans}\n\n\
Count of NoData: {nodata_count}\n\n\
Count of zeros: {zeros}\n\n\
Number of extreme outliers: {len(outliers)}\n\n\
File size: {file_size}", fontsize = 10)
    plt.show()   

    # Plot the DEM data
    fig, ax = plt.subplots(figsize=(12, 8))
    ep.plot_bands(masked_dem_data, ax=ax, cmap='terrain', title=f"{tail} with Outliers and NoData Highlighted")

    # Get the coordinates of the outliers
    outlier_coords = np.where(outlier_mask)

    # Overlay the outliers in a distinct color and size
    ax.scatter(outlier_coords[1], outlier_coords[0], c='red', s=30, label='Outliers')

    # Add legend entry for NoData values
    no_data_patch = Patch(color='white', label='NoData')
    outlier_patch = Patch(color='red', label='Outliers')
    ax.legend(handles=[no_data_patch, outlier_patch])

    plt.show()
        
    if histogram is True:
       # Plot histogram
       fig, ax = plt.subplots(figsize=(12, 8))
       ax.hist(elevation_values, bins=50, color='green', edgecolor='black')
       ax.set_title("Histogram of Elevation Values")
       ax.set_xlabel("Elevation")
       ax.set_ylabel("Frequency")
       plt.show()

    if scatter_plot is True:
       # Assuming elevation_values and outliers are already defined
       indices = np.arange(len(elevation_values))

       # Create a scatter plot
       fig, ax = plt.subplots(figsize=(12, 8))
       ax.scatter(indices, elevation_values, label='Normal Values')
       ax.scatter(indices[elevation_values < lower_bound], elevation_values[elevation_values < lower_bound], color='red', label='Outliers')
       ax.scatter(indices[elevation_values > upper_bound], elevation_values[elevation_values > upper_bound], color='red')

       ax.set_title("Scatter Plot with Outliers Highlighted")
       ax.set_xlabel("Index")
       ax.set_ylabel("Elevation")
       ax.legend()
       plt.show()

error_msg="\nError!\n\nSyntax: python DEMpreview /path to dem file\n\n\
or:\n\npython DEMpreview  - from a folder with multiple DEM files\n"

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

