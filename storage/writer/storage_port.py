"""
Abstraction upon different storage interfaces
"""

from datetime import datetime
from typing import Protocol, Dict, List

SUPPORTED_TYPES = int | float | str | bool | datetime

class StoragePort(Protocol):
    def create_table(self, table_name: str, table: Dict[str, type[SUPPORTED_TYPES]]): ...
    def insert_entry(self, table_name: str, table: Dict[str, SUPPORTED_TYPES]): ...
    def read_entries(self, table_name: str) -> List[Dict[str, SUPPORTED_TYPES]]: ...
