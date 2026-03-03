"""
generateparts.py - Olvasmányrészek feldolgozása CSV-ből.

Ez a feldolgozó a sources/ mappában lévő CSV fájlokból feldolgozza
az olvasmányokat és generálja a readings/ mappában tárolt JSON fájlokat.

FONTOS: Ez a script csak fejlesztés során szükséges. A readings/ mappában
már feldolgozott, kézzel tisztított adatok vannak, melyeket közvetlenül
használ a generate.py.

A CSV feldolgozás lépései:

1. sources/*.csv fájlok betöltése
2. saint és szentek adatok összeolvasztása (név alapján fuzzy matching)
3. CSV sorok feldolgozása az egyes readings típusok szerint:
   - vasA, vasB, vasC: vasárnapi olvasmányok
   - olvasmanyok: hétköznapi olvasmányok I-II
   - szentek: szentek saját olvasmányai
4. Parts generálása (partFromReading, partFromPsalm)
5. JSON-ba mentés a readings/ mappába

Használat:
    python generateparts.py

Figyelmeztetés: A readings/ mappában kézzel finomított adatok vannak!
Ezek felülírása az eredeti CSV adatokkal adatvesztéshez vezethet.
"""

import csv
import json
import datetime
import re
from typing import Dict, List, Any, Optional

import Levenshtein

from lib import part_processor, error_handler
from lib.error_handler import exit_with_error


# Hibanaplózás inicializálása
def init_error_log():
    """Hibanapló fájl inicializálása."""
    with open('readings/errors.txt', 'w', encoding='utf8') as file:
        file.write(f"{datetime.datetime.now()} -- generateparts.py hibaüzenete:\n")


def loadCsvData() -> Dict[str, List[Dict[str, str]]]:
    """
    CSV fájlok betöltése a sources/ mappából.
    
    Ez a függvény az összes CSV fájlt betölti, amelyekben az olvasmányok
    alapadata van. A CSV-ket Python dict-ek listájává konvertálja.
    
    Returns:
        Dict[str, List[Dict]]: Az összes CSV adat
            - vasA, vasB, vasC: vasárnapi olvasmányok
            - olvasmanyok: hétköznapi olvasmányok
            - szentek: szentek saját olvasmányai
            - saint: angol nyelvű szent adatok
    
    Examples:
        >>> csv_data = loadCsvData()
        >>> len(csv_data['vasA'])
        365  # Körülbelül annyi, mint a vasárnap az évben
    """
    csv_data = {}
    
    # Feldolgozandó CSV fájlok
    sources = ["olvasmanyok", "vasA", "vasB", "vasC", "szentek", "saint"]
    
    for source_name in sources:
        try:
            with open(f'sources/{source_name}.csv', 'r', encoding="utf8") as file:
                csv_reader = csv.DictReader(file, delimiter=",")
                csv_data[source_name] = [row for row in csv_reader]
                print(f"  ✓ {source_name}.csv ({len(csv_data[source_name])} sor)")
        except FileNotFoundError:
            print(f"  ✗ {source_name}.csv nem található")
            error_handler.error(f"Hiányzik a sources/{source_name}.csv fájl")
    
    return csv_data


def mergeSaintAndSzentekData(csv_data: Dict[str, List[Dict[str, str]]]) -> None:
    """
    Saint (angol) és szentek (magyar) adatok összeolvasztása.
    
    A saint.csv angol adatokat tartalmaz (birth_date, death_date, content, stb.),
    a szentek.csv pedig a magyar neveket. Ez a függvény Levenshtein-hasonlóság
    alapján megpróbálja az angol saint adatokat a magyar szentekhez illeszteni.
    
    In-place módosítja a csv_data-t: a szenet objektumokhoz hozzáadja az
    angol forrásból a többletinformációkat.
    
    Args:
        csv_data (Dict): A betöltött CSV adatok
    
    Returns:
        None (in-place módosítás)
    """
    if "saint" not in csv_data or "szentek" not in csv_data:
        return
    
    print("\n  Összeolvasztás: saint + szentek...", end='')
    
    matched_count = 0
    
    # Minden magyar szent feldolgozása
    for szent_idx, szent in enumerate(csv_data['szentek']):
        # Dátum feldolgozása (mm-dd formátum)
        match = re.match(r'^(\d{2})-(\d{2})([a-z]{0,1})$', szent.get("datum", ""))
        
        if not match:
            continue
        
        szent_month = int(match.group(1))
        szent_day = int(match.group(2))
        
        # Az angol saint-ek között keresünk
        for saint in csv_data['saint']:
            saint_month = int(saint.get("month", "0"))
            saint_day = int(saint.get("day", "0"))
            
            # Dátum egyezése és név hasonlósága
            if (szent_month == saint_month and
                szent_day == saint_day):
                
                # Fuzzy name matching
                name_ratio = Levenshtein.ratio(
                    szent.get('nev', ''),
                    saint.get('name', '')
                )
                
                if name_ratio > 0.6:  # 60% fölötti hasonlóság
                    # Összeolvasztás: angol adatok másolása
                    columns = [
                        'birth_date', 'death_date', 'content', 'excerpt',
                        'liturgy', 'prayer', 'source_id', 'color'
                    ]
                    
                    for col in columns:
                        if col in saint:
                            csv_data['szentek'][szent_idx][col] = saint[col]
                    
                    matched_count += 1
                    break
    
    print(f" {matched_count} találat")


