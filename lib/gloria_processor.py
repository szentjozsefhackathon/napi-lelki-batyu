import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from lib import (
    error_handler
)

gloriaTypes = {
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
            gloria = "van"
        else:
            gloria = "nincs"
    except Exception as e:
        error_handler.error(str(e))
        return "default"
    return gloriaTypes[gloria]
