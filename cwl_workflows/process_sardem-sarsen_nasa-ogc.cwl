cwlVersion: v1.2
$graph:
- class: Workflow
  label: sardem-sarsen
  doc: This application is designed to process Synthetic Aperture Radar (SAR) data
    from Sentinel-1 GRD (Ground Range Detected) products using a Digital Elevation
    Model (DEM) obtained from Copernicus.
  id: sardem-sarsen
  inputs:
    bbox:
      doc: Bounding box as 'LEFT BOTTOM RIGHT TOP'
      label: Bounding box
      type: string
      default: -118.06817 34.22169 -118.05801 34.22822
    sentinel_granule:
      doc: Sentinel granule URL
      label: Sentinel granule URL
      type: Directory
      default:
        class: Directory
        path: https://cmr.earthdata.nasa.gov/stac/ASF/collections/SENTINEL-1A_DP_GRD_HIGH_1/items/S1A_IW_GRDH_1SDV_20250330T171421_20250330T171446_058537_073E4F_985B-GRD_HD
    stac_asset_name:
      doc: STAC asset name
      label: asset name
      type: string?
      default: edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20250330T171421_20250330T171446_058537_073E4F_985B
  outputs:
    out:
      type: Directory
      outputSource: process/outputs_result
  steps:
    process:
      run: '#main'
      in:
        bbox: bbox
        sentinel_granule: sentinel_granule
        stac_asset_name: stac_asset_name
      out:
      - outputs_result
- class: CommandLineTool
  id: main
  requirements:
    DockerRequirement:
      dockerPull: ghcr.io/maap-project/sardem-sarsen:nasa-ogc
    NetworkAccess:
      networkAccess: true
    ResourceRequirement:
      ramMin: 5
      coresMin: 1
      outdirMax: 20
  baseCommand: /sardem-sarsen/sardem-sarsen.sh
  inputs:
    bbox:
      type: string
      inputBinding:
        position: 1
        prefix: --bbox
      default: -118.06817 34.22169 -118.05801 34.22822
    sentinel_granule:
      type: Directory
      inputBinding:
        position: 2
        prefix: --sentinel_granule
      default:
        class: Directory
        path: https://cmr.earthdata.nasa.gov/stac/ASF/collections/SENTINEL-1A_DP_GRD_HIGH_1/items/S1A_IW_GRDH_1SDV_20250330T171421_20250330T171446_058537_073E4F_985B-GRD_HD
    stac_asset_name:
      type: string?
      inputBinding:
        position: 3
        prefix: --stac_asset_name
      default: edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20250330T171421_20250330T171446_058537_073E4F_985B
  outputs:
    outputs_result:
      outputBinding:
        glob: ./output*
      type: Directory
s:author:
- class: s:Person
  s:name: arthurduf
s:contributor:
- class: s:Person
  s:name: arthurduf
s:citation: https://github.com/MAAP-Project/sardem-sarsen.git
s:codeRepository: https://github.com/MAAP-Project/sardem-sarsen.git
s:commitHash: fe12a43e9221529cbf03215aac2ce24f6bc6684c
s:dateCreated: 2026-07-01
s:license: https://github.com/MAAP-Project/sardem-sarsen/blob/main/LICENSE
s:softwareVersion: 1.0.0
s:version: nasa-ogc
s:releaseNotes: None
s:keywords: ogc, sar
$namespaces:
  s: https://schema.org/
$schemas:
- https://raw.githubusercontent.com/schemaorg/schemaorg/refs/heads/main/data/releases/9.0/schemaorg-current-http.rdf
