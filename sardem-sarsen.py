import argparse
import logging
import os
from dataclasses import dataclass
from functools import wraps
from time import time

import numpy as np
from osgeo import gdal  # type: ignore
from sardem import cop_dem
import sarsen
import pystac
import json
import zipfile

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Remove the sardem logging handler so we can control the output, because the
# cop_dem module adds its own handler (poor practice for a library to do).
logging.getLogger("sardem").handlers.clear()
logger = logging.getLogger("sardem-sarsen")


@dataclass(frozen=True, kw_only=True)
class Args:
    stac_catalog_folder: str
    bbox: tuple[float, float, float, float]
    stac_asset_name: str
    out_dir: str


def logtime(func):
    """Function decorator to log the time (seconds) a function takes to execute."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        logger.info("%s: %.1f seconds", func.__name__, time() - start)
        return result

    return wrapper

@logtime
def get_s1_grd_path(json_file, stac_asset_name):
    """
    Fetches the paths of S1 GRD products from the STAC catalog.

    Parameters
    ----------
    json_file : str
        Path to the JSON file containing the STAC catalog.
    stac_asset_name : str
        Identifier of the STAC asset containing the Sentinel-1 GRD product

    Returns
    -------
    List[str]
        List of paths of S1 GRD products.
    """
    logger.info("Fetching S1 GRD product paths from the STAC catalog...")

    s1_grd_paths = []

    try:
        # Read catalog.json
        with open(json_file, 'r') as file:
            catalog_data = json.load(file)
            catalog = pystac.Catalog.from_dict(catalog_data)

        if catalog.links:
            for link in catalog.links:
                # Read item, should be only one
                if link.rel == 'item':
                    absolute_link_href = os.path.normpath(os.path.join(os.path.dirname(json_file), link.target))
                    with open(absolute_link_href, 'r') as item_file:
                        item_data = json.load(item_file)
                        item = pystac.Item.from_dict(item_data)
                        # get the asset
                        if item.assets and stac_asset_name in item.assets:
                            s1_grd_paths.append(os.path.normpath(os.path.join(os.path.dirname(absolute_link_href), item.assets[stac_asset_name].href)))
                        else:
                            logger.warning(f"No '{stac_asset_name}' asset found in item {absolute_link_href}")
        else:
            logger.warning("No links found in the STAC catalog.")

    except Exception as e:
        logger.error(f"Error fetching S1 GRD product paths: {e}")

    return s1_grd_paths


@logtime
def get_dem(bbox: tuple[float, float, float, float], out_dir: str) -> str:
    """
    Download DEM from Copernicus using Sardem.

    Parameters
    ----------
    bbox : str
        Bounding box coordinates (min_lon, min_lat, max_lon, max_lat).
        Example: '-156 18.8 -154.7 20.3'.
    out_dir : str
        Path to the output directory.

    Returns
    -------
    str
        Path to the downloaded DEM file
    """
    logger.info("Downloading DEM from Copernicus...")
    dem_file = os.path.join(out_dir, "dem.tif")
    try:
        cop_dem.download_and_stitch(
            dem_file, bbox, output_format="GTiff"
        )
    except Exception as e:
        logger.error(f"Error downloading DEM: {e}")
        dem_file = ""
    return dem_file



@logtime
def run_sarsen(s1_file: str, dem_file: str, output_dir: str) -> str:
    """
    Runs SARsen processing on a Sentinel-1 GRD product and a DEM.

    Parameters
    ----------
    s1_file : str
        Path to the Sentinel-1 GRD product.
    dem_file : str
        Path to the DEM file.
    output_dir : str
        Path to the output directory.

    Returns
    -------
    str
        Path to the output of SARsen processing.
    """
    logger.info("Running SARsen on the S1 GRD product and the DEM...")
    output_file = os.path.join(
        output_dir, os.path.basename(s1_file).replace(".SAFE", "_sarsen_output.tif")
    )
    try:
        product = sarsen.Sentinel1SarProduct(
            s1_file, measurement_group="IW/VV"
        )
        sarsen.terrain_correction(
            product, output_urlpath=output_file, dem_urlpath=dem_file,correct_radiometry="gamma_nearest"
        )
    except Exception as e:
        logger.error(f"Error running SARsen: {e}")
        output_file = ""
    return output_file

def extract_zip(zip_file):
    """
    Extract a zip file.

    Args:
        zip_file: Path to the zip file.

    Returns:
        The absolute path of the unzipped file.
    """
    logger.info(f"Extracting zip file: {zip_file}")
    try:
        with zipfile.ZipFile(zip_file, "r") as zip_ref:
            # Create a temporary directory to extract the zip file
            temp_dir = os.path.abspath("temp_extract")
            os.makedirs(temp_dir, exist_ok=True)
            zip_ref.extractall(temp_dir)
            # Get the list of extracted files
            extracted_files = os.listdir(temp_dir)
            if extracted_files:
                return os.path.join(temp_dir, extracted_files[0])
            else:
                logger.warning("No files extracted from zip file.")
                return ""
    except Exception as e:
        logger.error(f"Error extracting zip file: {e}")
        return ""

def parse_args() -> Args:
    """Parse the command-line arguments."""

    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument(
        "--stac_catalog_folder",
        type=str,
        help="path to the STAC directory (containing catalog.json, item.json, and Sentinel-1 GRD product)",
        metavar="stac_catalog_folder",
        required=False,
    )
    parser.add_argument(
        "--bbox",
        type=float,
        help="lat/lon bounding box (example: --bbox '-118.068 34.222 -118.058 34.228')",
        nargs=4,
        metavar=("LEFT", "BOTTOM", "RIGHT", "TOP"),
        required=True,
    )
    parser.add_argument(
        "--stac_asset_name",
        type=str,
        help="Identifier of the STAC asset that contains the Sentinel-1 GRD product. Default: PRODUCT",
        default="PRODUCT",
        metavar="stac_asset_name",
        required=False,
    )
    parser.add_argument(
        "-o",
        "--out_dir",
        dest="out_dir",
        metavar="PATH",
        type=str,
        help="output directory",
        required=True,
    )

    raw_args = parser.parse_args()

    return Args(
        stac_catalog_folder=raw_args.stac_catalog_folder,
        bbox=raw_args.bbox,
        stac_asset_name=raw_args.stac_asset_name,
        out_dir=raw_args.out_dir,
    )

def bbox_to_geojson(bbox):
    """
    Convert bbox to GeoJSON geometry.
    
    Parameters:
    bbox (list): A list of 4 coordinates representing the bounding box [min_lon, min_lat, max_lon, max_lat]
    
    Returns:
    dict: A GeoJSON geometry dictionary
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }

