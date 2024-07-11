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
def get_s1_grd_path(json_file):
    """
    Fetches the paths of S1 GRD products from the STAC catalog.

    Parameters
    ----------
    json_file : str
        Path to the JSON file containing the STAC catalog.

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
                        # get PRODUCT asset
                        if item.assets and 'PRODUCT' in item.assets:
                            s1_grd_paths.append(item.assets['PRODUCT'].href)
                        else:
                            logger.warning(f"No 'PRODUCT' asset found in item {absolute_link_href}")
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
            temp_dir = os.path.join(os.path.dirname(zip_file), "temp_extract")
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
        out_dir=raw_args.out_dir,
    )


@logtime
def main() -> None:
    """
        Main function to execute the OGC application.

        Steps:
        1. Parse arguments
        2. Get S1 GRD product paths
        3. Download DEM
        4. Run SARsen
    """
    # Step 1: Parse arguments
    args = parse_args()

    # Step 2: Get S1 GRD product paths
    catalog_path = os.path.join(args.stac_catalog_folder,"catalog.json")
    s1_grd_paths = get_s1_grd_path(catalog_path)

    # Step 3: Download DEM
    dem_file = get_dem(args.bbox, args.out_dir)

    # Step 4: Run SARsen for each S1 GRD product
    for s1_grd_path in s1_grd_paths:
        extracted_s1_grd_path = extract_zip(s1_grd_path)
        if extracted_s1_grd_path:
            run_sarsen(extracted_s1_grd_path, dem_file, args.out_dir)
        else:
            logger.error("Error extracting zip file for %s", s1_grd_path)
            continue
    logger.info("SARSEN process completed for all S1 GRD products.")

if __name__ == "__main__":
    main()
