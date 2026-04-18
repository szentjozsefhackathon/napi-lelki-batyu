import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

gloriaTypes = {
    "van": "Dicsőség",
    "nincs": "",
    "keneDeNincs": "Dicsőség nincs"
}

def main (celebration: Dict[str, Any]) -> str:
    try:
        dayOfWeek = celebration["dayofWeek"]
        season = celebration["season"]
        level = celebration["level"]
        celebrationType = celebration["celebrationType"]
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    try:
        if (dayOfWeek == 0 and season != 6):
            gloria = "van"
        else:
            gloria = "nincs"
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    return gloriaTypes[gloria]
