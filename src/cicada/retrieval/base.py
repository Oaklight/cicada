from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import Session, SQLModel, create_engine, select

from ..core.utils import load_config


class BaseStore(ABC):
    """
    Base storage abstract class, encapsulates common CRUD operations.
    All specific storage implementations should inherit this class.
    """

    def __init__(
        self,
        db_url_or_engine: Union[str, Engine],
        models: Union[Type[SQLModel], List[Type[SQLModel]]],
        reuse_session: bool = False,
    ):
        """
        Initialize BaseStore.

        Parameters:
        - db_url_or_engine: Database connection URL string or created engine object.
        - models: Single SQLModel model class or list of model classes for creating tables.
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
        """Context manager for managing the lifecycle of a Session"""
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
        """Generic insert method, supports single and batch inserts

        Parameters:
        - data: Single data dictionary or list of data dictionaries

        Returns:
        - Returns SQLModel object for single data
        - Returns list of SQLModel objects for multiple data
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
        """Generic query method"""
        with self._managed_session() as session:
            obj = session.get(self.model, id)
            if obj:
                session.refresh(obj)
            return obj

    def update(self, id: Union[int, str], data: Dict) -> Optional[SQLModel]:
        """Generic update method"""
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
        """Generic delete method"""
        with self._managed_session() as session:
            obj = session.get(self.model, id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    def get_all(self) -> List[SQLModel]:
        """Retrieve all records"""
        with self._managed_session() as session:
            statement = select(self.model)
            return session.exec(statement).all()

    def get_many(self, ids: List[Union[int, str]]) -> List[SQLModel]:
        """Batch retrieve multiple records"""
        with self._managed_session() as session:
            statement = select(self.model).where(self.model.id.in_(ids))
            return session.exec(statement).all()

    def filter(self, **kwargs) -> List[SQLModel]:
        """Conditional query"""
        with self._managed_session() as session:
            statement = select(self.model)
            for key, value in kwargs.items():
                statement = statement.where(getattr(self.model, key) == value)
            return session.exec(statement).all()

    def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Paginated query"""
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
        """Batch insert"""
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

    # Test Model
    class TestModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        value: int

    # Initialize storage, pass in db_url and model list, automatically create tables
    store = BaseStore(db_url, [TestModel])

    # Test CRUD operations
    print("\n=== Test single insertion ===")
    obj1 = store.insert({"name": "test1", "value": 100})
    print(f"Insertion result: {obj1}")

    print("\n=== Test batch insertion ===")
    objs = store.insert(
        [{"name": "test2", "value": 200}, {"name": "test3", "value": 300}]
    )
    print(f"Batch insertion result: {objs}")

    print("\n=== Test query ===")
    obj = store.get(obj1.id)
    print(f"Query result: {obj}")

    print("\n=== Test update ===")
    updated = store.update(obj1.id, {"value": 200})
    print(f"Update result: {updated}")

    print("\n=== Test conditional query ===")
    results = store.filter(name="test2")
    print(f"Conditional query result: {results}")

    print("\n=== Test deletion ===")
    deleted = store.delete(obj1.id)
    print(f"Deletion result: {deleted}")

    # Clean up test table
    print("\n=== Clean up test table ===")
    TestModel.metadata.drop_all(store.engine)
    print("Test table deleted")
