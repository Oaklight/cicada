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

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.extend([parent_dir, grandparent_dir])

from common.utils import colorstring
from retrieval.core.basics import Document, Embeddings, VectorStore

logger = logging.getLogger(__name__)

Base = declarative_base()


class CollectionStore(Base):
    __tablename__ = "langchain_pg_collection"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    cmetadata = Column(JSON)
    embeddings = relationship(
        "EmbeddingStore", back_populates="collection", passive_deletes=True
    )


class EmbeddingStore(Base):
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
    def __init__(
        self,
        connection_string: str,
        embedding: Embeddings,
        collection_name: str = "langchain",
        pool_size: int = 5,
    ):
        self._engine = create_engine(
            connection_string, pool_size=pool_size, max_overflow=10
        )
        self._Session = sessionmaker(bind=self._engine)
        self._embedding = embedding
        self._collection_name = collection_name
        self.create_tables_if_not_exists()
        self.create_collection()

    def create_tables_if_not_exists(self) -> None:
        """Create tables if they don't exist."""
        try:
            Base.metadata.create_all(self._engine)
            logger.info(
                colorstring("Tables created or verified in PostgreSQL", "green")
            )
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
                colorstring(f"Collection '{self._collection_name}' created", "green")
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
        """Add texts to the vector store."""
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
                colorstring(f"Added {len(texts)} texts to the vector store", "green")
            )
            return ids
        except Exception as e:
            session.rollback()
            logger.error(colorstring(f"Failed to add texts: {e}", "red"))
            raise e
        finally:
            session.close()

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Perform a similarity search."""
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
        """Perform a similarity search by vector."""
        session = self._Session()
        try:
            collection = (
                session.query(CollectionStore)
                .filter_by(name=self._collection_name)
                .first()
            )
            results = (
                session.query(EmbeddingStore)
                .filter(EmbeddingStore.collection_id == collection.uuid)
                .order_by(EmbeddingStore.embedding.l2_distance(embedding))
                .limit(k)
                .all()
            )
            docs = [
                Document(page_content=result.document, metadata=result.cmetadata)
                for result in results
            ]
            logger.info(colorstring(f"Found {len(docs)} results for the query", "cyan"))
            return docs
        except Exception as e:
            logger.error(
                colorstring(
                    f"Failed to perform similarity search by vector: {e}", "red"
                )
            )
            raise e
        finally:
            session.close()


def main():
    """Test the PGVector class with SiliconFlowEmbeddings."""

    # Import the SiliconFlowEmbeddings class
    from siliconflow_embeddings import SiliconFlowEmbeddings

    # Initialize SiliconFlowEmbeddings
    embedding_model = SiliconFlowEmbeddings(
        api_key="sk-EFhZxTqkXfedmKP_p9uUwDWJqIMvY0LGSClJ56RpZM7yO4Byvwb7vuRHpXc",
        api_base_url="https://oneapi.service.oaklight.cn/v1",
        model_name="BAAI/bge-m3",
    )

    # Initialize PGVector
    connection_string = "postgresql://ppp:codecad_1s_g00d@localhost/codecad_db"  # Replace with your connection string
    collection_name = "test_collection"
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
    ]
    metadatas = [{"source": f"test{i+1}"} for i in range(len(texts))]
    ids = pg_vector.add_texts(texts, metadatas)
    print(colorstring(f"Added texts with IDs: {ids}", "green"))

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
        results = pg_vector.similarity_search(query, k=2)
        print(colorstring(f"Results for query '{query}':", "cyan"))
        for result in results:
            print(f"Document: {result.page_content}, Metadata: {result.metadata}")

    # Clean up (optional)
    with pg_vector._Session() as session:
        collection = (
            session.query(CollectionStore).filter_by(name=collection_name).first()
        )
        if collection:
            session.delete(collection)
            session.commit()
            print(colorstring(f"Removed test collection: {collection_name}", "yellow"))


if __name__ == "__main__":
    main()
