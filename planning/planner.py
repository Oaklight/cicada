import argparse
import logging
import os
import sys
from typing import Any, Dict, List, Optional

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.extend([_current_dir, _parent_dir])

from common import llm
from common.basics import DesignGoal, PromptBuilder
from common.utils import load_config, load_prompts, setup_logging
from planning.basics import DesignPlan

logger = logging.getLogger(__name__)


class Planner(llm.LanguageModel):
    """A DOT language planner that converts DesignGoal into a structured DesignPlan."""

    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        model_name: str,
        org_id: str,
        **model_kwargs,
    ):
        """Initialize the Planner.
        Args:
            api_key (str): The API key for the OpenAI service.
            api_base_url (str): The base URL for the OpenAI API.
            model_name (str): The name of the model to use.
            org_id (str): The organization ID for the OpenAI service.
            model_kwargs (dict): Additional keyword arguments for the model.
        """
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.plan_prompt = load_prompts("prompts.yaml", "planner")

    def generate_dot_plan(self, design_goal: DesignGoal) -> str:
        """Generate a DOT language representation of the design goal.

        Args:
            design_goal (DesignGoal): The design goal to be converted into a DOT plan.

        Returns:
            str: The generated DOT plan as a string.
        """
        # Construct the prompt
        pb = PromptBuilder()
        pb.add_system_prompt(self.plan_prompt["system_prompt"])
        pb.add_user_prompt(
            f"Design Goal:\n{design_goal.text}\n"
            f"Parts:\n{[p['part_name'] for p in design_goal.extra['decomposition']['parts']]}\n"
            f"Assembly Steps:\n{chr(10).join(design_goal.extra['decomposition']['assembly_plan'])}"
        )

        # Call LLM to generate DOT
        dot_response = self.query_with_promptbuilder(pb)
        return self._extract_dot_code(dot_response)

    def _extract_dot_code(self, response: str) -> str:
        """Extract the DOT code block from the response.

        Args:
            response (str): The response containing the DOT code.

        Returns:
            str: The extracted DOT code.
        """
        if "```dot" in response:
            return response.split("```dot")[1].split("```")[0].strip()
        return response

    def parse_dot_to_plan(self, dot_str: str, design_goal: DesignGoal) -> DesignPlan:
        """Parse the DOT code into a DesignPlan object tree.

        Args:
            dot_str (str): The DOT format string.
            design_goal (DesignGoal): The original design goal.

        Returns:
            DesignPlan: The parsed DesignPlan object tree.
        """
        root = DesignPlan(design_goal)  # Root node with the original design goal
        node_map = {
            part["part_name"]: child
            for part, child in zip(
                design_goal.extra["decomposition"]["parts"], root.children
            )
        }

        # Parse dependencies from DOT edges
        for line in dot_str.split("\n"):
            line = line.strip()
            if "->" in line:
                src, dst = line.split("->")[0].strip(), line.split("->")[1].split("[")[
                    0
                ].strip().rstrip(";")
                src_node = node_map.get(src)
                dst_node = node_map.get(dst)
                if src_node and dst_node:
                    dst_node.dependencies.append(src_node)

        return root


def _main():
    """Test the functionality of the Planner."""
    setup_logging()

    parser = argparse.ArgumentParser(description="DOT Language Planner")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "design_goal_json",
        type=str,
        help="The design goal in JSON format",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    planner_config = config["planner-llm"]

    planner = Planner(
        planner_config["api_key"],
        planner_config.get("api_base_url"),
        planner_config.get("model_name", "gpt-4"),
        planner_config.get("org_id"),
        **planner_config.get("model_kwargs", {}),
    )

    # Load DesignGoal from JSON
    with open(args.design_goal_json, "r") as f:
        design_goal = DesignGoal.from_json(f.read())

    design_plan = DesignPlan(design_goal)
    print(design_plan.to_dot())
    # # Generate DOT plan
    # dot_plan = planner.generate_dot_plan(design_goal)
    # print("Generated DOT Plan:")
    # print(dot_plan)

    # # Parse DOT to DesignPlan object
    # root_plan = planner.parse_dot_to_plan(dot_plan, design_goal)
    # print("\nParsed Plan Structure:")
    # print(root_plan.to_dot())

    # # Visualize the plan as an image
    # root_plan.show(format="png", filename="design_plan")


if __name__ == "__main__":
    _main()
