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


def derive_qt_from_qc_qv(
    qc: ArrayLike,
    qv: ArrayLike,
) -> ArrayLike:
    """Derive total water mixing ratio from cloud and vapor mixing ratios.

    Parameters
    ----------
    qc:
        Cloud liquid water mixing ratio.
    qv:
        Water vapor mixing ratio.

    Returns
    -------
    xr.DataArray | np.ndarray
        Total water mixing ratio with the same structural type as the input
        when possible.
    """
    qt_values = _to_numpy(qc) + _to_numpy(qv)
    units_text = _extract_units(qc) or _extract_units(qv)
    return _wrap_result(
        template=qc,
        values=qt_values,
        units_text=units_text,
        long_name="Total water mixing ratio",
    )


def derive_precipitation_from_rainc_rainnc(
    rainc: ArrayLike,
    rainnc: ArrayLike,
) -> ArrayLike:
    """Derive total accumulated precipitation from convective components.

    Parameters
    ----------
    rainc:
        Convective accumulated precipitation.
    rainnc:
        Non-convective accumulated precipitation.

    Returns
    -------
    xr.DataArray | np.ndarray
        Total accumulated precipitation with the same structural type as the
        input when possible.
    """
    precipitation_values = _to_numpy(rainc) + _to_numpy(rainnc)
    units_text = _extract_units(rainc) or _extract_units(rainnc)
    return _wrap_result(
        template=rainc,
        values=precipitation_values,
        units_text=units_text,
        long_name="Total accumulated precipitation",
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


def derive_specific_humidity_from_dewpoint_surface_pressure(
    surface_pressure: ArrayLike,
    dewpoint_temperature: ArrayLike,
) -> ArrayLike:
    """Derive specific humidity from dewpoint temperature and pressure.

    Parameters
    ----------
    surface_pressure:
        Surface pressure in canonical units expected by the derivation,
        typically Pa.
    dewpoint_temperature:
        Dewpoint temperature in canonical units expected by the derivation,
        typically K.

    Returns
    -------
    xr.DataArray | np.ndarray
        Specific humidity in `g kg-1` with the same structural type as the
        dewpoint-temperature input when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    specific_humidity_quantity = mpcalc.specific_humidity_from_dewpoint(
        _to_quantity(surface_pressure, units.pascal),
        _to_quantity(dewpoint_temperature, units.kelvin),
    ).to("g/kg")
    return _wrap_result(
        template=dewpoint_temperature,
        values=specific_humidity_quantity.magnitude,
        units_text="g kg-1",
        long_name="Specific humidity at 2 m",
    )


def derive_specific_humidity_from_temperature_relative_humidity_surface_pressure(
    temperature: ArrayLike,
    relative_humidity: ArrayLike,
    surface_pressure: ArrayLike,
) -> ArrayLike:
    """Derive specific humidity from temperature, RH and pressure.

    This implementation follows the project-requested approximation:

    `q = 0.622 * e / (p - e)`,

    where `e = RH * e_s(T)` and `RH` is interpreted as a fraction in `[0, 1]`.

    Parameters
    ----------
    temperature:
        Air temperature expected in degC.
    relative_humidity:
        Relative humidity as percentage (`0..100`) or fraction (`0..1`).
    surface_pressure:
        Surface pressure in canonical units expected by the derivation,
        typically Pa.

    Returns
    -------
    xr.DataArray | np.ndarray
        Specific humidity in `g kg-1` with the same structural type as the
        temperature input when possible.

    Raises
    ------
    ImportError
        If `MetPy` is not available in the environment.
    """
    mpcalc, units = _require_metpy()
    temperature_quantity = units.Quantity(
        _to_numpy(temperature),
        units.degC,
    )
    saturation_vapor_pressure = mpcalc.saturation_vapor_pressure(
        temperature_quantity
    )
    pressure_quantity = _to_quantity(surface_pressure, units.pascal).to(
        saturation_vapor_pressure.units
    )
    rh_fraction = _to_relative_humidity_fraction(relative_humidity)
    vapor_pressure = rh_fraction * saturation_vapor_pressure
    specific_humidity_quantity = (
        (vapor_pressure / (pressure_quantity - vapor_pressure)) * 0.622
    ).to("g/kg")
    return _wrap_result(
        template=temperature,
        values=specific_humidity_quantity.magnitude,
        units_text="g kg-1",
        long_name="Specific humidity at 2 m",
    )


def derive_hourly_flux_rate_from_accumulated_energy(
    accumulated_flux: ArrayLike,
    seconds: float = 3600.0,
    long_name: str = "Surface flux",
) -> ArrayLike:
    """Convert hourly accumulated surface energy to a flux rate.

    Parameters
    ----------
    accumulated_flux:
        Accumulated energy per unit area, expected in `J m^-2`.
    seconds:
        Accumulation period in seconds. The default is one hour.
    long_name:
        Descriptive name written to the output metadata.

    Returns
    -------
    xr.DataArray | np.ndarray
        Flux rate in `W m^-2` with the same structure as the input when
        possible.
    """
    if seconds <= 0:
        raise ValueError("Flux accumulation seconds must be positive.")

    flux_values = _to_numpy(accumulated_flux) / seconds
    return _wrap_result(
        template=accumulated_flux,
        values=flux_values,
        units_text="W m^-2",
        long_name=long_name,
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
    "qt_from_qc_qv": {
        "dependencies": ("qc", "qv"),
        "function": derive_qt_from_qc_qv,
        "accepted_options": (),
    },
    "precipitation_from_rainc_rainnc": {
        "dependencies": ("rainc", "rainnc"),
        "function": derive_precipitation_from_rainc_rainnc,
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
    "specific_humidity_from_dewpoint_surface_pressure": {
        "dependencies": (
            "surface_pressure",
            "dewpoint_temperature_2m",
        ),
        "function": derive_specific_humidity_from_dewpoint_surface_pressure,
        "accepted_options": (),
    },
    "specific_humidity_from_temperature_relative_humidity_surface_pressure": {
        "dependencies": ("temperature_2m", "rh", "surface_pressure"),
        "function": (
            derive_specific_humidity_from_temperature_relative_humidity_surface_pressure
        ),
        "accepted_options": (),
    },
    "sensible_heat_flux_from_hourly_accumulated_energy": {
        "dependencies": ("accumulated_sensible_heat_flux",),
        "function": derive_hourly_flux_rate_from_accumulated_energy,
        "accepted_options": ("seconds", "long_name"),
    },
    "latent_heat_flux_from_hourly_accumulated_energy": {
        "dependencies": ("accumulated_latent_heat_flux",),
        "function": derive_hourly_flux_rate_from_accumulated_energy,
        "accepted_options": ("seconds", "long_name"),
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


def _to_relative_humidity_fraction(
    relative_humidity: ArrayLike,
) -> np.ndarray:
    """Convert relative humidity input into a dimensionless fraction."""
    rh_values = _to_numpy(relative_humidity).astype(float, copy=False)
    units_text = (_extract_units(relative_humidity) or "").strip().lower()
    if units_text in {"percent", "%", "pct"}:
        return rh_values / 100.0
    if rh_values.size == 0:
        return rh_values
    finite_values = rh_values[np.isfinite(rh_values)]
    if finite_values.size == 0:
        return rh_values
    if np.nanmax(finite_values) > 1.5:
        return rh_values / 100.0

    return rh_values
