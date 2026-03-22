from __future__ import annotations

from importlib import import_module

_MODULE = import_module("legacy.code.plot_maps")

globals().update(
    {
        symbol: getattr(_MODULE, symbol)
        for symbol in dir(_MODULE)
        if not symbol.startswith("_")
    }
)

if __name__ == "__main__" and "main" in globals():
    main()
