$graph:
- class: Workflow
  doc: Echo the command line
  id: sardem-sarsen-process
  inputs:
    stac_catalog_folder:
      doc: STAC Catalog containing references to S1 GRD IW/VV product
      label: catalog
      type: Directory
    bbox:
      doc: Bounding box
      label:  Bounding box
      type: string
  label: s expressions
  outputs:
    wf_outputs:
      outputSource:
      - step_1/outputs_result
      type: Directory[]


  steps:
    step_1:
      in:
        stac_catalog_folder: stac_catalog_folder
        bbox: bbox
      out:
      - outputs_result
      run: '#process'


- baseCommand: /app/sardem-sarsen/sardem-sarsen.sh
  class: CommandLineTool

  id: process

  inputs:
    stac_catalog_folder:
      type: Directory
      inputBinding:
        position: 2
        prefix: --stac_catalog_folder
    bbox:
      type: string
      inputBinding:
        position: 1
        prefix: --bbox

  outputs:
    outputs_result:
      outputBinding:
        glob: ./output*
      type: Directory[]
  requirements:
    EnvVarRequirement:
      envDef:
        PATH: /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    ResourceRequirement: {}
    InlineJavascriptRequirement: {}
    DockerRequirement:
      dockerPull: sardem-sarsen:0.3.0
  #stderr: std.err
  #stdout: std.out

cwlVersion: v1.0

$namespaces:
  s: https://schema.org/
s:softwareVersion: 0.3.0
schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf
