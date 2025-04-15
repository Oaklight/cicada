import os
import unittest

from cicada.core.utils import load_config
from cicada.retrieval.sqlitevec_store import SQLiteVec

CONFIG_FILE = os.getenv("CONFIG")


# 创建一个简单的 DummyEmbedding 用于测试
class DummyEmbedding:
    def embed(self, texts):
        # 为每个文本返回一个固定的 3 维向量
        return [[0.0, 1.0, 2.0] for _ in texts]

    def embed_query(self, query):
        # 返回固定的查询向量
        return [0.0, 1.0, 2.0]


class TestBM25Search(unittest.TestCase):
    def setUp(self):
        # 创建一个临时数据库文件

        config = load_config(CONFIG_FILE, "sqlitevec_store")
        self.db_file = config["db_file"]
        self.table = config["table"]
        self.embedding = DummyEmbedding()
        # 初始化 SQLiteVec 实例
        self.store = SQLiteVec(
            table=self.table,
            db_file=self.db_file,
            pool_size=1,
            embedding=self.embedding,
        )
        # 添加一些测试文本
        self.texts = [
            "The apple is a sweet, edible fruit produced by an apple tree.",
            "Bananas are elongated, edible fruits produced by several kinds of large herbaceous flowering plants.",
            "Cherries are small, round fruits that are typically bright or dark red.",
            "Apple pie is a dessert made from apples and pastry.",
            "Banana split is a dessert made with bananas and ice cream.",
            "The quick brown fox jumps over the lazy dog.",
            "A journey of a thousand miles begins with a single step.",
            "To be or not to be, that is the question.",
            "All that glitters is not gold.",
            "The pen is mightier than the sword.",
        ]
        # 这里不关心 metadatas，使用默认空字典即可
        self.ids = self.store.add_texts(self.texts)

    def tearDown(self):
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_bm25_search(self):
        # 使用 bm25_search 搜索包含 "apple" 的文本
        results = self.store.bm25_search("apple", k=3)
        # 转化所有返回的 Document 的文本为小写，查找是否含有 "apple"
        result_texts = [doc.page_content.lower() for doc in results]
        print(result_texts)
        # 至少有一个结果中应包含 "apple"
        self.assertTrue(
            any("apple" in text for text in result_texts), f"Results: {result_texts}"
        )


if __name__ == "__main__":
    unittest.main()
