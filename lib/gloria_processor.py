import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

gloriaTypes = {
    "van": "Dicsőség",
    "nincs": "--",
    "keneDeNincs": "Dicsőség nincs"
}

def main (celebration: Dict[str, Any]) -> str:
    try:
        dayOfWeek = celebration["dayofWeek"]
        season = celebration["season"]
        level = celebration["level"]
        name = celebration["name"]
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    try:
        match level:
            case "1":
                if(dayOfWeek == 0):
                    gloria = "van"
                else:
                    gloria = "nincs"
            case "2":
                if(
                    (dayOfWeek == 0 and (season == "0" or season == "1"))
                    or
                    dayOfWeek == 0 and (season == "6" or season == "7")
                    ):
                    gloria = "keneDeNincs"
                elif("karácsony" in str.lower(name) or "vízkereszt" in str.lower(name) or "Urunk mennybemenetele" in str.lower(name) or "Pünkösd" in str.lower(name)
                     or
                     (dayOfWeek == 0 and (season == "10" or season == "11"))
                     or
                     (dayOfWeek == 4 and season == "7")
                     or
                     season == "9"
                     ):
                    gloria = "van"
                else:
                    gloria = "nincs"
            case "3":
                if("Halottak napja" in name):
                    gloria = "nincs"
                else:
                    gloria = "van"
            case "4":
                gloria = "van"
            case "5":
                gloria = "van"
            case "6":
                gloria = "van"
            case "7":
                gloria = "van"
            case "8":
                gloria = "van"
            case "9":
                if(season == "2"):
                    gloria = "van"
                else:
                    gloria = "nincs"
            case "10":
                gloria = "nincs"
            case "11":
                gloria = "nincs"
            case "12":
                gloria = "nincs"
            case "13":
                gloria = "nincs"
                
                
            
            
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    return gloriaTypes[gloria]
