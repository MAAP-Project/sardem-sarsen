cwlVersion: v1.2
$graph:
  - class: Workflow
    label: null 
    doc: null
    id: null
    inputs: null
    outputs: null
    steps:
      process:
        run: "#main"
        in: null
        out: null

  - class: CommandLineTool
    id: main
    requirements:
      DockerRequirement:
        dockerPull: null
      NetworkAccess:
        networkAccess: true
      EnvVarRequirement:
        envDef: null
    baseCommand: null
    inputs: null
    outputs: null

$namespaces:
  s: https://schema.org/
  s:author:
    - class: s:Person
      s:name: null

  s:contributor:
    - class: s:Person
      s:name: null

  s:citation: null
  s:codeRepository: null
  s:dateCreated: null
  s:license: null
  s:softwareVersion: null
  s:version: null
  s:releaseNotes: null
  s:keywords: null
$schemas:
- http://schema.org/version/9.0/schemaorg-current-http.rdf