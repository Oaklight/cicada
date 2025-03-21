import logging
import uuid
from typing import Dict, List, Optional, Tuple

import sqlalchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, create_engine, ForeignKey, JSON, String, UUID
from sqlalchemy.orm import declarative_base, relationship, Session, sessionmaker

from cicada.core.utils import colorstring, cprint, load_config, setup_logging
from cicada.retrieval.basics import Document, Embeddings, VectorStore

logger = logging.getLogger(__name__)

Base = declarative_base()


class CollectionStore(Base):
    """Represents a collection in the database.

    Attributes:
        uuid (UUID): Primary key for the collection.
        name (str): Name of the collection.
        cmetadata (dict): Metadata associated with the collection.
        embeddings (List[EmbeddingStore]): List of embeddings associated with the collection.
    """

    __tablename__ = "vectorsearch_pg_collection"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    cmetadata = Column(JSON)
    embeddings = relationship(
        "EmbeddingStore", back_populates="collection", passive_deletes=True
    )


class EmbeddingStore(Base):
    """Represents an embedding in the database.

    Attributes:
        uuid (UUID): Primary key for the embedding.
        collection_id (UUID): Foreign key referencing the collection.
        collection (CollectionStore): Collection associated with the embedding.
        embedding (Vector): The embedding vector.
        document (str): The document associated with the embedding.
        cmetadata (dict): Metadata associated with the embedding.
        custom_id (str): Custom ID for the embedding.
    """

    __tablename__ = "vectorsearch_pg_embedding"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("vectorsearch_pg_collection.uuid", ondelete="CASCADE"),
    )
    collection = relationship(CollectionStore, back_populates="embeddings")
    embedding = Column(Vector)
    document = Column(String, nullable=True)
    cmetadata = Column(JSON, nullable=True)
    custom_id = Column(String, nullable=True)


