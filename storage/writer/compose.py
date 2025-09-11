from typing import Literal

from storage import StoragePort
from storage.csv_storage import CSVStorage

STORAGE_OPTIONS = Literal['CSV']


def _build_csv_storage(folder_loc: str = '') -> CSVStorage:
    if folder_loc == '':
        raise ValueError("No folder locations provided")
    
    return CSVStorage(folder_loc)


def compose(storage_type: STORAGE_OPTIONS, **kwargs) -> StoragePort:
    if storage_type == 'CSV':
        return _build_csv_storage(**kwargs)