def retrieve_stac_item_by_rel(stac_catalog_file, stac_item_rel):
    """
    Retrieves from the STAC catalog the first STAC item having a link rel matching stac_item_rel.

    Parameters
    ----------
    stac_catalog_file : str
        Path to the STAC catalog file
    stac_item_rel : str
        Link rel value of the requested STAC Item

    Returns
    -------
    pystac.Item
        A pystac.Item object if the STAC catalog contains an item having a link rel matching stac_item_rel, None otherwise
    """
    try:
        # Read catalog.json
        with open(stac_catalog_file, 'r') as file:
            catalog_data = json.load(file)
            catalog = pystac.Catalog.from_dict(catalog_data)

        if not catalog.links:
            logger.warning("No links found in the STAC catalog.")
            return None

        for link in catalog.links:
            # Read item with the provided rel
            if link.rel != stac_item_rel:
                continue

            absolute_link_href = os.path.normpath(os.path.join(os.path.dirname(stac_catalog_file), link.target))

            with open(absolute_link_href, 'r') as item_file:
                item_data = json.load(item_file)
                return pystac.Item.from_dict(item_data)

    except Exception as e:
        logger.error(f"Error retrieving the STAC item: {e}")

    return None

def create_stage_out_catalog(output_dir, output_stac_item, bbox, asset_name, asset_path):
    """
    Creates a STAC catalog with the provided STAC item. 
    The STAC item is modified as follows:
    - self link is set to f"{output_dir}/{output_stac_item.id}/{output_stac_item.id}.json"
    - title property is set to the asset file name
    - bbox and geometry attributes are updated with the provided bbox
    - the STAC assets are replaced with the provided asset_path

    Parameters
    ----------
    output_dir : str
        Path to the folder where the STAC catalog and STAC item files will be created
    output_stac_item : str
        The STAC item to update and add to the STAC catalog
    bbox : [float]
        The STAC item bbox
    asset_name : str
        The STAC asset name
    asset_path : path
        The STAC asset path

    Returns
    -------
    pystac.Catalog
        A pystac.Catalog object representing the STAC catalog created by this function
    """
    output_stac_item_path = os.path.abspath(os.path.join(output_dir, output_stac_item.id, output_stac_item.id + ".json"))
    logger.info("Creating STAC item {output_stac_item_path}")

    output_stac_item.set_self_href(output_stac_item_path)
    output_stac_item.properties["title"] = os.path.basename(asset_path)
    output_stac_item.bbox = bbox
    output_stac_item.geometry = bbox_to_geojson(output_stac_item.bbox)

    output_stac_asset = output_stac_item.assets[asset_name].clone()
    output_stac_asset_path = os.path.abspath(asset_path)
    output_stac_asset.href = output_stac_asset_path
    output_stac_asset.title = "output"
    output_stac_asset.media_type = "image/tiff"
    output_stac_asset.extra_fields["file:size"] = os.path.getsize(output_stac_asset_path)
    output_stac_asset.roles = ["data"]

    output_stac_item.assets = {"output" : output_stac_asset}
    output_stac_item.make_asset_hrefs_relative()

    output_stac_catalog_path = os.path.join(output_dir, "catalog.json")
    logger.info(f"Creating STAC catalog {output_stac_catalog_path}")
    output_stac_catalog = pystac.Catalog(id="SARsen output catalog", description="SARsen output catalog", 
                         href=output_stac_catalog_path,
                         catalog_type=pystac.catalog.CatalogType.SELF_CONTAINED)
    output_stac_catalog.add_item(output_stac_item)
    output_stac_catalog.save()

    logger.info("Stage out catalog created")
    return output_stac_catalog

