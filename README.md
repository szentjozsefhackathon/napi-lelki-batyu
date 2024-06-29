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

