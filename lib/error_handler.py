"""
error_handler - Hibakezelés és hibanapló.

Ez a modul az alkalmazás hibáinak kezelésére és naplózására
szolgál. Minden hiba egy központi hibanapló fájlba kerül,
időbélyeggel ellátva.

Tipikus használat:

    from lib.error_handler import error, exit_with_error
    
    error("Valami nem stimmel az olvasmánnyal")
    exit_with_error("Kritikus hiba - a program nem folytatható")
"""

import datetime
import sys
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


def exit_with_error(text: str, error_file: str = 'readings/errors.txt', exit_code: int = 1) -> None:
    """
    Kritikus hibaüzenet kiírása és a program leállítása.
    
    Ez a függvény egy kritikus hibaüzenetet mind a konzolra ír ki,
    mind pedig egy hibanapló fájlba menti, majd a programot
    exit_code-dal leállítja.
    
    Args:
        text (str): A hibaüzenet szövege
        error_file (str): A hibanapló fájl elérési útja.
                         Alapértelmezés: 'readings/errors.txt'
        exit_code (int): A kilépési kód. Alapértelmezés: 1 (hiba)
    
    Returns:
        None (a függvény nem tér vissza, a program leáll)
    
    Examples:
        >>> exit_with_error("Hibás JSON fájl - a program nem folytatható")
        # Kiírja a hibát és sys.exit(1)-gyel leállít
    """
    # Hibakezelés az error() függvénnyel
    error(f"KRITIKUS HIBA: {text}", error_file)
    
    # Program leállítása hibajelzéssel
    sys.exit(exit_code)
