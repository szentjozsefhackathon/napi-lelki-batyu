"""
error_handler - Hibakezelés és hibanapló.

Ez a modul az alkalmazás hibáinak kezelésére és naplózására
szolgál. Minden hiba egy központi hibanapló fájlba kerül,
időbélyeggel ellátva.

Tipikus használat:

    from lib.error_handler import error
    
    error("Valami nem stimmel az olvasmánnyal")
"""

import datetime
from typing import Optional


def error(text: str, error_file: str = 'readings/errors.txt') -> None:
    """
    Hibaüzenet nyomtatása a konsolra és naplózása fájlba.
    
    Ez a függvény egy hibaüzenetet mind a konzolra ír ki,
    mind pedig egy hibanapló fájlba menti. Minden üzenet
    időbélyeggel lesz ellátva.
    
    Args:
        text (str): A hibaüzenet szövege
        error_file (str): A hibanapló fájl elérési útja.
                         Alapértelmezés: 'readings/errors.txt'
    
    Returns:
        None
    
    Raises:
        IOError: Ha a fájlba nem lehet írni
    
    Examples:
        >>> error("Hiányzó olvasmánykód: ABC123")
        # Konzolon: "Hiányzó olvasmánykód: ABC123"
        # Fájlban: "[2024-03-02 21:00:00.123456] Hiányzó olvasmánykód: ABC123"
    """
    # Formázott üzenet időbélyeggel
    timestamp = datetime.datetime.now()
    formatted_message = f"{text}"
    
    # Nyomtatás a konsolra
    print(formatted_message)
    
    # Naplózás a fájlba
    try:
        with open(error_file, 'a', encoding='utf8') as f:
            f.write(f"{timestamp} -- {formatted_message}\n")
    except IOError as e:
        # Ha nem lehet írni, még a konzolra kiírjuk az eredetit
        print(f"[HIBAKEZELÉS] Nem sikerült a hibanapló írása: {e}")
