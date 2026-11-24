"""Stable VAV planning interface backed by the shared multizone resolver."""

from common.multizone_plan import (
    PROFILE,
    CONTROLS,
    PROFILE_NOTES,
    assumption_review as review_assumptions,
    plan as resolve_plan,
)

PVAV_PROFILE = "prototype_pvav_v1"
PVAV_COILS = {
    "central_heating": "NaturalGas",
    "central_cooling": "DXTwoSpeed",
    "reheat": "Electricity",
}
PVAV_OPTIONS = dict(
    profile_name=PVAV_PROFILE,
    profile=dict(
        PROFILE,
        outdoor_air_schedule={"builtin": "AlwaysOnDiscrete"},
        fan=dict(
            total_efficiency=0.6045,
            motor_efficiency=0.93,
            pressure_rise=4.08525614408124,
            pressure_units="inH2O",
        ),
        design_temperatures_c=dict(PROFILE["design_temperatures_c"], zone_heating=50.0),
    ),
    controls=dict(CONTROLS, fan_end_use_subcategory="PVAV System Fans"),
    notes=dict(
        PROFILE_NOTES,
        equipment="Gas central heat, approved two-speed DX cooling and electric reheat",
        fan_power_profile="Shared harness VAV fan power curve and minimum flow settings",
    ),
)


def assumption_review(config):
    if config.get("defaults_profile") == PVAV_PROFILE:
        return review_assumptions(config, **PVAV_OPTIONS)
    return review_assumptions(config)


def plan(config, catalog, input_path):
    if config.get("defaults_profile") != PVAV_PROFILE:
        return resolve_plan(config, catalog, input_path)
    planned = resolve_plan(config, catalog, input_path, **PVAV_OPTIONS)
    for role, expected in PVAV_COILS.items():
        kind = config.get(role, {}).get("type")
        if kind is not None and kind != expected:
            planned["errors"].append(f"{role}.type: {PVAV_PROFILE} requires {expected}")
            planned["ready"] = False
    return planned
