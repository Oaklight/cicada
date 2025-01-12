import os
import sys
import uuid

import yaml
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    TEXT,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.schema import CreateSchema

EMBEDDING_SIZE = 1024

_current_dir = os.path.dirname(os.path.abspath(__file__))

# Load configuration from config.yaml
with open(os.path.join(_current_dir, "config.yaml"), "r") as file:
    config = yaml.safe_load(file)

db_config = config["db_config"]

# Extract database configuration
DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(
    user=db_config["user"],
    password=db_config["password"],
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"],
)

# Create an engine instance
engine = create_engine(DATABASE_URL)

# Create the schema if it doesn't exist
with engine.connect() as connection:
    if not engine.dialect.has_schema(connection, db_config["schema"]):
        connection.execute(CreateSchema(db_config["schema"]))
        connection.commit()

# Define the metadata
metadata = MetaData(schema=db_config["schema"])

# Define the tables
cad_objects = Table(
    "cad_objects",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String(255)),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
    Column(
        "parent_object_id",
        PGUUID(as_uuid=True),
        ForeignKey("cad_objects.id"),
        nullable=True,
    ),
)

files = Table(
    "files",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("cad_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column("file_type", Enum("STEP", "OBJ", "PLY", name="file_type_enum")),
    Column("file_path", String(255)),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

descriptions = Table(
    "descriptions",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("cad_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column(
        "description_type",
        Enum("LLM_GENERATED", "DISTILLED", name="description_type_enum"),
    ),
    Column("text", TEXT),
    Column("description_embedding", Vector(EMBEDDING_SIZE)),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

cadquery_codes = Table(
    "cadquery_codes",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("cad_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column("code", TEXT),
    Column("code_embedding", Vector(EMBEDDING_SIZE)),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

multiview_snapshots = Table(
    "multiview_snapshots",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("cad_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column("image_path", String(255)),
    Column("image_embedding", Vector(EMBEDDING_SIZE)),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

object_parts = Table(
    "object_parts",
    metadata,
    Column("id", PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("parent_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column("part_object_id", PGUUID(as_uuid=True), ForeignKey("cad_objects.id")),
    Column("created_at", TIMESTAMP),
    Column("updated_at", TIMESTAMP),
)

# Create the tables
metadata.create_all(engine)
