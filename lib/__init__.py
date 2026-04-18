"""
lib - Napi Lelki Batyú feldolgozási modulok.

Ez a csomag a napi lelki batyú generálásához szükséges
funkciókat logikus modulokra osztja fel:

- error_handler: Hibakezelés és naplózás
- file_handler: Fájl I/O operációk
- data_loader: Adatok betöltése különböző forrásokból
- part_processor: Olvasmányrészek feldolgozása
- data_transformer: Adatok transzformációja és feldolgozása
- reading_processor: Olvasmányok keresése és feldolgozása

Tipikus használat:

    from lib import data_loader, reading_processor

    breviar_data = data_loader.loadBreviarData(2024)
    readings = reading_processor.findReadings(celebration, katolikus_data, lelki_batyu)
"""

__version__ = "1.0.0"
__author__ = "Napi Lelki Batyú Development Team"

# Importok az egyszerűbb hozzáféréshez (opcionális)
from . import error_handler
from . import file_handler
from . import data_loader
from . import part_processor
from . import data_transformer
from . import reading_processor
from . import gloria_processor
from . import credo_processor

__all__ = [
    'error_handler',
    'file_handler',
    'data_loader',
    'part_processor',
    'data_transformer',
    'reading_processor',
    'gloria_processor',
    'credo_processor'
]
