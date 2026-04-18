import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

credotypes = {
    "van": "Hitvallás van",
    "nincs": "",
    "keneDeNincs": "Nincs hitvallás"
}

def main (celebration: Dict[str, Any]) -> str:
    try:
        dayOfWeek = celebration["dayofWeek"]
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    try:
        if (dayOfWeek == 0):
            credo = "van"
        else:
            credo = "nincs"
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    return credotypes[credo]
