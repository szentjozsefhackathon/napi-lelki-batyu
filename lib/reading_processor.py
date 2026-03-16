"""
reading_processor - Olvasmányok keresése és feldolgozása.

Ez a modul az olvasmányok keresésének, feldolgozásának, valamint
a kapcsolódó adatok (commentaries, level-10 olvasmányok) kezeléséért felelős.

Tartalmazza a komplex logikát, amely a zsolozsma azonosítóit összekapcsolja
a readings/ mappában tárolt olvasmányokkal.

Tipikus használat:

    from lib import reading_processor, data_loader
    
    readings = data_loader.loadKatolikusData()
    reading_processor.createReadingIds(celebration, day)
    reading_processor.findReadings(celebration, readings, lelki_batyu)
    reading_processor.findCommentaries(celebration, readings)
    reading_processor.addreadingstolevel10(celebration, readings)
"""

import re
import sys
from typing import Dict, Any, Optional, List

import Levenshtein

from .error_handler import error
from . import part_processor


def createReadingIds(celebration: Dict[str, Any], day: Dict[str, Any]) -> bool:
    """
    Olvasmánykódok generálása regex alapján és speciális esetek kezelése.
    
    Ez a függvény az olvasmánykódokat (readingsId) generálja, amelyek
    alapján majd megkeressük a readings mappában a megfelelő szövegeket.
    
    A feldolgozás során:
    - A readingsBreviarId-ből (amit a zsolozsma ad) kódot generál
    - Regex minták alapján azonosítja a típust (évközi, húsvéti, stb.)
    - Speciális napokra (Karácsony után, Szűz Mária, stb.) hardcoded kódokat használ
    - Köznapokon a fériai olvasmánykódokat is létrehozza
    
    In-place módosítja a celebration objektumot: hozzáadja a readingsId
    és opcionálisan a ferialReadingsId mezőket.
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai (readingsBreviarId-vel)
        day (Dict[str, Any]): A nap adatai (DateDay, DateMonth, DateYear)
    
    Returns:
        bool: True, ha sikerült az azonosítót generálni, False ha valami gond
    
    Examples:
        >>> cel = {'readingsBreviarId': '1C1', 'level': '13', 'season': '5', 'week': '1', 'dayofWeek': 1}
        >>> createReadingIds(cel, {'DateDay': '1', 'DateMonth': '1', 'DateYear': '2024'})
        True
        >>> cel['readingsId']
        'EVK011Hetfo'
    """
    # Szezon -> kód mappák
    season_codes = {
        '0': "ADV", '1': "ADV", '2': "KAR", '3': "KAR", '4': "KAR",
        '5': "EVK", "6": "NAB", "10": "HUS", "11": "HUS"
    }
    
    weekday_codes = {
        1: "Hetfo", 2: "Kedd", 3: "Szerda", 4: "Csutortok", 5: "Pentek", 6: "Szombat"
    }
    
    # A data_transformer-ben a addCustomCelebrationstoBreviarData()-ban már van egy lépés, ahol a readingsId-ket előre generáljuk bizonyos ünnepekre.
    if(celebration.get('readingsId')):
        return True  # Már van readingsId, nem kell újra generálni

    # 1. Ha nincs readingsBreviarId, akkor összeállítjuk (dátum alapján)
    if celebration.get('readingsBreviarId') is None:
        celebration['readingsBreviarId'] = f"{day['DateDay']}.{day['DateMonth']}."
    
    readings_breviar_id = celebration['readingsBreviarId']
    readings_code = "False"  # Default értékből indulunk
    
    # 2. Regex: évközi (C), húsvéti (V), nagyböjti (P), adventi (A), köznapok (K)
    # Formátum: "1C1" -> nap, év-betű, dayofweek (opcionális)
    match = re.search(r"^(\d{1,2})([ACVPK]{1})(\d{0,1})$", readings_breviar_id)
    if match:
        # Évhez és szezonhoz kötött kód
        breviar_code = {
            "A": "ADV", "C": "EVK", "P": "NAB", "V": "HUS", "K": "KAR"
        }
        readings_code = breviar_code[match.group(2)] + str(match.group(1)).zfill(2)
        
        # Ha van dayofweek addon, azt is hozzáadja
        if match.group(3):
            dayofweek_num = int(match.group(3))
            if dayofweek_num in weekday_codes:
                readings_code += str(dayofweek_num) + weekday_codes[dayofweek_num]
    
    # 3. Regex: konkrét dátumon alapuló kód
    # Formátum: "12.25." -> december 25
    match = re.search(r"^(\d{1,2})\.(\d{1,2})\.$", readings_breviar_id)
    if match:
        readings_code = f"{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
    
    # 4. Speciális ünnepek - hardcoded kódok
    celebration_name = celebration.get('name', '')
    
    if readings_breviar_id == 'SvR':
        readings_code = "KAR01"  # Szentcsalád vasárnapja
    
    # Speciális nevek kezelése
    special_names = {
        "Szűz Mária az Egyház Anyja": "PUNK01",
        "Votív mise a Szentlélekről": "PUNKOSDHetfo",
        "A mi Urunk, Jézus Krisztus, az Örök Főpap": "OrokFopap",
        "Krisztus Szent Teste és Vére": "HUS10",
        "Jézus Szent Szíve": "HUS105Pentek",
        "A Boldogságos Szűz Mária Szeplőtelen Szíve": "HUS106Szombat",
        "Pannonhalma: a bazilika felszentelése": "SzekesegyhazFelszentelése",
        "A Boldogságos Szűz Mária szeplőtelen fogantatása": "12-08",
    }
    
    for special_name, special_code in special_names.items():
        if celebration_name == special_name:
            readings_code = special_code
            break
    
    # 5. Köznapok fériai olvasmányainak kódja
    # Ha az ünnep nagy (level >= 10), akkor szükség lehet a köznapok olvasmányaira is
    if int(celebration.get('level', '13')) >= 10:
        season = celebration.get('season')
        week = str(celebration.get('week')).zfill(2)
        dayofweek = celebration.get('dayofWeek')
        
        # Általánosított fériai kód
        if season in season_codes and dayofweek in weekday_codes:
            ferial_readings_id = (
                season_codes[season] +
                week +
                str(dayofweek) +
                weekday_codes[dayofweek]
            )
        else:
            ferial_readings_id = ""
        
        # Karácsony után/előtt speciális kezelés
        day_month = int(day['DateMonth'])
        day_day = int(day['DateDay'])
        
        if ((day_month == 1 and day_day <= 12) or
            (day_month == 12 and day_day >= 25)):
            ferial_readings_id = f"{day_month:02d}-{day_day:02d}"
        
        # Ha már nem ugyanaz, akkor hozzáadja
        if ferial_readings_id and ferial_readings_id != readings_code:
            celebration['ferialReadingsId'] = ferial_readings_id
        
        # Karácsony nyolcadá, vagy Szűz Mária szombatjában is van munka
        if celebration.get('season') in ['2', '3']:
            celebration['ferialReadingsId'] = ferial_readings_id
        
        if celebration_name and celebration_name.startswith("Szűz Mária szombati emléknapja"):
            celebration['ferialReadingsId'] = ferial_readings_id
    
    # 6. Végső értékek beállítása
    celebration['readingsId'] = readings_code
    
    # Státusz jelzés a konzolra
    print(f"  ReadingsId: {readings_code}", end="\r", flush=True)
    
    # Siker?
    return readings_code != 'False'


