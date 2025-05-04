from abc import ABC
from contextlib import contextmanager
from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar, Union

from sqlalchemy import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import Session, SQLModel, create_engine, select

from ..core.utils import load_config


class HasId(Protocol):
    id: Union[int, str]


class HasIdAndMetadata(SQLModel):
    """Base class combining SQLModel and HasId requirements."""

    id: Union[int, str]  # Explicitly declare id field to satisfy HasId protocol


T = TypeVar("T", bound=HasIdAndMetadata)


class BaseStore(ABC, Generic[T]):
    """
    Base storage abstract class, encapsulates common CRUD operations.
    All specific storage implementations should inherit this class.
    """

    def __init__(
        self,
        db_url_or_engine: Union[str, Engine],
        models: Union[Type[T], List[Type[T]]],
        reuse_session: bool = False,
    ) -> None:
        """
        Initialize BaseStore.

        Args:
            db_url_or_engine (Union[str, Engine]): Database connection URL string or created engine object.
            models (Union[Type[SQLModel], List[Type[SQLModel]]]): Single SQLModel model class or list of model classes for creating tables.
        """
        if isinstance(db_url_or_engine, str):
            self.engine = create_engine(db_url_or_engine)
        else:
            self.engine = db_url_or_engine

        self._reuse_session = reuse_session
        self._session_factory = sessionmaker(bind=self.engine)
        self._scoped_session = None

        if isinstance(models, list):
            if not models:
                raise ValueError("At least one model must be provided")
            for model in models:
                if not hasattr(model, "metadata"):
                    raise TypeError(f"Model {model} must be a SQLModel subclass")
                model.metadata.create_all(self.engine)
            self.model = models[0]
        else:
            if not hasattr(models, "metadata"):
                raise TypeError(f"Model {models} must be a SQLModel subclass")
            models.metadata.create_all(self.engine)
            self.model = models

    @contextmanager
    def _managed_session(self):
        """
        Context manager for managing the lifecycle of a Session.

        Yields:
            Session: A managed session object.
        """
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

    @staticmethod
    def _insert(session: Session, model: Type[T], data: Dict[str, Any]) -> T:
        """
        Helper method to insert a new record.

        Args:
            session (Session): The database session.
            model (Type[T]): The model class to insert.
            data (Dict[str, Any]): A dictionary of fields to insert.

        Returns:
            T: The inserted record.
        """
        obj = model(**data)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    @staticmethod
    def _get(session: Session, model: Type[T], id: Union[int, str]) -> Optional[T]:
        """
        Helper method to get a record by ID.

        Args:
            session (Session): The database session.
            model (Type[T]): The model class to query.
            id (Union[int, str]): The ID of the record to retrieve.

        Returns:
            Optional[T]: The retrieved record or None if not found.
        """
        obj = session.get(model, id)
        if obj:
            session.refresh(obj)
        return obj

    @staticmethod
    def _update(
        session: Session, model: Type[T], id: Union[int, str], data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Helper method to update a record.

        Args:
            session (Session): The database session.
            model (Type[T]): The model class to update.
            id (Union[int, str]): The ID of the record to update.
            data (Dict[str, Any]): A dictionary of fields to update.

        Returns:
            Optional[T]: The updated record or None if not found.
        """
        obj = session.get(model, id)
        if obj:
            for key, value in data.items():
                setattr(obj, key, value)
            session.add(obj)
            session.commit()
            session.refresh(obj)
        return obj

    @staticmethod
    def _upsert(
        session: Session, model: Type[T], id: Union[int, str], data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Helper method to upsert a record.

        Args:
            session (Session): The database session.
            model (Type[T]): The model class to upsert.
            id (Union[int, str]): The ID of the record to upsert.
            data (Dict[str, Any]): A dictionary of fields to insert or update.

        Returns:
            T: The upserted record.
        """
        obj = session.get(model, id)
        if obj:
            obj = BaseStore._update(session, model, id, data)
        else:
            obj = BaseStore._insert(session, model, {**data, "id": id})
        return obj

    def _delete(self, session: Session, id: Union[int, str]) -> bool:
        """
        Helper method to delete a record by ID.

        Args:
            session (Session): The database session.
            id (Union[int, str]): The ID of the record to delete.

        Returns:
            bool: True if the record was deleted, False otherwise.
        """
        obj = session.get(self.model, id)
        if obj:
            session.delete(obj)
            session.commit()
            return True
        return False

    def insert(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[T, List[T]]:
        """
        Generic insert method that handles both single and batch inserts automatically.
        When given a single dictionary, performs a single insert.
        When given a list of dictionaries, performs a batch insert.

        Args:
            data (Union[Dict, List[Dict]]):
                - For single insert: a dictionary of field-value pairs
                - For batch insert: a list of such dictionaries

        Returns:
            Union[T, List[T]]:
                - For single insert: the inserted record
                - For batch insert: list of inserted records
        """
        with self._managed_session() as session:
            if isinstance(data, list):
                return self._bulk_insert(session, self.model, data)
            return self._insert(session, self.model, data)

    def get(self, id: Union[int, str]) -> Optional[T]:
        """
        Retrieve a single record by ID.

        Args:
            id (Union[int, str]): The ID of the record to retrieve.

        Returns:
            Optional[T]: The retrieved record or None if not found.
        """
        with self._managed_session() as session:
            return self._get(session, self.model, id)

    @staticmethod
    def _bulk_insert(
        session: Session, model: Type[T], data_list: List[Dict[str, Any]]
    ) -> List[T]:
        """
        Internal batch insert method. Users should use insert() instead.

        Args:
            session (Session): The database session.
            model (Type[T]): The model class to insert.
            data_list (List[Dict[str, Any]]): A list of data dictionaries to insert.

        Returns:
            List[T]: A list of inserted records.
        """
        objects = [model(**data) for data in data_list]
        session.bulk_save_objects(objects)
        session.commit()
        return objects

    def update(self, id: Union[int, str], data: Dict[str, Any]) -> Optional[T]:
        """
        Generic update method.

        Args:
            id (Union[int, str]): The ID of the record to update.
            data (Dict): A dictionary of fields to update.

        Returns:
            Optional[T]: The updated record or None if not found.
        """
        with self._managed_session() as session:
            return self._update(session, self.model, id, data)

    def upsert(self, id: Union[int, str], data: Dict[str, Any]) -> Optional[T]:
        """
        Upsert method to insert a new record or update an existing one.

        Args:
            id (Union[int, str]): The ID of the record to upsert.
            data (Dict): A dictionary of fields to insert or update.

        Returns:
            T: The upserted record.
        """
        with self._managed_session() as session:
            return self._upsert(session, self.model, id, data)

    def delete(self, id: Union[int, str]) -> bool:
        """
        Generic delete method.

        Args:
            id (Union[int, str]): The ID of the record to delete.

        Returns:
            bool: True if the record was deleted, False otherwise.
        """
        with self._managed_session() as session:
            return self._delete(session, id)

    def get_all(self) -> List[T]:
        """
        Retrieve all records.

        Returns:
            List[T]: A list of all records.
        """
        with self._managed_session() as session:
            statement = select(self.model)
            return session.exec(statement).all()

    def get_many(self, ids: List[Union[int, str]]) -> List[T]:
        """Batch retrieve multiple records.

        Args:
            ids (List[Union[int, str]]): A list of IDs to retrieve.

        Returns:
            List[T]: A list of retrieved records.
        """
        with self._managed_session() as session:
            statement = select(self.model).where(getattr(self.model, "id").in_(ids))
            return session.exec(statement).all()

    def filter(self, **kwargs: Any) -> List[T]:
        """
        Conditional query.

        Args:
            **kwargs: Field-value pairs to filter records.
                For 'in' queries, pass field__in=[value1, value2]

        Returns:
            List[T]: A list of records matching the conditions.
        """
        with self._managed_session() as session:
            statement = select(self.model)
            for key, value in kwargs.items():
                if key.endswith("__in"):
                    field = getattr(self.model, key[:-4])
                    statement = statement.where(field.in_(value))
                else:
                    statement = statement.where(getattr(self.model, key) == value)
            return session.exec(statement).all()

    def paginate(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Paginated query.

        Args:
            page (int): The page number to retrieve.
            per_page (int): The number of records per page.

        Returns:
            Dict[str, Any]: A dictionary containing pagination details and records.
        """
        with self._managed_session() as session:
            total = session.exec(select(self.model)).count()
            statement = select(self.model).offset((page - 1) * per_page).limit(per_page)
            items = session.exec(statement).all()
            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            }


if __name__ == "__main__":  # type: ignore
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
    class TestModel(HasIdAndMetadata, table=True):
        id: int = Field(primary_key=True)
        name: str
        value: int

    # Initialize storage, pass in db_url and model list, automatically create tables
    store = BaseStore[TestModel](db_url, [TestModel])

    # Clean up any existing test data before starting
    TestModel.metadata.drop_all(store.engine)
    TestModel.metadata.create_all(store.engine)

    # Test CRUD operations
    print("\n=== Test single insertion ===")
    obj1 = store.insert({"id": 1, "name": "test1", "value": 100})
    assert isinstance(obj1, TestModel)
    print(f"Insertion result: {obj1}")
    assert obj1 is not None, "Single insert failed"
    assert obj1.name == "test1", "Inserted name incorrect"
    assert obj1.value == 100, "Inserted value incorrect"

    print("\n=== Test batch insertion ===")
    objs = store.insert(
        [
            {"id": 2, "name": "test2", "value": 200},
            {"id": 3, "name": "test3", "value": 300},
        ]
    )
    print(f"Batch insertion result: {objs}")
    assert isinstance(objs, list), "Batch insert should return list"
    assert len(objs) == 2, "Batch insert count incorrect"
    assert objs[0].name == "test2", "Batch insert name 1 incorrect"
    assert objs[1].name == "test3", "Batch insert name 2 incorrect"

    # Get inserted objects with their IDs
    objs: List[TestModel] = store.filter(name__in=["test2", "test3"])  # type: ignore
    assert len(objs) == 2, "Failed to retrieve batch inserted objects"

    print("\n=== Test query ===")
    obj: Optional[TestModel] = store.get(obj1.id)
    print(f"Query result: {obj}")
    assert obj is not None, "Query failed"
    assert obj.id == obj1.id, "Queried object ID mismatch"

    print("\n=== Test update ===")
    updated: Optional[TestModel] = store.update(obj1.id, {"value": 200})  # type: ignore
    print(f"Update result: {updated}")
    assert updated is not None, "Update failed"
    assert updated.value == 200, "Updated value incorrect"

    print("\n=== Test conditional query ===")
    results: List[TestModel] = store.filter(name="test2")  # type: ignore
    print(f"Conditional query result: {results}")
    assert len(results) == 1, "Conditional query count incorrect"
    assert results[0].name == "test2", "Conditional query result incorrect"

    print("\n=== Test deletion ===")
    deleted: bool = store.delete(obj1.id)  # type: ignore
    print(f"Deletion result: {deleted}")
    assert deleted, "Deletion failed"
    assert store.get(obj1.id) is None, "Object still exists after deletion"

    print("\n=== Test get_all ===")
    all_objs: List[TestModel] = store.get_all()  # type: ignore
    print(f"All objects count: {len(all_objs)}")
    print(f"First object: {all_objs[0] if all_objs else None}")
    assert len(all_objs) == 2, "get_all count incorrect"
    assert all(obj.name in ["test2", "test3"] for obj in all_objs), (
        "get_all content incorrect"
    )

    print("\n=== Test get_many ===")
    ids: List[int] = [obj.id for obj in objs]  # type: ignore
    many_objs: List[TestModel] = store.get_many(ids)  # type: ignore
    print(f"Retrieved objects count: {len(many_objs)}")
    print(f"First retrieved object: {many_objs[0] if many_objs else None}")
    assert len(many_objs) == 2, "get_many count incorrect"
    assert set(obj.id for obj in many_objs) == set(ids), "get_many IDs mismatch"

    # Clean up test table
    print("\n=== Clean up test table ===")
    TestModel.metadata.drop_all(store.engine)
    print("Test table deleted")
