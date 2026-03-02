"""
part_processor - Olvasmányrészek feldolgozása.

Ez a modul az egyes olvasmány- és zsoltárrészek feldolgozásáért
felelős. A HTML formátumú szövegeket "part" objektumokká alakítja,
amelyek tartalmazzák a címet, referenciát, teasert és magát a szöveget.

Tipikus használat:

    from lib.part_processor import partFromReading, partFromPsalm
    
    part = partFromReading(html_reading_text)
    psalm = partFromPsalm(html_psalm_text)
"""

import re
from typing import Dict, Optional, Any

from .error_handler import error


def partFromReading(text: str, reading_id: str = "") -> Dict[str, Optional[str]]:
    """
    HTML olvasmány szövegét feldolgozza és part objektummá konvertálja.
    
    Ez a függvény egy zsolozsma-ből származó olvasmányt (evangélium, szentlecke, etc.)
    feldolgozza, kinyeri a lényeges részeket és egy strukturált objektummá alakítja.
    
    A feldolgozás During során:
    - Felismeri a teaser-t (szögletes zárójelben lévő szöveg)
    - Kinyeri a szöveg típusát (evangélium, szentlecke, olvasmány, passió)
    - Eltávolítja az HTML tageket (pl. <br>, <i>)
    - Elkülöníti a szöveg végén lévő záró formulát ("Ezek az evangélium igéi." stb.)
    
    Args:
        text (str): A feldolgozandó HTML formátumú olvasmány szöveg
        reading_id (str): Az olvasmány azonosítója (hibakezeléshez).
                         Alapértelmezés: "" (nincs ID)
    
    Returns:
        Dict[str, Optional[str]]: Part objektum a következő mezőkkel:
            - short_title (str): "evangélium", "olvasmány", "szentlecke", "passió", vagy None
            - ref (Optional[str]): Az olvasmány bibliográfiai referenciája
            - teaser (Optional[str]): Az olvasmány elején lévő bevezető szöveg
            - title (str): Az olvasmány címe
            - text (str): Az olvasmány fő szövege
            - ending (Optional[str]): A záró formula ("Ezek az evangélium igéi." stb.)
    
    Examples:
        >>> text = "EVANGÉLIUM\\nMáté 5:1-12\\n<i>Ekkor Jézus...</i>\\nEzek az evangélium igéi."
        >>> part = partFromReading(text)
        >>> part['short_title']
        'evangélium'
        >>> part['ending']
        'Ezek az evangélium igéi.'
    """
    # Speciális esetek (ezek kézzel kezelendők)
    if reading_id == "08-06":
        error("YYY Urunk színeváltozása 08-06-ra van berakva hibásan. Ez kézzel kezelendő.")
        return {
            "short_title": None,
            "ref": None,
            "teaser": None,
            "title": None,
            "text": text,
            "ending": None
        }
    
    if reading_id == "11-02":
        error("YYY Halottak napján 11-02-re az evangélium mindenféle és bármi. Ez kézzel kezelendő.")
        return {
            "short_title": None,
            "ref": None,
            "teaser": None,
            "title": None,
            "text": text,
            "ending": None
        }
    
    # Ha túl rövid a szöveg és nem látszik információ, raw szöveget adunk vissza
    if len(text) < 300:
        return {
            "short_title": None,
            "ref": None,
            "teaser": None,
            "title": None,
            "text": text,
            "ending": None
        }
    
    # 1. Hosszabb/rövidebb forma kezelése
    first_line = text.split('\n', 1)[0]
    
    if first_line == "<i>Hosszabb forma:</i>":
        text = text.split('\n', 2)[2]
    elif first_line == "<i>Hosszabb forma:</i><br>":
        text = text.split('\n', 1)[1]
    
    # Az "Vagy:" többféle lehetőséget jelent
    if first_line == "<i>Vagy:</i><br>" or first_line == "<i>vagy</i><br>":
        error("!!! Itt többféle lehetőség van, ezért fontos lenne majd kézzel megcsinálni: " + reading_id)
        text = text.split('\n', 1)[1]
    
    # 2. Cím kinyerése (első sor után)
    title = text.split('\n', 1)[0]
    
    # 3. Típus megállapítása a cím alapján
    title_upper = title.upper()
    if title_upper.startswith("SZENTLECKE"):
        short_title = "szentlecke"
    elif title_upper.startswith("OLVASMÁNY"):
        short_title = "olvasmány"
    elif "EVANGÉLIUM" in title_upper:
        short_title = "evangélium"
    elif title.startswith("A MI URUNK JÉZUS KRISZTUS KÍNSZENVEDÉSE"):
        short_title = "passió"
    else:
        error("!!! Ez vajon mi lehet? " + title)
        short_title = None
    
    # 4. Teaser kinyerése (szögletes zárójelben vagy dőlt szöveg)
    teaser = None
    delete_lines = 1
    
    lines = text.split('\n')
    if len(lines) > 2:
        potential_teaser = lines[2]
        
        if potential_teaser.startswith('<i>'):
            # Dőlt szöveg a teaser
            if re.match(r'(.*)</i>(<br>|)$', potential_teaser):
                teaser = potential_teaser
                delete_lines = 2
            elif len(lines) > 3 and re.match(r'(.*)</i>(<br>|)$', lines[3]):
                teaser = lines[2] + '\n' + lines[3]
                delete_lines = 3
            elif len(lines) > 4 and re.match(r'(.*)</i>(<br>|)$', lines[4]):
                teaser = lines[2] + '\n' + lines[3] + '\n' + lines[4]
                delete_lines = 4
            
            # Dőlt tagek eltávolítása
            if teaser:
                pattern = r'^<i>(.*)</i>(<br>|)$'
                teaser = re.sub(pattern, r'\1', teaser.strip())
        else:
            delete_lines = 1
    
    # 5. Szöveg feldolgozása (teaser eltávolítása után)
    lines = text.split('\n', delete_lines + 1)
    if len(lines) > delete_lines:
        text = lines[delete_lines]
    
    # 6. Passió speciális kezelése (nincs ending)
    if short_title == "passió":
        ending = None
    else:
        # Utolsó sor = záró formula
        if '\n' in text:
            ending = text[text.rfind('\n') + 1:].strip()
        else:
            ending = text.strip()
        
        # Ellenőrzés az ending helyességéről
        if short_title == "evangélium" and ending != "Ezek az evangélium igéi.":
            error("!!! Az evangéliumot kézzel át kell nézni! " + ending)
        elif (short_title in ["szentlecke", "olvasmány"]) and ending != "Ez az Isten igéje.":
            error("!!! Az olvasmányt/szentleckét kézzel át kell nézni! " + ending)
        else:
            # Végén levő formula eltávolítása
            text = text[:text.rfind('\n')].strip()
    
    # 7. HTML tagek eltávolítása (start és vég)
    text = re.sub(r'^<br>', '', text)
    text = re.sub(r'^<br>', '', text)
    text = re.sub(r'<br>$', '', text)
    text = re.sub(r'<br>$', '', text)
    
    return {
        "short_title": short_title,
        "ref": None,
        "teaser": teaser,
        "title": title,
        "text": text,
        "ending": ending
    }


def partFromPsalm(text: str) -> Dict[str, Optional[str]]:
    """
    HTML zsoltár szövegét feldolgozza és part objektummá konvertálja.
    
    Zsoltárok feldolgozása sokkal egyszerűbb, mint az olvasmányoké.
    Praktikusan csak az első sort használjuk teaserként, a többi pedig
    a szöveg.
    
    Args:
        text (str): A feldolgozandó zsoltár szöveg
    
    Returns:
        Dict[str, Optional[str]]: Part objektum:
            - short_title: "zsoltár"
            - ref: None
            - teaser: Az első sor
            - text: A teljes szöveg
            - title: (opcionális, itt nem használjuk)
    
    Examples:
        >>> psalm = "ZSOLTÁR 23\\nAz Úr az én pásztorom..."
        >>> part = partFromPsalm(psalm)
        >>> part['short_title']
        'zsoltár'
        >>> part['teaser']
        'ZSOLTÁR 23'
    """
    # Első sor = teaser
    first_line = text.split('\n')[0]
    
    return {
        "short_title": "zsoltár",
        "ref": None,
        "teaser": first_line,
        "text": text
    }
