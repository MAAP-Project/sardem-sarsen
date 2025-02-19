cwlVersion: v1.2
$graph:
- class: Workflow
  label: sardem-sarsen
  doc: sardem-sarsen algorithm
  id: sardem-sarsen
  inputs:
    bbox:
      doc: Bounding box as 'LEFT BOTTOM RIGHT TOP'
      label: Bounding box as 'LEFT BOTTOM RIGHT TOP'
      type: Directory
    stac_catalog_folder:
      doc: STAC catalog folder
      label: STAC catalog folder
      type: Directory
    o:
      doc: Output directory
      label: Output directory
      type: Directory
  outputs:
    out:
      type: Directory
      outputSource: process/outputs_result
  steps:
    process:
      run: '#process'
      in:
        bbox: bbox
        stac_catalog_folder: stac_catalog_folder
        o: o
      out:
      - outputs_result
- class: CommandLineTool
  id: process
  requirements:
    DockerRequirement:
      dockerPull: sardem-sarsen
    NetworkAccess:
      networkAccess: true
    EnvVarRequirement:
      envDef:
        PATH: /opt/conda/bin:/opt/conda/condabin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  baseCommand: /app/sardem-sarsen/sardem-sarsen.sh
  arguments: []
  inputs:
    bbox:
      type: Directory
      inputBinding:
        position: 1
        prefix: --bbox
    stac_catalog_folder:
      type: Directory
      inputBinding:
        position: 2
        prefix: --stac_catalog_folder
    o:
      type: Directory
      inputBinding:
        position: 3
        prefix: --o
  outputs:
    outputs_result:
      outputBinding:
        glob: ./output*
      type: Directory
$namespaces:
  s: https://schema.org/
s:softwareVersion: 1.0.0
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
