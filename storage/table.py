from storage.writer import compose, STORAGE_OPTIONS
from storage.writer import SUPPORTED_TYPES

from typing import Any, List, Type
from pydantic import BaseModel

import uuid


class TableConfig(BaseModel):
    primary_id_column: Optional[str] = None


class Table:
    def __init__(
        self,
        table_name: str,
        table: Type[BaseModel],  # schema is now a Pydantic model class
        storage_type: STORAGE_OPTIONS,
        table_config: TableConfig,
        **kwargs,
    ):
        _validate_schema(table)

        self.storage = compose(storage_type, **kwargs)
        self.table_name = table_name
        self.schema = table
        self.table_config = table_config

        # Create storage with schema extracted from Pydantic model
        schema_dict = {name: field.annotation for name, field in table.model_fields.items()}
        self.storage.create_table(table_name, schema_dict)

    def insert_entry(self, data: dict[str, Any]) -> BaseModel:
        """
        Validate and insert entry into the table.
        Pydantic will enforce types and coerce values where possible.
        """
        if self.table_config.primary_id_column is not None:
            col = self.table_config.primary_id_column
            if col not in data or data[col] is None:
                # Generate unique id
                unique_id = uuid.uuid4()
                # Cast to correct type (e.g. str, int)
                target_type = self.schema.model_fields[col].annotation
                try:
                    unique_id = target_type(unique_id)
                except Exception as e:
                    raise e

                data[col] = unique_id

        model_instance = self.schema(**data)  # validate and cast
        self.storage.insert_entry(self.table_name, model_instance.model_dump())

        return model_instance

    def read_entries(self) -> List[BaseModel]:
        """
        Read rows from storage and return as list of Pydantic model instances.
        """
        rows = self.storage.read_entries(self.table_name)
        return [self.schema(**row) for row in rows]


def _validate_schema(schema: Type[BaseModel]):
    """
    Ensure all fields in the Pydantic model use supported types.
    """
    allowed_types = SUPPORTED_TYPES.__args__  # expands union
    for name, field in schema.model_fields.items():
        if field.annotation not in allowed_types:
            raise ValueError(f"Unsupported type {field.annotation} for field '{name}'")


def build_table(table_name: str, table: Type[BaseModel], config: TableConfig) -> Table:
    """
    Helper to build a CSV-backed table at /data.
    """
    return Table(
        table_name=table_name,
        table=table,
        storage_type="CSV",
        table_config=config,
        folder_loc="/data",
    )
