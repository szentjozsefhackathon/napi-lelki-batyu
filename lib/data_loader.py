"""
data_loader - Adatok betöltése különféle forrásokból.

Ez a modul az alkalmazás adatforrásainak betöltésért felelős:
- Zsolozsma XML naptárának letöltése és JSON-ra konvertálása
- readings/ mappában tárolt JSON fájlok betöltése
- Az év-kódok (A, B, C) hozzáadása a readings adatokhoz
- Több forrásból azonos kulcs esetén az adatok összeolvasztása

Tipikus használat:

    from lib import data_loader
    
    breviar = data_loader.loadBreviarData(2024)
    readings = data_loader.loadKatolikusData()
"""

import json
import sys
from typing import Any, Dict, List, Optional

import requests
import xmltodict
import Levenshtein

from .file_handler import writeDataFormattedJSONfile
from .error_handler import error, exit_with_error


def downloadBreviarData(year: int) -> None:
    """
    Zsolozsma naptárának letöltése és JSON-ra konvertálása.
    
    Ez a függvény letölti a breviar.kbs.sk szerverről a teljes
    évi zsolozsma naptárat (XML formátumban), majd átalakítja
    JSON-ra és egy helyi fájlba menti.
    
    Args:
        year (int): Az év, amire az adatokat le szeretnénk tölteni
    
    Returns:
        None (az adat fájlba kerül: breviarData_yyyy.json)
    
    Raises:
        requests.RequestException: Ha a letöltés nem sikerül
        Exception: Ha az XML feldolgozás nem sikerül
    
    Examples:
        >>> downloadBreviarData(2024)
        Downloading data from breviar.kbs.sk... OK
        Write breviarData_2024.json... OK
    """
    # Konzol üzenet: indítás
    print("Downloading data from breviar.kbs.sk", end='')
    sys.stdout.flush()
    
    # XML letöltés a zsolozsma szerverről
    # Paraméterek:
    #   qt=pxml - XML formátum
    #   d=* - minden dátum
    #   m=* - minden hónapot
    #   r={year} - az adott év
    #   j=hu - magyar nyelv
    url = f"https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=*&r={year}&j=hu"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Ha HTTP hiba történt, azt dobjon ki
    except requests.RequestException as e:
        print(f" HIBA: {e}")
        raise
    
    # XML-ből Python dict-be konvertálás
    breviar_data = xmltodict.parse(response.content)
    
    # JSON fájlba mentés (szép formázottá)
    writeDataFormattedJSONfile(breviar_data, f"breviarData_{year}.json", sort_keys=True)


def loadBreviarData(year: int) -> Dict[str, Any]:
    """
    Zsolozsma naptárának betöltése a helyi JSON fájlból.
    
    Ez a függvény egy korábban letöltött és JSON-ba konvertált
    zsolozsma naptárat tölt be a memóriába Python dict objektumként.
    
    Args:
        year (int): Az év, amire az adatokat be szeretnénk tölteni
    
    Returns:
        Dict[str, Any]: A zsolozsma naptár adatai Python dict-ben
    
    Raises:
        FileNotFoundError: Ha a breviarData_yyyy.json fájl nem létezik
        json.JSONDecodeError: Ha a fájl nem érvényes JSON
    
    Examples:
        >>> data = loadBreviarData(2024)
        Loading breviarData_2024.json... OK
        >>> 'LHData' in data
        True
    """
    filename = f"breviarData_{year}.json"
    
    print(f"Loading {filename}...", end='')
    sys.stdout.flush()
    
    try:
        with open(filename, encoding='utf8') as f:
            data = json.load(f)
        print(" OK")
        return data
    except FileNotFoundError:
        exit_with_error(f"A fájl nem található: {filename}")
    except json.JSONDecodeError as e:
        exit_with_error(f"Hibás JSON a {filename} fájlban: {e}")


