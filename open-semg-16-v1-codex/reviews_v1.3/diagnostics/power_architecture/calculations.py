"""Reproduce proposal arithmetic; no schematic writes or electrical simulation."""
import json
from pathlib import Path

rtop, rbottom, tol = 58000.0, 10000.0, 0.001
main_min = .495 * (1 + rtop*(1-tol)/(rbottom*(1+tol))) - 100e-9*rtop*(1+tol)
main_max = .505 * (1 + rtop*(1+tol)/(rbottom*(1-tol))) + 100e-9*rtop*(1+tol)
afe_min = 98e-6*29800*(1-tol)-.002
afe_max = 102e-6*29800*(1+tol)+.002

def battery_trip(threshold_min, threshold_max):
    return [
        threshold_min * (1+22000*(1-tol)/(10000*(1+tol))) - .2e-6*22000*(1+tol),
        threshold_max * (1+22000*(1+tol)/(10000*(1-tol))) + .2e-6*22000*(1+tol),
    ]

results = {
    "scope": "Conditional arithmetic only; stated efficiency/load/capacitance assumptions are not measurements",
    "main_dc_V": [main_min, main_max],
    "afe_dc_V": [afe_min, afe_max],
    "minimum_static_headroom_V": main_min-afe_max,
    "headroom_above_300mV_screen_V": main_min-afe_max-.300,
    "positive_main_margin_to_3V6_V": 3.6-main_max,
    "en_falling_battery_V": battery_trip(.97, 1.03),
    "en_rising_battery_V": battery_trip(1.07, 1.13),
    "bleeder_current_min_A": afe_min/(2700*1.01),
    "bleeder_current_nominal_A": 2.98/2700,
    "bleeder_power_nominal_W": 2.98**2/2700,
    "nominal_supervisor_thresholds_V": [.405*(1+67800/10000), .405*(1+59100/10000)],
    "common_mode_gain6_bounds_V": [
        {"differential_V":vd, "AVDD3V3":[.2+6*vd/2,3.3-.2-6*vd/2],
         "AVDD2V98":[.2+6*vd/2,2.98-.2-6*vd/2],
         "AVDD_low_corner":[.2+6*vd/2,afe_min-.2-6*vd/2]}
        for vd in [.3,.35,.4]
    ],
    "battery_current_scenarios": [
        {"main_A":i,"main_W":3.4*i,"battery3V7_eta90_A":3.4*i/(3.7*.9),
         "battery3V2_eta85_A":3.4*i/(3.2*.85)}
        for i in [.1,.2,.4,.56,.75]
    ],
    "converter_thermal_screens": [
        {"main_A":i,"assumed_efficiency":.85,"loss_W":3.4*i*(1/.85-1),
         "rise_C_all_loss_in_IC":3.4*i*(1/.85-1)*81}
        for i in [.56,.75]
    ],
    "ldo_thermal_power_W":(3.4-2.98)*.020+3.4*.005,
    "capacitor_only_droop_V": .3*100e-6/200e-6,
    "C57_charge_C":200e-6*3.4,
    "C57_energy_J":.5*200e-6*3.4**2,
    "hypothetical_runtime_h_per_usable_Ah_at_main200mA":3.7*.9/(3.4*.2),
}
Path(__file__).with_name("calculations.json").write_text(json.dumps(results,indent=2)+"\n")
print(json.dumps({k:results[k] for k in ["main_dc_V","afe_dc_V","minimum_static_headroom_V","en_falling_battery_V","en_rising_battery_V","bleeder_current_min_A"]},indent=2))
