from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional, Union

import numpy as np
import xarray as xr

ArrayLike = Union[xr.DataArray, np.ndarray]
DerivationFunction = Callable[..., ArrayLike]


def derive_theta_from_pressure_temperature(
    pressure: ArrayLike,
    temperature: ArrayLike,
) -> ArrayLike:
    """Derive potential temperature from pressure and temperature.

    Parameters
    ----------
    pressure:
        Pressure in canonical units expected by the derivation, typically Pa.
    temperature:
        Temperature in canonical units expected by the derivation, typically K.

    Returns
    -------
    xr.DataArray | np.ndarray
        Potential temperature with the same structural type as the
        temperature input when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    theta_quantity = mpcalc.potential_temperature(
        _to_quantity(pressure, units.pascal),
        _to_quantity(temperature, units.kelvin),
    )
    return _wrap_result(
        template=temperature,
        values=theta_quantity.magnitude,
        units_text="K",
        long_name="Potential temperature",
    )


def derive_wind_speed_from_uv(
    u_wind: ArrayLike,
    v_wind: ArrayLike,
) -> ArrayLike:
    """Derive wind speed from its zonal and meridional components.

    Parameters
    ----------
    u_wind:
        Zonal wind component.
    v_wind:
        Meridional wind component.

    Returns
    -------
    xr.DataArray | np.ndarray
        Wind speed with the same structural type as the input when possible.
    """
    u_values = _to_numpy(u_wind)
    v_values = _to_numpy(v_wind)
    wind_speed = np.hypot(u_values, v_values)
    units_text = _extract_units(u_wind) or _extract_units(v_wind)
    return _wrap_result(
        template=u_wind,
        values=wind_speed,
        units_text=units_text,
        long_name="Wind speed",
    )


def derive_rh_from_qv_temperature_pressure(
    pressure: ArrayLike,
    temperature: ArrayLike,
    qv: ArrayLike,
    phase: str = "liquid",
) -> ArrayLike:
    """Derive relative humidity from mixing ratio, temperature and pressure.

    Parameters
    ----------
    pressure:
        Pressure in canonical units expected by the derivation, typically Pa.
    temperature:
        Temperature in canonical units expected by the derivation, typically K.
    qv:
        Water vapor mixing ratio in canonical units, typically kg/kg.
    phase:
        Phase argument forwarded to `MetPy`. The default is `"liquid"`.

    Returns
    -------
    xr.DataArray | np.ndarray
        Relative humidity as a fraction with the same structural type as the
        temperature input when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    rh_function = mpcalc.relative_humidity_from_mixing_ratio
    rh_kwargs: Dict[str, Any] = {}
    signature = inspect.signature(rh_function)

    if "phase" in signature.parameters:
        rh_kwargs["phase"] = phase
    elif phase != "liquid":
        raise ValueError(
            "The installed MetPy version does not support the `phase` "
            "argument for `relative_humidity_from_mixing_ratio`."
        )

    rh_quantity = rh_function(
        _to_quantity(pressure, units.pascal),
        _to_quantity(temperature, units.kelvin),
        _to_quantity(qv, units.dimensionless),
        **rh_kwargs,
    )
    return _wrap_result(
        template=temperature,
        values=rh_quantity.magnitude,
        units_text="1",
        long_name="Relative humidity",
    )


def derive_height_from_pressure_standard_atmosphere(
    pressure: ArrayLike,
) -> ArrayLike:
    """Derive standard-atmosphere height from pressure.

    Parameters
    ----------
    pressure:
        Pressure in canonical units expected by the derivation, typically Pa.

    Returns
    -------
    xr.DataArray | np.ndarray
        Height in metres with the same structural type as the pressure input
        when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    height_quantity = mpcalc.pressure_to_height_std(
        _to_quantity(pressure, units.pascal)
    )
    height_quantity = height_quantity.to(units.meter)
    return _wrap_result(
        template=pressure,
        values=height_quantity.magnitude,
        units_text="m",
        long_name="Standard atmosphere height",
    )


def derive_pressure_from_height_standard_atmosphere(
    height: ArrayLike,
) -> ArrayLike:
    """Derive standard-atmosphere pressure from height.

    Parameters
    ----------
    height:
        Height in canonical units expected by the derivation, typically m.

    Returns
    -------
    xr.DataArray | np.ndarray
        Pressure in pascal with the same structural type as the height input
        when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    pressure_quantity = mpcalc.height_to_pressure_std(
        _to_quantity(height, units.meter)
    )
    pressure_quantity = pressure_quantity.to(units.pascal)
    return _wrap_result(
        template=height,
        values=pressure_quantity.magnitude,
        units_text="Pa",
        long_name="Standard atmosphere pressure",
    )