def loadKatolikusData() -> Dict[str, Any]:
    """
    Katolikus liturgiás adatok betöltése a readings/ mappából.
    
    Ez a függvény betölti az összes JSON fájlt a readings/ mappából,
    majd azokat feldolgozza:
    
    1. vasA, vasB, vasC fájlokhoz hozzáadja a év-betűt (A/B/C)
       az 'igenaptarId' mezőben
    2. Ha ugyanaz a kulcs több forrásból is jól van, azokat
       listába összefésüli
    3. A commentaries.json-t is betölti
    
    Returns:
        Dict[str, Any]: Egy nagy szótár, amiben az összes readings adat
    
    Raises:
        FileNotFoundError: Ha valamelyik readings/*.json fájl hiányzik
        json.JSONDecodeError: Ha valamelyik fájl hibás JSON
    
    Examples:
        >>> readings = loadKatolikusData()
        Loading katolikusData from jsons: .vasA..vasB..vasC..olvasmanyok..szentek..custom. OK
        >>> 'vasA01' in readings or 'A01' in readings
        True
    """
    print("Loading katolikusData from jsons: ", end='')
    sys.stdout.flush()
    
    katolikus_data = {}
    
    # A fájlok, amiket be kell tölteni
    sources = ["vasA", "vasB", "vasC", "olvasmanyok", "szentek", "custom"]
    
    for name in sources:
        # Státusz jelzés a konzolra
        print("." + name + ".", end='')
        sys.stdout.flush()
        
        # JSON fájl betöltése
        try:
            with open(f'readings/{name}.json', 'r', encoding="utf8") as file:
                data = json.load(file)
        except FileNotFoundError:
            exit_with_error(f"Hiányzik a readings/{name}.json fájl")
        except json.JSONDecodeError as e:
            exit_with_error(f"Hibás JSON a readings/{name}.json-ben: {e}")
        
        # vasA, vasB, vasC speciális kezelése: év-betű hozzáadása
        if name in ["vasA", "vasB", "vasC"]:
            year_letter = name[3]  # "vasA" -> "A", "vasB" -> "B", "vasC" -> "C"
            transformed_data = {}
            
            for key, value in data.items():
                # Új kulcs az év-betűvel: "01" -> "A01"
                year_letter_key = year_letter + key
                transformed_data[year_letter_key] = value
                
                # Az 'igenaptarId' mezőt is frissítjük
                transformed_data[year_letter_key]['igenaptarId'] = year_letter_key
            
            data = transformed_data
        
        # Az adatok egyesítése a nagy szótárba
        # Több forrásból ugyanaz a kulcs? Akkor lista lesz belőle
        for key, data_value in data.items():
            if key in katolikus_data:
                # Már létezik ez a kulcs
                existing = katolikus_data[key]
                
                # Ha mindkettő dict, listára konvertálás
                if isinstance(existing, dict) and isinstance(data_value, dict):
                    katolikus_data[key] = [existing, data_value]
                # Ha az egyik már lista
                elif isinstance(existing, dict) and isinstance(data_value, list):
                    # Az eredeti dict hozzáadása a listához
                    data_value.append(existing)
                    katolikus_data[key] = data_value
                elif isinstance(existing, list) and isinstance(data_value, dict):
                    # Lista + új dict
                    existing.append(data_value)
                    katolikus_data[key] = existing
                elif isinstance(existing, list) and isinstance(data_value, list):
                    # Két lista egyesítése
                    katolikus_data[key] = existing + data_value
            else:
                # Új kulcs, egyszerű hozzáadás
                katolikus_data[key] = data[key]
    
    # Commentaries betöltése (különálló kezelés)
    try:
        with open('readings/commentaries.json', 'r', encoding="utf8") as file:
            commentaries_data = json.load(file)
        katolikus_data['commentaries'] = commentaries_data
    except FileNotFoundError:
        exit_with_error("Hiányzik a readings/commentaries.json fájl")
    except json.JSONDecodeError as e:
        exit_with_error(f"Hibás JSON a readings/commentaries.json-ben: {e}")
    
    print(" OK")
    return katolikus_data
