"""
generate.py - Napi Lelki Batyú generátor.

Ez a főprogram a teljes napi lelki batyú generálásért felelős.
A feldolgozás lépései:

1. Zsolozsma naptárának letöltése/betöltése (breviarData_yyyy.json)
2. Readings mappában tárolt olvasmányok betöltése
3. Minden nap feldolgozása: ünnepek transzformálása, olvasmányok keresése
4. JSON fájlok generálása a batyuk/ mappába
5. Indexek építése a gyors kereséshez

Használat:
    python generate.py --year 2024
    python generate.py --year 2024 --do-next-year
    python generate.py --year 2024 --previous-years 2
"""

import argparse
from datetime import datetime, timedelta
import json
import sys

from lib import (
    file_handler,
    data_loader,
    data_transformer,
    reading_processor,
    error_handler,
    credo_processor,
    gloria_processor
)


def generateLelkiBatyuk(year: int) -> dict:
    """
    Egy év teljes napi lelki batyúját generálja.

    Ez a függvény egy teljes évhez létrehozza az összes napi lelki batyú
    fájlt JSON formátumban. A feldolgozás komplexek:

    1. Zsolozsma adatok betöltése
    2. Readings adatok betöltése
    3. Minden nap feldolgozása:
       - Ünnepek transzformálása
       - Olvasmányok keresése
       - Kommentárok hozzáadása
       - Év-paritás szerinti szűrés
    4. Indexek építése
    5. JSON fájlok írása

    Args:
        year (int): Az év, amire az adatokat generálni szeretnénk

    Returns:
        dict: A teljes év lelki batyú adata (2024-01-01 -> ... -> 2024-12-31)

    Examples:
        >>> all_data = generateLelkiBatyuk(2024)
        >>> len(all_data)  # Napok száma
        366  # 2024 szökőév
    """
    print(f"\n=== {year}. év feldolgozása ===\n")

    # 1. Zsolozsma adatok letöltése/betöltése
    if file_handler.isFileOldOrMissing(f"breviarData_{year}.json"):
        data_loader.downloadBreviarData(year)

    breviar_data = data_loader.loadBreviarData(year)

    # 2. Readings (olvasmányok) betöltése
    katolikus_data = data_loader.loadKatolikusData()

    # 3. Adatstruktúrák inicializálása
    lelki_batyuk = {}  # Összes nap
    index_dayofweek = {}  # Nap/hét/szezon szerinti index
    index_readings_id = {}  # Olvasmánykód szerinti index
    index_name = {}  # Ünnep név szerinti index

    # 4. Minden nap feldolgozása
    calendar_days = breviar_data['LHData']['CalendarDay']

    for calendar_day in calendar_days:
        date_iso = calendar_day['DateISO']
        print(f"{date_iso}: ", end="")
        sys.stdout.flush()

        # Napi batyú inicializálása
        lelki_batyu = {}

        # A. Nap alapadatai
        lelki_batyu['date'] = {
            'ISO': calendar_day['DateISO'],
            'dayOfYear': calendar_day['DayOfYear'],
            'dayofWeek': calendar_day['DayOfWeek']['@Id'],
            'dayofWeekText': calendar_day['DayOfWeek']['#text']
        }

        # B. Ünnepek feldolgozása
        lelki_batyu['celebration'] = []

        # Celebrations lehet dict vagy list
        celebrations = (
            calendar_day['Celebration']
            if isinstance(calendar_day['Celebration'], list)
            else [calendar_day['Celebration']]
        )

        for celebration in celebrations:
            # Ünnep transzformálása XML-ből
            transformed = data_transformer.transformCelebration(celebration, calendar_day)
            lelki_batyu['celebration'].append(transformed)

        # C. Speciális ünnepek szétbontása (pl. Karácsony többrészes ünneplése)
        data_transformer.addCustomCelebrationstoBreviarData(lelki_batyu)

        # D. Minden ünnep feldolgozása
        for key in range(len(lelki_batyu['celebration'])):
            celebration = lelki_batyu['celebration'][key]
            celebration['celebrationKey'] = key
            print("", end='\r', flush=True)
            sys.stdout.flush()

            # 1. Olvasmánykódok generálása
            reading_processor.createReadingIds(celebration, calendar_day)

            # 2. Olvasmányok keresése
            reading_processor.findReadings(celebration, katolikus_data, lelki_batyu)

            # 3. Köznapi olvasmányok hozzáadása (level 10, 11, 12)
            reading_processor.addreadingstolevel10(celebration, katolikus_data)

            # 4. Év-paritás szerinti olvasmányok szűrése
            data_transformer.clearYearIorII(celebration)

            # 5. Kommentárok keresése
            reading_processor.findCommentaries(celebration, katolikus_data)

            # 6. Bűnbánati napok megállapítása
            celebration['dayOfPenance'] = data_transformer.dayOfPenance(celebration)

            # 7. gloria
            celebration['gloria'] = gloria_processor.main(celebration)

            # 8. Credo
            celebration['credo'] = credo_processor.main(celebration)

            print("  OK                                  ", end="\r", flush=True)

        # E. Napi fájl mentése
        file_handler.writeDataFormattedJSONfile(
            lelki_batyu,
            f"batyuk/{date_iso}.json",
            ensure_ascii=False
        )

        # F. Index frissítése
        lelki_batyuk[date_iso] = lelki_batyu
        data_transformer.index_celebration_data(
            index_dayofweek,
            index_readings_id,
            index_name,
            calendar_day,
            lelki_batyu
        )

    # 5. Összefoglaló JSON-ök mentése
    # A. Egyszerű verzió (napi adat, celebrationok, de nincs parts feldolgozás)
    file_handler.writeDataFormattedJSONfile(
        lelki_batyuk,
        f"batyuk/{year}_simple.json",
        ensure_ascii=False
    )

    # B. Index fájl
    index = {
        "seasonWeekDayofWeek": index_dayofweek,
        "readingsId": index_readings_id,
        "name": index_name
    }
    file_handler.writeDataFormattedJSONfile(
        index,
        f"batyuk/{year}_index.json",
        ensure_ascii=False
    )

    # 6. Komplex verzió (parts feldolgozása: lista/dict tipizálás)
    lelki_batyuk_complex = lelki_batyuk

    for day_value in lelki_batyuk_complex.values():
        for cid, celebration in enumerate(day_value['celebration']):
            # Parts és parts2 feldolgozása
            for parts_key in ['parts', 'parts2']:
                if parts_key in day_value['celebration'][cid]:
                    for pid, part in enumerate(day_value['celebration'][cid][parts_key]):
                        # Ha dict, akkor egyszerűen "object" típus
                        if isinstance(part, dict):
                            day_value['celebration'][cid][parts_key][pid]['type'] = 'object'
                        else:
                            # Ha lista, akkor létrehozunk egy wrapper objektumot
                            tmp = {
                                'type': 'array',
                                'content': part
                            }

                            # Minden elem a listában is "object"
                            for content in tmp['content']:
                                content['type'] = 'object'

                            day_value['celebration'][cid][parts_key][pid] = tmp

    # C. Komplex verzió mentése
    file_handler.writeDataFormattedJSONfile(
        lelki_batyuk_complex,
        f"batyuk/{year}.json",
        ensure_ascii=False
    )

    return lelki_batyuk_complex


