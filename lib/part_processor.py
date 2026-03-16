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
from typing import Dict, Optional, Any, List

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


def generate_psalm_text(part: Dict[str, Any]) -> Dict[str, Any]:
    """
    Zsoltár szövegét generálja verses és answer mezőkből.
    
    Ha egy zsoltár part rendelkezik 'verses' tömbvel és 'answer' mezővel,
    ez a függvény automatikusan generálja a formázott 'text' mezőt az alábbi
    sablonnal:
    
    Válasz: <b>answer</b><br>
    Előénekes: verses[0]<br>
    V: <b>answer</b><br>
    E: verses[1]<br>
    V: <b>answer</b><br>
    E: verses[2]<br>
    ... (verses tömb végéig alternálva V és E között)
    
    Args:
        part (Dict[str, Any]): Zsoltár part objektum potenciális verses és answer mezőkkel
    
    Returns:
        Dict[str, Any]: Az eredeti part, a generált 'text' mezővel (ha verses és answer van)
    
    Examples:
        >>> part = {
        ...     'short_title': 'zsoltár',
        ...     'answer': 'Válasz szövege',
        ...     'verses': ['Első vers', 'Második vers', 'Harmadik vers']
        ... }
        >>> result = generate_psalm_text(part)
        >>> 'V: <b>Válasz szövege</b><br>' in result['text']
        True
    """
    # Csak zsoltárokra alkalmazzuk
    if part.get('short_title') != 'zsoltár':
        return part
    
    # Csak akkor generálunk, ha verses tömb és answer mező van
    verses = part.get('verses')
    answer = part.get('answer')
    
    if not verses or not answer or not isinstance(verses, list):
        return part
    
    # Formázott szöveg generálása
    text_parts = []
    
    # Kezdés: "Válasz: <b>answer</b><br>"
    text_parts.append(f"Válasz: <b>{answer}</b><br>")
    
    # "Előénekes: verses[0]<br>"
    if len(verses) > 0:
        text_parts.append(f"Előénekes: {verses[0]}<br>")
    
    # Alternáló V és E versíszögek
    for i in range(1, len(verses)):
        text_parts.append(f"V: <b>{answer}</b><br>")
        text_parts.append(f"E: {verses[i]}<br>")
            
    #  Utolsó verse után is van válasz
    text_parts.append(f"V: <b>{answer}</b>")

    # A generált szöveg hozzáadása a parthoz
    part['text'] = ''.join(text_parts)
    
    return part


def process_psalm_texts(parts: List[Any]) -> List[Any]:
    """
    Psalm text generation alkalmazása parts tömbökre.
    
    Ez a függvény egy parts tömbön iterál és minden zsoltár partra,
    amely verses és answer mezőkkel rendelkezik, alkalmazza a
    generate_psalm_text() függvényt.
    
    Rekurzívan kezeli a beágyazott parts tömböket is, valamint
    kezel olyan eseteket is, ahol a parts tömb elemei lehetnek
    listák vagy szótárak.
    
    Args:
        parts (List[Any]): Parts tömb feldolgozásra
    
    Returns:
        List[Any]: Az eredeti parts tömb, generált psalm szövegekkel
    
    Examples:
        >>> parts = [
        ...     {
        ...         'short_title': 'zsoltár',
        ...         'answer': 'Válasz',
        ...         'verses': ['Vers 1', 'Vers 2']
        ...     }
        ... ]
        >>> result = process_psalm_texts(parts)
        >>> 'V: <b>Válasz</b><br>' in result[0]['text']
        True
    """
    for i, part in enumerate(parts):
        # Ha a part maga egy lista, rekurzívan feldolgozzuk
        if isinstance(part, list):
            parts[i] = process_psalm_texts(part)
        # Ha a part egy szótár
        elif isinstance(part, dict):
            # Ha beágyazott parts van, rekurzívan feldolgozzuk
            if 'parts' in part and isinstance(part['parts'], list):
                part['parts'] = process_psalm_texts(part['parts'])
            
            # Generáljuk a psalm szöveget, ha szükséges
            parts[i] = generate_psalm_text(part)
    
    return parts


def process_missing_endings(parts: List[Any]) -> List[Any]:
    """
    Hiányzó "ending" mezők kitöltése.
    
    Ha egy part short_title-je "olvasmány" vagy "szentlecke" és nincs "ending" mező,
    akkor beállítja az ending-et "Ez az Isten igéje"-re.
    Ha a short_title "evangélium" és nincs "ending" mező, akkor "Ezek az evangélium igéi."-re.
    
    Rekurzívan kezeli a beágyazott parts tömböket is.
    
    Args:
        parts (List[Any]): Parts tömb feldolgozásra
    
    Returns:
        List[Any]: Az eredeti parts tömb, kitöltött ending mezőkkel
    
    Examples:
        >>> parts = [
        ...     {
        ...         'short_title': 'olvasmány',
        ...         'text': 'Valami szöveg',
        ...         'ending': None
        ...     }
        ... ]
        >>> result = process_missing_endings(parts)
        >>> result[0]['ending']
        'Ez az Isten igéje'
        
        >>> parts = [
        ...     {
        ...         'short_title': 'evangélium',
        ...         'text': 'Valami szöveg',
        ...         'ending': None
        ...     }
        ... ]
        >>> result = process_missing_endings(parts)
        >>> result[0]['ending']
        'Ezek az evangélium igéi.'
    """
    for i, part in enumerate(parts):
        # Ha a part maga egy lista, rekurzívan feldolgozzuk
        if isinstance(part, list):
            parts[i] = process_missing_endings(part)
        # Ha a part egy szótár
        elif isinstance(part, dict):
            # Ha beágyazott parts van, rekurzívan feldolgozzuk
            if 'parts' in part and isinstance(part['parts'], list):
                part['parts'] = process_missing_endings(part['parts'])
            
            # Ha short_title evangélium ÉS nincs ending
            if part.get('short_title') == 'evangélium' and not part.get('ending'):
                part['ending'] = 'Ezek az evangélium igéi.'
            # Ha short_title olvasmány vagy szentlecke ÉS nincs ending
            elif part.get('short_title') in ['olvasmány', 'szentlecke'] and not part.get('ending'):
                part['ending'] = 'Ez az Isten igéje'
    
    return parts