def findReadings(
    celebration: Dict[str, Any],
    katolikus_data: Dict[str, Any],
    lelki_batyu: Dict[str, Any]
) -> bool:
    """
    Olvasmányok keresése a katholikusData szótárban.
    
    Ez a függvény megtalálja az adott ünnephez szükséges olvasmányokat.
    A keresés több lépésből áll:
    
    1. Levenshtein-távolságon alapuló fuzzy matching az ünnep nevével
    2. Regex-alapú speciális párosítások (pl. advent vasárnapjai)
    3. Ha még mindig nincs találat, hibát dob
    
    In-place módosítja a celebration-t: hozzáadja a parts, parts2, title
    és egyéb mezőket.
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai (readingsId-vel már)
        katolikus_data (Dict[str, Any]): A readings/ mappából betöltött adatok
        lelki_batyu (Dict[str, Any]): A teljes napi batyú (kontextushoz)
    
    Returns:
        bool: True, ha találat, False, ha nem
    
    Examples:
        >>> found = findReadings(celebration, readings_data, lelki_batyu)
        >>> if found:
        ...     print(f"Olvasmányok: {celebration['name']}")
    """
    readings_id = celebration.get('readingsId')
    if not readings_id:
        return False
    
    # 1. Kód alapján keres
    if readings_id not in katolikus_data:
        # 2. Év-betűvel próbálkozik
        year_letter = celebration.get('yearLetter', '')
        year_letter_key = year_letter + readings_id
        
        if year_letter_key not in katolikus_data:
            # Speciális eset: székesegyháza felszentelése
            if (re.search("székesegyház felszentelése", celebration.get('name', '')) or
                re.search("bazilika felszentelése", celebration.get('name', ''))):
                celebration['readingsId'] = "SzekesegyhazFelszentelése"
                return findReadings(celebration, katolikus_data, lelki_batyu)
            else:
                error(f"Ez az olvasmánykód ({readings_id}) hiányzik a kulcsok között. "
                      f"Ünnep: '{celebration.get('name', '')}'")
                return False
        else:
            readings_id = year_letter_key
            celebration['readingsId'] = readings_id
    
    # 3. Olvasmány-lehetőségek összegyűjtése
    readings_data = katolikus_data[readings_id]
    
    if isinstance(readings_data, dict):
        possibilities = [readings_data]
    else:
        possibilities = readings_data
    
    # 4. Szűz Mária szombatja hozzáadása (ha szombat és magasabb rangú)
    if (celebration.get('dayofWeek') == 6 and
        int(celebration.get('level', '13')) > 9):
        if 'SzuzMariaSzombatja' in katolikus_data:
            possibilities.append(katolikus_data['SzuzMariaSzombatja'])
    
    # 5. Székesegyháza felszentelése hozzáadása speciális esetben
    if re.search("székesegyház felszentelése", celebration.get('name', '')):
        if 'SzekesegyhazFelszentelése' in katolikus_data:
            possibilities.append(katolikus_data['SzekesegyhazFelszentelése'])
    
    
    if isinstance(readings_data, dict):
        possibility = readings_data
    # Van, hogy egyetlen readingsId-hez több szent is tartozik, például amikor egy napon több szentet is ünnepelhetünk. 
    # Ilyenkor valami alapján ki kell találni, hogy épp melyik szenthez tartozó olvasmányt kell használni. 
    # Ezért van a possibilities lista, amiben az összes lehetséges olvasmány benne van, és ezek közül kell kiválasztani a megfelelőt.
    else:
        

        # 6. Levenshtein-alapú fuzzy matching
        celebration_name = celebration.get('name', '')
        best_match = None
        best_ratio = 0.65  # Minimum 65% hasonlóság
        
        for possibility in possibilities:
            possibility_name = possibility.get('name', '')
            ratio = Levenshtein.ratio(celebration_name, possibility_name)
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = possibility
        
        # 7. Ha nincs fuzzy match, regex-alapú párosítást próbál
        if not best_match:
            # Speciális regex párosítások
            pairs = [
                ["^A Szent Család", "^Szent Család"],
                ["^adventi idő", "^Adventi köznapok - december"],
                [r"^adventi idő ([0-9]{1})\. hét, vasárnap$", r"^Advent ([0-9]{1})\. vasárnapja"],
                [r"^nagyböjti idő ([0-9]{1})\. hét, vasárnap$", r"^Nagyböjt ([0-9]{1})\. vasárnapja"],
                ["Rózsafüzér Királynője", "Rózsafüzér Királynője"],
                ["Kármelhegyi Boldogasszony", "Kármelhegyi Boldogasszony"],
                ["Krisztus Király", "Évközi 34. vasárnap – Krisztus, a Mindenség Királya"],
                ["karácsony nyolcada 1. hét", "Karácsonyi idő - december"],
                ["karácsonyi idő 1. hét", "Karácsonyi idő - január"],
                [r"^(évközi idő ([0-9]{1,2})\. hét, vasárnap)", r"^(Évközi ([0-9]{1,2})\. vasárnap)"],
                ["Vasárnap Húsvét nyolcadában", "Húsvét 2. vasárnapja"],
                ["Virágvasárnap", "Virágvasárnap"],
                ["\nKrisztus feltámadása$", "Húsvétvasárnap"],
                [r"nagyböjti idő 0\. hét", "hamvazószerda után"],
                ["a bazilika felszentelése", "Székesegyház felszentelése"],
                ["főszékesegyház felszentelése", "Székesegyház felszentelése"]
            ]
            
            for pattern_celebration, pattern_possibility in pairs:
                if re.search(pattern_celebration, celebration_name):
                    for possibility in possibilities:
                        if re.search(pattern_possibility, possibility.get('name', '')):
                            best_match = possibility
                            break
                    if best_match:
                        break
        
        # 8. Ha még mindig nincs találat
        if not best_match:
                error(f"Nincs eléggé jól passzoló olvasmány. Keresett: '{celebration_name}'")
                return False
        
        # 9. Ünnep adatainak frissítése az olvasmánnyal
        possibility = best_match
    
    # Title frissítése
    if possibility.get('name'):
        if lelki_batyu.get('date', {}).get('dayofWeek') != '0' or \
           celebration.get('celebrationType') != 'köznap':
            celebration['title'] = (
                f"{celebration.get('name')} ({celebration.get('celebrationType')})"
            )
        else:
            celebration['title'] = celebration.get('name')
    
    # Parts hozzáadása
    if 'parts' in possibility:
        celebration['parts'] = possibility['parts']
        
        # Ellenőrzés: van-e többrészes struktúra?
        has_multiple_parts = any('parts' in part for part in possibility['parts'])
        
        if has_multiple_parts:
            # Parts szétbontása
            celebration['parts'] = possibility['parts'][0]['parts']
            if len(possibility['parts']) > 1:
                celebration['parts2'] = possibility['parts'][1]['parts']
                
                # Oka a parts2-nak
                if 'cause' in possibility['parts'][1]:
                    celebration['parts2cause'] = possibility['parts'][1]['cause']
        
        # Psalm szövegek generálása (verses + answer mezőkből)
        if 'parts' in celebration:
            celebration['parts'] = part_processor.process_psalm_texts(celebration['parts'])
            celebration['parts'] = part_processor.process_missing_endings(celebration['parts'])
        if 'parts2' in celebration:
            celebration['parts2'] = part_processor.process_psalm_texts(celebration['parts2'])
            celebration['parts2'] = part_processor.process_missing_endings(celebration['parts2'])
    
    # Egyéb mezők másolása
    if 'excerpt' in possibility:
        celebration['teaser'] = possibility['excerpt']
    
    if 'content' in possibility:
        celebration['commentary'] = {
            "type": "object",
            "short_title": "Élete",
            "text": possibility['content']
        }
    
    if 'image' in possibility:
        celebration['image'] = possibility['image']
    
    return True


