import os
import unittest

from cicada.core.utils import load_config
from cicada.retrieval.pgvector_store import PGVector

CONFIG_FILE = os.getenv("CONFIG")

class DummyEmbedding:
    def embed(self, texts):
        # 返回一个固定的嵌入向量
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_query(self, query):
        # 返回一个固定的查询嵌入向量
        return [0.1, 0.2, 0.3]


class TestPGVectorBM25(unittest.TestCase):
    def setUp(self):
        # 创建一个内存中的 SQLite 数据库
        config = load_config(CONFIG_FILE, "pgvector_store")
        self.connection_string = config["connection_string"]
        self.embedding = DummyEmbedding()
        self.collection_name = config["collection_name"]
        self.pg_vector = PGVector(
            connection_string=self.connection_string,
            embedding=self.embedding,
            collection_name=self.collection_name,
        )
        # 添加测试数据
        self.texts = [
            "The apple is a sweet, edible fruit produced by an apple tree.",
            "Bananas are elongated, edible fruits produced by several kinds of large herbaceous flowering plants.",
            "Cherries are small, round fruits that are typically bright or dark red.",
            "Apple pie is a dessert made from apples and pastry.",
            "Banana split is a dessert made with bananas and ice cream.",
        ]
        self.metadatas = [{"source": f"test{i+1}"} for i in range(len(self.texts))]
        ids = self.pg_vector.add_texts(self.texts, self.metadatas)
        print(f"Added Text IDs: {ids}")

    def test_bm25_search(self):
        # 使用 bm25_search 搜索包含 "apple" 的文本
        results = self.pg_vector.bm25_search("apple", k=3)
        print(f"BM25 Search Results: {results}")
        result_texts = [doc.page_content.lower() for doc in results]
        self.assertTrue(
            any("apple" in text for text in result_texts), f"Results: {result_texts}"
        )
