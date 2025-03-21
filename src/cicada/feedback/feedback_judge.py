import argparse
import logging
import re
from typing import Any, Dict, Tuple

from cicada.core import model
from cicada.core.basics import PromptBuilder
from cicada.core.utils import colorstring, cprint

logger = logging.getLogger(__name__)


class FeedbackJudge(model.MultiModalModel):
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
        self.prompt_templates = prompt_templates

    def is_design_goal_achieved(
        self, feedback: str, design_goal: str
    ) -> Tuple[bool, float]:
        """
        Determine if the design goal has been achieved and provide a score based on the Hits.

        :param feedback: The feedback to process.
        :param design_goal: The design goal to compare against.
        :return: A tuple containing a boolean indicating if the goal is achieved and a score between 0 and 1.
        """
        feedback_hits = self._extract_hits(feedback)
        cprint(f"Feedback Hits:\n{feedback_hits}", "magenta")
        # Construct the prompt
        prompt = self.prompt_templates["is_design_goal_achieved"][
            "prompt_template"
        ].format(
            design_goal=design_goal,
            feedback_hits=feedback_hits,
        )

        pb = PromptBuilder()
        pb.add_system_message(
            self.prompt_templates["is_design_goal_achieved"]["system_prompt"]
        )
        pb.add_user_message(prompt)

        # Query the LLM
        response = self.query(prompt_builder=pb, stream=self.stream)["content"]
        logger.info(colorstring(f"Feedback Judge determines that:\n{response}", "cyan"))

        # Parse the Markdown-formatted response
        achieved = (
            self._parse_markdown_response(response, key="Achieved").lower() == "yes"
        )
        score = float(self._parse_markdown_response(response, key="Score"))
        return achieved, score

    def _extract_hits(self, feedback: str) -> str:
        """
        Extract the Hits section from the feedback.

        :param feedback: The feedback to parse.
        :return: The Hits section of the feedback, formatted as a string.
        """

        if feedback:
            hits_match = re.search(
                r"##\s*Hits:\s*([\s\S]+?)(?:##|$)", feedback, re.IGNORECASE
            )
            return hits_match.group(1).strip() if hits_match else ""
        return ""

    def _parse_markdown_response(self, response: str, key: str) -> str:
        """
        Parse a Markdown-formatted response to extract the value for a specific key.
        Strips all Markdown formatting (e.g., **, *, _) from the extracted value.

        :param response: The Markdown-formatted response.
        :param key: The key to extract.
        :return: The value associated with the key, stripped of Markdown formatting.
        """

        match = re.search(rf"{key}:\s*(.*)", response, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            value = re.sub(r"[\\*\\_\\`]", "", value)
            return value
        raise ValueError(f"Key '{key}' not found in response.")


def parse_args() -> Dict[str, Any]:
    """
    Parse command line arguments.

    Returns:
        Dict[str, Any]: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Feedback Judge")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts", help="Path to the prompts YAML file or folder"
    )
    parser.add_argument(
        "--design_goal",
        required=True,
        help="Text description of the design goal or path to a JSON file containing the design goal",
    )
    parser.add_argument(
        "--feedback",
        required=True,
        help="Path to the file containing feedback",
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    from cicada.core.utils import (
        load_config,
        load_prompts,
        parse_design_goal,
        setup_logging,
    )

    args = parse_args()
    setup_logging()

    # Load configuration
    config = load_config(args["config"], "feedback_judge")
    prompt_templates = load_prompts(args["prompts"], "feedback_judge")

    # Initialize FeedbackJudge
    feedback_judge = FeedbackJudge(
        config["api_key"],
        config.get("api_base_url"),
        config.get("model_name", "gpt-4"),
        config.get("org_id"),
        prompt_templates,
        **config.get("model_kwargs", {}),
    )

    # Load design goal
    design_goal = parse_design_goal(args["design_goal"])

    # Load feedback
    with open(args["feedback"], "r") as f:
        feedback = f.read().strip()

    # Evaluate if the design goal is achieved in the feedback
    is_achieved, score = feedback_judge.is_design_goal_achieved(feedback, design_goal)
    print(f"Is design goal achieved? {is_achieved} (Score: {score})")
