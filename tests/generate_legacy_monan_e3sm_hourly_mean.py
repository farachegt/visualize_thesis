from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_SCRIPT = import_module(
    "scripts.recipes.generate_legacy_monan_e3sm_hourly_mean"
)

globals().update(
    {
        name: getattr(_SCRIPT, name)
        for name in dir(_SCRIPT)
        if not name.startswith("_")
    }
)

if __name__ == "__main__":
    main()
