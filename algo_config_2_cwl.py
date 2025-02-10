import yaml
import json
import argparse

def yaml_to_cwl(yaml_file, cwl_file, template_file):
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)
    
    with open(template_file, 'r') as f:
        workflow = yaml.safe_load(f)
    
    workflow["$graph"][0]["label"] = config["algorithm_name"]
    workflow["$graph"][0]["doc"] = config["algorithm_description"]
    workflow["$graph"][0]["id"] = config["algorithm_name"]
    workflow["$graph"][1]["requirements"]["DockerRequirement"]["dockerPull"] = config["algorithm_name"]
    workflow["$graph"][1]["baseCommand"] = "/app/" + config["algorithm_name"] + "/" + config["run_command"]
    
    workflow_inputs = workflow["$graph"][0]["inputs"]
    process_inputs = workflow["$graph"][1]["inputs"]
    step_inputs = workflow["$graph"][0]["steps"]["process"]["in"]
    
    for param in config.get("inputs", {}).get("positional", []):
        input_name = param["name"]
        input_type = "Directory" if param.get("type", True) else "string"
        
        workflow_inputs[input_name] = {
            "doc": param["description"],
            "label": param["description"],
            "type": input_type
        }
        
        process_inputs[input_name] = {
            "type": input_type,
            "inputBinding": {
                "position": len(process_inputs) + 1,
                "prefix": f"--{input_name}"
            }
        }
        
        step_inputs[input_name] = input_name
    
    with open(cwl_file, 'w') as f:
        yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
    
    print(f"CWL workflow saved to {cwl_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert YAML config to CWL workflow.")
    parser.add_argument("yaml_file", help="Path to the input algorithm YAML configuration file.")
    parser.add_argument("cwl_file", help="Path to the output CWL workflow file.")
    parser.add_argument("template_file", help="Path to the CWL template file.")
    
    args = parser.parse_args()
    yaml_to_cwl(args.yaml_file, args.cwl_file, args.template_file)
