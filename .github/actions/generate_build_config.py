'''

MAAP OGC Application Package Wrapper

This is a project-specific OGC wrapper that invokes the reference implementation for
OGC application package generation.

'''
import sys
import yaml
import json
import logging
import json
import os
from ogc_app_pack import AppPackGenerator

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app_pack.log'
)


def generate_config(data):
    """
    Constructs list of environment variables from algorithm data to be used in algorithm registration.
    :return
    """
    try:
        config_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        logging.debug("Writing build config file to {config_filepath}")
        print(f"Writing config file at {config_filepath}")

        repo_name = os.path.basename(data.get('repository_url'))
        repo_name = str(repo_name).replace(".git", "")
        with open(config_filepath, "w") as f:
            f.write(f"BASE_IMAGE_NAME={data.get('docker_container_url')}\n")
            f.write(f"REPO_URL_WITH_TOKEN={data.get('repository_url')}\n")
            f.write(f"REPO_NAME={repo_name}\n")
            f.write(f"BRANCH={data.get('algorithm_version')}\n")
            f.write(f"ALGORITHM_NAME={data.get('algorithm_name')}\n")
            if data.get('build_command'):
                f.write(f"BUILD_CMD={data.get('build_command')}\n")
        print("Completed writing config file")
    except Exception as ex:
        print("Failed to generate build configuration for algorithm {REPO_NAME}:{BRANCH}")
        print(ex)


def read_algorithm_yaml_file(filepath):
    with open(filepath, 'r') as fp:
        data = yaml.safe_load(fp)
        return data


def main(args):
    if len(sys.argv) <= 1:
        logging.error("An input must be provided. Exiting.")
        raise Exception("An input must be provided. Exiting.")

    data = {}
    algo_file = args[1]
    logging.info("Generating application package using: %s", algo_file)

    # TODO: determine if input is already cwl or not
    try:
        # data = yaml.safe_load(algo_file)
        # data = json.loads(json.loads(algo_file))
        data = read_algorithm_yaml_file(algo_file)

        # OGC does not support file, positional inputs the way MAAP does, so we need to flatten the inputs.
        flattened_inputs = []
        algo_config_inputs = data.get("inputs", {})
        for value in ["positional", "config", "file"]:
            if value in algo_config_inputs:
                for k in algo_config_inputs.get(value):
                    if value == "file":
                        k.update({"type": "File"})
                    elif value == "config":
                        k.update({"type": "String"})
                        k.update({"prefix": f"--{k.get('name')}"})
                    flattened_inputs.append(k)
        data['inputs'] = flattened_inputs
    except Exception as e:
        logging.error("An error occurred: %s", str(e))

    # Generate the OGC package using the reference implementation
    generate_config(data)
    return 0

if __name__ == '__main__':
    return_code = main(sys.argv)