def findCommentaries(celebration: Dict[str, Any], katolikus_data: Dict[str, Any]) -> None:
    """
    Kommentárok és teasers keresése az olvasmányokhoz.
    
    Ez a függvény külön kommentárokat keres az olvasmányokhoz,
    amelyeket később a felület megjelenítheti.
    
    In-place módosítja a celebration-t: hozzáadja a teaser és commentary mezőket.
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai
        katolikus_data (Dict[str, Any]): A readings/ mappából betöltött adatok
    
    Returns:
        None
    """
    readings_id = celebration.get('readingsId')
    if not readings_id:
        return
    
    # Kommentáriák szótárában keresünk
    commentaries = katolikus_data.get('commentaries', {})
    
    for commentary_key in commentaries:
        commentary_data = commentaries[commentary_key]
        
        # Az olvasmánykód alapján keresünk
        if commentary_data.get('readingsBreviarId') == readings_id:
            # Teaser hozzáadása
            if 'teaser' in commentary_data:
                celebration['teaser'] = commentary_data['teaser'].get('text', '')
            
            # Commentary hozzáadása
            if 'commentary' in commentary_data:
                celebration['commentary'] = {
                    "type": "object",
                    "short_title": "Gondolatok a mai napról",
                    "text": commentary_data['commentary'].get('text', '')
                }
            
            break