DERIVATION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "theta_from_pressure_temperature": {
        "dependencies": ("pressure", "temperature"),
        "function": derive_theta_from_pressure_temperature,
        "accepted_options": (),
    },
    "wind_speed_from_uv": {
        "dependencies": ("u_wind", "v_wind"),
        "function": derive_wind_speed_from_uv,
        "accepted_options": (),
    },
    "rh_from_qv_temperature_pressure": {
        "dependencies": ("qv", "temperature", "pressure"),
        "function": derive_rh_from_qv_temperature_pressure,
        "accepted_options": ("phase",),
    },
    "height_from_pressure_standard_atmosphere": {
        "dependencies": ("pressure",),
        "function": derive_height_from_pressure_standard_atmosphere,
        "accepted_options": (),
    },
    "pressure_from_height_standard_atmosphere": {
        "dependencies": ("height",),
        "function": derive_pressure_from_height_standard_atmosphere,
        "accepted_options": (),
    },
}


def get_derivation_spec(kind: str) -> Dict[str, Any]:
    """Return the registry entry for a derivation kind.

    Parameters
    ----------
    kind:
        Stable derivation identifier stored in `VariableSpecification`.

    Returns
    -------
    dict[str, Any]
        Registry entry containing dependencies, function and accepted options.

    Raises
    ------
    KeyError
        If the requested derivation kind is not registered.
    """
    try:
        return DERIVATION_REGISTRY[kind]
    except KeyError as exc:
        raise KeyError(
            f"Unknown derivation kind: {kind!r}."
        ) from exc


def _require_metpy() -> tuple[Any, Any]:
    """Import `MetPy` lazily and fail with a clear error when unavailable.

    Returns
    -------
    tuple[Any, Any]
        `metpy.calc` and `metpy.units.units`.

    Raises
    ------
    ImportError
        If `MetPy` is not installed in the current environment.
    """
    try:
        import metpy.calc as mpcalc
        from metpy.units import units
    except ImportError as exc:
        raise ImportError(
            "MetPy is required for this derivation but is not installed in "
            "the current environment."
        ) from exc

    return mpcalc, units


def _to_quantity(values: ArrayLike, units_obj: Any) -> Any:
    """Convert array-like input to a pint quantity.

    Parameters
    ----------
    values:
        Input data as numpy array or xarray data array.
    units_obj:
        Target unit object from `metpy.units`.

    Returns
    -------
    Any
        Pint quantity built from the input values.
    """
    return _to_numpy(values) * units_obj


def _to_numpy(values: ArrayLike) -> np.ndarray:
    """Convert supported array-like input to `numpy.ndarray`.

    Parameters
    ----------
    values:
        Input data as numpy array or xarray data array.

    Returns
    -------
    np.ndarray
        Plain numpy representation of the input values.
    """
    if isinstance(values, xr.DataArray):
        return values.values

    return np.asarray(values)


def _wrap_result(
    template: ArrayLike,
    values: np.ndarray,
    units_text: Optional[str],
    long_name: str,
) -> ArrayLike:
    """Wrap derived values using the structure of a template input.

    Parameters
    ----------
    template:
        Reference object used to preserve dims, coords and metadata when it is
        an `xarray.DataArray`.
    values:
        Derived numeric values.
    units_text:
        Output units to be written into attrs when available.
    long_name:
        Descriptive name for the derived result.

    Returns
    -------
    xr.DataArray | np.ndarray
        Derived values with structure preserved when possible.
    """
    if isinstance(template, xr.DataArray):
        result = xr.DataArray(
            values,
            dims=template.dims,
            coords=template.coords,
            attrs=dict(template.attrs),
            name=template.name,
        )
        if units_text is not None:
            result.attrs["units"] = units_text
        result.attrs["long_name"] = long_name
        return result

    return values


def _extract_units(values: ArrayLike) -> Optional[str]:
    """Extract units metadata from an input object when available.

    Parameters
    ----------
    values:
        Input data as numpy array or xarray data array.

    Returns
    -------
    str | None
        Units text from attrs when available.
    """
    if isinstance(values, xr.DataArray):
        units_value = values.attrs.get("units")
        if units_value is not None:
            return str(units_value)

    return None
