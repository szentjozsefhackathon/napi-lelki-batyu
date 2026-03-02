# Python Kód Refaktorálás - Összefoglaló

## ✅ Befejezett Refaktorálás

A "Napi Lelki Batyú" projekt Python kódja sikeresen átszervezésre és dokumentálásra került.

---

## 📁 Új Mappastruktúra

```
napi-lelki-batyu/
├── lib/                              # ← ÚJ: feldolgozási modulok
│   ├── __init__.py
│   ├── error_handler.py              # Hibakezelés
│   ├── file_handler.py               # Fájl I/O
│   ├── data_loader.py                # Adatok betöltése
│   ├── data_transformer.py           # Adatok feldolgozása
│   ├── reading_processor.py          # Olvasmánykereső
│   └── part_processor.py             # Részfeldolgozás
├── generate.py                       # ← REFAKTORÁLT: főprogram
├── generateparts.py                  # ← REFAKTORÁLT: CSV feldolgozó
├── sources/                          # Eredeti (változatlan)
├── readings/                         # Eredeti (változatlan)
├── batyuk/                           # Eredeti (változatlan)
├── REFACTOR_PLAN.md                  # Részletes terv
└── REFACTOR_SUMMARY.md              # Ez a fájl
```

---

## 📚 Modulok Leírása

### 🔴 `lib/error_handler.py` (20 sor)
**Hibakezelés és naplózás**

```python
from lib.error_handler import error

error("Valami gond van az olvasmánnyal")
# → konzolra: "Valami gond van az olvasmánnyal"
# → readings/errors.txt-be: "[2024-03-02 21:00:00] Valami gond van az olvasmánnyal"
```

**Függvények:**
- `error(text, error_file)` - Hiba naplózása

---

### 📝 `lib/file_handler.py` (70 sor)
**Fájlkezelés és JSON írás**

```python
from lib import file_handler

# JSON formázott írása
file_handler.writeDataFormattedJSONfile(data, "batyuk/2024.json")
# → Write batyuk/2024.json... OK

# Fájl öregsség ellenőrzése
if file_handler.isFileOldOrMissing("breviarData_2024.json"):
    # → A fájl 1 óránál régebbi vagy nem létezik
    download_new_data()
```

**Függvények:**
- `writeDataFormattedJSONfile(data, filename, sort_keys=False, ensure_ascii=True)` - JSON mentése
- `isFileOldOrMissing(file_path, max_age_seconds=3600)` - Fájl öregsség ellenőrzése

---

### 🌐 `lib/data_loader.py` (190 sor)
**Adatok betöltése külső forrásokból**

```python
from lib import data_loader

# Zsolozsma XML letöltése
data_loader.downloadBreviarData(2024)
# → breviarData_2024.json letöltve és mentve

# Zsolozsma betöltése
breviar = data_loader.loadBreviarData(2024)
# → dict objektum az összes napi adattal

# Readings betöltése
readings = data_loader.loadKatolikusData()
# → dict az összes olvasmánnyal (vasA, vasB, vasC, stb.)
```

**Függvények:**
- `downloadBreviarData(year)` - Zsolozsma XML letöltése
- `loadBreviarData(year)` - Zsolozsma JSON betöltése
- `loadKatolikusData()` - Readings JSON betöltése

---

### 🔄 `lib/data_transformer.py` (380 sor)
**Adatok feldolgozása és transzformáció**

Ez a modul a legösszetettebb. Az XML celebration objektumokat feldolgozza,
év-páritást számol, és indexeket épít.

```python
from lib import data_transformer

# Év-paritás megállapítása (I vagy II)
parity = data_transformer.yearIorII("C", 2024, "5")  # → "I"

# Bűnbánati nap szintje
penance_level = data_transformer.dayOfPenance(celebration)  # → 0, 1, 2, 3

# Celebration transzformálása XML-ből
transformed = data_transformer.transformCelebration(xml_celebration, day)

# Speciális ünnepek szétbontása (Karácsony, Húsvét, Pünkösd)
data_transformer.addCustomCelebrationstoBreviarData(lelki_batyu)

# Év szerinti olvasmányok szűrése (I. év → I. évi olvasmányok)
data_transformer.clearYearIorII(celebration)

# Indexek építése
data_transformer.index_celebration_data(
    index_dayofweek, index_readings_id, index_name,
    calendar_day, lelki_batyu
)
```

