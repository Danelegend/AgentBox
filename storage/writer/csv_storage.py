from .storage_port import StoragePort, SUPPORTED_TYPES

from typing import Dict, List
from datetime import datetime
import os
import csv


class CSVStorage(StoragePort):
    def __init__(self, folder_loc: str):
        self.folder_loc = folder_loc
        os.makedirs(folder_loc, exist_ok=True)
        
        self.files: Dict[str, str] = {}

    def create_table(self, table_name: str, schema: Dict[str, type[SUPPORTED_TYPES]]):
        """
        Create a new CSV file with the given schema.
        schema: dict mapping column name -> type (int, float, str, bool, datetime).
        """
        filename = f"{table_name}.csv"
        file_path = os.path.join(self.folder_loc, filename)

        if _does_file_exist(file_path):
            raise FileExistsError(f"Table '{table_name}' already exists.")

        # Save schema alongside the table (for type restoration on read)
        _create_csv_file(file_path, list(schema.keys()))
        
        self.files[table_name] = file_path

        schema_path = file_path + ".schema"
        with open(schema_path, "w") as f:
            for col, typ in schema.items():
                f.write(f"{col}:{typ.__name__}\n")

    def insert_entry(self, table_name: str, entry: Dict[str, SUPPORTED_TYPES]):
        """
        Insert a new row into the CSV table.
        """
        file_path = self.files[table_name]

        if not _does_file_exist(file_path):
            raise FileNotFoundError(f"Table '{table_name}' does not exist.")

        with open(file_path, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=entry.keys())
            writer.writerow({k: _serialize_value(v) for k, v in entry.items()})

    def read_entries(self, table_name: str) -> List[Dict[str, SUPPORTED_TYPES]]:
        """
        Read all rows from the CSV table as list of dicts.
        Restores types using the stored schema if available.
        """
        file_path = self.files[table_name]

        if not _does_file_exist(file_path):
            raise FileNotFoundError(f"Table {table_name} does not exist.")

        # Try to load schema
        schema_path = file_path + ".schema"
        schema = {}
        if os.path.exists(schema_path):
            with open(schema_path) as f:
                for line in f:
                    col, typ_name = line.strip().split(":")
                    schema[col] = _resolve_type(typ_name)

        with open(file_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            rows = []
            for row in reader:
                if schema:
                    rows.append({k: _deserialize_value(v, schema.get(k, str)) for k, v in row.items()})
                else:
                    rows.append(row)  # raw strings if no schema
            return rows


def _does_file_exist(file_path: str) -> bool:
    return os.path.exists(file_path)


def _create_csv_file(file_path: str, keys: List[str]):
    """Create a new CSV file with headers from keys."""
    with open(file_path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()


def _serialize_value(value: SUPPORTED_TYPES) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _deserialize_value(value: str, typ: type) -> SUPPORTED_TYPES:
    if typ is int:
        return int(value)
    if typ is float:
        return float(value)
    if typ is bool:
        return value.lower() in ("true", "1", "yes")
    if typ is datetime:
        return datetime.fromisoformat(value)
    return value  # str fallback


def _resolve_type(name: str) -> type:
    mapping = {
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "datetime": datetime,
    }
    return mapping.get(name, str)