def processCsvToJson(csv_data: Dict[str, List[Dict[str, str]]]) -> None:
    """
    CSV adatok feldolgozása és JSON-ba konvertálása.
    
    Ez a függvény az összes CSV adatot feldolgozza, az olvasmányrészeket
    (parts) generálja, és JSON-ba menti a readings/ mappába.
    
    A feldolgozás típusonként:
    - vasA, vasB, vasC: vasárnapi olvasmányok (3 rész: 1. lecke, zsoltár, 2. lecke)
    - olvasmanyok: hétköznapi olvasmányok (I-II év variációk)
    - szentek: szentek saját olvasmányai
    
    Args:
        csv_data (Dict): A betöltött és feldolgozott CSV adatok
    
    Returns:
        None (JSON fájlok a readings/ mappába)
    """
    # Feldolgozandó sources
    sources = ["szentek"]  # Jelenleg csak a szenteket feldolgozzuk
    
    for source_name in sources:
        if source_name not in csv_data:
            print(f"  ✗ {source_name} adatok nem érhetők el")
            continue
        
        print(f"\n  Feldolgozás: {source_name}")
        
        readings_by_id = {}
        
        # CSV sorok feldolgozása
        for row_idx, row in enumerate(csv_data[source_name]):
            if row_idx % 10 == 0:
                print(f"    {row_idx}/{len(csv_data[source_name])}", end='\r')
            
            # Azonosító kinyerése
            if source_name == "szentek":
                # Dátum alapján
                match = re.match(r'^(\d{2})-(\d{2})([a-z]{0,1})$', row.get("datum", ""))
                if not match:
                    error_handler.error(f"Szentről van szó, de nem jó a dátum formátuma: {row.get('datum', '')}")
                    continue
                
                reading_id = f"{match.group(1)}-{match.group(2)}"
            else:
                reading_id = row.get("kod", "")
            
            # Reading objektum inicializálása
            reading = {
                'igenaptarId': row.get("datum" if source_name == "szentek" else "kod", ""),
                'name': row.get("nev", ""),
                'parts': []
            }
            
            # Opcionális mezők másolása (szakont függően)
            optional_fields = [
                'birth_date', 'death_date', 'content', 'excerpt',
                'liturgy', 'prayer', 'source_id', 'color'
            ]
            
            for field in optional_fields:
                if field in row:
                    reading[field] = row[field]
            
            # Parts feldolgozása forrástípus szerint
            if source_name == "szentek":
                # Szentek feldolgozása: 1. lecke, zsoltár, 2. lecke
                if row.get('elsoolv', ''):
                    part = part_processor.partFromReading(row['elsoolv'], reading_id)
                    part['ref'] = row.get('elsoolvhely', '')
                    reading['parts'].append(part)
                
                part = part_processor.partFromPsalm(row.get('zsoltar', ''))
                part['ref'] = row.get('zsoltarhely', '')
                reading['parts'].append(part)
                
                if row.get('masodikolv', ''):
                    part = part_processor.partFromReading(row['masodikolv'], reading_id)
                    part['ref'] = row.get('masodikolvhely', '')
                    reading['parts'].append(part)
            
            # Alleluja és evangélium (ha van)
            if row.get('alleluja', ''):
                part = {
                    'short_title': 'alleluja' if source_name != "szentek" else None,
                    'ref': None,
                    'teaser': row.get('alleluja', ''),
                    'text': row.get('alleluja', '')
                }
                reading['parts'].append(part)
            
            if row.get('evangelium', ''):
                part = part_processor.partFromReading(row['evangelium'], reading_id)
                part['ref'] = row.get('evhely', '')
                reading['parts'].append(part)
            
            # Ha már van ilyen ID, listává konvertálunk
            if reading_id in readings_by_id:
                existing = readings_by_id[reading_id]
                
                if isinstance(existing, dict):
                    readings_by_id[reading_id] = [existing, reading]
                else:
                    readings_by_id[reading_id].append(reading)
            else:
                readings_by_id[reading_id] = reading
        
        # Rendezés és JSON mentése
        readings_by_id = dict(sorted(readings_by_id.items()))
        
        try:
            with open(f"readings/{source_name}.json", "w", encoding='utf8') as f:
                f.write(json.dumps(readings_by_id, indent=4, sort_keys=False, ensure_ascii=False))
            print(f"\n  ✓ {source_name}.json mentve ({len(readings_by_id)} elem)")
        except (IOError, TypeError, ValueError) as e:
            exit_with_error(f"Nem sikerült írni a readings/{source_name}.json fájlt: {e}")


def main():
    """
    Főprogram: CSV betöltés, feldolgozás, JSON generálás.
    
    FIGYELMEZTETÉS: Ez az script csak fejlesztési céllal hasznos!
    A readings/ mappában kézzel finomított adatok vannak, ezek
    felülírása adatvesztéshez vezethet.
    """
    print("\n" + "="*60)
    print("WARNUNG: Ez az script csak fejlesztéshez szükséges!")
    print("A readings/ mappában kézzel finomított adatok vannak.")
    print("="*60 + "\n")
    
    # Hibanaplózás inicializálása
    init_error_log()
    
    # CSV adatok betöltése
    print("1. CSV fájlok betöltése...")
    csv_data = loadCsvData()
    
    # Saint + szentek összeolvasztása
    print("\n2. Saint és szentek adatok összeolvasztása...")
    mergeSaintAndSzentekData(csv_data)
    
    # CSV feldolgozása és JSON generálása
    print("\n3. Feldolgozás és JSON generálás...")
    processCsvToJson(csv_data)
    
    print("\nKész!")


if __name__ == "__main__":
    main()
