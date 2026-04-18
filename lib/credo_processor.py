import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

credotypes = {
    "van": "Hitvallás van",
    "nincs": "",
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
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    try:
        if (
                (dayOfWeek == "0") or
                (level == "6") or
                (level == "3" and name != "Halottak napja") or
                (level == "2" and
                    (
                        name != "Hamvazószerda" and
                        not "krizma" in str(name).lower() and
                        season != "7"
                    )
                )
            ):
            credo = "van"
        else:
            if (
                season == "9" or
                season == "3"
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
