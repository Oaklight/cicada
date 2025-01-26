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

logger = logging.getLogger(__name__)


class LLMFastFilter(llm.LanguageModel):
    def __init__(self, summary_file: str = "summary.json", *args, **kwargs):
        """
        Initialize the LLM fast filter.

        Args:
            summary_file: Path to the summary JSON file.
            *args, **kwargs: Arguments passed to the parent LanguageModel class.
        """
        super().__init__(*args, **kwargs)
        self.summary_file = summary_file
        self._load_summary()

    def _load_summary(self):
        """Load the summary of classes, methods, and variables."""
        try:
            with open(self.summary_file, "r") as f:
                self.summary = json.load(f)
        except FileNotFoundError:
            logger.error(f"Summary file not found: {self.summary_file}")
            self.summary = {"classes": [], "methods": [], "variables": []}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in summary file: {self.summary_file}")
            self.summary = {"classes": [], "methods": [], "variables": []}

    def filter(self, query: str, k: int = 5) -> List[str]:
        """
        Use LLM to filter the most relevant names from the summary.

        Args:
            query: User query.
            k: Number of results to return.

        Returns:
            List of relevant names.
        """
        # Prepare prompt
        prompt = f"""
        You are a code search assistant. Below is a summary of classes, methods, and variables:

        {json.dumps(self.summary, indent=2)}

        Based on the user query: "{query}", select the top {k} most relevant names.
        Return ONLY a JSON list of names, like this:
        ["name1", "name2", ...]
        """

        # Call LLM
        try:
            response = self.query(prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return []
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return []


class Build123dRetriever:
    def __init__(self, llm_filter: LLMFastFilter, db_file: str = "build123d.db"):
        """
        Initialize the retriever with LLM fast filter.

        Args:
            llm_filter: LLMFastFilter instance.
            db_file: Path to the SQLite database.
        """
        self.llm_filter = llm_filter
        self.db_file = db_file
        self.helper = CodeDocHelper()

    def query(self, query: str, k: int = 5) -> List[Dict]:
        """
        Query the database using LLM fast filter.

        Args:
            query: User query.
            k: Number of results to return.

        Returns:
            List of detailed results.
        """
        # Step 1: Use LLM to filter relevant names
        relevant_names = self.llm_filter.filter(query, k=k)
        if not relevant_names:
            return []

        # Step 2: Retrieve detailed information for each name
        results = []
        for name in relevant_names:
            try:
                info = self.helper.get_info(name, with_docstring=True)
                results.append(info)
            except Exception as e:
                logger.error(f"Failed to retrieve info for {name}: {e}")

        return results