def main():
    """
    Főprogram: parancssori argumentumok feldolgozása és a generálás indítása.

    Opciók:
    --year YYYY : Az év (alapértelmezés: mostani év)
    --do-next-year : Jövő évét is generálja (alapértelmezés: nem)
    --previous-years N : Előző N évet is generálja (alapértelmezés: 0)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description='Napi lelki batyuk generalasa'
    )
    parser.add_argument(
        '--year',
        default=datetime.now().year,
        type=int,
        help='the year to generate'
    )
    parser.add_argument(
        '--do-next-year',
        action='store_false',
        help='generate next year as well',
        default=False,
        dest='next_year'
    )
    parser.add_argument(
        '--previous-years',
        type=int,
        default=0,
        help='generate previous N years in addition to the given year'
    )

    args = parser.parse_args()

    # Generálandó évek összeállítása
    years = set()
    years.add(args.year)

    # Előző évek hozzáadása
    for i in range(1, args.previous_years + 1):
        years.add(args.year - i)

    # Jövő év hozzáadása (ha kérte)
    if args.next_year:
        years.add(args.year + 1)

    # Generálás minden évre
    all_lelki_batyuk = {}

    for y in sorted(years):
        all_lelki_batyuk = all_lelki_batyuk | generateLelkiBatyuk(y)

    # Szűrés: csak a releváns napok (30 nap múlt + 365 nap jövő)
    today = datetime.now()
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = (today + timedelta(days=365)).strftime('%Y-%m-%d')

    filtered_lelki_batyuk = {
        k: v for k, v in all_lelki_batyuk.items()
        if start_date <= k <= end_date
    }

    # Szűrt verzió mentése (a felület használja)
    file_handler.writeDataFormattedJSONfile(
        filtered_lelki_batyuk,
        "batyuk/igenaptar.json",
        ensure_ascii=False
    )

    print("\nDone!")


if __name__ == "__main__":
    main()
