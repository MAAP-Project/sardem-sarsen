cwlVersion: v1.2
$graph:
- class: Workflow
  label: Sardem Sarsen Demo 09
  doc: This application is designed to process Synthetic Aperture Radar (SAR) data
    from Sentinel-1 GRD (Ground Range Detected) products using a Digital Elevation
    Model (DEM) obtained from Copernicus.
  id: sardem-sarsen-demo-09
  inputs:
    bbox:
      doc: Bounding box as 'LEFT BOTTOM RIGHT TOP'
      label: bounding box
      type: string
    stac_catalog_folder:
      doc: STAC catalog folder
      label: catalog folder
      type: Directory
    stac_asset_name:
      doc: STAC asset name
      label: asset name
      type: string?
  outputs:
    out:
      type: Directory
      outputSource: process/outputs_result
  steps:
    process:
      run: '#main'
      in:
        bbox: bbox
        stac_catalog_folder: stac_catalog_folder
        stac_asset_name: stac_asset_name
      out:
      - outputs_result
- class: CommandLineTool
  id: main
  requirements:
    DockerRequirement:
      dockerPull: ghcr.io/maap-project/sardem-sarsen:esa-ogc-0.1
    NetworkAccess:
      networkAccess: true
    ResourceRequirement:
      ramMin: 5
      coresMin: 1
      outdirMax: 20
  baseCommand: /app/sardem-sarsen/sardem-sarsen.sh
  inputs:
    bbox:
      type: string
      inputBinding:
        position: 1
        prefix: --bbox
    stac_catalog_folder:
      type: Directory
      inputBinding:
        position: 2
        prefix: --stac_catalog_folder
    stac_asset_name:
      type: string?
      default: PRODUCT
      inputBinding:
        position: 3
        prefix: --stac_asset_name
  outputs:
    outputs_result:
      outputBinding:
        glob: ./output*
      type: Directory
$namespaces:
  s: https://schema.org/
s:author: arthurduf
s:contributor: arthurduf
s:citation: https://github.com/MAAP-Project/sardem-sarsen.git
s:codeRepository: https://github.com/MAAP-Project/sardem-sarsen.git
s:dateCreated: 2025-02-18
s:commitHash: test
s:license: https://github.com/MAAP-Project/sardem-sarsen/blob/main/LICENSE
s:softwareVersion: 1.1.0
s:version: esa
s:releaseNotes: None
s:keywords: ogc, sar
$schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
