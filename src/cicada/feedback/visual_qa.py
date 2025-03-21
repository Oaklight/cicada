import logging
from typing import List

from cicada.core import model
from cicada.core.basics import PromptBuilder
from cicada.core.utils import get_image_paths, image_to_base64

logger = logging.getLogger(__name__)


def load_images(path: str) -> List[str]:
    """
    Load images from a folder and convert them to base64.

    Args:
        path (str): Path to the folder containing images.

    Returns:
        List[bytes]: List of images in base64 format.
    """
    if path:
        return [image_to_base64(img) for img in get_image_paths(path)]
    else:
        return []


class VisualQA(model.MultiModalModel):
    def __init__(
        self,
        api_key,
        api_base_url,
        model_name,
        org_id,
        prompt_templates,
        **model_kwargs,
    ):
        """
        Initialize the VisualQA model.
        Args:
            api_key (str): API key for the model.
            api_base_url (str): Base URL for the API.
            model_name (str): Name of the model.
            org_id (str): Organization ID.
            prompt_templates (dict): Dictionary of prompt templates.
            **model_kwargs: Additional keyword arguments for the model.
        """
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.visual_qa_prompts = prompt_templates

    def generate_questions(
        self,
        design_goal: str,
        reference_images: List[str] | None,
        num_questions: int = 5,
    ) -> List[str]:
        """
        Generate questions based on the design goal and images.
        Args:
            design_goal (str): Text description of the design goal.
            reference_images (List[str]): List of reference images paths.
            num_questions (int): Number of questions to generate.

        Returns:
            List[str]: List of generated questions.
        """
        prompt = self.visual_qa_prompts["question_generation"][
            "prompt_template"
        ].format(design_goal=design_goal, num_questions=num_questions)

        pb = PromptBuilder()
        pb.add_system_message(
            self.visual_qa_prompts["question_generation"]["system_prompt"]
        )
        pb.add_user_message(prompt)
        if reference_images:
            pb.add_text("The following is a set of reference images:")
            pb.add_images(reference_images)

        response = self.query(prompt_builder=pb, stream=self.stream)["content"]

        questions = [q.strip() for q in response.split("\n") if q.strip()]
        return questions

    def generate_answers(
        self,
        design_goal: str,
        questions: List[str],
        reference_images: List[str] | None,
        rendered_images: List[str],
    ) -> dict:
        """
        Generate answers to the provided questions based on the design goal and images.

        Args:
            design_goal (str): Text description of the design goal.
            questions (List[str]): List of questions to answer.
            reference_images (List[str]): List of reference images in str.
            rendered_images (List[str]): List of rendered images in str.

        Returns:
            dict: Dictionary of questions and their corresponding answers.
        """
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

        prompt = self.visual_qa_prompts["answer_generation"]["prompt_template"].format(
            design_goal=design_goal, questions=questions_text
        )

        # construct using PromptBuilder
        pb = PromptBuilder()
        pb.add_system_message(
            self.visual_qa_prompts["answer_generation"]["system_prompt"]
        )
        pb.add_user_message(prompt)  # Add the formatted prompt to the PromptBuilder
        if reference_images:
            pb.add_text("The followings are reference images of design goal:")
            pb.add_images(reference_images)
        pb.add_text("The following is a set of rendered object images:")
        pb.add_images(rendered_images)

        response = self.query(prompt_builder=pb, stream=self.stream)["content"]

        return response

    def automated_qa(
        self,
        design_goal: str,
        reference_images: List[str] | None,
        rendered_images: List[str],
        num_questions: int = 5,
    ) -> dict:
        """
        Generate questions and then generate answers to those questions.

        Args:
            design_goal (str): Text description of the design goal.
            reference_images (List[str]): List of reference images in str.
            rendered_images (List[str]): List of rendered images in str.
            num_questions (int): Number of questions to generate.

        Returns:
            dict: Dictionary containing the generated questions and answers.
        """
        questions = self.generate_questions(
            design_goal=design_goal,
            reference_images=reference_images,
            num_questions=num_questions,
        )
        answers = self.generate_answers(
            design_goal, questions, reference_images, rendered_images
        )
        return {"questions": questions, "answers": answers}


if __name__ == "__main__":
    import argparse
    import json

    from cicada.core.utils import (
        colorstring,
        cprint,
        get_image_paths,
        image_to_base64,
        load_config,
        load_prompts,
        parse_design_goal,
        setup_logging,
    )

    setup_logging()

    parser = argparse.ArgumentParser(description="Visual QA Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts", help="Path to the prompts YAML file or folder"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["question_generation", "answer_generation", "automated_qa"],
        help="Operating mode: question_generation, answer_generation, or automated_qa",
    )
    parser.add_argument(
        "--design_goal",
        help="Text description of the design goal or path to a JSON file containing the design goal",
    )
    parser.add_argument("--questions", nargs="+", help="List of questions to answer")
    parser.add_argument(
        "--reference_images", help="Path to the folder containing reference images"
    )
    parser.add_argument(
        "--rendered_images", help="Path to the folder containing rendered object images"
    )
    parser.add_argument(
        "--num_questions", type=int, default=5, help="Number of questions to generate"
    )
    args = vars(parser.parse_args())

    config = load_config(args["config"], "visual_qa")
    prompt_templates = load_prompts(args["prompts"], "visual_qa")

    visual_qa = VisualQA(
        config["api_key"],
        config.get("api_base_url"),
        config.get("model_name", "gpt-4"),
        config.get("org_id"),
        prompt_templates,
        **config.get("model_kwargs", {}),
    )

    if args["mode"] == "question_generation":
        if not args["design_goal"]:
            raise ValueError("Design goal is required for question generation.")
        design_goal = parse_design_goal(args["design_goal"])
        questions = visual_qa.generate_questions(
            design_goal=design_goal,
            reference_images=args["reference_images"],
            num_questions=args["num_questions"],
        )
        cprint(json.dumps(questions, indent=4), "cyan")

    elif args["mode"] == "answer_generation":
        if not args["questions"]:
            raise ValueError("Questions are required for answer generation.")
        questions = args["questions"]
        design_goal = (
            parse_design_goal(args["design_goal"]) if args["design_goal"] else ""
        )
        answers = visual_qa.generate_answers(
            design_goal=design_goal,
            questions=questions,
            reference_images=args["reference_images"],
            rendered_images=args["rendered_images"],
        )
        cprint(json.dumps(answers, indent=4), "cyan")

    elif args["mode"] == "automated_qa":
        if not args["design_goal"]:
            raise ValueError("Design goal is required for automated QA.")
        design_goal = parse_design_goal(args["design_goal"])
        qa_result = visual_qa.automated_qa(
            design_goal=design_goal,
            reference_images=args["reference_images"],
            rendered_images=args["rendered_images"],
            num_questions=args["num_questions"],
        )
        cprint(json.dumps(qa_result, indent=4), "cyan")

    else:
        raise ValueError("Invalid mode selected.")
