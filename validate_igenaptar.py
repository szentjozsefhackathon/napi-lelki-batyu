#!/usr/bin/env python3
"""
validate_igenaptar.py - Az igenaptar.json fájl validálása.

Ez a script ellenőrzi, hogy az igenaptar.json fájl:
1. Megvan-e (létezik-e az fájl)
2. Érvényes JSON-e (helyes szintaxis)
3. Megfelel-e az igenaptar-schema.json sémának

Típushibák vagy sémavégrehajtási hibák esetén a script exit code 1-gyel kilép.

Használat:
    python validate_igenaptar.py
    python validate_igenaptar.py --schema custom-schema.json
    python validate_igenaptar.py --igenaptar custom-igenaptar.json

Opciók:
    --igenaptar FILE : Az ellenőrizendő JSON fájl (alapértelmezés: batyuk/igenaptar.json)
    --schema FILE    : A JSON schema fájl (alapértelmezés: igenaptar-schema.json)
"""

import json
import sys
import argparse
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("HIBA: A jsonschema modul nincs telepítve.")
    print("Telepítse: pip install jsonschema")
    sys.exit(1)


def validate_igenaptar(igenaptar_path: str, schema_path: str) -> bool:
    """
    Az igenaptar.json fájl teljes validálása.
    
    Elvégzi a következő ellenőrzéseket:
    1. A fájl léte
    2. Érvényes JSON-e
    3. Megfelel-e az adott JSON schema-nak
    
    Args:
        igenaptar_path (str): Az igenaptar.json fájl elérési útja
        schema_path (str): Az igenaptar-schema.json fájl elérési útja
    
    Returns:
        bool: True, ha a validálás sikeres, False egyébként
    """
    print("=" * 60)
    print("NAPI LELKI BATYU - IGENAPTAR VALIDÁCIÓ")
    print("=" * 60 + "\n")
    
    # 1. Fájllétezés ellenőrzése
    print(f"1. Fájllétezés ellenőrzése: {igenaptar_path}")
    
    if not Path(igenaptar_path).exists():
        print(f"   ✗ HIBA: A fájl nem található: {igenaptar_path}")
        return False
    
    print(f"   ✓ A fájl létezik")
    
    # 2. JSON szintaxis ellenőrzése
    print(f"\n2. JSON szintaxis ellenőrzése")
    
    try:
        with open(igenaptar_path, 'r', encoding='utf-8') as f:
            igenaptar_data = json.load(f)
        print(f"   ✓ Érvényes JSON (cellan {len(igenaptar_data)} nap)")
    except json.JSONDecodeError as e:
        print(f"   ✗ HIBA: Hibás JSON szintaxis")
        print(f"      Hiba: {e}")
        print(f"      Sor: {e.lineno}, Oszlop: {e.colno}")
        return False
    except Exception as e:
        print(f"   ✗ HIBA: Fájl olvasási hiba")
        print(f"      {e}")
        return False
    
    # 3. Schema fájl betöltése
    print(f"\n3. Schema betöltése: {schema_path}")
    
    if not Path(schema_path).exists():
        print(f"   ✗ HIBA: A schema fájl nem található: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        print(f"   ✓ Schema sikeresen betöltve")
    except json.JSONDecodeError as e:
        print(f"   ✗ HIBA: A schema JSON szintaxisa hibás")
        print(f"      {e}")
        return False
    except Exception as e:
        print(f"   ✗ HIBA: Schema fájl olvasási hiba")
        print(f"      {e}")
        return False
    
    # 4. Schema validálása
    print(f"\n4. Schema szerinti validálás")
    
    try:
        jsonschema.validate(instance=igenaptar_data, schema=schema_data)
        print(f"   ✓ A JSON megfelel a sémának")
    except jsonschema.ValidationError as e:
        print(f"   ✗ HIBA: Sémavégrehajtási hiba")
        print(f"      Üzenet: {e.message}")
        print(f"      Elérési út: {list(e.path)}")
        print(f"      Hiba típusa: {e.validator}")
        return False
    except jsonschema.SchemaError as e:
        print(f"   ✗ HIBA: A schema maga hibás")
        print(f"      {e}")
        return False
    except Exception as e:
        print(f"   ✗ HIBA: Ismeretlen validálási hiba")
        print(f"      {e}")
        return False
    
    # 5. Alapvető tartalom-ellenőrzések
    print(f"\n5. Tartalom-ellenőrzések")
    
    error_count = 0
    warning_count = 0
    
    # Napok ellenőrzése
    day_count = len(igenaptar_data)
    print(f"   - Napok száma: {day_count}")
    
    if day_count == 0:
        print(f"   ✗ HIBA: Nincsenek napok az igenaptárban")
        error_count += 1
    elif day_count < 300:
        print(f"   ✗ HIBA: Túl kevés nap ({day_count}, minimum 300 elvárt)")
        error_count += 1
    else:
        print(f"   ✓ Napok száma elfogadható")
    
    # Ünnepek ellenőrzése
    total_celebrations = 0
    days_without_celebrations = 0
    
    for date_str, day_data in igenaptar_data.items():
        if 'celebration' not in day_data:
            days_without_celebrations += 1
        else:
            total_celebrations += len(day_data['celebration'])
    
    print(f"   - Összes ünnep: {total_celebrations}")
    print(f"   - Napi átlag: {total_celebrations / day_count:.1f} ünnep/nap")
    
    if days_without_celebrations > 0:
        print(f"   ✗ HIBA: {days_without_celebrations} nap ünnep nélkül")
        error_count += 1
    else:
        print(f"   ✓ Minden nap ünneppel")
    
    # Olvasmányok ellenőrzése
    celebrations_with_readings = 0
    celebrations_without_readings = 0
    
    for date_str, day_data in igenaptar_data.items():
        for celebration in day_data.get('celebration', []):
            if 'parts' in celebration and celebration['parts']:
                celebrations_with_readings += 1
            else:
                celebrations_without_readings += 1
    
    print(f"   - Olvasmányokkal rendelkező ünnepek: {celebrations_with_readings}")
    print(f"   - Olvasmányok nélküli ünnepek: {celebrations_without_readings}")
    
    if celebrations_without_readings > 0:
        print(f"   ⚠ FIGYELMEZTETÉS: {celebrations_without_readings} ünnepnek nincs olvasmánya")
        warning_count += 1
    
    # 6. Összefoglalás
    print(f"\n" + "=" * 60)
    
    if error_count > 0:
        print(f"EREDMÉNY: SIKERTELEN ✗")
        print(f"Hibák: {error_count}, Figyelmeztetések: {warning_count}")
        print("=" * 60)
        return False
    else:
        print(f"EREDMÉNY: SIKERES ✓")
        if warning_count > 0:
            print(f"Figyelmeztetések: {warning_count}")
        print("=" * 60)
        return True


def main():
    """
    Főprogram: parancssori argumentumok feldolgozása és validálás indítása.
    """
    parser = argparse.ArgumentParser(
        description='Az igenaptar.json fájl validálása'
    )
    parser.add_argument(
        '--igenaptar',
        default='batyuk/igenaptar.json',
        help='Az igenaptar.json fájl elérési útja (alapértelmezés: batyuk/igenaptar.json)'
    )
    parser.add_argument(
        '--schema',
        default='igenaptar-schema.json',
        help='Az igenaptar-schema.json fájl elérési útja (alapértelmezés: igenaptar-schema.json)'
    )
    
    args = parser.parse_args()
    
    # Validálás futtatása
    success = validate_igenaptar(args.igenaptar, args.schema)
    
    # Exit code beállítása
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
