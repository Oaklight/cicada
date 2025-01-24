import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from typing import Dict, List

from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_grandparent_dir = os.path.dirname(_parent_dir)
sys.path.extend([_parent_dir, _grandparent_dir])

from coding.code_dochelper import CodeDocHelper
from common.rerank import Rerank
from common.utils import load_config, setup_logging
from retrieval.core.basics import Embeddings
from retrieval.core.siliconflow_embeddings import SiliconFlowEmbeddings
from retrieval.core.sqlitevec_store import Document, SQLiteVec

logger = logging.getLogger(__name__)


class Build123dRetriever:
    def __init__(
        self,
        db_file: str = "build123d_vec.db",
        table: str = "build123d_objects",
        embedding_model: Embeddings = None,
        reranking_model: Rerank = None,
        **kwargs,
    ):
        """
        Initialize the Build123dRetriever.

        Args:
            db_file (str): Path to the SQLite database file. Defaults to "build123d_vec.db".
            table (str): Name of the table to store the vectors. Defaults to "build123d_objects".
        """
        self.db_file = db_file
        self.table = table
        self.helper = CodeDocHelper()

        if embedding_model:
            self.embedding_model = embedding_model
        else:
            # check config parameters from kwargs, raise error if missing
            embedding_config = kwargs.get("embedding_config")
            if not embedding_config or not embedding_config.get("api_key"):
                raise ValueError("Missing embedding_config or api_key")
            # Initialize the embedding model
            self.embedding_model = SiliconFlowEmbeddings(
                embedding_config["api_key"],
                embedding_config.get("api_base_url"),
                embedding_config.get("model_name", "text-embedding-3-small"),
                embedding_config.get("org_id"),
                **embedding_config.get("model_kwargs", {}),
            )

        # Initialize the SQLiteVec instance with the embedding model
        self.vector_store = SQLiteVec(
            table=table, db_file=db_file, embedding=self.embedding_model
        )
        self._init_database(force_rebuild=False, batch_size=15)

    def _init_database(
        self, force_rebuild: bool = False, only_names: bool = True, batch_size: int = 16
    ):
        """
        Build initial database records of all the object names inside the build123d module.
        Providing a basic search capability for queryable objects.

        Args:
            force_rebuild (bool): Whether to force rebuild the database. Defaults to False.
            only_names (bool): Whether to only store names and their embeddings. Defaults to True.
        """
        if os.path.exists(self.db_file) and not force_rebuild:
            try:
                if self.vector_store.get_metadata("complete") == "true":
                    print(
                        f"Database already exists at {self.db_file} and is complete. Skipping build."
                    )
                    return
                else:
                    print(
                        f"Database file exists at {self.db_file} but is incomplete. Rebuilding..."
                    )
            except Exception as e:
                print(f"Error checking database completeness: {e}. Rebuilding...")

        module_info_json = self.helper.get_info("build123d", with_docstring=True)
        objects = self.extract_all_objects(module_info_json)

        # Generate embeddings in parallel
        texts, metadatas = self.generate_embedding_pairs(objects, only_names)

        # Batch texts/metadatas into chunks of 16
        text_batches = [
            texts[i : i + batch_size] for i in range(0, len(texts), batch_size)
        ]
        metadata_batches = [
            metadatas[i : i + batch_size] for i in range(0, len(metadatas), batch_size)
        ]

        # Add batches sequentially in main thread
        with tqdm(total=len(texts), desc="Building database", unit="object") as pbar:
            for batch_texts, batch_metadatas in zip(text_batches, metadata_batches):
                self.vector_store.add_texts(batch_texts, batch_metadatas)
                pbar.update(len(batch_texts))  # Update progress by batch size

        # Mark the database as complete
        self.vector_store.set_metadata("complete", "true")
        print(f"Database built with {len(objects)} objects.")

    def extract_all_objects(self, module_info_json: Dict) -> List[Dict]:
        """Extract objects with type categorization from raw JSON."""
        objects = []

        # Add type field directly to raw JSON entries
        for cls in module_info_json.get("classes", []):
            cls["type"] = "class"
            objects.append(cls)

        for func in module_info_json.get("functions", []):
            func["type"] = "function"
            objects.append(func)

        for var in module_info_json.get("variables", []):
            var["type"] = "variable"
            objects.append(var)

        return objects

    @staticmethod
    def _process_object(obj: Dict, only_names: bool) -> tuple[str, dict]:
        """Modified as static method with explicit parameter passing"""
        if only_names:
            text = obj["name"]
            metadata = {"type": obj["type"], "name": obj["name"]}
        else:
            text = f"{obj['type']}: {obj['name']}\n{obj.get('docstring', '')}"
            metadata = {
                "type": obj["type"],
                "name": obj["name"],
                **{k: v for k, v in obj.items() if k not in ["type", "name"]},
            }
        return text, metadata

    def generate_embedding_pairs(self, objects: List[Dict], only_names: bool = True):
        texts = []
        metadatas = []
        processor = partial(self._process_object, only_names=only_names)

        # Process objects sequentially
        for obj in tqdm(objects, desc="Generating embeddings", unit="object"):
            text, metadata = processor(obj)
            texts.append(text)
            metadatas.append(metadata)

        return texts, metadatas

    def query(self, query_text: str, k: int = 5) -> List[Dict]:
        """
        Query the database with a sentence or description in parallel.

        Args:
            query_text (str): The query text.
            k (int): The number of results to return. Defaults to 5.

        Returns:
            List[Dict]: A list of metadata dictionaries for the most relevant objects.
        """
        query_embedding = self.embedding_model.embed_query(query_text)
        results, scores = self.vector_store.similarity_search_by_vector(
            query_embedding, k
        )
        logger.debug(f"Query results: {results}")
        return [doc.metadata for doc in results], scores

    def get_complete_info(
        self, query_text: str, k: int = 5, with_docstring: bool = False
    ) -> List[Dict]:
        """
        Get complete information about the queried objects in parallel.

        Args:
            query_text (str): The query text.
            k (int): The number of results to return. Defaults to 5.

        Returns:
            List[Dict]: A list of dictionaries containing complete information about the objects.
        """
        results, scores = self.query(query_text, k)
        complete_info = []

        # Function to fetch complete info for a single result
        def fetch_info(result: Dict) -> Dict:
            if result["type"] == "class":
                return self.helper.get_class_info(
                    result["name"], with_docstring=with_docstring
                )
            elif result["type"] == "function":
                return self.helper.get_function_info(
                    result["name"], with_docstring=with_docstring
                )
            elif result["type"] == "variable":
                return {
                    "name": result["name"],
                    "type": result["type_info"],
                    "value": result["value"],
                }

        # Use ThreadPoolExecutor to fetch info in parallel
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_info, result) for result in results]
            for future in as_completed(futures):
                complete_info.append(future.result())

        return complete_info


# Example usage
if __name__ == "__main__":
    setup_logging()
    parser = argparse.ArgumentParser(description="Build123d Retriever")
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild the database",
    )
    args = parser.parse_args()

    retriever_config = load_config("config.yaml", "build123d_retriever")

    # # Initialize SiliconFlowEmbeddings
    # embedding_model = SiliconFlowEmbeddings(
    #     retriever_config["api_key"],
    #     retriever_config.get("api_base_url"),
    #     retriever_config.get("model_name", "text-embedding-3-small"),
    #     retriever_config.get("org_id"),
    #     **retriever_config.get("model_kwargs", {}),
    # )

    retriever = Build123dRetriever(
        db_file=retriever_config["db_file"],
        table=retriever_config["table"],
        embedding_config=retriever_config["embedding_config"],
    )

    # Build the database only if it doesn't exist or if forced
    retriever._init_database(
        force_rebuild=False, only_names=True
    )  # Set force_rebuild=True to rebuild

    # Query the database
    query_text = "How to create a box in build123d?"
    results = retriever.get_complete_info(query_text)
    for result in results:
        print(result)
