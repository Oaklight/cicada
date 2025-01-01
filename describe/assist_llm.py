import argparse
import logging
import os
import sys
from typing import List

from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import llm
from common.utils import load_config, load_prompts
from describe.utils import save_descriptions

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class AssistLLM(llm.LanguageModel):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.user_prompt_templates = prompt_templates.get("user_prompt_template", {})
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def distill_what_it_is(self, input_text: str) -> str:
        user_prompt_template = self.user_prompt_templates.get("what_is_this_object")
        prompt = user_prompt_template.format(generated_description=input_text)

        relevant_text = self.query(prompt)
        return relevant_text

    def extract_object_description(self, input_text: str) -> str:
        user_pompt_template = self.user_prompt_templates.get(
            "object_description_with_features"
        )
        prompt = user_pompt_template.format(generated_description=input_text)

        relevant_text = self.query(prompt, system_prompt=self.system_prompt_template)
        return relevant_text

    def extract_parts_list(self, input_text: str) -> str:
        user_prompt_template = self.user_prompt_templates.get("potential_parts_list")
        prompt = user_prompt_template.format(generated_description=input_text)

        relevant_text = self.query(prompt, system_prompt=self.system_prompt_template)
        return relevant_text

    def extract_building_steps(self, input_text: str) -> str:
        user_prompt_template = self.user_prompt_templates.get(
            "CAD_construction_instructions"
        )
        prompt = user_prompt_template.format(generated_description=input_text)

        relevant_text = self.query(prompt, system_prompt=self.system_prompt_template)
        return relevant_text


def load_object_metadata(task_path: str) -> List[dict]:
    """
    param task_path: Path to the task YAML file or path to certain metadata.json or directory containing a metadata.json

    returns: List of metadata dictionaries
    """
    if os.path.isdir(task_path):
        # single metadata
        metadata = {
            "base_path": task_path,
            "metadata": load_config(os.path.join(task_path, "metadata.json")),
        }
        metadata_collection = [metadata]
    elif os.path.isfile(task_path) and task_path.endswith("metadata.json"):
        # single metadata
        metadata = {
            "base_path": os.path.dirname(task_path),
            "metadata": load_config(task_path),
        }
        metadata_collection = [metadata]
    elif os.path.isfile(task_path) and task_path.endswith("tasks.yaml"):
        tasks = load_config(task_path)
        metadata_collection = [
            {
                "base_path": obj["base_path"],
                "metadata": load_config(
                    os.path.join(obj["base_path"], "metadata.json")
                ),
            }
            for obj in tasks
        ]
    return metadata_collection


def _main():
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "-t",
        "--task",
        default="tasks.yaml",
        help="Path to the task YAML file or directory containing images from a single object",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save generated descriptions to metadata.yaml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    tasks = load_object_metadata(args.task)

    assist_llm_config = config["assist-llm"]

    llm = AssistLLM(
        assist_llm_config["api_key"],
        assist_llm_config.get("api_base_url"),
        assist_llm_config.get("model_name", "gpt-4o-mini"),
        assist_llm_config.get("org_id"),
        load_prompts(args.prompts, "assist-llm"),
        **assist_llm_config.get("model_kwargs", {}),
    )

    for each_task in tqdm(tasks):
        metadata = each_task["metadata"]
        image_description = metadata["generated_description"]

        # extract object descriptions
        obj_description = llm.extract_object_description(image_description)
        # generate what it is
        what_it_is = llm.distill_what_it_is(image_description)
        # extract parts list
        parts_list = llm.extract_parts_list(image_description)
        # extract building steps
        building_steps = llm.extract_building_steps(image_description)

        logging.debug(f"Object Description:\n{obj_description}")
        logging.debug("-" * 50)
        logging.debug(f"What it is:\n{what_it_is}")
        logging.debug("-" * 50)
        logging.debug(f"Parts List:\n{parts_list}")
        logging.debug("-" * 50)
        logging.debug(f"Building Steps:\n{building_steps}")

        if args.save:
            update_metadata = {
                "object_description": obj_description,
                "what_it_is": what_it_is,
                "parts_list": parts_list,
                "building_steps": building_steps,
            }
            save_descriptions(each_task["base_path"], update_metadata)


if __name__ == "__main__":
    _main()
