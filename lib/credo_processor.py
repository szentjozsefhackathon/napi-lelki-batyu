import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

credotypes = {
    "van": "Hitvallás van",
    "nincs": "",
    "terdhajtas": "Hitvallás (térdhajtással)",
    "keneDeNincs": "(nincs Hitvallás)",
    "szekesegyhaz": "(a székesegyházban van, azon kívül nincs Hitvallás)",
    "szent": "(az egyházmegyében van, azon kívül nincs Hitvallás)"
}

def main (celebration: Dict[str, Any]) -> str:
    try:
        dayOfWeek = celebration["dayofWeek"]
        season = celebration["season"]
        level = celebration["level"]
        name = celebration["name"]
        typeLocal = celebration["typeLocal"]
        dateISO = celebration["dateISO"]
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    try:
        ##### Amikor biztosan van
        if (
                ##### Karácsony és Évközi minden vasárnap
                (dayOfWeek == 0) or (level == "6") or
                #### Minden 3-as szintű kivéve Halottak napja
                (level == "3" and name != "Halottak napja") or
                #### Minden 2-es szintű kivéve ha ....
                #### Hamavazószerda, Húsvét nyolcad, nagyböjti időszak és karácsony nyolcada
                #### DE nagycsütörtök Krizmaszentelőjén sem
                (level == "2" and
                    (
                        name != "Hamvazószerda" and
                        not "krizma" in str(name).lower() and
                        season != "7" and
                        season != "9" and
                        season != "2"
                    )
                )
            ):
            credo = "van"
        else:
            #### Karácsony 12-25 minden miséjén térdhajtással
            if (
                    (season == "2" and "12-25" in str(dateISO).lower())
                ):
                    credo = "terdhajtas"
            else:
                ##### Húsvét és karácsony nyolcadában kéne DE nincs!
                if (
                    season == "9" or
                    (season == "2" and not "12-25" in str(dateISO).lower())
                ):
                    credo = "keneDeNincs"
                else:
                    if "székes" in str(typeLocal).lower():
                        credo = "szekesegyhaz"
                    else:
                        if "védő" in str(typeLocal).lower():
                            credo = "szent"
                        else:
                            credo = "nincs"
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    return credotypes[credo]
