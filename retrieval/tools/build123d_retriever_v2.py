import argparse
import json
import logging
import os
import sys
from typing import Dict, List

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_grandparent_dir = os.path.dirname(_parent_dir)
sys.path.extend([_parent_dir, _grandparent_dir])

from coding.code_dochelper import CodeDocHelper
from common import llm
from common.utils import load_config, load_prompts, setup_logging

logger = logging.getLogger(__name__)


class LLMFastFilter(llm.LanguageModel):
    """
    A fast filtering mechanism using a language model to process and filter queries.

    Attributes:
        llm_filter_prompt (str): The prompt template used for filtering.
        cheat_sheet_content (str): Content of the cheat sheet used for reference.
    """

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
        Initialize the LLMFastFilter with necessary configurations.

        Args:
            api_key (str): API key for the language model.
            api_base_url (str): Base URL for the API.
            model_name (str): Name of the model to be used.
            org_id (str): Organization ID for the API.
            prompt_templates (str): Template for the prompt used in filtering.
            **model_kwargs: Additional keyword arguments for the model.
        """
        super().__init__(
            api_key,
            api_base_url,
            model_name,
            org_id,
            **model_kwargs,
        )
        self.llm_filter_prompt = prompt_templates

    def filter(
        self, query: str, k: int = 5, cheat_sheet_content: str = None
    ) -> List[str]:
        """
        Filter the query using the language model and return the top k results.
        Args:
            query (str): The query to be filtered.
            k (int): Number of top results to return.
            cheat_sheet_content (str): Content of the cheat sheet for reference.

        Returns:
            List[str]: List of top k results.
        """
        prompt = self.llm_filter_prompt.format(
            cheat_sheet_content=cheat_sheet_content, query=query, k=k
        )

        try:
            response = self.query(prompt)
            logger.info(f"LLM raw response: {response}")

            result = json.loads(response)
            if not isinstance(result, dict) or "picks" not in result:
                raise ValueError("Invalid response format")

            return result["picks"][:k]

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Response parsing failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"LLM query failed: {str(e)}")
            return []


class Build123dRetriever:
    """
    A retriever class that uses LLMFastFilter to retrieve relevant information.

    Attributes:
        llm_filter (LLMFastFilter): Instance of LLMFastFilter for filtering.
        cheat_sheet_file (str): Path to the cheat sheet file.
        cheat_sheet_content (str): Content of the cheat sheet.
        helper (CodeDocHelper): Helper for code documentation.
    """

    def __init__(self, config: Dict, prompt_templates: Dict):
        """
        Initialize the retriever with LLM fast filter.

        Args:
            config (Dict): Configuration dictionary for the retriever.
            prompt_templates (Dict): Dictionary of prompt templates.
        """
        llm_filter_config = config["llm_filter"]
        llm_filter_prompt_templates = prompt_templates["llm_filter_prompt"]
        self.llm_filter = LLMFastFilter(
            llm_filter_config["api_key"],
            llm_filter_config.get("api_base_url"),
            llm_filter_config.get("model_name", "gpt-4"),
            llm_filter_config.get("org_id"),
            llm_filter_prompt_templates,
            **llm_filter_config.get("model_kwargs", {}),
        )

        self.cheat_sheet_file = config["cheat_sheet_file"]
        self.cheat_sheet_content = self.load_cheat_sheet(self.cheat_sheet_file)

        self.helper = CodeDocHelper()

    def load_cheat_sheet(self, cheat_sheet_file: str) -> str:
        """
        Load the content of the cheat sheet from the specified file.

        Args:
            cheat_sheet_file (str): Path to the cheat sheet file.

        Returns:
            str: Content of the cheat sheet.
        """
        try:
            with open(cheat_sheet_file, "r") as f:
                self.cheat_sheet_content = f.read()
        except FileNotFoundError:
            logger.error(f"Cheat sheet file not found: {cheat_sheet_file}")
            self.cheat_sheet_content = ""

    def query(self, query: str, k: int = 5) -> List[Dict]:
        """
        Query the retriever and return the top k relevant results.

        Args:
            query (str): The query to be processed.
            k (int): Number of top results to return.

        Returns:
            List[Dict]: List of dictionaries containing the retrieved information.
        """
        relevant_names = self.llm_filter.filter(query, k, self.cheat_sheet_content)
        logger.info(f"Preliminary filtering results: {relevant_names}")

        results = []
        for name in relevant_names:
            try:
                full_path = f"build123d.{name}"
                info = self.helper.get_info(full_path, with_docstring=True)
                results.append(info)
                logger.debug(f"Successfully retrieved: {full_path}")
            except Exception as e:
                error_type = type(e).__name__
                logger.warning(
                    f"Document retrieval failed | Name: {name} | Error type: {error_type} | Details: {str(e)}"
                )
                continue

        return results


if __name__ == "__main__":
    setup_logging(log_level="DEBUG")
    parser = argparse.ArgumentParser(description="Assistive Large Language Model")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    parser.add_argument(
        "--prompts", default="prompts.yaml", help="Path to the prompts YAML file"
    )
    parser.add_argument(
        "--output_dir",
        default="./code_examples",
        help="Directory to save the generated code",
    )
    parser.add_argument(
        "query",
        type=str,
        help="Query to search for in the cheat sheet",
    )
    args = parser.parse_args()

    setup_logging()

    os.makedirs(args.output_dir, exist_ok=True)

    retriever_config = load_config(args.config, "build123d_retriever_v2")
    prompt_templates = load_prompts(args.prompts, "build123d_retriever_v2")

    retriever = Build123dRetriever(retriever_config, prompt_templates)

    results = retriever.query(args.query, k=5)
    print(results)
