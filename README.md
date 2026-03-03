# 🙏 Napi Lelki Batyu

[![Deploy Static Content](https://github.com/szentjozsefhackathon/napi-lelki-batyu/actions/workflows/static.yml/badge.svg)](https://github.com/szentjozsefhackathon/napi-lelki-batyu/actions/workflows/static.yml)
[![JSON/YAML Validate](https://github.com/szentjozsefhackathon/napi-lelki-batyu/actions/workflows/json-validate.yml/badge.svg)](https://github.com/szentjozsefhackathon/napi-lelki-batyu/actions/workflows/json-validate.yml)

https://szentjozsefhackathon.github.io/napi-lelki-batyu/

Minden napra megadja a napi szenteket, olvasmányokat, liturgikus információkat és imádságokat.

---

## 🚀 Gyors Indítás

### 1. Függőségek Telepítése
```bash
pip install -r requirements.txt
```

### 2. Egy Év Feldolgozása
```bash
# Mostani év
python generate.py

# Konkrét év (pl. 2024)
python generate.py --year 2024

# Jövő év is
python generate.py --year 2024 --do-next-year

# Előző 3 év is
python generate.py --year 2024 --previous-years 3
```

### 3. Igenaptar Validálása
```bash
# Alapértelmezett elérési utakkal
python validate_igenaptar.py [ --igenaptar batyuk/igenaptar.json --schema igenaptar-schema.json ]
```

Ez a script ellenőrzi:
- ✓ Az `igenaptar.json` fájl léte
- ✓ Érvényes JSON szintaxis
- ✓ Megfelel-e az `igenaptar-schema.json` JSON Schema-nak
- ✓ Tartalom-ellenőrzések (napok száma, ünnepek, olvasmányok)

### 4. Várt Kimenet
Sikeresen feldolgozás után a `batyuk/` mappában találod:

| Fájl | Tartalom | Felhasználás |
|------|----------|--------------|
| `2024.json` | Teljes év, parts feldolgozva (típusjelzések) | Backend API-hoz |
| `2024_simple.json` | Teljes év, egyszerű verzió | Archívumhoz |
| `2024_index.json` | Indexek (nap, olvasmánykód, név) | Gyors kereséshez |
| `2024-01-15.json` | Egy nap minden ünnepe | Frontend |
| `igenaptar.json` | Szűrt verzió (30 nap múlt + 365 jövő) | Frontend (ma + körül) |

---

## 📚 Backend API

### Kimeneti Fájlformátum

A `batyuk/2024.json` vagy `batyuk/2024-01-15.json` fájlok ebben a formátumban adják az adatokat.

#### Legfelső szint - Egyéves adat

```json
{
  "2024-01-01": { "date": {...}, "celebration": [...] },
  "2024-01-02": { "date": {...}, "celebration": [...] },
  ...
  "2024-12-31": { "date": {...}, "celebration": [...] }
}
```

---

#### 📅 Date Object (Naptári adatok)

Minden naphoz tartozó, liturgiástól független alapinformációk:

```json
{
  "ISO": "2024-01-15",          // ISO dátum (éééé-hh-nn)
  "dayOfYear": "15",             // Az év hányadik napja (január 1 = 1)
  "dayofWeek": "1",              // A hét napja (vasárnap=0, hétfő=1, ... szombat=6)
  "dayofWeekText": "hétfő"       // Nap neve betűvel
}
```

---

#### ⛪ Celebration Object (Ünnep/Liturgia)

Az adott nap liturgikus információi és olvasmányai:

```json
{
  "dateISO": "2024-01-15",                      // Naptári dátum
  "yearLetter": "A",                            // Liturgikus év betűje (A, B, C)
  "yearParity": "II",                           // Év paritása (I vagy II köznapokhoz)
  "week": "2",                                  // Heti sorszám az adott időszakban
  "dayofWeek": 1,                               // A hét napja (szám)
  "weekOfPsalter": "2",                         // A zsolozsmában használt zsoltáros hét (1-4)
  
  "season": "5",                                // Liturgikus időszak azonosítója
  "seasonText": "évközi idő",                   // Időszak megnevezése
  "typeLocal": null,                            // Helyi liturgikus megjegyzés (ha van)
  "level": "13",                                // Az ünnep rangja (1-13, 1=legmagasabb)
  "required": "1",                              // Kötelezőség (0 vagy 1)
  
  "name": "évközi idő 2. hét, hétfő",           // Az ünnep/köznap megnevezése
  "title": "évközi idő 2. hét, hétfő",          // A kijelzendő cím (name + rang info)
  "celebrationType": "köznap",                  // Az ünnep típusa (köznap, főünnep, ünnep, emléknap, stb.)
  
  "readingsBreviarId": "1A1",                   // Az XML-ből jövő olvasmánykód (belső)
  "readingsId": "ADV011Hetfo",                  // A readers/...json-ekben keresett kód
  "ferialReadingsId": "01-01",                  // Az opcionális köznapok olvasmányainak kódja
  
  "volumeOfBreviary": "III",                    // A 4 kötetes zsolozsma hanyadik kötete (I, II, III, IV)
  "colorId": "3",                               // Liturgikus szín azonosítója
  "colorText": "zöld",                          // Liturgikus szín megnevezése
  "comunia": null,                              // Közös részek hivatkozása (null vagy lista)
  
  "celebrationKey": 0,                          // Ha több ünnep van egy napon, a sorszáma
  "dayOfPenance": 0,                            // Bűnbánati nap szintje (0=nem, 1=péntek, 2=nagyböjti, 3=nagypéntek/hamvazószerda)
  
  "parts": [...],                               // Az ünnep olvasmányai (lent)
  "parts2": [...],                              // Opcionális: alternatív olvasmányok (opcionális emléknapokon)
  "parts2cause": "(Vagy) saját olvasmányok",   // A parts2 magyarázata
  
  "teaser": "...",                              // Az ünnep rövid bemutatása (opcionális)
  "commentary": {...},                          // Az ünnepre vonatkozó kommentár (opcionális)
  "image": "..."                                // Az ünnep képe (opcionális)
}
```

---

#### 📖 Parts Array (Olvasmányok)

Az ünnephez tartozó olvasmányrészek (evangélium, Szent Lecke, zsoltár, stb.):

```json
[
  {
    "type": "object",                          // Típus: "object" vagy "array"
    "short_title": "evangélium",               // Rész típusa: evangélium, olvasmány, szentlecke, zsoltár, passió
    "title": "EVANGÉLIUM Máté 1:1-17",        // Rész címe
    "ref": "Mt 1:1-17",                       // Bibliográfiai referencia
    "teaser": "Jézus Krisztus nemzetségtáblázata...",  // Rövid kivonat az elején
    "text": "Abraham nemzetsége: Abraham atya volt Izsák atyja...",  // A teljes szöveg
    "ending": "Ezek az evangélium igéi."      // A záró formula
  },
  
  // Ha egy rész több verzióban van (I. és II. év):
  {
    "type": "array",                          // Array típus
    "content": [
      {
        "type": "object",
        "short_title": "olvasmány",
        "title": "1. OLVASMÁNY – I. ÉVBEN",
        "ref": "1Kor 2:1-5",
        "text": "...",
        "cause": "I. évben"                   // A verzió megjelölése
      },
      {
        "type": "object",
        "short_title": "olvasmány",
        "title": "1. OLVASMÁNY – II. ÉVBEN",
        "ref": "2Kor 1:3-7",
        "text": "...",
        "cause": "II. évben"
      }
    ]
  }
]
```

---

## 🏗️ Fejlesztői Dokumentáció

### Mappastruktúra

```
napi-lelki-batyu/
├── lib/                          # Feldolgozási modulok (REFAKTORÁLT)
│   ├── error_handler.py         # Hibakezelés és naplózás
│   ├── file_handler.py          # JSON fájlkezelés
│   ├── data_loader.py           # XML/JSON adatok betöltése
│   ├── data_transformer.py      # Adattranszformáció és feldolgozás
│   ├── reading_processor.py     # Olvasmánykereső
│   └── part_processor.py        # HTML olvasmányrészek feldolgozása
│
├── sources/                      # Eredeti CSV adatok
│   ├── vasA.csv, vasB.csv, vasC.csv        # Vasárnapi olvasmányok (A, B, C év)
│   ├── olvasmanyok.csv                     # Hétköznapi olvasmányok (I-II év)
│   ├── szentek.csv                         # Szentek saját olvasmányai
│   └── saint.csv                           # Angol nyelvű saint adatok
│
├── readings/                     # Feldolgozott JSON olvasmányok
│   ├── vasA.json, vasB.json, vasC.json    # Feldolgozott vasárnapi olvasmányok
│   ├── olvasmanyok.json                    # Feldolgozott hétköznapi olvasmányok
│   ├── szentek.json                        # Feldolgozott szentek
│   ├── commentaries.json                   # Kommentárok
│   └── errors.txt                          # Feldolgozási hibák napló
│
├── batyuk/                       # Generált kimeneti JSON fájlok
│   ├── 2024.json                           # Teljes év (komplex, types-elhöz)
│   ├── 2024_simple.json                    # Teljes év (egyszerű)
│   ├── 2024_index.json                     # Indexek (gyors kereséshez)
│   ├── 2024-01-15.json                     # Egy nap minden ünnepe
│   ├── igenaptar.json                      # Szűrt verzió (frontend számára)
│   └── ... (sok 2024-XX-XX.json fájl)
│
├── generate.py                   # Főprogram: napi lelki batyu generálása
├── generateparts.py              # CSV feldolgozó (fejlesztéshez)
├── validate_igenaptar.py         # Igenaptar validáló script
├── igenaptar-schema.json         # JSON Schema az igenaptar.json-hez
├── REFACTOR_PLAN.md             # Refaktorálási terv
├── REFACTOR_SUMMARY.md          # Refaktorálás összefoglalója
└── README.md                     # Ez a fájl
```

### Feldolgozási Folyamat

```
1. XML LETÖLTÉS
   breviar.kbs.sk → breviarData_2024.json

2. ADATOK BETÖLTÉSE
   ├─ breviarData_2024.json → XML → dict
   └─ readings/*.json → dict

3. NAPI FELDOLGOZÁS (minden napra)
   ├─ XML celebration → dict (transformCelebration)
   ├─ Speciális ünnepek szétbontása (karácsony, húsvét)
   ├─ Olvasmánykódok generálása (regex alapján)
   ├─ Olvasmányok keresése (fuzzy matching)
   ├─ Kommentárok keresése
   ├─ Év-paritás szerinti szűrés
   └─ Parts feldolgozása (HTML → JSON)

4. FÁJLOK MENTÉSE
   ├─ batyuk/YYYY-MM-DD.json (minden nap)
   ├─ batyuk/YYYY.json (teljes év)
   ├─ batyuk/YYYY_simple.json (egyszerű verzió)
   ├─ batyuk/YYYY_index.json (indexek)
   └─ batyuk/igenaptar.json (szűrt verzió)

5. FRONTEND ÁLTAL HASZNÁLT FÁJLOK
   ├─ batyuk/igenaptar.json (30 nap múlt + 365 nap jövő)
   └─ batyuk/YYYY-MM-DD.json (konkrét nap)
```

### API Modulok

#### 📦 `lib.file_handler`
```python
from lib import file_handler

# JSON formázott mentése
file_handler.writeDataFormattedJSONfile(data, "batyuk/2024.json")

# Fájl öregsség ellenőrzése (1 óránál régebbi?)
if file_handler.isFileOldOrMissing("breviarData_2024.json"):
    download_new_data()
```

#### 📦 `lib.data_loader`
```python
from lib import data_loader

# Zsolozsma XML letöltése és JSON-ba konvertálása
data_loader.downloadBreviarData(2024)

# Zsolozsma JSON betöltése
breviar = data_loader.loadBreviarData(2024)

# Readings JSON betöltése
readings = data_loader.loadKatolikusData()
```

#### 📦 `lib.data_transformer`
```python
from lib import data_transformer

# Év-paritás (I vagy II)
parity = data_transformer.yearIorII("C", 2024, "5")  # → "I"

# Bűnbánati nap szintje
level = data_transformer.dayOfPenance(celebration)  # → 0-3

# XML celebration transzformálása
cel = data_transformer.transformCelebration(xml_cel, day)

# Indexek építése
data_transformer.index_celebration_data(...)
```

#### 📦 `lib.reading_processor`
```python
from lib import reading_processor

# Olvasmánykódok generálása
reading_processor.createReadingIds(celebration, day)

# Olvasmányok keresése
reading_processor.findReadings(celebration, readings, lelki_batyu)

# Kommentárok keresése
reading_processor.findCommentaries(celebration, readings)

# Köznapok olvasmányai hozzáadása
reading_processor.addreadingstolevel10(celebration, readings)
```

#### 📦 `lib.part_processor`
```python
from lib import part_processor

# HTML olvasmány feldolgozása
part = part_processor.partFromReading(html_text, "01-15")

# HTML zsoltár feldolgozása
psalm = part_processor.partFromPsalm(html_psalm)
```

---

## 🔧 Fejlesztés

### CSV → JSON Feldolgozás (generateparts.py)

⚠️ **FIGYELMEZTETÉS:** A `readings/` mappában kézzel finomított adatok vannak! Csak akkor futtasd ezt, ha új CSV adatok érkeztek!

```bash
python generateparts.py
```

Ez feldolgozza a `sources/*.csv` fájlokat és generálja a `readings/*.json` fájlokat.

### Hibakezelés és Biztonsági Lépések

#### 🚨 JSON Validálás

A `generate.py` futtatása után **kötelezően** futtasd a validálást:

```bash
python validate_igenaptar.py
```

Ez megvédi az alkalmazást attól, hogy hibás adatok kerüljenek az igenaptar.json-ba.

#### 📋 Validálási Lépések

1. **Fájllétezés**: Ellenőrzi, hogy az `igenaptar.json` fájl megvan-e
2. **JSON Szintaxis**: Biztosítja, hogy a fájl érvényes JSON
3. **Schema Validálás**: Ellenőrzi, hogy a JSON megfelel a `igenaptar-schema.json` sémának
4. **Tartalom-ellenőrzések**:
   - Napok száma (minimum 300 elvárás)
   - Minden naphoz van-e ünnep
   - Ünnepekhez vannak-e olvasmányok

#### ⚠️ Hibakezelés

**JSON Decode Hibák leállítják az alkalmazást:**

Ha a JSON betöltésénél hiba lép fel (szintaxis, típushiba, stb.), az alkalmazás:
1. Kiír egy **KRITIKUS HIBA** üzenetet
2. **Naplózza** a hibát az `readings/errors.txt` fájlba
3. **Leállítódik** `exit(1)` kóddal

Ez biztosítja, hogy hibás adatok ne kerüljenek a rendszerbe.

#### 🤖 GitHub Actions Integráció

A GitHub Actions workflow **automatikus** biztonsági ellenőrzéseket végez:

```yaml
# .github/workflows/static.yml

- name: Run script
  run: python generate.py
  continue-on-error: false        # Ha hiba, workflow leállítódik

- name: Validate igenaptar.json
  run: python validate_igenaptar.py
  continue-on-error: false        # Ha validáció fails, workflow leállítódik
```

**Ez azt jelenti:**
- Ha a `generate.py` hiba kóddal kilép, az Actions fails
- Ha az `igenaptar.json` nem valid, az Actions fails
- **Hibás adat nem fog publikálódni a GitHub Pages-en**

#### 🔍 Hibakeresés

A feldolgozás közben fellépő hibák több helyen találhatók:

1. **Konzolon** - Valós idejű hibaüzenetek
2. **`readings/errors.txt`** - Feldolgozási hibák naplója:
   ```
   2024-03-02 21:00:00.123456 -- Ez az olvasmánykód (ABC123) hiányzik a kulcsok között...
   ```
3. **GitHub Actions** - Actions run sikertelen lesz, ha hiba van

---

## 📋 Liturgikus Szezonok

| ID | Megnevezés | Kötet |
|----|------------|-------|
| 0-1 | Advent I-II | I |
| 2-4 | Karácsony, Karácsony nyolcada, Karácsony II | I |
| 5 | Évközi idő | III |
| 6 | Nagyböjti idő | II |
| 7-9 | Húsvét előtti napok, Húsvét nyolcada | II |
| 10-11 | Húsvéti idő I-II | II |

---

## 📊 Ünnepek Rangja (Level)

| Level | Típus | Olvasmányok |
|-------|-------|------------|
| 1-4 | Főünnep | Saját |
| 5-8 | Ünnep | Saját |
| 9 | Emléknap | Saját |
| 10-12 | Kötelező emléknap | Köznapok + saját (választható) |
| 13 | Köznap | Szezonhoz kötött köznapok |

---

## 🎨 Liturgikus Szín

| ID | Szín |
|----|------|
| 1 | Piros (mártírok, adventus) |
| 2 | Fehér (ünnepek, karácsony) |
| 3 | Zöld (évközi idő) |
| 4 | Lila (nagyböjt, advent) |
| 5 | Rózsaszín (Advent 3. vasárnap, nagyböjt 4. vasárnap) |
| 6 | Fekete (halottak napja) |
| 9 | Rózsaszín\|Lila (választható) |

---

## 💾 Adatforrások

- **Breviar:** https://breviar.kbs.sk/ (XML - digitális zsolozsma)
- **Readings:** `sources/*.csv` (igenaptar.katolikus.hu adatbázis)
- **Commentaries:** `readings/commentaries.json` (saját és egyházi források)

---

## 🌐 Frontend Felhasználás

### Naptar Nézet
https://szentjozsefhackathon.github.io/napi-lelki-batyu/naptar.html

Egy éves összefoglaló az összes ünneppel, olvasmánnyal és bűnbánati napokkal.

### Napi Nézet
https://szentjozsefhackathon.github.io/napi-lelki-batyu/?date=2024-06-30

A konkrét napon lévő összes ünnep, olvasmány és imádság egy helyen.

---

## 📝 Publicálás

Az adatok nyilvánosan használhatók:

```
https://szentjozsefhackathon.github.io/napi-lelki-batyu/[ÉÉÉÉ].json
https://szentjozsefhackathon.github.io/napi-lelki-batyu/[ÉÉÉÉ]-HH-NN.json
```

Javasolt: KAPP, egyéb liturgikus applikációk, egyházi oldalak.

---

## 📞 Technikai Részletek

- **Függőségek:** `requests`, `xmltodict`, `Levenshtein`, `jsonschema`
- **Python verzió:** 3.8+
- **Karakterkódolás:** UTF-8
- **Típusjelzések:** Type hints az összes függvénynél

Az egész projekt **jól dokumentált, moduláris és könnyűen bővíthető**!

---

**Utolsó frissítés:** 2026-03-03