class PGVector(VectorStore):
    """A vector store implementation using PostgreSQL and pgvector.

    Attributes:
        _engine (sqlalchemy.engine.Engine): SQLAlchemy engine for database connection.
        _Session (sqlalchemy.orm.sessionmaker): SQLAlchemy session maker.
        _embedding (Embeddings): Embedding model used for generating embeddings.
        _collection_name (str): Name of the collection in the database.
        _collection (CollectionStore): The collection associated with this vector store.
    """

    def __init__(
        self,
        connection_string: str,
        embedding: Embeddings,
        collection_name: str = "vectorsearch",
        pool_size: int = 5,
        **kwargs,
    ):
        """Initialize the PGVector store.

        Args:
            connection_string (str): Database connection string.
            embedding (Embeddings): Embedding model to use.
            collection_name (str, optional): Name of the collection. Defaults to "vectorsearch".
            pool_size (int, optional): Connection pool size. Defaults to 5.
        """
        self._engine = create_engine(
            connection_string, pool_size=pool_size, max_overflow=10
        )
        self._Session = sessionmaker(bind=self._engine)
        self._embedding = embedding
        self._collection_name = collection_name
        self.create_tables_if_not_exists()
        self._collection = self._get_or_create_collection()
        # Validate embedding dimensions
        self._validate_embedding_dimensionality()

    def _validate_embedding_dimensionality(self):
        """Check if embedding dimensions match the database schema."""
        dummy_embedding = self._embedding.embed_query("test")
        column_type = EmbeddingStore.embedding.type
        if hasattr(column_type, "dimensions") and column_type.dimensions is not None:
            if len(dummy_embedding) != column_type.dimensions:
                raise ValueError(
                    f"Embedding dimension ({len(dummy_embedding)}) "
                    f"does not match database schema ({column_type.dimensions})."
                )

    def _get_or_create_collection(self) -> CollectionStore:
        """Get existing collection or create a new one.
        Returns:
            CollectionStore: The collection object.
        """
        session = self._Session()
        try:
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            if not collection:
                collection = CollectionStore(name=self._collection_name, cmetadata={})
                session.add(collection)
                session.commit()
            return collection
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def set_collection_metadata(self, key: str, value: str):
        """Set metadata for the collection.

        Args:
            key (str): Metadata key.
            value (str): Metadata value.
        """
        with self._Session() as session:
            # Using session.merge to re-attach the detached instance
            collection = session.merge(self._collection)
            if not collection.cmetadata:
                collection.cmetadata = {}
            collection.cmetadata[key] = value
            session.commit()

    def get_collection_metadata(self, key: str) -> Optional[str]:
        """Get metadata from the collection.

        Args:
            key (str): Metadata key.

        Returns:
            Optional[str]: The metadata value if it exists, otherwise None.
        """
        with self._Session() as session:
            # Re-fetch the collection within the new session context
            # ===== NOT Correct ========
            # collection = session.get(CollectionStore, self._collection.uuid)
            #
            # ===== Correct ========
            # collection = (
            #     session.query(CollectionStore)
            #     .filter_by(name=self._collection_name)
            #     .first()
            # )
            #
            # ===== Why? ========
            # The original code was incorrect because it directly accessed self._collection.uuid,
            # which could be detached from the session.
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            return collection.cmetadata.get(key) if collection.cmetadata else None

    def get_all_collection_metadata(self) -> Dict:
        """Get all metadata from the collection.

        Returns:
            Dict: A dictionary containing all metadata.
        """
        with self._Session() as session:
            # Re-fetch the collection within the new session context (see above for explanation)
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            return collection.cmetadata or {}

    def create_tables_if_not_exists(self) -> None:
        """Create tables in the database if they don't exist."""
        try:
            Base.metadata.create_all(self._engine)
            logger.info(colorstring("Tables created or verified in PostgreSQL", "blue"))
        except Exception as e:
            logger.error(colorstring(f"Failed to create tables: {e}", "red"))
            raise e

    def create_collection(self) -> None:
        """Create a collection in the database."""
        session = self._Session()
        try:
            collection = CollectionStore(name=self._collection_name)
            session.add(collection)
            session.commit()
            logger.info(
                colorstring(f"Collection '{self._collection_name}' created", "blue")
            )
        except Exception as e:
            session.rollback()
            logger.error(colorstring(f"Failed to create collection: {e}", "red"))
            raise e
        finally:
            session.close()

    def delete_by_ids(self, ids: List[str]):
        """Delete documents by their IDs."""
        session = self._Session()
        try:
            session.query(EmbeddingStore).filter(
                EmbeddingStore.custom_id.in_(ids)
            ).delete()
            session.commit()
            logger.info(colorstring(f"Deleted {len(ids)} documents", "blue"))
        except Exception as e:
            session.rollback()
            logger.error(colorstring(f"Failed to delete documents: {e}", "red"))
            raise e
        finally:
            session.close()

    def add_texts(
        self, texts: List[str], metadatas: Optional[List[Dict]] = None
    ) -> List[str]:
        """Add texts to the vector store.

        Args:
            texts (List[str]): The texts to add.
            metadatas (Optional[List[Dict]], optional): Metadata for each text. Defaults to None.

        Returns:
            List[str]: The IDs of the added texts.
        """
        session = self._Session()
        try:
            embeddings = self._embedding.embed_documents(texts)
            metadatas = metadatas or [{} for _ in texts]
            ids = [str(uuid.uuid4()) for _ in texts]
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            documents = [
                EmbeddingStore(
                    embedding=embedding,
                    document=text,
                    cmetadata=metadata,
                    custom_id=id,
                    collection_id=collection.uuid,
                )
                for text, metadata, embedding, id in zip(
                    texts, metadatas, embeddings, ids
                )
            ]
            session.bulk_save_objects(documents)
            session.commit()
            logger.info(
                colorstring(f"Added {len(texts)} texts to the vector store", "blue")
            )
            return ids
        except Exception as e:
            session.rollback()
            logger.error(colorstring(f"Failed to add texts: {e}", "red"))
            raise e
        finally:
            session.close()

    def add_texts_with_embeddings(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
    ) -> List[str]:
        """Add texts with precomputed embeddings to the vector store.

        Args:
            texts (List[str]): The texts to add.
            embeddings (List[List[float]]): Precomputed embeddings.
            metadatas (Optional[List[Dict]], optional): Metadata for each text. Defaults to None.

        Returns:
            List[str]: The IDs of the added texts.
        """
        if len(texts) != len(embeddings):
            raise ValueError("Texts and embeddings must have the same length.")

        session = self._Session()
        try:
            metadatas = metadatas or [{} for _ in texts]
            ids = [str(uuid.uuid4()) for _ in texts]
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            documents = [
                EmbeddingStore(
                    embedding=embedding,
                    document=text,
                    cmetadata=metadata,
                    custom_id=id,
                    collection_id=collection.uuid,
                )
                for text, metadata, embedding, id in zip(
                    texts, metadatas, embeddings, ids
                )
            ]
            session.bulk_save_objects(documents)
            session.commit()
            logger.info(
                colorstring(f"Added {len(texts)} texts with custom embeddings", "blue")
            )
            return ids
        except Exception as e:
            session.rollback()
            logger.error(colorstring(f"Failed to add texts: {e}", "red"))
            raise e
        finally:
            session.close()

    def similarity_search(
        self, query: str, k: int = 4
    ) -> Tuple[List[Document], List[float]]:
        """Perform a similarity search for a query.

        Args:
            query (str): The query to search for.
            k (int, optional): The number of results to return. Defaults to 4.

        Returns:
            Tuple[List[Document], List[float]]: A tuple containing the list of documents that match the query and their corresponding similarity scores.
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
            distance_metric (str, optional): The distance metric to use. Defaults to "l2". Options are "l2" and "cosine". see https://github.com/pgvector/pgvector?tab=readme-ov-file#querying for more details.

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

        session = self._Session()
        try:
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            match distance_metric:
                case "cosine":
                    distance_expr = EmbeddingStore.embedding.cosine_distance(embedding)
                case "l2":
                    distance_expr = EmbeddingStore.embedding.l2_distance(embedding)
                case _:
                    raise ValueError("Invalid distance metric. Use 'l2', or 'cosine'.")

            results = (
                session.query(EmbeddingStore, distance_expr.label("distance"))
                .filter(EmbeddingStore.collection_id == collection.uuid)
                .order_by(distance_expr)
                .limit(k)
                .all()
            )
            docs = [
                Document(
                    page_content=result.EmbeddingStore.document,
                    metadata=result.EmbeddingStore.cmetadata,
                )
                for result in results
            ]
            scores = [result.distance for result in results]
            logger.info(
                colorstring(
                    f"Found {len(docs)} results using {distance_metric} metric",
                    "cyan",
                )
            )
            return docs, scores
        except Exception as e:
            logger.error(
                colorstring(f"Similarity search failed ({distance_metric}): {e}", "red")
            )
            raise e
        finally:
            session.close()


if __name__ == "__main__":
    import argparse

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

    pgvector_store_config = load_config(args.config, "pgvector_store")
    connection_string = pgvector_store_config["connection_string"]
    collection_name = pgvector_store_config["collection_name"]
    pg_vector = PGVector(
        connection_string=connection_string,
        embedding=embedding_model,
        collection_name=collection_name,
        pool_size=5,
    )

    # ============ metadata operations ============
    # Test metadata functionality
    cprint("\nTesting metadata operations...", "cyan")

    # Set metadata
    pg_vector.set_collection_metadata("version", "1.0")
    pg_vector.set_collection_metadata("status", "active")

    # Get single metadata
    version = pg_vector.get_collection_metadata("version")
    cprint(f"Retrieved version: {version}", "green")

    # Get all metadata
    all_metadata = pg_vector.get_all_collection_metadata()
    cprint(f"All metadata: {all_metadata}", "blue")

    # Test non-existent key
    missing = pg_vector.get_collection_metadata("nonexistent")
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
    ids = pg_vector.add_texts(texts, metadatas)
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
        results, scores = pg_vector.similarity_search(query, k=10)
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
    with pg_vector._Session() as session:
        collection = (
            session.query(CollectionStore).filter_by(name=collection_name).first()
        )
        if collection:
            session.delete(collection)
            session.commit()
            cprint(f"Removed test collection: {collection_name}", "yellow")
