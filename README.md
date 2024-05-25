# napi-lelki-batyu

https://szentjozsefhackathon.github.io/napi-lelki-batyu/

Minden napra megadja a napi szenteket, olvasmányokat, liturgikus információkat

A zsolozsma xml naptárát használja, mert az a legjobb.
Amit összefűz az igenaptar.katolikus.hu információival

És főként xml/json kimenetet generál a github pages-re, hogy onnan bárki használhassa, páldául a KAPP
Használata: https://szentjozsefhackathon.github.io/napi-lelki-batyu/[éééé].json vagy https://szentjozsefhackathon.github.io/napi-lelki-batyu/[éééé-hh-nn].json

### Működés (ezen kódé, nem a honlapé)
- A [readings](readings/) mappában vannak json formába rendezve a liturgiákon használt olvasmányos könyvek. Vasárnapi A, B és C, továbbá hétköznapi olvasmányok I-II (egyben), valamint a szentek saját olvasmányai.
- A ```python generate.py```
     - beolvassa a digitális zsolozsma igenaptárját a teljes évre (breviarData.json fájlba)
     - megpróbálja megkeresni minden nap minden ünnepére/emléknapjára/liturgiájára a readings/....json fáljok közül a megfelelőből a megfelelő sorokat
     - kicsit rendezi az opciókat
     - és legyártja a kimeneti json fájlokat a batuk/ mappába ( [éééé-hh-nn].json, [éééé].json, [éééé]_simple.json )
- A batyuk/index.html hoz egy kissé igényeteln frontendet is

### Fejlesztés
- A [sources](sources/) mappában vannak külfönéle csv fájlokban mindenféle alapanyagok
- A ```python generateparts.py``` a fenti alapanyagokból megpróbálja elkészíteni a readings/ mappába lévő .json fájlokat és jól felül is írja azokat - pedig azokban már rengeteg a kézi tisztítás. Ezt használata csak bajt okoz.
- Ha nem tud valamivel mit kezdnei akkor a readings/errors.txt -be beleírja hogy érzése szerint van valami gond, és akkor kézzel javítani kell.
- push vagy pull_request esetén lefut a json validátor és elvérzik, ha valami nem stimmel. éljen.
- push esetén, akár a validátor eredményes volt akár nem, deploy-t kap a honlap: feltölti a /batyuk tartalmát (zip, index.html, sok json) és mindenki boldok
