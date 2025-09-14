"""
Abstraction upon different storage interfaces
"""

from datetime import datetime
from typing import Protocol, Dict, List

# Include None in supported runtime values so storages can return Optional[T]
SUPPORTED_TYPES = int | float | str | bool | datetime | None

class StoragePort(Protocol):
    def create_table(self, table_name: str, table: Dict[str, object]): ...
    def insert_entry(self, table_name: str, table: Dict[str, SUPPORTED_TYPES]): ...
    def read_entries(self, table_name: str) -> List[Dict[str, SUPPORTED_TYPES]]: ...
