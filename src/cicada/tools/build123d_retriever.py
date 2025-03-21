import logging
import os
from concurrent.futures import as_completed, ThreadPoolExecutor
from functools import partial
from typing import Dict, List, Literal

from cicada.core.rerank import Rerank
from cicada.core.utils import colorstring
from cicada.retrieval.basics import Embeddings
from cicada.retrieval.siliconflow_embeddings import SiliconFlowEmbeddings
from cicada.retrieval.siliconflow_rerank import SiliconFlowRerank
from cicada.retrieval.sqlitevec_store import Document, SQLiteVec

from cicada.tools.code_dochelper import CodeDocHelper

from tqdm import tqdm


logger = logging.getLogger(__name__)


class Build123dRetriever:
    def __init__(
        self,
        db_file: str = "build123d_vec.db",
        table: str = "build123d_objects",
        embedding_model: Embeddings = None,
        reranking_model: Rerank = None,
        embedding_config: Dict = None,
        rerank_config: Dict = None,
        k: int = 10,
        k_rerank: int = 10,
    ):
        """
        Initialize the Build123dRetriever.

        Args:
            db_file (str): Path to the SQLite database file. Defaults to "build123d_vec.db".
            table (str): Name of the table to store the vectors. Defaults to "build123d_objects".
            embedding_model (Embeddings): Pre-initialized embedding model. Defaults to None.
            reranking_model (Rerank): Pre-initialized reranking model. Defaults to None.
            embedding_config (Dict): Configuration for the embedding model. Defaults to None.
            rerank_config (Dict): Configuration for the reranking model. Defaults to None.
        """
        self.db_file = db_file
        self.table = table
        self.helper = CodeDocHelper()
        self.default_k = k
        self.default_k_rerank = k_rerank

        if embedding_model:
            self.embedding_model = embedding_model
        else:
            # check config parameters from kwargs, raise error if missing
            if not embedding_config and not embedding_config.get("api_key"):
                raise ValueError("Missing embedding_config or api_key")
            # Initialize the embedding model
            self.embedding_model = SiliconFlowEmbeddings(
                embedding_config["api_key"],
                embedding_config.get("api_base_url"),
                embedding_config.get("model_name"),
                embedding_config.get("org_id"),
                **embedding_config.get("model_kwargs", {}),
            )
        if reranking_model:
            self.rerank_model = reranking_model
        else:
            if not rerank_config and not rerank_config.get("api_key"):
                raise ValueError("Missing rerank_config or api_key")
            self.rerank_model = SiliconFlowRerank(
                rerank_config["api_key"],
                rerank_config.get("api_base_url"),
                rerank_config.get("model_name"),
                **rerank_config.get("model_kwargs", {}),
            )

        # Initialize the SQLiteVec instance with the embedding model
        self.vector_store = SQLiteVec(
            table=table, db_file=db_file, embedding=self.embedding_model
        )
        self._init_database(force_rebuild=False, batch_size=100, embed_batch_size=32)

    def _init_database(
        self,
        force_rebuild: bool = False,
        only_names: bool = False,
        batch_size: int = 500,
        embed_batch_size: int = 40,
    ):
        """
        Build initial database records of all the object names inside the build123d module.
        Providing a basic search capability for queryable objects.

        Args:
            force_rebuild (bool): Whether to force rebuild the database. Defaults to False.
            only_names (bool): Whether to only store names and their embeddings. Defaults to True.
            batch_size (int): The size of batches for writing to the database. Defaults to 16.
            embed_batch_size (int): The size of batches for embedding computation. Defaults to 100.
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
        else:
            # Force rebuild: Drop the existing table and start fresh
            print(f"Force rebuilding database at {self.db_file}...")
            self.vector_store.drop_table()  # Drop the existing table
            self.vector_store.create_table()  # Recreate the table

        module_info_json = self.helper.get_info("build123d", with_docstring=True)
        objects = self.extract_all_objects(module_info_json)

        # Generate texts and metadatas
        texts, metadatas = self.generate_embedding_pairs(objects, only_names)

        # Compute embeddings in parallel using a thread pool
        embeddings = []
        with tqdm(total=len(texts), desc="Computing embeddings", unit="object") as pbar:
            with ThreadPoolExecutor() as executor:
                # Submit tasks to the thread pool
                futures = [
                    executor.submit(
                        self.embedding_model.embed_documents,
                        texts[i : i + embed_batch_size],
                    )
                    for i in range(0, len(texts), embed_batch_size)
                ]

                # Collect results as they complete
                for future in as_completed(futures):
                    batch_embeddings = future.result()
                    embeddings.extend(batch_embeddings)
                    pbar.update(len(batch_embeddings))  # Update progress by batch size

        # Batch texts/metadatas/embeddings into chunks of batch_size
        text_batches = [
            texts[i : i + batch_size] for i in range(0, len(texts), batch_size)
        ]
        metadata_batches = [
            metadatas[i : i + batch_size] for i in range(0, len(metadatas), batch_size)
        ]
        embedding_batches = [
            embeddings[i : i + batch_size]
            for i in range(0, len(embeddings), batch_size)
        ]

        # Add batches sequentially in main thread
        with tqdm(total=len(texts), desc="Building database", unit="object") as pbar:
            for batch_texts, batch_metadatas, batch_embeddings in zip(
                text_batches, metadata_batches, embedding_batches
            ):
                self.vector_store.add_texts_with_embeddings(
                    batch_texts, batch_embeddings, batch_metadatas
                )
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

            # Extract methods from the class and treat them as standalone functions
            for method in cls.get("methods", []):
                method_info = {
                    "name": f"{method['name']}",  # this name has been expanded at function_info level
                    "type": "method",
                    "signature": method["signature"],
                    "docstring": method.get("docstring", ""),
                }
                objects.append(method_info)

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

    def query(
        self,
        query_text: str,
        k: int = 10,
        k_rerank: int = 10,
        distance_metric: Literal["l2", "cosine"] = "cosine",
    ) -> List[Dict]:
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
            query_embedding, k=k, distance_metric=distance_metric
        )

        logger.debug(colorstring(f"Initial results: {results}", "blue"))
        logger.debug(colorstring(f"Initial scores: {scores}", "blue"))

        reranked_results = self.rerank_model.rerank(query_text, results, k_rerank // 2)
        # [{'index': 0, 'relevance_score': 0.455078125, 'document': {'text': '苹果'}}, {'index': 2, 'relevance_score': 0.33984375, 'document': {'text': '水果'}}, {'index': 1, 'relevance_score': 0.25, 'document': {'text': 'banana'}}, {'index': 4, 'relevance_score': 0.189453125, 'document': {'text': 'manzana'}}]
        logger.debug(
            colorstring(f"Reranked results: {reranked_results}", "bright_green")
        )
        # get rerank order by sequencing `index`
        rerank_order = [int(r["index"]) for r in reranked_results]
        rerank_score = [float(r["relevance_score"]) for r in reranked_results]
        results = [results[i] for i in rerank_order]
        scores = rerank_score

        logger.debug(f"Query results: {results}")
        return [doc.metadata for doc in results], scores

    def get_complete_info(
        self,
        query_text: str,
        k: int = None,
        k_rerank: int = None,
        with_docstring: bool = False,
        threshold: float = 0.8,
        distance_metrics: Literal["l2", "cosine"] = "cosine",
    ) -> List[Dict]:
        """
        Get complete information about the queried objects in parallel.

        Args:
            query_text (str): The query text.
            k (int): The number of results to return. Defaults to 5.

        Returns:
            List[Dict]: A list of dictionaries containing complete information about the objects.
        """
        k = k if k else self.default_k
        k_rerank = k_rerank if k_rerank else self.default_k_rerank

        reranked_results, reranked_scores = self.query(
            query_text,
            k=k,
            k_rerank=k_rerank,
            distance_metric=distance_metrics,
        )
        for result, score in zip(reranked_results, reranked_scores):
            logger.debug(
                colorstring(f"Result: {result}, Score: {score}", "bright_yellow")
            )  # Log each result and its score

        if threshold:
            complete_info_with_score = [
                (
                    self.helper.get_info(result["name"], with_docstring=with_docstring),
                    score,
                )
                for result, score in zip(reranked_results, reranked_scores)
                if score >= threshold
            ]
        else:
            complete_info_with_score = [
                (
                    self.helper.get_info(result["name"], with_docstring=with_docstring),
                    score,
                )
                for result, score in zip(reranked_results, reranked_scores)
            ]
        return complete_info_with_score


if __name__ == "__main__":

    import argparse

    from cicada.core.utils import cprint, load_config, setup_logging

    parser = argparse.ArgumentParser(description="Build123d Retriever")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Force rebuild the database",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode to ask multiple questions",
    )
    parser.add_argument(
        "--metric",
        type=str,
        choices=["l2", "cosine"],
        default="cosine",
        help="Distance metric to use for similarity search",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query text to search in the database",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode for detailed logging",
    )
    args = parser.parse_args()

    if args.debug:
        setup_logging(log_level="DEBUG")
    else:
        setup_logging(log_level="INFO")

    retriever_config = load_config(args.config, "build123d_retriever")

    retriever = Build123dRetriever(
        db_file=retriever_config.get("db_file", "build123d_retriever.db"),
        table=retriever_config.get("table", "build123d_objects"),
        embedding_config=retriever_config.get("embedding_config", {}),
        rerank_config=retriever_config.get("rerank_config", {}),
        k=retriever_config.get("k", 10),
        k_rerank=retriever_config.get("k_rerank", 10),
    )

    # Build the database only if it doesn't exist or if forced
    retriever._init_database(
        force_rebuild=args.force_rebuild, only_names=True
    )  # Set force_rebuild=True to rebuild

    if args.interactive:
        # Interactive mode: keep asking for queries until the user exits
        while True:
            query_text = input("\nEnter your query (or type 'q' to quit): ").strip()
            if query_text.lower() in ["exit", "quit", "q"]:
                cprint("Exiting interactive mode. Goodbye!", "bright_green")
                break

            if not query_text:
                cprint("Please enter a valid query.", "bright_red")
                continue

            # Query the database
            results = retriever.get_complete_info(
                query_text,
                k=100,
                with_docstring=True,
                threshold=0.1,
                distance_metrics=args.metric,
            )
            if not results:
                cprint("No results found.", "bright_red")
            else:
                for result, score in results:
                    cprint(f"Score: {score}", "bright_yellow")
                    print(result)
    else:
        # Non-interactive mode: run a single query
        query_text = "How to create a box in build123d?"
        results = retriever.get_complete_info(
            query_text,
            k=100,
            with_docstring=True,
            threshold=0.1,
            distance_metrics=args.metric,
        )
        for result, score in results:
            cprint(f"Score: {score}", "bright_yellow")
            print(result)
