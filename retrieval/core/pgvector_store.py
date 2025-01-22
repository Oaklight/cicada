import logging
import os
import sys
import uuid
from typing import Dict, List, Optional

import sqlalchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    UUID,
    Column,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
_grandparent_dir = os.path.dirname(_parent_dir)
sys.path.extend([_parent_dir, _grandparent_dir])

from common.utils import colorstring, cprint, load_config, setup_logging
from retrieval.core.basics import Document, Embeddings, VectorStore

logger = logging.getLogger(__name__)

Base = declarative_base()


class CollectionStore(Base):
    """Represents a collection in the database."""

    __tablename__ = "langchain_pg_collection"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    cmetadata = Column(JSON)
    embeddings = relationship(
        "EmbeddingStore", back_populates="collection", passive_deletes=True
    )


class EmbeddingStore(Base):
    """Represents an embedding in the database."""

    __tablename__ = "langchain_pg_embedding"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("langchain_pg_collection.uuid", ondelete="CASCADE"),
    )
    collection = relationship(CollectionStore, back_populates="embeddings")
    embedding = Column(Vector)
    document = Column(String, nullable=True)
    cmetadata = Column(JSON, nullable=True)
    custom_id = Column(String, nullable=True)


class PGVector(VectorStore):
    """A vector store implementation using PostgreSQL and pgvector."""

    def __init__(
        self,
        connection_string: str,
        embedding: Embeddings,
        collection_name: str = "langchain",
        pool_size: int = 5,
    ):
        """Initialize the PGVector instance.

        Args:
            connection_string (str): The PostgreSQL connection string.
            embedding (Embeddings): The embedding model to use.
            collection_name (str, optional): The name of the collection. Defaults to "langchain".
            pool_size (int, optional): The size of the connection pool. Defaults to 5.
        """
        self._engine = create_engine(
            connection_string, pool_size=pool_size, max_overflow=10
        )
        self._Session = sessionmaker(bind=self._engine)
        self._embedding = embedding
        self._collection_name = collection_name
        self.create_tables_if_not_exists()
        self.create_collection()

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

    def similarity_search(
        self, query: str, k: int = 4
    ) -> tuple[List[Document], List[float]]:
        """Perform a similarity search for a query.

        Args:
            query (str): The query to search for.
            k (int, optional): The number of results to return. Defaults to 4.

        Returns:
            tuple[List[Document], List[float]]: A tuple containing the list of documents that match the query and their corresponding similarity scores.
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
    ) -> tuple[List[Document], List[float]]:
        """Perform a similarity search by vector."""
        session = self._Session()
        try:
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            results = (
                session.query(
                    EmbeddingStore,
                    EmbeddingStore.embedding.l2_distance(embedding).label("distance"),
                )
                .filter(EmbeddingStore.collection_id == collection.uuid)
                .order_by("distance")
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
            logger.info(colorstring(f"Found {len(docs)} results for the query", "cyan"))
            return docs, scores
        except Exception as e:
            logger.error(f"Failed to perform similarity search by vector: {e}")
            raise e
        finally:
            session.close()


def _main():
    setup_logging()
    """Test the PGVector class with SiliconFlowEmbeddings."""

    # Import the SiliconFlowEmbeddings class
    from siliconflow_embeddings import SiliconFlowEmbeddings
    from siliconflow_rerank import SiliconFlowRerank

    embed_config = load_config("config.yaml", "embed")

    # Initialize SiliconFlowEmbeddings
    embedding_model = SiliconFlowEmbeddings(
        embed_config["api_key"],
        embed_config.get("api_base_url"),
        embed_config.get("model_name", "text-embedding-3-small"),
        embed_config.get("org_id"),
        **embed_config.get("model_kwargs", {}),
    )

    rerank_config = load_config("config.yaml", "rerank")

    # Initialize SiliconFlowRerank
    rerank_model = SiliconFlowRerank(
        api_key=rerank_config["api_key"],
        api_base_url=rerank_config.get(
            "api_base_url", "https://api.siliconflow.cn/v1/"
        ),
        model_name=rerank_config.get("model_name", "BAAI/bge-reranker-v2-m3"),
        **rerank_config.get("model_kwargs", {}),
    )

    # Initialize PGVector
    pgvector_store_config = load_config("config.yaml", "pgvector_store")
    connection_string = pgvector_store_config["connection_string"]
    collection_name = pgvector_store_config["collection_name"]
    pg_vector = PGVector(
        connection_string=connection_string,
        embedding=embedding_model,
        collection_name=collection_name,
        pool_size=5,
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


if __name__ == "__main__":
    _main()
