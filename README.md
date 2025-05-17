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

Nyilvános felhasználása javasolt bárki számára (pl. KAPP):
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
- Ha nem tud valamivel mit kezdeni akkor a readings/errors.txt -be beleírja hogy érzése szerint van valami gond, és akkor kézzel javítani kell.
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
Minden "éééé-hh-nn" formátumú kulcshoz tartozó elem egy olyan object aminek pontosan két eleme van amik kulcsa: "date" és "celebration"

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
Minden naptári naphoz tartozik egy "celebration" lista, aminek mindig van legalább egy eleme. Nagyon gyakran néhány eleme van. Például, ha választani lehet szentek közül, vagy ha karácsonykor külön ünneplés az éjféli mise és a pásztorok miséje, stb. Egy, egy celebration jó sok adatot tartalmaz.

```
[{
     "dateISO": "2024-01-08", #Az adott dátum éééé-hh-nn formátumban
     "yearLetter": "B", # A liturgikus év betújele. Lehet A, B, vagy C. Advent első vasárnapja előestén vált mindig, vagyis év közben.
     "yearParity": "II", # A liturgikus év köznapjain az olvasmányok páros és páratlan év szerint váltakoznak. Ezért lehet ez I vagy II. Ez is advent első vasárnapja előestéjén vált.
     "week": "1", # Az adott liturgikus időszakon belüli hét sorszáma. Például advent 3. hetében ez 3-as. Olykor lehet 0 is, például hamvazószerdától nagyböjt első vasárnapjáig
     "dayofWeek": 1, # A hét napjának sorszáma. Vasárnap = 0
     "weekOfPsalter": "1", # A zsolozsmában használt zsoltáros hét sorszáma. 1, 2, 3, vagy 4. Nagy ünnepekkor - amikor minden zsoltár saját - nem releváns ez az információ, de liturgikus időszak alapján akkor is van itt érték.
     "season": "5", # A litrugikus időszak azonosítója. Van itt mindenféle: advent I, advent II, karácsony, karácsony nyolcada, karácsony II, évközi idő, stb. Kicsit több mint amit fejből mondanál.
     "seasonText": "évközi idő", # A liturgikus időszak megnevezése. Mindig párban változik az előző azonosítóval
     "typeLocal": null, # Lehet null vagy string. Ha az adott ünnep csak bizonyos egyházmegyékben ünneplendő, akkor itt van hozzá szöveg. 
     "level": "13", # Az ünnep rangja. Legmagasabb az 1, legkisebb a 13. A Misekönyv elején van pontos leírás arról, hogy mi milyen rangú. Ezek alapján alakul a naptár.
     "required": "1", # Nem egészen beazonosított érték. Kb 15 esetben "0", amikor igen nagy már-már kötelező ünnep van. Beazonosításához a zsolozsma naptárra kéne ránézni.
     "name": "évközi idő 1. hét, hétfő", # Az adott ünneplés megnevezése. 
     "readingsBreviarId": "1C1", # A zsolozsma naptárja ezen azonosító szerint keresi meg az ünnep olvasmányait. A fejlesztés korábbi fázisában használtuk, ma már nem.
     "volumeOfBreviary": "III", # A négy kötetes zsolozsma hanyadik kötetében találjuk meg a zsolozsma elemeit: I, II, III, vagy IV
     "title": "évközi idő 1. hét, hétfő (köznap)", # A 'name' társa vagyis az adott ünnep megnevezése. Itt az ünnep rangjával is. A KAPP például ezt írja ki és nem a 'name' értékét
     "celebrationType": "köznap", # A 'level' érték alapján az ünneplés ragjának megnevezése (ez kerül a 'title' végére). 0 = köznap, 1= főünnep, ... ünnep, emléknap, tetszés szerinti emléknap, 5 = egyéb saját szöveg...
     "colorId": "3", # A liturgikus szín azonosítója. 1 = piros, 2 = fehér, ... zöld, lila, rózsaszín, fekete, 9 = rózsaszín|lila
     "colorText": "zöld", # A liturgikus szín szöveggel kíírva. Figyelj a rózsaszín|lila -val!
     "comunia": null, # Null vagy lista, hogy a közös részeket a zsolozsmában honnan lehet venni (pl. lelkipásztorok, egyháztanítók, stb.) Formátuma változni fog!
     "celebrationKey": 0, # Egy szám. Amennyiben több celebration object van a listában, akkor itt egy azonosító, hogy ez épp hányadik a sorban. 
     "readingsId": "EVK011Hetfo", # Ezen azonosító alapján próbáljuk megtalálni, hogy melyik olvasmány való ide. Leginkább az igenaptár.katolikus.hu azonosítójára hasonlít, de vannak eltérések / kivételek.
     "ferialReadingsId": "01-08", # Zsolozsmából jövő olvasmány-azonosító. Amennyiben lehet köznapi olvasmányokat választani, akkor azok azonsoítója. Mi nem használjuk. Lehetne?
     "parts": [ ... ], # A napról való olvasmányok és más információk. Lent külön szétszálazzuk
     "parts2": [ ... ], # Opcionális. Ha egy emléknapnál lehet választani, hogy a köznapi olvasmányokat vesszük vagy az ünnepieket, akkor a parts tartalmazza az alapértelmezettet (köznapi) és a parts2 a sajátokat (opcionális)
     "dayOfPenance": 0 # b
},...]
```

#### parts
folytatjuk...