**Függvények:**
- `yearIorII(abc, year, season, month=None)` - Év-paritás
- `dayOfPenance(celebration)` - Bűnbánati nap szintje
- `transformCelebration(celebration, day)` - XML → JSON
- `addCustomCelebrationstoBreviarData(lelki_batyu)` - Speciális ünnepek
- `clearYearIorII(celebration)` - Év-szűrés
- `index_celebration_data(...)` - Indexek építése

---

### 🔎 `lib/reading_processor.py` (450 sor)
**Olvasmányok keresése és feldolgozása**

Az egyik legbonyolultabb modul. Az olvasmánykódokat generálja és
a readings szótárban megtalálja az olvasmányokat.

```python
from lib import reading_processor

# Olvasmánykódok generálása
reading_processor.createReadingIds(celebration, day)
# → celebration['readingsId'] = "EVK011Hetfo"

# Olvasmányok keresése fuzzy matching-gel
reading_processor.findReadings(celebration, readings_data, lelki_batyu)
# → celebration['parts'] = [...]

# Kommentárok keresése
reading_processor.findCommentaries(celebration, readings_data)
# → celebration['teaser'] = "..."

# Köznapi olvasmányok hozzáadása (level 10, 11, 12)
reading_processor.addreadingstolevel10(celebration, readings_data)
# → celebration['parts2'] = [...]
```

**Függvények:**
- `createReadingIds(celebration, day)` - Olvasmánykódok generálása
- `findReadings(celebration, readings_data, lelki_batyu)` - Keresés fuzzy match-gel
- `findCommentaries(celebration, readings_data)` - Kommentárok keresése
- `addreadingstolevel10(celebration, readings_data)` - Köznapok hozzáadása

---

### 📖 `lib/part_processor.py` (210 sor)
**Olvasmányrészek feldolgozása**

A HTML formátumú szövegeket strukturált JSON objektumokká alakítja.

```python
from lib import part_processor

# Olvasmány feldolgozása
part = part_processor.partFromReading(html_text, "01-15")
# → {
#     "short_title": "evangélium",
#     "ref": "Mt 5:1-12",
#     "teaser": "Amikor Jézus felment a hegyre...",
#     "title": "EVANGÉLIUM",
#     "text": "Amikor Jézus felment a hegyre...",
#     "ending": "Ezek az evangélium igéi."
# }

# Zsoltár feldolgozása
psalm = part_processor.partFromPsalm(html_psalm)
# → {
#     "short_title": "zsoltár",
#     "teaser": "ZSOLTÁR 23",
#     "text": "Az Úr az én pásztorom..."
# }
```

**Függvények:**
- `partFromReading(text, reading_id)` - Olvasmány feldolgozása
- `partFromPsalm(text)` - Zsoltár feldolgozása

---

## 🚀 Főprogramok

### `generate.py` (200 sor)
**Napi lelki batyú generátor**

Használat:
```bash
# Mostani év
python generate.py

# Konkrét év
python generate.py --year 2024

# Jövő év is
python generate.py --year 2024 --do-next-year

# Előző 3 év is
python generate.py --year 2024 --previous-years 3
```

Kimenet:
- `batyuk/2024.json` - Teljes év (komplex verzió, parts feldolgozva)
- `batyuk/2024_simple.json` - Teljes év (egyszerű verzió)
- `batyuk/2024_index.json` - Indexek (nap, olvasmánykód, ünnep név)
- `batyuk/2024-01-15.json` - Egy nap (minden ünneppel)
- `batyuk/igenaptar.json` - Szűrt verzió (30 nap múlt + 365 nap jövő)

---

### `generateparts.py` (250 sor)
**CSV feldolgozó (fejlesztéshez)**

⚠️ **FIGYELMEZTETÉS:** Ez az script csak fejlesztési céllal hasznos!
A `readings/` mappában kézzel finomított adatok vannak.

Használat:
```bash
python generateparts.py
```

Ez feldolgozza a `sources/*.csv` fájlokat és generálja a `readings/*.json` fájlokat.
De mivel a readings mappában már vannak kézzel tisztított adatok, ezt
csak akkor szabad futtatni, ha tudod, mit csinálsz!

---

## 💡 Előnyök a Refaktorálás Után

### ✅ Olvashatóság
- Minden modul ~30-50 sor (part_processor) - ~450 sor (reading_processor) között van
- Egyértelmű nevet viselnek a függvények
- Minden függvénynél van részletes docstring

