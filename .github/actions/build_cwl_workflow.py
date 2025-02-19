'''
Builds a CWL workflow from a YML input file.

Inputs:

--yaml_file (required)
YML file containing algorithm information that will be parsed to create the workflow file.
See data/workflow_configuration.yml for an example. This example contains the information
needed to create a workflow that is compliant with OGC and CWL best practices.

--workflow_output_dir (optional)
The directory the workflow files should be written to. If not provided, the default is `workflows`
and the directory will be created if it does not exist.

--cwl_template_file (optional)
Template file to use when creating the workflow file. Currently, only CWL v1.2 is supported and
will be used by default if not provided.

Outputs:

CWL v1.2 workflow file. Workflow file names will have the process name and version appended to
them. For example, if the process name is `myProcess` and its version is `main`, the resulting 
workflow file will be named `process_myProcess_main.cwl`.

Sample execution:
build_cwl_workflow.py --yaml_file data/workflow_configuration.yml --workflow_output_dir workflows/

'''

import yaml
import argparse
import os
from datetime import date


def set_path_value(workflow, path, value):
    """
    Set value to path in workflow template.
    """
    for key in path[:-1]:
        workflow = workflow[key]
    workflow[path[-1]] = value


def handle_value(key, value):
    """
    Processes the given key-value pair for cases where a simple read from the
    YML input is insufficient. 
    """
    if key == "env_def":
        val = []
        for env in value:
            for key, value in env.items():
                val.append((key, value))
        val = dict(val)
    else:
        return value
    return val


def yaml_to_cwl(yaml_file, workflow_output_dir, template_file):
    # Load workflow configuration YML file
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)

    # Load CWL template file
    with open(template_file, 'r') as f:
        workflow = yaml.safe_load(f)

    # Create output directory if nonexistent
    if not os.path.exists(workflow_output_dir):
        os.makedirs(workflow_output_dir)


    # Attempt to retrieve information required to be compliant with OGC and CWL v1.2 best practices
    #
    # See CWL v1.2 docs here: https://www.commonwl.org/v1.2/Workflow.html#Workflow 
    # See OGC docs here: https://docs.ogc.org/bp/20-089r1.html#toc24
    
    # Define mapping of YML input file fields to OGC and CWL generic fields
    OGC_CWL_KEY_MAP = {
                "algorithm_description": [("$graph", 0, "doc")],
                "algorithm_name": [("$graph", 0, "label"), ("$graph", 0, "id"), ("$graph", 1, "requirements", "DockerRequirement", "dockerPull")],
                "algorithm_version": [("$namespaces", "s:version")],
                "author": [("$namespaces", "s:author")],
                "citation": [("$namespaces", "s:citation")],
                "code_repository": [("$namespaces", "s:codeRepository")],
                "contributor": [("$namespaces", "s:contributor")],
                "keywords": [("$namespaces", "s:keywords")],
                "license": [("$namespaces", "s:license")],
                "release_notes": [("$namespaces", "s:releaseNotes")],
                "run_command": [("$graph", 1, "baseCommand")]
              }
    
    for key in OGC_CWL_KEY_MAP:
        targets = OGC_CWL_KEY_MAP[key]
        if key in config:
            #value = handle_value(key, config[key])
            value = config[key]
            for target in targets:
                set_path_value(workflow, target, value)
        else:
            print("Expected key `{}` not found!", key)


    # Handle inputs and outputs separately since the same information is used in
    # slightly different formats across several different fields.
    workflow_inputs = []
    step_inputs = []
    process_inputs = []
    
    workflow_outputs = []
    step_outputs = []
    process_outputs = []

    for input in config.get("inputs", []):
        input_name = input.get("name")
        input_type = input.get("type")
        input_doc = input.get("doc")
        input_label = input.get("label")

        if input_name is None or input_type is None:
            print("Expected name and type to be specified for input!")
        
        # Workflow inputs
        tmp = {input_name: {
            "doc": input_doc,
            "label": input_label,
            "type": input_type
        }}
        workflow_inputs.append(tmp)

        # Process inputs
        tmp = {input_name: {
            "type": input_type,
            "inputBinding": {
                "position": len(process_inputs) + 1,
                "prefix": f"--{input_name}"
        }}}
        process_inputs.append(tmp)

        # Step inputs
        tmp = {input_name: input_name}
        step_inputs.append(tmp)

    # Need to merge the lists of dicts to properly format output
    workflow_inputs = {k: v for d in workflow_inputs for k, v in d.items()}
    process_inputs = {k: v for d in process_inputs for k, v in d.items()}
    step_inputs = {k: v for d in step_inputs for k, v in d.items()}

    workflow["$graph"][0]["inputs"] = workflow_inputs
    workflow["$graph"][1]["inputs"] = process_inputs
    workflow["$graph"][0]["steps"]["process"]["in"] = step_inputs


    for output in config.get("outputs", []):
        output_name = output.get("name")
        output_type = output.get("type")
        #output_doc = output.get("doc")
        #output_label = output.get("label")

        if output_name is None or output_type is None:
            print("Expected name and type to be specified for output!")

        # Workflow outputs
        tmp = {output_name: {
            "type": output_type,
            "outputSource": f"process/outputs_result"
        }}
        workflow_outputs.append(tmp)

        # Process outputs
        tmp = {f"outputs_result" :{
            "outputBinding": {
                "glob": f"./output*"
            },
            "type": output_type
            }
        }
        process_outputs.append(tmp)

        # Step outputs
        step_outputs.append("outputs_result")


    workflow_outputs = {k: v for d in workflow_outputs for k, v in d.items()}
    process_outputs = {k: v for d in process_outputs for k, v in d.items()}
    
    workflow["$graph"][0]["outputs"] = workflow_outputs
    workflow["$graph"][1]["outputs"] = process_outputs
    workflow["$graph"][0]["steps"]["process"]["out"] = step_outputs

    # Add information that is required to be compliant with OGC and CWL best practices
    # that will not be in the YML input file
    workflow["$namespaces"]["s:dateCreated"] = date.today()
    workflow["$namespaces"]["s:softwareVersion"] = "1.0.0"

    # Define additional mapping that extends beyond OGC and CWL v1.2 best practices
    EXT_KEY_MAP = {
                "env_def": [("$graph", 1, "requirements", "EnvVarRequirement", "envDef")]
              }

    for key in EXT_KEY_MAP:
        targets = EXT_KEY_MAP[key]
        if key in config:
            value = handle_value(key, config[key])
            for target in targets:
                set_path_value(workflow, target, value)


    # Dump data to workflow file
    file_name = 'process_' + config["algorithm_name"].replace('/', '_') + '_' + config["algorithm_version"].replace('/', '_') + '.cwl'
    workflow_file = os.path.join(workflow_output_dir, file_name)
    with open(workflow_file, 'w') as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)

    print(f"CWL workflow saved to {workflow_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert YML workflow configuration to CWL workflow.")
    parser.add_argument("--yaml_file", type=str, help="Path to the input workflow YML configuration file.", required=True)
    parser.add_argument("--workflow_output_dir", type=str, default="workflows", help="Directory workflow files will be written to. If not provided, `workflows` will be used as default. If the `workflows` directory does not exist, it will be created.")
    parser.add_argument("--cwl_template_file", type=str, default=".github/actions/templates/process.v1_2.cwl", help="Path to the CWL template file. Default template used is compliant with CWL v1.2.")

    args = parser.parse_args()
    yaml_to_cwl(args.yaml_file, args.workflow_output_dir, args.cwl_template_file)
