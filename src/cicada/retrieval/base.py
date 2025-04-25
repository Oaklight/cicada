from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import Session, SQLModel, create_engine, select

from ..core.utils import load_config


class BaseStore(ABC):
    """
    基础存储抽象类，封装通用CRUD操作。
    所有具体存储实现都应继承此类。
    """

    def __init__(
        self,
        db_url_or_engine: Union[str, Engine],
        models: Union[Type[SQLModel], List[Type[SQLModel]]],
        reuse_session: bool = False,
    ):
        """
        初始化BaseStore。

        参数:
        - db_url_or_engine: 数据库连接URL字符串或已创建的engine对象。
        - models: 单个SQLModel模型类或模型类列表，用于创建数据表。
        """
        if isinstance(db_url_or_engine, str):
            self.engine = create_engine(db_url_or_engine)
        else:
            self.engine = db_url_or_engine

        self._reuse_session = reuse_session
        self._session_factory = sessionmaker(bind=self.engine)
        self._scoped_session = None

        if isinstance(models, list):
            for model in models:
                model.metadata.create_all(self.engine)
            self.model = models[0] if models else None
        else:
            models.metadata.create_all(self.engine)
            self.model = models

    @contextmanager
    def _managed_session(self):
        """管理Session生命周期的上下文管理器"""
        if self._reuse_session:
            if self._scoped_session is None:
                self._scoped_session = scoped_session(self._session_factory)
            try:
                yield self._scoped_session
                self._scoped_session.commit()
            except:
                self._scoped_session.rollback()
                raise
        else:
            with Session(self.engine) as session:
                yield session

    def insert(self, data: Union[Dict, List[Dict]]) -> Union[SQLModel, List[SQLModel]]:
        """通用插入方法，支持单条和批量插入

        参数:
        - data: 单条数据字典或数据字典列表

        返回:
        - 单条数据时返回SQLModel对象
        - 多条数据时返回SQLModel对象列表
        """
        if isinstance(data, list):
            return self.bulk_insert(data)
        with self._managed_session() as session:
            obj = self.model(**data)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    def get(self, id: Union[int, str]) -> Optional[SQLModel]:
        """通用查询方法"""
        with self._managed_session() as session:
            obj = session.get(self.model, id)
            if obj:
                session.refresh(obj)
            return obj

    def update(self, id: Union[int, str], data: Dict) -> Optional[SQLModel]:
        """通用更新方法"""
        with self._managed_session() as session:
            obj = session.get(self.model, id)
            if obj:
                for key, value in data.items():
                    setattr(obj, key, value)
                session.add(obj)
                session.commit()
                session.refresh(obj)
            return obj

    def delete(self, id: Union[int, str]) -> bool:
        """通用删除方法"""
        with self._managed_session() as session:
            obj = session.get(self.model, id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    def get_all(self) -> List[SQLModel]:
        """获取所有记录"""
        with self._managed_session() as session:
            statement = select(self.model)
            return session.exec(statement).all()

    def get_many(self, ids: List[Union[int, str]]) -> List[SQLModel]:
        """批量获取多条记录"""
        with self._managed_session() as session:
            statement = select(self.model).where(self.model.id.in_(ids))
            return session.exec(statement).all()

    def filter(self, **kwargs) -> List[SQLModel]:
        """条件查询"""
        with self._managed_session() as session:
            statement = select(self.model)
            for key, value in kwargs.items():
                statement = statement.where(getattr(self.model, key) == value)
            return session.exec(statement).all()

    def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """分页查询"""
        with self._managed_session() as session:
            total = session.query(self.model).count()
            statement = select(self.model).offset((page - 1) * per_page).limit(per_page)
            items = session.exec(statement).all()
            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            }

    def bulk_insert(self, data_list: List[dict]) -> List[SQLModel]:
        """批量插入"""
        with self._managed_session() as session:
            objects = [self.model(**data) for data in data_list]
            session.bulk_save_objects(objects)
            session.commit()
            return objects


if __name__ == "__main__":
    import argparse
    from typing import Optional

    from sqlmodel import Field, SQLModel, create_engine

    parser = argparse.ArgumentParser(description="Test BaseStore")
    parser.add_argument("--config", type=str, help="Path to the configuration file")
    parser.add_argument(
        "--which",
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Which database to use",
    )
    args = parser.parse_args()

    config = load_config(args.config, "vector_store")
    db_url = config[args.which]["connection_string"]

    # 测试模型
    class TestModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        value: int

    # 初始化存储，传入db_url和模型列表，自动创建表
    store = BaseStore(db_url, [TestModel])

    # 测试CRUD操作
    print("\n=== 测试单条插入 ===")
    obj1 = store.insert({"name": "test1", "value": 100})
    print(f"插入结果: {obj1}")

    print("\n=== 测试批量插入 ===")
    objs = store.insert(
        [{"name": "test2", "value": 200}, {"name": "test3", "value": 300}]
    )
    print(f"批量插入结果: {objs}")

    print("\n=== 测试查询 ===")
    obj = store.get(obj1.id)
    print(f"查询结果: {obj}")

    print("\n=== 测试更新 ===")
    updated = store.update(obj1.id, {"value": 200})
    print(f"更新结果: {updated}")

    print("\n=== 测试条件查询 ===")
    results = store.filter(name="test2")
    print(f"条件查询结果: {results}")

    print("\n=== 测试删除 ===")
    deleted = store.delete(obj1.id)
    print(f"删除结果: {deleted}")

    # 清理测试表
    print("\n=== 清理测试表 ===")
    TestModel.metadata.drop_all(store.engine)
    print("测试表已删除")
