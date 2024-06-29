# napi-lelki-batyu

https://szentjozsefhackathon.github.io/napi-lelki-batyu/

Minden napra megadja a napi szenteket, olvasmányokat, liturgikus információkat

## Backend: [éééé.json](https://szentjozsefhackathon.github.io/napi-lelki-batyu/2024.json)

- A [readings](readings/) mappában vannak json formába rendezve a liturgiákon használt olvasmányos könyvek. Vasárnapi A, B és C, továbbá hétköznapi olvasmányok I-II (egyben), valamint a szentek saját olvasmányai.
- A ```python generate.py```
     - beolvassa a digitális zsolozsma XML formátumú igenaptárját a teljes évre (breviarData.json fájlba)
     - megpróbálja megkeresni minden nap minden ünnepére/emléknapjára/liturgiájára a readings/....json fáljok közül a megfelelőből a megfelelő sorokat
     - kicsit rendezi az opciókat
     - és legyártja a kimeneti json fájlokat a batyuk/ mappába ( [éééé-hh-nn].json, [éééé].json, [éééé]_simple.json )
     - majd a frontendet is: batyuk/index.html, batyuk/naptar.html

Nyilvános felszanálásra javasolt a bárki számára (pl. KAPP):
- https://szentjozsefhackathon.github.io/napi-lelki-batyu/[éééé].json vagy
- https://szentjozsefhackathon.github.io/napi-lelki-batyu/[éééé-hh-nn].json

## Frontend
A fent említett [éééé].json-ból táplálkozva összeállít különféle igenaptárat, direktóriumot, liturgikus rendet

### [naptar.html](https://szentjozsefhackathon.github.io/napi-lelki-batyu/naptar.html)
Egy éves összefoglaló az ünnepekkel, olvasmányokkal, bűnbánati napokkal 

### [index.html?date=2024-06-30](https://szentjozsefhackathon.github.io/napi-lelki-batyu/index.html?date=2024-06-30)
Béna! 
Egy-egy konkrét napra állítja össze a nagy json fájl alapján a napi liturgikus olvasmányokat és tudnivalókat. Ha az url-ben nem kap "date" argumentumot, akkor választ egy véletlen napot.


## Fejlesztés
- A [sources](sources/) mappában vannak külfönéle csv fájlokban mindenféle alapanyagok az igenaptar.katolikus.hu adatbázisából
- A ```python generateparts.py``` a fenti alapanyagokból megpróbálja elkészíteni a readings/ mappába lévő .json fájlokat és jól felül is írja azokat - pedig azokban már rengeteg a kézi tisztítás. Ezt használata csak bajt okoz.
- Ha nem tud valamivel mit kezdnei akkor a readings/errors.txt -be beleírja hogy érzése szerint van valami gond, és akkor kézzel javítani kell.
- push vagy pull_request esetén lefut a json validátor és elvérzik, ha valami nem stimmel. éljen.
- push esetén, akár a validátor eredményes volt akár nem, deploy-t kap a honlap: feltölti a /batyuk tartalmát (zip, index.html, sok json) és mindenki boldok
- cél, hogy a frontend már ne gondolkodjon igazán, minél inkább a json tartalmazzon mindent ami fontos!


## éééé.json specifikáció
Következik a yyyy.json fájl dokumentációja 

#### A legfelső szint
Egy nagy json objectünk van, amiben sok-sok elem van. A kulcs mindig "éééé-hh-nn" formátumban egy konkrét dátum. Minden dátumhoz tartozik egy object.

```
{
     "2024-01-01": { ... },
     "2024-01-02": { ... },
     "2024-01-03": { ... },
     ...
     "2024-12-31": { ... },
}
```

#### egy naptári nap
Minden "éééé-hh-nn" formátumú kulcshoz tarozó elem egy olyan object aminek pontosan két eleme van amik kulcsa: "date" és "celebration"

```
{
     "date": { ... },
     "celebration": [ ... ],
}
```

#### date object
Ez object amiben a naptári naphoz tartozó olyan információk tartoznak, amik a liturgikus rendtől függetlenek:

```
{
     "ISO": "2024-01-03", # éééé-hh-nn formátumban a dátum.
     "dayOfYear": "3", # Az év hannyadik napjáról van szó. Január 1 = 1
     "dayofWeek": "3", # A hét hanyadik napjáról van szó. Vasárnap = 0
     "dayofWeekText": "szerda" # A nap kiírva betűvel
}
```

#### celebration object
Minden naptári naphoz tartozik egy "celebration" lista, aminek mindig van leglaább egy eleme. Nagyon gyakran néhány eleme van. Például, ha választani lehet szentek közül, vagy ha karácsonykor külön ünneplés az éjféli mise és a pásztorok miséje, stb. Egy, egy celebration jó sok adatot tartalmaz.

```
[{
     "dateISO": "2024-01-08",
     "yearLetter": "B",
     "yearParity": "II",
     "week": "1",
     "dayofWeek": 1,
     "weekOfPsalter": "1",
     "season": "5",
     "seasonText": "évközi idő",
     "typeLocal": null,
     "level": "13",
     "required": "1",
     "name": "évközi idő 1. hét, hétfő",
     "readingsBreviarId": "1C1",
     "volumeOfBreviary": "III",
     "title": "évközi idő 1. hét, hétfő (köznap)",
     "celebrationType": "köznap",
     "colorId": "3",
     "colorText": "zöld",
     "comunia": null,
     "celebrationKey": 0,
     "readingsId": "EVK011Hetfo",
     "ferialReadingsId": "01-08",
     "parts": [ ... ],
     "dayOfPenance": 0
},...]
```

#### parts
folytatjuk...
