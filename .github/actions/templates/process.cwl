cwlVersion: v1.2
$graph:
  - class: Workflow
    label: ""
    doc: ""
    id: ""
    inputs: {}
    outputs:
      out:
        type: Directory
        outputSource: process/outputs_result
    steps:
      process:
        run: "#process"
        in: {}
        out:
          - outputs_result

  - class: CommandLineTool
    id: process
    requirements:
      DockerRequirement:
        dockerPull: ""
      NetworkAccess:
        networkAccess: true
      EnvVarRequirement:
        envDef:
          PATH: "/opt/conda/bin:/opt/conda/condabin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    baseCommand: ""
    arguments: []
    inputs: {}
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