"""
file_handler - Fájlkezelési operációk.

Ez a modul a JSON fájlok írásáért, formázásáért és
az adatfájlok öregsség-ellenőrzéséért felelős.

Tipikus használat:

    from lib.file_handler import writeDataFormattedJSONfile, isFileOldOrMissing
    
    data = {'key': 'value'}
    writeDataFormattedJSONfile(data, 'batyuk/2024.json')
    
    if isFileOldOrMissing('breviarData_2024.json'):
        # Újra kell letölteni az adatokat
        download_new_data()
"""

import json
import os
import sys
import time
from typing import Any, Dict, Optional


def writeDataFormattedJSONfile(
    data: Any,
    filename: str,
    sort_keys: bool = False,
    ensure_ascii: bool = True
) -> None:
    """
    Adatok formázott JSON-ként mentése fájlba.
    
    Ez a függvény egy Python objektumot (dict, list stb.) JSON formátumban
    ment el egy fájlba, szép indentálással. A konzolra is ír egy
    előrehaladást jelző üzenetet.
    
    Args:
        data (Any): A mentendő Python objektum (általában dict vagy list)
        filename (str): A célként szolgáló fájl elérési útja
        sort_keys (bool): Ha True, a JSON kulcsok abc-sorrendbe lesznek.
                         Alapértelmezés: False (az eredeti sorrend)
        ensure_ascii (bool): Ha True, az UTF-8 karakterek escape-elve lesznek.
                            Alapértelmezés: True (a magyar karakterek normálisan maradnak)
    
    Returns:
        None
    
    Raises:
        IOError: Ha a fájlba nem lehet írni
        TypeError: Ha az adat nem JSON-szerializálható
    
    Examples:
        >>> data = {'nap': '2024-03-02', 'ünnepe': 'Szentháromság vasárnapja'}
        >>> writeDataFormattedJSONfile(data, 'batyuk/2024-03-02.json', ensure_ascii=False)
        Write batyuk/2024-03-02.json... OK
    """
    with open(filename, "w", encoding='utf8') as data_file:
        # Konzol üzenet: "Write filename..." (előbb, mint az írás)
        print(f"Write {filename}...", end='')
        sys.stdout.flush()  # Azonnal megjelenítés (nem várakozunk a bufferpolásra)
        
        try:
            # JSON szöveggé alakítás 4-es indentálással
            json_text = json.dumps(
                data,
                indent=4,
                sort_keys=sort_keys,
                ensure_ascii=ensure_ascii
            )
            
            # Fájlba írás
            data_file.write(json_text)
            
            # Sikeres befejezés
            print(" OK")
        except (TypeError, ValueError) as e:
            print(f" HIBA: {e}")
            raise


def isFileOldOrMissing(file_path: str, max_age_seconds: int = 3600) -> bool:
    """
    Ellenőrzi, hogy egy fájl hiányzik-e vagy elavult-e.
    
    Ez a függvény megállapítja, hogy egy adott fájl:
    - Nem létezik-e az adat még,
    - vagy túl régi-e (alapértelmezés: 1 óránál régebbi).
    
    Ezt arra használjuk, hogy eldöntsük: újra kell-e letölteni
    az adatokat a szerverről.
    
    Args:
        file_path (str): Az ellenőrizendő fájl elérési útja
        max_age_seconds (int): Maximális életkor másodpercekben.
                              Alapértelmezés: 3600 (1 óra)
    
    Returns:
        bool: True, ha a fájl hiányzik vagy túl régi
              False, ha a fájl létezik és friss
    
    Examples:
        >>> if isFileOldOrMissing('breviarData_2024.json'):
        ...     download_fresh_data()
    """
    # 1. Ellenőrzés: a fájl létezik-e?
    if not os.path.exists(file_path):
        return True
    
    # 2. Ellenőrzés: nem túl régi-e?
    file_mod_time = os.path.getmtime(file_path)  # Fájl utolsó módosítás ideje
    current_time = time.time()  # Most
    age_in_seconds = current_time - file_mod_time
    
    # Ha régebbi a megadott korláltnál, szükséges az újra letöltés
    if age_in_seconds > max_age_seconds:
        return True
    
    # Fájl friss, nem szükséges újra letölteni
    return False
