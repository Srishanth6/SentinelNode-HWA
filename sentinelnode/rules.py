TEMP_HOT_C, DELTA_T_C, VIB_RMS_G, RIPPLE_MV = 85.0, 30.0, 1.5, 250.0

def check(r: dict) -> list[str]:
    out = []
    if r["temp_hot_c"] > TEMP_HOT_C: out.append("hotspot_over_temp")
    if r["temp_hot_c"] - r["temp_amb_c"] > DELTA_T_C: out.append("excess_temp_rise")
    if r["vibration_g"] > VIB_RMS_G: out.append("high_vibration")
    if r["ripple_mv"] > RIPPLE_MV: out.append("high_ripple")
    return out
