# Python Kód Refaktorálási Terv

## Cél
Az átláthatatlan, nagy Python fájlokat szétbontani logikus, kisebb modulokra, mindegyiket jól dokumentálva.

## Új Mappastruktúra

```
napi-lelki-batyu/
├── lib/                              # Új modulok mappa
│   ├── __init__.py
│   ├── file_handler.py              # Fájlkezelés
│   ├── data_loader.py               # Adatok betöltése
│   ├── data_transformer.py          # Adattranszformáció
│   ├── reading_processor.py         # Olvasmánykereső
│   ├── part_processor.py            # Részek feldolgozása
│   └── error_handler.py             # Hibakezelés
├── generate.py                       # Főprogram (refaktorált)
├── generateparts.py                 # Részfeldolgozó (refaktorált)
├── sources/                         # Eredeti (változatlan)
├── readings/                        # Eredeti (változatlan)
├── batyuk/                          # Eredeti (változatlan)
└── ...
```

---

## Modulok Részletezése

### 1. `lib/file_handler.py`
**Felelőssége:** JSON fájlok írása és fájl-öregsség ellenőrzése

**Tartalmazza:**
- `writeDataFormattedJSONfile(data, filename, sort_keys=False, ensure_ascii=True)`
  - JSON fájlok formázott írása
  - Progress jelzés a konzolon
  
- `isFileOldOrMissing(filePath)`
  - Ellenőrzi, hogy fájl létezik-e
  - Ellenőrzi, hogy 1 óránál régebbi-e

---

### 2. `lib/data_loader.py`
**Felelőssége:** Különböző adatforrások betöltése

**Tartalmazza:**
- `downloadBreviarData(year)`
  - Zsolozsma naptárának letöltése XML-ből
  - Átalakítás JSON-ba
  
- `loadBreviarData(year)`
  - breviarData_yyyy.json betöltése
  
- `loadKatolikusData()`
  - readings/ JSON fájlok betöltése
  - vasA, vasB, vasC, olvasmanyok, szentek, custom, commentaries
  - Év-kódok hozzáadása (A/B/C)
  - Adatok összefésülése, ha több forrásból jön ugyanaz a kulcs

---

### 3. `lib/data_transformer.py`
**Felelőssége:** Adatok feldolgozása és transzformáció

**Tartalmazza:**
- `yearIorII(ABC, year, season, month=None)`
  - Liturgikus év páritásának megállapítása (I vagy II)
  - Naptári év alapján kalkulál
  
- `dayOfPenance(celebration)`
  - Megállapítja, hogy bűnbánati nap-e
  - 0 = nem, 1 = közönséges péntek, 2 = nagyböjti péntek, 3 = nagypéntek/hamvazószerda
  
- `transformCelebration(celebration, day)`
  - Breviar XML celebration → JSON struktura
  - Év-betű, év-paritás, heti sorszám, nap, szezon
  - VolumeOfBreviary megállapítása
  - Név generálása ha szükséges
  - Szín, típus, title feldolgozása
  - Communia kezelése
  
- `addCustomCelebrationstoBreviarData(data)`
  - Többrészes ünnepek feldolgozása (Karácsony, Húsvét, Pünkösd, stb.)
  - Extra celebration objektumok létrehozása
  
- `clearYearIorII(celebration)`
  - Év-paritás szerinti olvasmányok szűrése
  - II. évben az I. évbeli olvasmányok eltávolítása és fordítva
  
- `index_celebration_data(index_dayOfWeek, index_readingsId, index_name, calendarDay, lelkiBatyu)`
  - Indexek létrehozása nap, olvasmánykód, név alapján

---

### 4. `lib/reading_processor.py`
**Felelőssége:** Olvasmányok keresése és feldolgozása

**Tartalmazza:**
- `createReadingIds(celebration, day)`
  - Olvasmánykódok generálása regex alapján
  - Speciális esetek: Karácsony, Szűz Mária, Szekesegyház, stb.
  - Köznapi olvasmánykódok létrehozása
  
- `findReadings(celebration, katolikusData, lelkiBatyu)`
  - Levenshtein-távolsággal hasonló nevű olvasmányok keresése
  - Regex párosítás (speciális nevek)
  - Parts hozzáadása (teaser, commentary, image, stb.)
  
