import json
import logging
import os
import sqlite3
import struct
import sys
from typing import Dict, List, Optional

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_grandparent_dir = os.path.dirname(_parent_dir)
sys.path.extend([_parent_dir, _grandparent_dir])

from common.utils import colorstring, cprint
from retrieval.core.basics import Document, Embeddings, VectorStore

logger = logging.getLogger(__name__)


class SQLiteVec(VectorStore):
    """SQLite with Vec extension as a vector database."""

    def __init__(
        self,
        table: str,
        db_file: str = "vec.db",
        pool_size: int = 5,
        embedding: Embeddings = None,
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

    def _create_connection_pool(self, pool_size: int) -> sqlite3.Connection:
        """Create a connection pool for SQLite.
        Args:
            pool_size (int): The size of the connection pool.

        Returns:
            sqlite3.Connection: A list of SQLite connections.
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

    def create_table_if_not_exists(self) -> None:
        """Create tables if they don't exist.

        Raises:
            sqlite3.Error: If the table creation fails.
        """
        connection = self._get_connection()
        try:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table} (
                    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    metadata BLOB,
                    text_embedding BLOB
                );
            """
            )
            connection.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self._table}_vec USING vec0(
                    rowid INTEGER PRIMARY KEY,
                    text_embedding float[{self.get_dimensionality()}]
                );
            """
            )
            connection.commit()
            logger.info(
                colorstring(
                    f"Tables created or verified: {self._table}, {self._table}_vec",
                    "green",
                )
            )
        except sqlite3.Error as e:
            logger.error(colorstring(f"Failed to create tables: {e}", "red"))
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

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform a similarity search.

        Args:
            query (str): The query string.
            k (int, optional): The number of results to return. Defaults to 4.

        Returns:
            List[Document]: The list of documents that match the query.

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
        self, embedding: List[float], k: int = 4
    ) -> List[Document]:
        """Perform a similarity search by vector.

        Args:
            embedding (List[float]): The embedding vector to search with.
            k (int, optional): The number of results to return. Defaults to 4.

        Returns:
            List[Document]: The list of documents that match the query.

        Raises:
            sqlite3.Error: If the similarity search fails.
        """
        connection = self._get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                SELECT text, metadata, distance
                FROM {self._table} AS e
                INNER JOIN {self._table}_vec AS v ON v.rowid = e.rowid
                WHERE v.text_embedding MATCH ? AND k = ?
                ORDER BY distance
                LIMIT ?
                """,
                [self.serialize_f32(embedding), k, k],
            )
            results = [
                Document(page_content=row["text"], metadata=json.loads(row["metadata"]))
                for row in cursor.fetchall()
            ]
            logger.info(
                colorstring(f"Found {len(results)} results for the query", "cyan")
            )
            return results
        except sqlite3.Error as e:
            logger.error(
                colorstring(
                    f"Failed to perform similarity search by vector: {e}", "red"
                )
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


def _main():
    """Test the SQLiteVec class with SiliconFlowEmbeddings."""

    # Import the SiliconFlowEmbeddings class
    from siliconflow_embeddings import SiliconFlowEmbeddings
    from siliconflow_rerank import SiliconFlowRerank

    # Initialize SiliconFlowEmbeddings
    embedding_model = SiliconFlowEmbeddings(
        api_key="sk-EFhZxTqkXfedmKP_p9uUwDWJqIMvY0LGSClJ56RpZM7yO4Byvwb7vuRHpXc",
        api_base_url="https://oneapi.service.oaklight.cn/v1",
        model_name="BAAI/bge-m3",
    )

    # Initialize SQLiteVec
    db_file = "test_vec.db"
    table = "test_table"
    sqlite_vec = SQLiteVec(
        table=table, db_file=db_file, pool_size=5, embedding=embedding_model
    )

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
        results = sqlite_vec.similarity_search(query, k=10)
        cprint(f"Similarity search results: {results}", "yellow")

        # Initialize SiliconFlowRerank
        rerank_model = SiliconFlowRerank(
            api_key="sk-EFhZxTqkXfedmKP_p9uUwDWJqIMvY0LGSClJ56RpZM7yO4Byvwb7vuRHpXc",
            api_base_url="https://oneapi.service.oaklight.cn/v1",
            model_name="BAAI/bge-reranker-v2-m3",
        )

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


if __name__ == "__main__":
    _main()
