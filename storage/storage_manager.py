from typing import Dict, List, Any, Type, Optional
from pydantic import BaseModel

from storage.table import Table, build_table, TableConfig

import logging
logger = logging.getLogger(__name__)

"""
Does things like checking that types are correct and keeping in-memory temporary copies
"""

class StorageManager:
    def __init__(self):
        self.tables: Dict[str, Table] = {}


    def create_table(
        self, 
        table_name: str, 
        table: Type[BaseModel],
        primary_id_column: Optional[str] = None
    ) -> bool: 
        if table_name in self.tables:
            return False
        
        try:
            table = build_table(
                table_name, 
                table,
                TableConfig(
                    primary_id_column=primary_id_column
                )
            )
            self.tables[table_name] = table
        except ValueError as e:
            logger.error(f"Error creating table {table_name}, e={str(e)}")
            raise e

        return True

    
    def insert_entry(self, table_name: str, entry: Dict[str, Any]) -> Optional[Type[BaseModel]]:
        if table_name not in self.tables:
            return None
        
        table = self.tables[table_name]
        inserted_result = table.insert_entry(entry)

        return inserted_result

    
    def read_entries(self, table_name: str) -> List[Type[BaseModel]]:
        table = self._get_table(table_name)

        return table.read_entries()


    def get_entry(self, table: str, column: str, value: Any) -> List[BaseModel]:
        """
        Given a column and value, gets all records that match
        """
        entries = self.read_entries(table)

        results = []

        for entry in entries:
            model = entry.model_dump()
            if column in model and model[column] == value:
                results.append(entry)

        return results


    def _get_table(self, table_name: str) -> Table:
        if table_name not in self.tables:
            raise ValueError("Table not found")

        return self.tables[table_name]
