"""
data_transformer - Adatok transzformációja és feldolgozása.

Ez a modul felelős a zsolozsma adatok Python objektummá alakításáért,
feldolgozásáért és értelmezéséért. Tartalmazza a celebration objektumok
transzformációját, a liturgikus év páritásának megállapítását, valamint
a napi índexek építéshez szükséges logikát.

Tipikus használat:

    from lib import data_transformer
    
    transformed = data_transformer.transformCelebration(xml_celebration, day)
    parity = data_transformer.yearIorII("C", 2024, "5")
    penance_level = data_transformer.dayOfPenance(celebration)
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def yearIorII(abc: str, year: int, season: str, month: Optional[int] = None) -> str:
    """
    Liturgikus év páritásának megállapítása.
    
    A katolikus liturgiában van az I. és II. év koncepciója. Ez azt jelenti,
    hogy köznapokon az olvasmányok párosodnak - vannak I. évi és II. évi
    olvasmányok. Ez a függvény eldönti, hogy egy adott nap melyik év-típusba
    tartozik.
    
    Az év váltás Advent első vasárnapja előestén történik. Az év-betű (A, B, C)
    az első Vasárnapot jelöli, és ez határozza meg a páritást:
    - 2024-2025 (C) = I. év
    - 2025-2026 (A) = II. év
    - 2026-2027 (B) = I. év
    (és így tovább, felváltva)
    
    Args:
        abc (str): A liturgikus év betűje (A, B vagy C)
        year (int): A naptári év
        season (str): A liturgikus szezon ID (0=Advent I, 1=Advent II, stb.)
        month (Optional[int]): A hónap (1-12). Opcionális, de fontos a decemberi
                              dátumok helyes kezeléséhez.
    
    Returns:
        str: "I" vagy "II", attól függően, hogy melyik év-típus az adott nap
    
    Examples:
        >>> yearIorII("C", 2024, "5")
        'I'
        >>> yearIorII("A", 2025, "0")
        'II'
        >>> yearIorII("B", 2026, "2")
        'I'
    """
    # 1. Advent (szezon 0-1) azt jelzi, hogy az új liturgikus év kezdődik
    # Más szezonokban az előző év szeptemberétől számítunk
    if season in ('0', '1'):
        # Ez az Advent, tehát az új év már szeptemberben elkezdődött
        start_year = int(year)
    else:
        # Nem Advent. Általában az előző naptári év szeptemberében kezdődött az év
        if month is not None and int(month) == 12 and season in ('2', '3', '4'):
            # December alatt karácsony időszaka (szezón 2-4)
            # Ez az év még szeptemberben kezdődött
            start_year = int(year)
        else:
            # Máskor már az előző év szeptemberében kezdődött az év
            start_year = int(year) - 1
    
    # 2. Referencia: a 2024-2025 liturgikus év (szeptember 2024 - augusztus 2025)
    # az I. év (mert C betű van hozzárendelve)
    # Ez az év páritása: (2024 - 2024) % 2 = 0 -> I
    parity_index = (start_year - 2024) % 2
    
    return "I" if parity_index == 0 else "II"


def dayOfPenance(celebration: Dict[str, Any]) -> int:
    """
    Megállapítja, hogy bűnbánati nap-e az adott nap.
    
    A katolikus egyházban vannak speciális bűnbánati napok:
    - Közönséges péntek: 1 pont
    - Nagyböjti péntek: 2 pont
    - Nagypéntek és hamvazószerda: 3 pont
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai (celebration objektum),
                                     amit transformCelebration() adott vissza
    
    Returns:
        int: A bűnbánati szint:
            0 = nem bűnbánati nap
            1 = közönséges péntek
            2 = nagyböjti péntek
            3 = nagypéntek vagy hamvazószerda
    
    Examples:
        >>> cel = {'dateISO': '2024-03-01', 'level': '12', 'season': '5', 'readingsId': 'EVK011Hetfo'}
        >>> dayOfPenance(cel)
        0
        >>> cel_good_friday = {'dateISO': '2024-03-29', 'readingsId': 'NAB065Pentek'}
        >>> dayOfPenance(cel_good_friday)
        3
    """
    penance_level = 0
    
    # A dátum naaaagy alakítása datetime objektummá
    try:
        date_obj = datetime.strptime(celebration['dateISO'], '%Y-%m-%d')
    except (KeyError, ValueError):
        return 0
    
    # 1. Péntek ellenőrzése (hétfő=0, ..., péntek=4, szombat=5, vasárnap=6)
    if date_obj.weekday() == 4:  # Péntek
        # Kivételek: nagyobb ünnepek és bizonyos naptári dátumok
        exceptions = ["02-02", "03-25", "05-01", "08-20", "09-08", "12-24", "12-31", "10-23"]
        month_day = date_obj.strftime('%m-%d')
        
        if month_day in exceptions or int(celebration.get('level', '13')) < 10:
            # Ezek a napok nem bűnbánati péntek
            penance_level = 0
        else:
            # Közönséges péntek
            penance_level = 1
        
        # 2. Nagyböjti péntek speciális kezelése (még erősebb bűnbánat)
        if celebration.get('season') == "6":  # Nagyböjti idő
            penance_level = 2
    
    # 3. Nagypéntek és hamvazószerda speciális esete
    readings_id = celebration.get('readingsId', '')
    if readings_id == "NAB065Pentek" or readings_id == "NAB003Szerda":
        penance_level = 3
    
    return penance_level


def transformCelebration(celebration: Dict[str, Any], day: Dict[str, Any]) -> Dict[str, Any]:
    """
    Zsolozsma XML celebration objektumát feldolgozza és strukturált JSON-á alakítja.
    
    Ez a függvény az XML-ből jövő celebration (ünnep) objektumokat feldolgozza,
    kinyeri a lényeges információkat, és egy "tiszta" JSON struktúrát hoz létre,
    amit később könnyebb feldolgozni.
    
    A feldolgozás során:
    - Az év-betű, páritás, heti infók kinyerése
    - A liturgikus szín azonosítása
    - Az ünnep neve generálása, ha szükséges
    - A breviárium kötet megállapítása
    
    Args:
        celebration (Dict[str, Any]): Az XML-ből xmltodict-tal konvertált celebration
        day (Dict[str, Any]): A nap adatai (DateISO, DayOfWeek, stb.)
    
    Returns:
        Dict[str, Any]: Strukturált celebration objektum:
            - dateISO, yearLetter, yearParity, week, dayofWeek, season, ...
            - name, title, celebrationType, colorText, ...
            - volumeOfBreviary, comunia, readingsBreviarId
    
    Examples:
        >>> cel = transformCelebration(xml_cel, day_data)
        >>> cel['dateISO']
        '2024-01-15'
        >>> cel['name']
        'évközi idő 2. hét, hétfő'
    """
    # Év páritása megállapítása
    year_parity = yearIorII(
        celebration['LiturgicalYearLetter'],
        int(day['DateYear']),
        celebration['LiturgicalSeason']['@Id'],
        int(day['DateMonth'])
    )
    
    # Alapinformációk átmásolása
    transformed = {
        'dateISO': day['DateISO'],
        'yearLetter': celebration['LiturgicalYearLetter'],
        'yearParity': year_parity,
        'week': celebration['LiturgicalWeek'],
        'dayofWeek': int(day["DayOfWeek"]['@Id']),
        'weekOfPsalter': celebration['LiturgicalWeekOfPsalter'],
        'season': celebration['LiturgicalSeason']['@Id'],
        'seasonText': celebration['LiturgicalSeason']['#text'],
        'typeLocal': celebration['LiturgicalCelebrationTypeLocal'],
        'level': celebration['LiturgicalCelebrationLevel'],
        'required': celebration['LiturgicalCelebrationRequired'],
        'name': celebration['LiturgicalCelebrationName'],
        'readingsBreviarId': celebration['LiturgicalReadingsId']
    }
    
    # VolumeOfBreviary megállapítása (melyik kötetben van a szöveg)
    season_id = celebration['LiturgicalSeason']['@Id']
    week_num = int(celebration['LiturgicalWeek'])
    
    if season_id in ['0', '1', '2', '3', '4']:
        # Advent, karácsony, karácsony nyolcada
        transformed['volumeOfBreviary'] = "I"
    elif season_id in ['6', '7', '8', '9', '10', '11']:
        # Nagyböjti idő, húsvét, húsvét nyolcada
        transformed['volumeOfBreviary'] = "II"
    elif week_num > 17:
        # Évközi időből az utolsó rész
        transformed['volumeOfBreviary'] = "IV"
    else:
        # Évközi idő
        transformed['volumeOfBreviary'] = "III"
    
    # Név feldolgozása (lehet HTML is)
    if (isinstance(celebration['LiturgicalCelebrationName'], dict) and
        "#text" in celebration['LiturgicalCelebrationName']):
        transformed['name'] = celebration['LiturgicalCelebrationName']['#text']
    
    # Ha nincs név, generálunk
    if transformed['name'] is None:
        weekday_names = {
            0: "vasárnap", 1: "hétfő", 2: "kedd", 3: "szerda",
            4: "csütörtök", 5: "péntek", 6: "szombat"
        }
        season_text = celebration['LiturgicalSeason']['#text']
        day_of_week = int(day["DayOfWeek"]['@Id'])
        
        # Vasárnap speciális kezelése
        if day_of_week == 0:
            if season_text == "évközi idő":
                transformed['name'] = f"évközi {week_num}. vasárnap"
            else:
                transformed['name'] = f"{season_text[:-5]} {week_num}. vasárnapja"
        else:
            # Nagyböjti idő 0. hét speciális kezelése (hamvazószerda után)
            if season_text == "nagyböjti idő" and week_num == 0 and day_of_week >= 4:
                # csütörtök, péntek, szombat hamvazószerda után
                transformed['name'] = f"{weekday_names[day_of_week]} hamvazószerda után"
            else:
                transformed['name'] = (
                    f"{season_text} {week_num}. hét, "
                    f"{weekday_names[day_of_week]}"
                )
    
    # Ünnep típusa (féria -> köznap konverzió)
    celebration_type = celebration['LiturgicalCelebrationType']['#text']
    if celebration_type == "féria":
        celebration_type = "köznap"
    
    transformed['celebrationType'] = celebration_type
    
    # Title (name + parenthesized type)
    if transformed['name']:
        transformed['title'] = transformed['name']
    else:
        transformed['title'] = celebration_type
    
    # Szín feldolgozása
    transformed['colorId'] = celebration['LiturgicalCelebrationColor']['@Id']
    if "#text" in celebration['LiturgicalCelebrationColor']:
        transformed['colorText'] = celebration['LiturgicalCelebrationColor']['#text']
    
    # Communia (közös részek) feldolgozása
    if "LiturgicalCelebrationCommunia" in celebration:
        if isinstance(celebration['LiturgicalCelebrationCommunia'], dict):
            transformed['comunia'] = [celebration['LiturgicalCelebrationCommunia']]
        else:
            transformed['comunia'] = celebration['LiturgicalCelebrationCommunia']
    else:
        transformed['comunia'] = None
    
    return transformed


def addCustomCelebrationstoBreviarData(lelki_batyu: Dict[str, Any]) -> None:
    """
    Speciális ünnepek szétbontása több részre.
    
    Vannak olyan nagy ünnepek, amelyeknek több ünneplése van.
    Például Karácsonynak van vigília mise, éjféli mise, pásztorok miséje
    és ünnepi mise. Ezeket egy ünnepből több ünneppé kell szétbontani.
    
    Ezzel a függvénnyel in-place módosítjuk a lelkiBatyu objektumot.
    
    Args:
        lelki_batyu (Dict[str, Any]): A napi lelki batyú adata (mit modify-olunk)
    
    Returns:
        None (az objektum in-place módosul)
    """
    # Az ünnepek, amelyeknek több ünneplésük van
    special_celebrations = {
        "Nagycsütörtök": [
            {"name": "Nagycsütörtök - Krizmaszentelési mise", "colorId": "2", "colorText": "fehér"},
            {"name": "Nagycsütörtök, az utolsó vacsora emléknapja"}
        ],
        "Húsvétvasárnap": [
            {"name": "Húsvétvasárnap, Urunk feltámadásának ünnepe - Húsvéti vigília"},
            {"name": "Húsvétvasárnap, Urunk feltámadásának ünnepe"}
        ],
        "Urunk születése (Karácsony)": [
            {"name": "Urunk születése: Karácsony – Vigília mise"},
            {"name": "Karácsony – Éjféli mise"},
            {"name": "Urunk születése: Karácsony – Pásztorok miséje"},
            {"name": "Urunk születése: Karácsony – Ünnepi mise"}
        ],
        "Pünkösd": [
            {"name": "Pünkösd, vigília mise"},
            {"name": "Pünkösdvasárnap"}
        ],
        "Szűz Mária az Egyház Anyja": [
            {"name": "Szűz Mária az Egyház Anyja"},
            {"name": "Votív mise a Szentlélekről", "title": "Votív mise a Szentlélekről"}
        ],
        "Keresztelő Szent János születése": [
            {"name": "Vigília - Keresztelő Szent János születése"},
            {"name": "Keresztelő Szent János születése"}
        ],
        "Szűz Mária mennybevétele (Nagyboldogasszony)": [
            {"name": "Vigília - Szűz Mária mennybevétele (Nagyboldogasszony)"},
            {"name": "Szűz Mária mennybevétele (Nagyboldogasszony)"}
        ]
    }
    
    # Ünnepek feldolgozása
    celebrations = lelki_batyu.get('celebration', [])
    for celebration in celebrations:
        celebration_name = celebration.get('name', '')
        
        if celebration_name in special_celebrations:
            to_add = special_celebrations[celebration_name]
            
            # Új celebration-ök létrehozása az eredeti alapján
            new_celebrations = []
            for i in range(len(to_add)):
                new_celebration = celebrations[0].copy()
                
                # Az adott ünnep-variáció adatainak hozzáadása
                for key, value in to_add[i].items():
                    new_celebration[key] = value
                
                new_celebrations.append(new_celebration)
            
            # Az eredeti celebration listát helyettesítjük az új listával
            lelki_batyu['celebration'] = new_celebrations
            break


def clearYearIorII(celebration: Dict[str, Any]) -> None:
    """
    Év szerinti olvasmányok szűrése.
    
    A köznapokon az olvasmányok paritása szerint különböznek.
    Ez a függvény eldönti, hogy az aktuális nap I. vagy II. évi olvasmányokra
    szűkítsen, az I. évbelit vagy II. évbelit tartja meg, a másik eltávolítja.
    
    In-place módosítja a celebration objektumot.
    
    Args:
        celebration (Dict[str, Any]): Az ünnep adatai (már van benne yearParity)
    
    Returns:
        None (in-place módosítás)
    """
    if 'parts' not in celebration:
        return
    
    year_parity = celebration.get('yearParity')
    
    # Az olvasmányok feldolgozása
    for kid, part in enumerate(celebration['parts']):
        # Ha ez a rész egy lista (több opció közül egy)
        if not isinstance(part, dict):
            # Ez egy lista (pl. I. és II. év)
            to_remove = []
            
            for possibility in part:
                # Van-e "cause" (ok) mező, ami az éveket jelöli?
                if "cause" in possibility:
                    if (possibility["cause"] == "II. évben" and year_parity == "I"):
                        # II. évbeli, de I. év van - törlendő
                        to_remove.append(possibility)
                    elif (possibility["cause"] == "I. évben" and year_parity == "II"):
                        # I. évbeli, de II. év van - törlendő
                        to_remove.append(possibility)
            
            # Törlés
            for p in to_remove:
                part.remove(p)
            
            # Ha csak egy maradt, az már nem lista, hanem dict
            if len(part) == 1:
                celebration['parts'][kid] = part[0]
                # A "cause" mező már nem kell
                if "cause" in celebration['parts'][kid]:
                    celebration['parts'][kid].pop("cause")


def index_celebration_data(
    index_dayofweek: Dict[str, List[str]],
    index_readings_id: Dict[str, List[str]],
    index_name: Dict[str, List[str]],
    calendar_day: Dict[str, Any],
    lelki_batyu: Dict[str, Any]
) -> None:
    """
    Ünnepek indexelése gyors kereséshez.
    
    Ez a függvény indexeket épít az ünnepek keresésére:
    - nap/hét/szezon alapján
    - olvasmánykód alapján
    - ünnep neve alapján
    
    In-place módosítja az index szótárakat.
    
    Args:
        index_dayofweek: Index kereséshez season-week-dayofweek alapján
        index_readings_id: Index kereséshez readingsId alapján
        index_name: Index kereséshez ünnep nama alapján
        calendar_day: A nap adatai (DateISO)
        lelki_batyu: A napi lelki batyú adatai
    
    Returns:
        None (in-place módosítás)
    """
    date_iso = calendar_day.get('DateISO', '')
    
    celebrations = lelki_batyu.get('celebration', [])
    if not isinstance(celebrations, list):
        celebrations = [celebrations]
    
    for celebration in celebrations:
        # 1. Nap/hét/szezon index
        season = celebration.get("season")
        week = celebration.get('week')
        dayofweek = celebration.get('dayofWeek')
        
        if week is not None and dayofweek is not None:
            key = f"{season}-{week}-{dayofweek}"
            if key not in index_dayofweek:
                index_dayofweek[key] = []
            if date_iso not in index_dayofweek[key]:
                index_dayofweek[key].append(date_iso)
        
        # 2. Olvasmánykód index
        readings_id = celebration.get('readingsId')
        if readings_id:
            if readings_id not in index_readings_id:
                index_readings_id[readings_id] = []
            if date_iso not in index_readings_id[readings_id]:
                index_readings_id[readings_id].append(date_iso)
        
        # 3. Név index
        name = celebration.get('name')
        if name:
            if name not in index_name:
                index_name[name] = []
            if date_iso not in index_name[name]:
                index_name[name].append(date_iso)