def addreadingstolevel10(
    celebration: Dict[str, Any],
    katolikus_data: Dict[str, Any]
) -> Optional[bool]:
    """
    Kötelező emléknapokon (level 10, 11, 12) köznapok olvasmányainak hozzáadása.
    
    Ezeken a napokon az ünnep saját olvasmánya és a köznapi olvasmány is
    választható. Az alapértelmezés általában a köznapok, a parts2 pedig
    az ünnep saját olvasmánya.
    
    In-place módosítja a celebration-t: parts és parts2 összeállítása.
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai
        katolikus_data (Dict[str, Any]): A readings/ mappából betöltött adatok
    
    Returns:
        Optional[bool]: None ha siker (in-place módosítás)
    """
    level = celebration.get('level', '13')
    
    # Csak kötelező emléknapok (level 10, 11, 12)
    if level not in ['10', '11', '12']:
        return None
    
    ferial_readings_id = celebration.get('ferialReadingsId')
    if not ferial_readings_id:
        error("Köznapi olvasmányoknak is kéne lenniük, de nem találjuk az azonosítójukat.")
        return False
    
    # Köznapok olvasmányainak keresése
    if ferial_readings_id not in katolikus_data:
        error(f"A köznapi olvasmányok ({ferial_readings_id}) nem találhatók meg az adatbázisunkban.")
        return False
    
    ferial_readings = None
    ferial_data = katolikus_data[ferial_readings_id]
    
    # Ha lista, megpróbáljuk kiválasztani az egyiket
    if not isinstance(ferial_data, dict):
        # Többféle köznapok között keresünk
        for item in ferial_data:
            if re.search("^Karácsonyi idő - január", item.get('name', '')):
                ferial_readings = item
                break
        
        if not ferial_readings:
            error("Több köznapi olvasmányos csoport van itt, vagy csak nehéz megtalálni?")
            return False
    else:
        ferial_readings = ferial_data
    
    # Saját olvasmányok parts2-be mennek
    if 'parts' in celebration:
        celebration['parts2'] = celebration['parts']
    else:
        celebration['parts2'] = [{
            "teaser": "Saját olvasmányokat nem találtunk. Elnézést.",
            "text": "Saját olvasmányokat nem találtunk. Elnézést."
        }]
        error("Kéne legyen saját olvasmánya is, de csak a közös olvasmányokat találtunk meg.")
    
    celebration['parts2cause'] = "(Vagy) saját olvasmányok"
    
    # Köznapok lesznek az alapértelmezés (parts)
    if 'parts' in ferial_readings:
        celebration['parts'] = ferial_readings["parts"]
    
    # Psalm szövegek generálása (verses + answer mezőkből)
    if 'parts' in celebration:
        celebration['parts'] = part_processor.process_psalm_texts(celebration['parts'])
        celebration['parts'] = part_processor.process_missing_endings(celebration['parts'])
    if 'parts2' in celebration:
        celebration['parts2'] = part_processor.process_psalm_texts(celebration['parts2'])
        celebration['parts2'] = part_processor.process_missing_endings(celebration['parts2'])
    
    return None
