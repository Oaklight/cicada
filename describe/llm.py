import argparse
import logging
import os
import sys
from typing import List

import openai
from tqdm import tqdm

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from desc_utils import load_config, load_prompts, save_descriptions

logger = logging.getLogger("asssitive lm")
log_level = "DEBUG"
logger.setLevel(log_level)
handler = logging.StreamHandler()
handler.setLevel(log_level)
logger.addHandler(handler)


class LLM:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.org_id = org_id
        self.model_kwargs = model_kwargs

        self.client = openai.OpenAI(
            api_key=self.api_key, base_url=self.api_base_url, organization=self.org_id
        )
        self.user_prompt_templates = prompt_templates.get("user_prompt_template", {})
        self.system_prompt_template = prompt_templates.get("system_prompt_template", "")

    def query(self, prompt, system_prompt=None):
        messages = [
            {"role": "user", "content": prompt},
        ]

        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
            ] + messages

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **self.model_kwargs,
        )

        return response.choices[0].message.content.strip()

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


def main():
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

    llm = LLM(
        assist_llm_config["api_key"],
        assist_llm_config.get("api_base_url"),
        assist_llm_config.get("model_name", "gpt-4o-mini"),
        assist_llm_config.get("org_id"),
        load_prompts(args.prompts, "llm"),
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

        logger.debug(f"Object Description:\n{obj_description}")
        logger.debug("-" * 50)
        logger.debug(f"What it is:\n{what_it_is}")
        logger.debug("-" * 50)
        logger.debug(f"Parts List:\n{parts_list}")
        logger.debug("-" * 50)
        logger.debug(f"Building Steps:\n{building_steps}")

        if args.save:
            update_metadata = {
                "object_description": obj_description,
                "what_it_is": what_it_is,
                "parts_list": parts_list,
                "building_steps": building_steps,
            }
            save_descriptions(each_task["base_path"], update_metadata)


if __name__ == "__main__":
    main()
