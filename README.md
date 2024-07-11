# sardem-sarsen
This application is designed to process Synthetic Aperture Radar (SAR) data from Sentinel-1 GRD (Ground Range Detected) products using a Digital Elevation Model (DEM) obtained from Copernicus. 

## Introduction
Sardem-Sarsen is an application tailored for SAR (Synthetic Aperture Radar) and DEM (Digital Elevation Model) data processing. 
It utilizes two main tools: `SARsen` : https://github.com/bopen/sarsen/tree/main and `sardem`: https://github.com/scottstanie/sardemlibraries.

Sardem-Sarsen automates the process of SAR data processing by fetching S1 GRD products from the Copernicus STAC Catalog, retrieving a DEM, and running SARsen processing on both the S1 GRD product and the DEM. The output is the result of the SARsen processing.

This application automates SAR data processing by fetching S1 GRD products from the Copernicus STAC Catalog, retrieving a DEM, and running SARsen processing on both the S1 GRD product and the DEM. The output is the result of the SARsen processing.

The application facilitates the following steps:

1. Parsing command-line arguments : Parses arguments such as bounding box coordinates and catalog path.
2. Fetching S1 GRD Product Paths: Retrieves paths of Sentinel-1 GRD products from the STAC catalog.
3. Downloading DEM from Copernicus: Downloads a DEM from Copernicus using the sardem library.
4. Performing SAR Processing with SARsen: Applies topographic correction using SARsen on each Sentinel-1 GRD product.

Example cmd line calls:

```
python sardem-sarsen.py 
    --bbox -118.06817 34.22169 -118.05801 34.22822  # bounding box: [left  bottom  right top]
    --stac_catalog_folder ./catalog_dir
    --o output
```

## The three test `bbox`'s

Let's use these three bounding boxes for development and to compare between platforms:

1) "Mount Wilson"
   - `--bbox -118.06817 34.22169 -118.05801 34.22822`
   - Very small (24 x 37 pixels)
   - Should take ~5-8 seconds to complete the algorithm*

2) "California and Nevada"
   - `--bbox -124.81360 32.44506 -113.75989 42.24498`
   - 35280 x 39793 pixels
   - With 8 cores on NASA DPS, takes 9-10 min to fetch+stitch DEM, and ~13-14 min for computations*
   - Warning: Please be mindful of memory usage

3) Italy
   - `--bbox 6.26868 36.00380 18.57179 47.28139`
   - 40599 x 44291 pixels
   - With 8 cores on NASA DPS, takes 9-10 min to fetch+stitch DEM, and ~23-25 min for computations*
   - Warning: Please be mindful of memory usage
   
* Time estimates are for timings internal to the algorithm; they do not include DPS packaging time, etc.
  
## Requirements
  
* Python 3.10
  
* GDAL 3.6.3
  
* Sardem 0.11
  
* Dask 2023.3.2
  
* Proj-data 1.13
  
* Sarsen 0.9.3
  
* Rasterio 1.3.6
  
* Pystac