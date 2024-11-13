import argparse
import json
import os
import sys

import openai

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from desc_utils import load_config, load_prompts


class LLM:
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs
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


def main():
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=str,
        required=True,
        help="Path to the metadata JSON file",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    assist_llm_config = config["assist-llm"]

    llm = LLM(
        assist_llm_config["api_key"],
        assist_llm_config.get("api_base_url"),
        assist_llm_config.get("model_name", "gpt-4"),
        assist_llm_config.get("org_id"),
        load_prompts(args.prompts, "llm"),
        **assist_llm_config.get("model_kwargs", {}),
    )

    with open(args.metadata, "r") as f:
        metadata = json.load(f)

    image_description = metadata["image_descriptions"]

    # extract object descriptions
    obj_description = llm.extract_object_description(image_description)

    # generate what it is
    what_it_is = llm.distill_what_it_is(image_description)

    # extract parts list
    parts_list = llm.extract_parts_list(image_description)

    # extract building steps
    building_steps = llm.extract_building_steps(image_description)

    print("Object Description:\n", obj_description)
    print("-" * 50)
    print("What it is:\n", what_it_is)
    print("-" * 50)
    print("Parts List:\n", parts_list)
    print("-" * 50)
    print("Building Steps:\n", building_steps)


if __name__ == "__main__":
    main()