- `findCommentaries(celebration, katolikusData)`
  - Kommentárok és teasers keresése olvasmánykód alapján
  
- `addreadingstolevel10(celebration, katolususData)`
  - Kötelező emléknapokon (level 10, 11, 12) köznapi olvasmányok beillesztése
  - parts2-be kerül az alapértelmezés

---

### 5. `lib/part_processor.py`
**Felelőssége:** Olvasmányrészek feldolgozása

**Tartalmazza:**
- `partFromReading(text)`
  - HTML szöveg → JSON struktúra (saint_title, ref, teaser, title, text, ending)
  - Hosszabb/rövidebb forma kezelése
  - Olvasmány/evangélium/szentlecke felismerése
  - Teaser kinyerése (dőlt szöveg)
  
- `partFromPsalm(text)`
  - Zsoltár feldolgozása
  - Teaser = első sor

---

### 6. `lib/error_handler.py`
**Felelőssége:** Hibakezelés és hibanapló

**Tartalmazza:**
- `error(text, error_file='readings/errors.txt')`
  - Hibaüzenetek nyomtatása és naplózása
  - Időbélyeg hozzáadása

---

## Függvényhálózat

```
generate.py (főprogram)
├── data_loader.downloadBreviarData()
├── data_loader.loadBreviarData()
├── data_loader.loadKatolikusData()
├── data_transformer.transformCelebration()
│   └── data_transformer.yearIorII()
├── data_transformer.addCustomCelebrationstoBreviarData()
├── reading_processor.createReadingIds()
├── reading_processor.findReadings()
│   └── part_processor.partFromReading() 
│       └── part_processor.partFromPsalm()
├── reading_processor.findCommentaries()
├── reading_processor.addreadingstolevel10()
├── data_transformer.clearYearIorII()
├── data_transformer.dayOfPenance()
├── data_transformer.index_celebration_data()
└── file_handler.writeDataFormattedJSONfile()
└── file_handler.isFileOldOrMissing()

generateparts.py
├── data_loader.loadKatolikusData()
└── part_processor.partFromReading()
    └── part_processor.partFromPsalm()
```

---

## Dokumentációs Szabványok

### Docstring format
```python
def function_name(param1: str, param2: int) -> dict:
    """
    Rövid leírás egy sorban (mit csinál a függvény).
    
    Hosszabb leírás (opcionális): részletesebb magyarázat,
    ha szükséges értékek megértéséhez.
    
    Args:
        param1 (str): Paraméter leírása
        param2 (int): Paraméter leírása
    
    Returns:
        dict: Visszatérési érték leírása
        
    Raises:
        ValueError: Ha valami nincs jól
    
    Examples:
        >>> function_name("test", 42)
        {'result': 'ok'}
    """
```

### Inline kommentek
```python
# Fontos logika magyarázata, miért ez az érték
if condition:
    # A feltétel magyarázata
    do_something()
```

---

## Megvalósítási Lépések

1. ✅ Terv elkészítése (ez a fájl)
2. ⏳ Code módra váltás
3. ⏳ `lib/` mappa és `__init__.py` létrehozása
4. ⏳ `lib/error_handler.py` (legegyszerűbb)
5. ⏳ `lib/file_handler.py`
6. ⏳ `lib/data_loader.py`
7. ⏳ `lib/part_processor.py`
8. ⏳ `lib/data_transformer.py` (összetett)
9. ⏳ `lib/reading_processor.py` (összetett)
10. ⏳ `generate.py` refaktor (főprogram összeillesztése)
11. ⏳ `generateparts.py` refaktor
12. ⏳ Tesztelés

---

## Előnyök a Refaktorálás Után

✅ **Olvashatóság:** Minden modul ~30-50 sor, egyértelműen érthető  
✅ **Dokumentáció:** Minden függvénynél részletes docstring  
✅ **Karbantarthatóság:** Egyértelmű felelősségek  
✅ **Újrahasználhatóság:** Modulok máshol is importálhatók  
✅ **Hibakeresés:** Kisebb fájlokban könnyebb bugokat találni  
✅ **Teszt írásához:** Modulok külön tesztelhetők