@logtime
def main() -> None:
    """
        Main function to execute the OGC application.

        Steps:
        1. Parse arguments
        2. Get S1 GRD product paths
        3. Download DEM
        4. Run SARsen
        5. Create the STAC catalog for stage out of the processor outputs
    """
    # Step 1: Parse arguments
    args = parse_args()

    # Step 2: Get S1 GRD product paths
    catalog_path = os.path.join(args.stac_catalog_folder,"catalog.json")
    s1_grd_paths = get_s1_grd_path(catalog_path, args.stac_asset_name)

    # Step 3: Download DEM
    dem_file = get_dem(args.bbox, args.out_dir)

    # Step 4: Run SARsen for each S1 GRD product
    output_files = []
    for s1_grd_path in s1_grd_paths:
        extracted_s1_grd_path = extract_zip(s1_grd_path)
        if extracted_s1_grd_path:
            output_files.append(run_sarsen(extracted_s1_grd_path, dem_file, args.out_dir))
        else:
            logger.error("Error extracting zip file for %s", s1_grd_path)
            continue
    logger.info("SARSEN process completed for all S1 GRD products.")

    # Step 5: Create the STAC catalog for stage out of the processor outputs
    create_stage_out_catalog(args.out_dir, 
                             retrieve_stac_item_by_rel(catalog_path, "item").clone(), 
                             args.bbox,
                             args.stac_asset_name,
                             output_files[0])

if __name__ == "__main__":
    main()
