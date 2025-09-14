from .storage_port import StoragePort, SUPPORTED_TYPES

from typing import Dict, List, Tuple, Optional, Union, get_origin, get_args
from datetime import datetime
import types
import os
import csv


class CSVStorage(StoragePort):
    def __init__(self, folder_loc: str):
        self.folder_loc = folder_loc
        os.makedirs(folder_loc, exist_ok=True)
        
        self.files: Dict[str, str] = {}

    def create_table(self, table_name: str, schema: Dict[str, object]):
        """
        Create a new CSV file with the given schema.
        schema: dict mapping column name -> type annotation (supports Optional[T]).
        """
        filename = f"{table_name}.csv"
        file_path = os.path.join(self.folder_loc, filename)

        if _does_file_exist(file_path):
            # Existing table: validate header matches expected schema and ensure schema file exists
            expected_header = list(schema.keys())
            header = _read_csv_header(file_path)

            if header is None or len(header) == 0:
                # Empty file: initialize with expected header
                _create_csv_file(file_path, expected_header)
            else:
                if header != expected_header:
                    raise ValueError(
                        f"Existing CSV header for table '{table_name}' does not match provided schema. "
                        f"existing={header} expected={expected_header}"
                    )

            # Ensure schema sidecar exists and matches expected types
            schema_path = file_path + ".schema"
            if os.path.exists(schema_path):
                existing_schema: Dict[str, Tuple[type, bool]] = {}
                with open(schema_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        col, typ_name = line.split(":", 1)
                        existing_schema[col] = _parse_schema_type(typ_name)

                expected_schema: Dict[str, Tuple[type, bool]] = {}
                for col, ann in schema.items():
                    base_typ, is_optional = _normalize_annotation(ann)
                    expected_schema[col] = (base_typ, is_optional)

                if existing_schema != expected_schema:
                    raise ValueError(
                        f"Existing schema for table '{table_name}' does not match provided schema. "
                        f"existing={existing_schema} expected={expected_schema}"
                    )
            else:
                with open(schema_path, "w") as f:
                    for col, ann in schema.items():
                        base_typ, is_optional = _normalize_annotation(ann)
                        f.write(f"{col}:{_format_schema_type(base_typ, is_optional)}\n")

            # Register file path and return without error
            self.files[table_name] = file_path
            return

        # New table: create file with header and schema
        _create_csv_file(file_path, list(schema.keys()))
        
        self.files[table_name] = file_path

        schema_path = file_path + ".schema"
        with open(schema_path, "w") as f:
            for col, ann in schema.items():
                base_typ, is_optional = _normalize_annotation(ann)
                f.write(f"{col}:{_format_schema_type(base_typ, is_optional)}\n")

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
        schema_info: Dict[str, Tuple[type, bool]] = {}
        if os.path.exists(schema_path):
            with open(schema_path) as f:
                for line in f:
                    col, typ_name = line.strip().split(":")
                    schema_info[col] = _parse_schema_type(typ_name)

        with open(file_path, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            rows = []
            for row in reader:
                if schema_info:
                    rows.append({
                        k: _deserialize_value(v, *(schema_info.get(k, (str, False)))) for k, v in row.items()
                    })
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


def _read_csv_header(file_path: str) -> List[str] | None:
    """Read the header row (field names) from an existing CSV file."""
    try:
        with open(file_path, mode="r", newline="") as file:
            reader = csv.reader(file)
            return next(reader, None)
    except FileNotFoundError:
        return None


def _serialize_value(value: SUPPORTED_TYPES) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _deserialize_value(value: str, typ: type, is_optional: bool) -> SUPPORTED_TYPES:
    if is_optional and (value is None or value == ""):
        return None
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


def _parse_schema_type(raw: str) -> Tuple[type, bool]:
    """Parse a stored schema type string into (base_type, is_optional).

    Supported formats:
    - "int", "float", "str", "bool", "datetime"
    - With optional marker: "int?", "str?", ...
    - Legacy: "Optional" (defaults to str?)
    - Legacy extended: "Optional[int]"
    """
    raw = raw.strip()
    if raw == "Optional":
        return (str, True)
    if raw.startswith("Optional[") and raw.endswith("]"):
        inner = raw[len("Optional["):-1]
        return (_resolve_type(inner), True)
    if raw.endswith("?"):
        base = raw[:-1]
        return (_resolve_type(base), True)
    return (_resolve_type(raw), False)


def _format_schema_type(base_typ: type, is_optional: bool) -> str:
    name = base_typ.__name__
    return f"{name}?" if is_optional else name


def _normalize_annotation(annotation: object) -> Tuple[type, bool]:
    """Normalize a Pydantic/typing annotation to (base_type, is_optional)."""
    origin = get_origin(annotation)
    if origin is None:
        # Direct runtime type (int, str, ...)
        return (annotation if isinstance(annotation, type) else str, False)

    # Handle Optional[T] == Union[T, NoneType]
    if origin is list or origin is dict or origin is tuple:
        # Not supported in this storage; fallback to str
        return (str, False)

    args = get_args(annotation)
    if origin is Union or origin is getattr(types, "UnionType", None):
        non_none_args = [a for a in args if a is not type(None)]
        is_optional = len(args) != len(non_none_args)
        base = non_none_args[0] if non_none_args else str
        # If base is typing constructs, fallback to str
        if not isinstance(base, type):
            base = str
        # Ensure supported base types
        if base not in {int, float, str, bool, datetime}:
            base = str
        return (base, is_optional)

    # Fallback
    return (str, False)
