import json
import os
from typing import List, Union

import yaml


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def load_prompts(prompts_path: str, which_model: str = "vlm") -> dict:
    prompts_all = load_config(prompts_path)
    return prompts_all[which_model]


def save_descriptions(
    base_dirs: Union[str, List[str]], descriptions: Union[dict, List[dict]]
):

    if not isinstance(base_dirs, list):
        base_dirs = [base_dirs]
    if not isinstance(descriptions, list):
        descriptions = [descriptions]

    assert len(base_dirs) == len(
        descriptions
    ), "Number of base paths and descriptions do not match"

    for directory, desc in zip(base_dirs, descriptions):
        metadata = {}
        metadata_path = os.path.join(directory, "metadata.json")
        if os.path.exists(metadata_path):
            metadata = load_config(metadata_path)

        # extend metadata.json with the new descriptions
        metadata.update(desc)

        with open(metadata_path, "w") as file:
            json.dump(metadata, file, indent=4)