### ✅ Dokumentáció
- Modulok docstring-je elmagyarázza, mi a feladata
- Függvények docstring-je tartalmazza az argumentumokat, visszatérési értékeket, és példákat
- Inline kommentek magyarázzák a bonyolultabb részeket

### ✅ Karbantarthatóság
- Egyértelmű szeparáció a felelősségek között
- Egy bug keresése sokkal gyorsabb egy 50-soros fájlban, mint egy 700-soros fájlban
- Könnyebb módosításokat eszközölni (pl. egy új olvasmánytípus)

### ✅ Újrahasználhatóság
- A modulok egymástól függetlenül importálhatók
- Más projectek is felhasználhatják a `part_processor`-t vagy a `file_handler`-t

### ✅ Teszt írásához
- Minden modul külön tesztelhetővé vált
- Könnyebb unit testeket írni

### ✅ Type hints (típusjelzések)
- Minden függvénynél vannak típusjelzések
- IDE-ből könnyebb kódkiegészítés

---

## 🔗 Függőségi Grafikon

```
generate.py (főprogram)
├── file_handler
│   └── (JSON írás)
├── data_loader
│   ├── file_handler
│   └── error_handler
├── data_transformer
│   └── (adatfeldolgozás, no external dependencies)
├── reading_processor
│   ├── error_handler
│   └── Levenshtein (külső lib)
└── error_handler

generateparts.py (CSV feldolgozó)
├── part_processor
│   └── error_handler
├── error_handler
└── Levenshtein (külső lib)
```

---

## 📖 Használati Minták

### 1. Egy év teljes feldolgozása
```python
from lib import data_loader, data_transformer, reading_processor, file_handler

# Adatok betöltése
breviar = data_loader.loadBreviarData(2024)
readings = data_loader.loadKatolikusData()

# Egy nap feldolgozása
for day in breviar['LHData']['CalendarDay'][:1]:  # Csak az első nap
    for celebration in day['Celebration']:
        # Transzformálás
        cel = data_transformer.transformCelebration(celebration, day)
        
        # Olvasmánykódok
        reading_processor.createReadingIds(cel, day)
        
        # Olvasmányok keresése
        reading_processor.findReadings(cel, readings, {'date': {}})
        
        print(f"{cel['name']}: {cel.get('readingsId', 'N/A')}")
```

### 2. Csak egy nap betöltése fájlból
```python
import json

with open("batyuk/2024-01-15.json") as f:
    day_data = json.load(f)

print(f"Nap: {day_data['date']['dayofWeekText']}")

for celebration in day_data['celebration']:
    print(f"  - {celebration['name']} ({celebration['level']})")
```

### 3. Index használata
```python
import json

with open("batyuk/2024_index.json") as f:
    index = json.load(f)

# Advent 1. vasárnap keresése
key = "0-1-0"  # szezon-hét-nap
dates = index['seasonWeekDayofWeek'].get(key, [])
print(f"Advent 1. vasárnap: {dates}")
```

---

## 🧪 Tesztelés

A modulok teszteléséhez:

```python
import unittest
from lib import file_handler, data_transformer

class TestFileHandler(unittest.TestCase):
    def test_writeDataFormattedJSONfile(self):
        data = {'test': 'data'}
        file_handler.writeDataFormattedJSONfile(data, 'test.json')
        # Ellenőrzés...

class TestYearIorII(unittest.TestCase):
    def test_year_parity(self):
        assert data_transformer.yearIorII("C", 2024, "5") == "I"
        assert data_transformer.yearIorII("A", 2025, "0") == "II"

if __name__ == '__main__':
    unittest.main()
```

---

## 🎯 Következő Lépések

1. **Teszt suite készítése** - unittest-ekben a modulok teszteléséhez
2. **Type hints finomítása** - Több specifikus type hint (Union, Optional, stb.)
3. **Dokumentáció folytatása** - README.md frissítése
4. **Performance optimalizálás** - Levenshtein távolság cachelése
5. **Konfigurációs fájl** - Konstansok externalizálása (year mappings, stb.)

---

## 📞 Kérdések?

Ha bármilyen kérdés van a refaktorálással kapcsolatban:

1. **Olvashatóság:** Minden docstring-nél vannak példák
2. **Függvények:** Type hints-ek mutatják az input/output formátumot
3. **Hibák:** error_handler.error() függvénnyel logozz
4. **Adatok:** data_transformer.py-ban vannak az átalakítási szabályok

---

**Szépítést végzete: 2026-03-02**
