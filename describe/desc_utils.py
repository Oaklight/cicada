import yaml


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def load_prompts(prompts_path: str, which_model: str = "vlm") -> dict:
    prompts_all = load_config(prompts_path)
    return prompts_all[which_model]
