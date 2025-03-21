import json
import logging
import sqlite3
import struct
from typing import Dict, List, Optional, Tuple

from cicada.core.utils import colorstring
from cicada.retrieval.basics import Document, Embeddings, VectorStore

logger = logging.getLogger(__name__)


class SQLiteVec(VectorStore):
    """SQLite with Vec extension as a vector database."""

    def __init__(
        self,
        table: str,
        db_file: str = "vec.db",
        pool_size: int = 5,
        embedding: Optional[Embeddings] = None,
    ):
        """Initialize the SQLiteVec instance.

        Args:
            table (str): The name of the table to store the vectors.
            db_file (str, optional): The path to the SQLite database file. Defaults to "vec.db".
            pool_size (int, optional): The size of the connection pool. Defaults to 5.
            embedding (Embeddings, optional): The embedding model to use. Defaults to None.
        """
        self._db_file = db_file
        self._table = table
        self._embedding = embedding
        self._pool = self._create_connection_pool(pool_size)
        self.create_table_if_not_exists()
        self.create_metadata_table()

    def drop_table(self):
        """Drop the main table and the virtual table if they exist."""
        connection = self._get_connection()
        try:
            # Drop the main table
            connection.execute(f"DROP TABLE IF EXISTS {self._table}")
            # Drop the virtual table
            connection.execute(f"DROP TABLE IF EXISTS {self._table}_vec")
            connection.commit()
            logger.info(
                colorstring(
                    f"Dropped tables: {self._table} and {self._table}_vec", "red"
                )
            )
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to drop tables: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def create_table(self):
        """Create the main table and the virtual table."""
        connection = self._get_connection()
        try:
            # Create the main table
            connection.execute(
                f"""
                CREATE TABLE {self._table} (
                    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    metadata BLOB,
                    text_embedding BLOB
                );
            """
            )
            # Create the virtual table
            connection.execute(
                f"""
                CREATE VIRTUAL TABLE {self._table}_vec USING vec0(
                    rowid INTEGER PRIMARY KEY,
                    text_embedding float[{self.get_dimensionality()}]
                );
            """
            )
            connection.commit()
            logger.info(
                colorstring(
                    f"Created tables: {self._table} and {self._table}_vec", "green"
                )
            )
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to create tables: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def _create_connection_pool(self, pool_size: int) -> List[sqlite3.Connection]:
        """Create a connection pool for SQLite.

        Args:
            pool_size (int): The size of the connection pool.

        Returns:
            List[sqlite3.Connection]: A list of SQLite connections.
        """
        pool = []
        for _ in range(pool_size):
            connection = self._create_connection()
            pool.append(connection)
        logger.info(
            colorstring(
                f"Created SQLite connection pool with {pool_size} connections", "green"
            )
        )
        return pool

    def _get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool.

        Returns:
            sqlite3.Connection: A SQLite connection.
        """
        if not self._pool:
            logger.warning(
                colorstring(
                    "Connection pool is empty. Creating a new connection.", "yellow"
                )
            )
            return self._create_connection()
        return self._pool.pop()

    def _release_connection(self, connection: sqlite3.Connection):
        """Release a connection back to the pool.

        Args:
            connection (sqlite3.Connection): The SQLite connection to release.
        """
        self._pool.append(connection)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a single SQLite connection.

        Returns:
            sqlite3.Connection: A SQLite connection.

        Raises:
            ImportError: If the sqlite_vec extension is not installed.
            sqlite3.Error: If the connection to the database fails.
        """
        try:
            import sqlite_vec

            connection = sqlite3.connect(self._db_file)
            connection.row_factory = sqlite3.Row
            connection.enable_load_extension(True)
            sqlite_vec.load(connection)
            connection.enable_load_extension(False)
            logger.info(
                colorstring(
                    f"Successfully connected to SQLite database: {self._db_file}",
                    "green",
                )
            )
            return connection
        except ImportError as e:
            logger.error(
                colorstring(
                    "Failed to load sqlite_vec extension. Please ensure it is installed.",
                    "red",
                )
            )
            raise e
        except sqlite3.Error as e:
            logger.error(
                colorstring(f"Failed to connect to SQLite database: {e}", "red")
            )
            raise e

    def create_table_if_not_exists(self):
        """Create tables if they don't exist.

        Raises:
            sqlite3.Error: If the table creation fails.
        """
        connection = self._get_connection()
        try:
            # Check if the main table exists
            cursor = connection.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self._table}'"
            )
            main_table_exists = cursor.fetchone() is not None

            # Check if the virtual table exists
            cursor = connection.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self._table}_vec'"
            )
            virtual_table_exists = cursor.fetchone() is not None

            # If either table does not exist, create both tables
            if not main_table_exists or not virtual_table_exists:
                self.create_table()
                logger.info(
                    colorstring(
                        f"Tables created: {self._table}, {self._table}_vec",
                        "green",
                    )
                )
            else:
                logger.info(
                    colorstring(
                        f"Tables already exist: {self._table}, {self._table}_vec",
                        "blue",
                    )
                )
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to check or create tables: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def create_metadata_table(self):
        """Create metadata table if not exists"""
        connection = self._get_connection()
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)"
            )
            connection.commit()
        finally:
            self._release_connection(connection)

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value by key.
        Args:
            key (str): The key to retrieve the metadata value for.
        Returns:
            Optional[str]: The metadata value if found, otherwise None.
        """
        connection = self._get_connection()
        try:
            cursor = connection.execute(
                "SELECT value FROM metadata WHERE key = ?", (key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            self._release_connection(connection)

    def set_metadata(self, key: str, value: str):
        """Set metadata key-value pair.
        Args:
            key (str): The key to set.
            value (str): The value to associate with the key.
        """
        connection = self._get_connection()
        try:
            connection.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                (key, value),
            )
            connection.commit()
        finally:
            self._release_connection(connection)

    def delete_by_ids(self, ids: List[str]):
        """Delete documents by their row IDs."""
        connection = self._get_connection()
        try:
            placeholders = ",".join("?" for _ in ids)
            # Delete from main table
            connection.execute(
                f"DELETE FROM {self._table} WHERE rowid IN ({placeholders})", ids
            )
            # Delete from virtual table
            connection.execute(
                f"DELETE FROM {self._table}_vec WHERE rowid IN ({placeholders})", ids
            )
            connection.commit()
            logger.info(colorstring(f"Deleted {len(ids)} documents", "blue"))
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to delete documents: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def add_texts(
        self, texts: List[str], metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """Add texts to the vector store.
        Args:
            texts (List[str]): The list of texts to add.
            metadatas (Optional[List[Dict]], optional): The list of metadata dictionaries. Defaults to None.

        Returns:
            List[str]: The list of row IDs for the added texts.

        Raises:
            sqlite3.Error: If the addition of texts fails.
        """
        connection = self._get_connection()
        try:
            embeds = self._embedding.embed_documents(texts)
            metadatas = metadatas or [{} for _ in texts]
            data_input = [
                (text, json.dumps(metadata), self.serialize_f32(embed))
                for text, metadata, embed in zip(texts, metadatas, embeds)
            ]

            # Insert into the main table and get the rowids
            rowids = []
            for text, metadata, embed in zip(texts, metadatas, embeds):
                cursor = connection.execute(
                    f"INSERT INTO {self._table}(text, metadata, text_embedding) VALUES (?, ?, ?)",
                    (text, json.dumps(metadata), self.serialize_f32(embed)),
                )
                rowid = cursor.lastrowid  # Get the rowid of the inserted row
                rowids.append(rowid)

                # Insert into the virtual table
                connection.execute(
                    f"INSERT INTO {self._table}_vec(rowid, text_embedding) VALUES (?, ?)",
                    (rowid, self.serialize_f32(embed)),
                )

            connection.commit()
            logger.info(
                colorstring(f"Added {len(texts)} texts to the vector store", "blue")
            )
            return [str(rowid) for rowid in rowids]
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to add texts: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def add_texts_with_embeddings(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
    ) -> List[str]:
        """Add texts with precomputed embeddings to the vector store.

        Args:
            texts (List[str]): The list of texts to add.
            embeddings (List[List[float]]): The list of precomputed embeddings.
            metadatas (Optional[List[Dict]], optional): The list of metadata dictionaries. Defaults to None.

        Returns:
            List[str]: The list of row IDs for the added texts.

        Raises:
            sqlite3.Error: If the addition of texts fails.
        """
        if len(texts) != len(embeddings):
            raise ValueError("The number of texts and embeddings must be the same.")

        connection = self._get_connection()
        try:
            metadatas = metadatas or [{} for _ in texts]
            rowids = []

            # Insert into the main table and get the rowids
            for text, metadata, embed in zip(texts, metadatas, embeddings):
                cursor = connection.execute(
                    f"INSERT INTO {self._table}(text, metadata, text_embedding) VALUES (?, ?, ?)",
                    (text, json.dumps(metadata), self.serialize_f32(embed)),
                )
                rowid = cursor.lastrowid  # Get the rowid of the inserted row
                rowids.append(rowid)

                # Insert into the virtual table
                connection.execute(
                    f"INSERT INTO {self._table}_vec(rowid, text_embedding) VALUES (?, ?)",
                    (rowid, self.serialize_f32(embed)),
                )

            connection.commit()
            logger.info(
                colorstring(f"Added {len(texts)} texts to the vector store", "blue")
            )
            return [str(rowid) for rowid in rowids]
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to add texts: {e}", "red"))
            raise e
        finally:
            self._release_connection(connection)

    def similarity_search(
        self, query: str, k: int = 4
    ) -> Tuple[List[Document], List[float]]:
        """Perform a similarity search.

        Args:
            query (str): The query string.
            k (int, optional): The number of results to return. Defaults to 4.

        Returns:
            Tuple[List[Document], List[float]]: A tuple containing the list of documents that match the query and their corresponding similarity scores.

        Raises:
            Exception: If the similarity search fails.
        """
        try:
            embedding = self._embedding.embed_query(query)
            logger.info(
                colorstring(f"Performing similarity search for query: {query}", "cyan")
            )
            return self.similarity_search_by_vector(embedding, k)
        except Exception as e:
            logger.error(
                colorstring(f"Failed to perform similarity search: {e}", "red")
            )
            raise e

    def similarity_search_by_vector(
        self, embedding: List[float], k: int = 4, distance_metric: str = "cosine"
    ) -> Tuple[List[Document], List[float]]:
        """Perform a similarity search by vector with configurable distance metrics.

        Args:
            embedding (List[float]): The embedding vector to search with.
            k (int, optional): The number of results to return. Defaults to 4.
            distance_metric (str, optional): Distance metric to use.
                Supported: 'l2' (Euclidean), 'cosine'. Defaults to "l2". see https://alexgarcia.xyz/sqlite-vec/api-reference.html#distance for more details.

        Returns:
            Tuple[List[Document], List[float]]: Documents and similarity scores.
        """
        # Validate distance metric
        if distance_metric not in ["l2", "cosine"]:
            raise ValueError(
                f"Unsupported distance metric: {distance_metric}. Use 'l2' or 'cosine'."
            )

        # Normalization check (same for both implementations)
        if distance_metric == "cosine":
            l2_norm = sum(x**2 for x in embedding) ** 0.5
            if not (0.99 < l2_norm < 1.01):
                distance_metric = "l2"
                logger.warning(
                    colorstring("Non-unit vector - using L2 distance", "yellow")
                )

        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            # Use SQLiteVec's built-in distance functions
            match distance_metric:
                case "l2":
                    distance_function = "vec_distance_l2"
                case "cosine":
                    distance_function = "vec_distance_cosine"
                case _:
                    raise ValueError("Invalid distance metric. Use 'l2', or 'cosine'.")

            cursor.execute(
                f"""
                SELECT text, metadata, {distance_function}(v.text_embedding, ?) AS distance
                FROM {self._table} AS e
                INNER JOIN {self._table}_vec AS v ON v.rowid = e.rowid
                WHERE v.text_embedding MATCH ? AND k = ?
                ORDER BY distance
                LIMIT ?
                """,
                [
                    self.serialize_f32(embedding),  # For distance calculation
                    self.serialize_f32(embedding),  # For MATCH operator
                    k,  # For MATCH operator
                    k,  # For LIMIT
                ],
            )
            results = []
            scores = []
            for row in cursor.fetchall():
                document = Document(
                    page_content=row["text"], metadata=json.loads(row["metadata"])
                )
                results.append(document)
                scores.append(row["distance"])
            logger.info(
                colorstring(
                    f"Found {len(results)} results using {distance_metric} metric",
                    "cyan",
                )
            )
            return results, scores
        except sqlite3.Error as e:
            logger.error(
                colorstring(f"Similarity search failed ({distance_metric}): {e}", "red")
            )
            raise e
        finally:
            self._release_connection(connection)

    @staticmethod
    def serialize_f32(vector: List[float]) -> bytes:
        """Serialize a list of floats into bytes.

        Args:
            vector (List[float]): The list of floats to serialize.

        Returns:
            bytes: The serialized bytes.
        """
        return struct.pack(f"{len(vector)}f", *vector)

    def get_dimensionality(self) -> int:
        """Get the dimensionality of the embeddings.

        Returns:
            int: The dimensionality of the embeddings.
        """
        return len(self._embedding.embed_query("dummy text"))


if __name__ == "__main__":

    """Test the SQLiteVec class with SiliconFlowEmbeddings."""
    import argparse

    from cicada.core.utils import cprint, load_config, setup_logging

    from cicada.retrieval.siliconflow_embeddings import SiliconFlowEmbeddings
    from cicada.retrieval.siliconflow_rerank import SiliconFlowRerank

    setup_logging()
    parser = argparse.ArgumentParser(description="Feedback Judge")
    parser.add_argument(
        "--config", default="config.yaml", help="Path to the configuration YAML file"
    )
    args = parser.parse_args()

    embed_config = load_config(args.config, "embed")

    embedding_model = SiliconFlowEmbeddings(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    rerank_config = load_config(args.config, "rerank")

    rerank_model = SiliconFlowRerank(
        api_key=rerank_config["api_key"],
        api_base_url=rerank_config.get(
            "api_base_url", "https://api.siliconflow.cn/v1/"
        ),
        model_name=rerank_config.get("model_name", "BAAI/bge-reranker-v2-m3"),
        **rerank_config.get("model_kwargs", {}),
    )

    # Initialize SQLiteVec
    sqlitevec_store_config = load_config(args.config, "sqlitevec_store")
    db_file = sqlitevec_store_config["db_file"]
    table = sqlitevec_store_config["table"]
    sqlite_vec = SQLiteVec(
        table=table, db_file=db_file, pool_size=5, embedding=embedding_model
    )

    # ============ metadata operations ============
    # Test metadata functionality
    cprint("\nTesting metadata operations...", "cyan")

    # Set metadata
    sqlite_vec.set_metadata("version", "1.0")
    sqlite_vec.set_metadata("status", "active")

    # Get single metadata
    version = sqlite_vec.get_metadata("version")
    cprint(f"Retrieved version: {version}", "green")

    # Test non-existent key
    missing = sqlite_vec.get_metadata("nonexistent")
    cprint(f"Non-existent key returns: {missing}", "yellow")

    # ============ text operations ============
    # Add texts
    texts = [
        "apple",  # English
        "PEAR",  # English (uppercase)
        "naranja",  # Spanish
        "葡萄",  # Chinese
        "The quick brown fox jumps over the lazy dog.",  # English sentence
        "La rápida zorra marrón salta sobre el perro perezoso.",  # Spanish sentence
        "敏捷的棕色狐狸跳过了懒狗。",  # Chinese sentence
        "12345",  # Numbers
        "Café au lait",  # French with special character
        "🍎🍐🍇",  # Emojis
        "manzana",  # Spanish for apple
        "pomme",  # French for apple
        "苹果",  # Chinese for apple
        "grape",  # English for grape
        "uva",  # Spanish for grape
        "fox",  # English for fox
        "zorro",  # Spanish for fox
    ]
    metadatas = [{"source": f"test{i+1}"} for i in range(len(texts))]
    ids = sqlite_vec.add_texts(texts, metadatas)
    cprint(f"Added texts with IDs: {ids}", "blue")

    # Perform similarity search
    queries = [
        "Vínber",  # Icelandic for grape
        "manzana",  # Spanish for apple
        "狐狸",  # Chinese for fox
        "lazy",  # English word
        "rápida",  # Spanish word
        "🍇",  # Grape emoji
        "Café",  # French word with special character
        "123",  # Partial number
    ]

    for query in queries:
        cprint(f"\nQuery: {query}", "blue")
        results, scores = sqlite_vec.similarity_search(query, k=10)
        cprint(f"Similarity search results: {list(zip(results, scores))}", "yellow")

        # Rerank the results
        reranked_results = rerank_model.rerank(
            query,
            results,
            top_n=5,
            return_documents=True,
        )
        cprint(f"Reranked results: {reranked_results}", "cyan")

    # Clean up (optional)
    import os

    if os.path.exists(db_file):
        os.remove(db_file)
        cprint(f"Removed test database: {db_file}", "yellow")
