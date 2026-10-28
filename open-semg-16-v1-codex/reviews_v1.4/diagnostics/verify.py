#!/usr/bin/env python3
"""Independent pin/net verification of the native V1.4 KiCad exports.

Run beside final-netlist.xml, final-erc.json and baseline-v1.2-netlist.xml.
Writes verification.json only; never edits a KiCad design.
"""
from __future__ import annotations

import json
import hashlib
from collections import Counter
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
CHECKS = []


def check(name, condition, detail=None):
    record = {"name": name, "pass": bool(condition)}
    if detail is not None:
        record["detail"] = detail
    CHECKS.append(record)


def read_netlist(path):
    root = ET.parse(path).getroot()
    components = {c.attrib["ref"]: c for c in root.find("components")}
    nets = {}
    pin_net = {}
    for net in root.find("nets"):
        name = net.attrib["name"]
        nodes = {(n.attrib["ref"], n.attrib["pin"]) for n in net}
        nets[name] = nodes
        for node in nodes:
            if node in pin_net:
                raise ValueError(f"Pin occurs in two nets: {node}")
            pin_net[node] = name
    return components, nets, pin_net


def main():
    phase = "candidate" if "--candidate" in sys.argv else "final"
    components, nets, pin_net = read_netlist(HERE / f"{phase}-netlist.xml")
    baseline, baseline_nets, _ = read_netlist(HERE / "baseline-v1.2-netlist.xml")
    expected_retained = ({f"C{i}" for i in range(1, 53)}
                         | {f"R{i}" for i in range(1, 38)}
                         | {f"E{i}" for i in range(1, 17)}
                         | {"U1", "U2", "U3"})
    added = {f"C{i}" for i in range(58, 64)} | {"R39", "R40", "R41"}
    expected = expected_retained | added
    check("exact component set (117)", set(components) == expected,
          {"missing": sorted(expected - set(components)),
           "unexpected": sorted(set(components) - expected)})
    check("no test points, batteries or obsolete regulators",
          not any(ref.startswith(("TP", "BT")) for ref in components)
          and {ref for ref in components if ref.startswith("U")} == {"U1", "U2", "U3"})

    def net(ref, pin):
        return pin_net.get((ref, str(pin)))

    def named(name):
        found = [n for n in nets if n.lstrip("/") == name]
        return found[0] if len(found) == 1 else None

    def exact(name, pins):
        n = named(name)
        check(f"{name} exact membership", n is not None and nets[n] == set(pins),
              {"actual": sorted(nets.get(n, set())), "expected": sorted(pins)})

    rail = net("U3", 1)
    ground = net("U3", 22)
    check("one named 3.3V rail and common GND",
          rail == named("+3.3V") and ground == named("GND") and rail != ground)
    for adc in ("U1", "U2"):
        for pin in (19, 21, 22, 54, 56, 59, 48, 50):
            check(f"{adc}.{pin} supply", net(adc, pin) == rail)
        for pin in (20, 23, 32, 53, 57, 58, 33, 49, 51, 25, 31, 41, 42, 44, 45, 46):
            check(f"{adc}.{pin} ground/unused-input tie", net(adc, pin) == ground)
        for pin in (17, 18, 62):
            check(f"{adc}.{pin} unused analog tie to actual AVDD", net(adc, pin) == rail)
    check("all DevKit 3V3/GND header pins", net("U3", 2) == rail
          and all(net("U3", p) == ground for p in (23, 24, 44)))
    check("master CLKSEL high; slave CLKSEL low",
          net("U1", 52) == rail and net("U2", 52) == ground)
    exact("ADC_CLK", {("U1", "37"), ("U2", "37")})

    digital = {
        "SPI_MOSI": {("U1", "34"), ("U2", "34"), ("U3", "17"), ("R36", "1")},
        "SPI_SCLK": {("U1", "40"), ("U2", "40"), ("U3", "18"), ("R37", "1")},
        "SPI_MISO": {("U1", "43"), ("U2", "43"), ("U3", "37")},
        "CS_ADC1": {("U1", "39"), ("U3", "27"), ("R39", "1")},
        "CS_ADC2": {("U2", "39"), ("U3", "36"), ("R40", "1")},
        "START": {("U1", "38"), ("U2", "38"), ("U3", "12"), ("R33", "1")},
        "RESET": {("U1", "36"), ("U2", "36"), ("U3", "6"), ("R34", "1")},
        "PWDN": {("U1", "35"), ("U2", "35"), ("U3", "7"), ("R35", "1")},
        "DRDY_ADC1": {("U1", "47"), ("U3", "38")},
        "DRDY_ADC2": {("U2", "47"), ("U3", "39")},
    }
    for name, pins in digital.items():
        exact(name, pins)
    for ref in ("R33", "R34", "R35", "R36", "R37"):
        check(f"{ref} defined low bias", net(ref, 2) == ground)
    for ref in ("R39", "R40"):
        check(f"{ref} chip-select high bias", net(ref, 2) == rail)
    check("GPIO3 external strap high", net("U3", 13) == net("R41", 1)
          and net("R41", 2) == rail)
    for ref in ("R33", "R34", "R35", "R36", "R37", "R39", "R40", "R41"):
        check(f"{ref} 10k bias value", components[ref].findtext("value") == "10k")
    for pin in (3, 21):
        n = net("U3", pin)
        check(f"DevKit pin {pin} has no carrier supply/control source",
              n is not None and nets[n] == {("U3", str(pin))})

    adc_input_nets = []
    for channel in range(1, 17):
        adc = "U1" if channel <= 8 else "U2"
        local = (channel - 1) % 8 + 1
        for polarity, electrode_pin, resistor, adc_pin in (
                ("P", "1", 2 * channel - 1, 18 - 2 * local),
                ("N", "2", 2 * channel, 17 - 2 * local)):
            ref = f"R{resistor}"
            electrode = f"E{channel}"
            input_net = net(adc, adc_pin)
            adc_input_nets.append(input_net)
            cap = [r for r, p in nets.get(input_net, set()) if r.startswith("C") and p == "1"]
            check(f"CH{channel:02}_{polarity} electrode-to-resistor exact path",
                  net(electrode, electrode_pin) == net(ref, 1)
                  and nets.get(net(ref, 1)) == {(electrode, electrode_pin), (ref, "1")})
            check(f"CH{channel:02}_{polarity} ADC RC exact path",
                  len(cap) == 1 and nets.get(input_net) == {
                      (adc, str(adc_pin)), (ref, "2"), (cap[0], "1")}
                  and net(cap[0], 2) == ground
                  and components[cap[0]].findtext("value") == "620pF"
                  and input_net == named(f"CH{channel:02}_{polarity}"))
    check("all 32 ADC inputs distinct", len(set(adc_input_nets)) == 32
          and rail not in adc_input_nets and ground not in adc_input_nets)

    for adc, offset in (("U1", 0), ("U2", 26)):
        number = 1 if adc == "U1" else 2
        for pin, cnum, value in ((28, 23, "22uF"), (30, 24, "1uF"),
                                 (55, 25, "1uF"), (26, 26, "1uF")):
            cap = f"C{cnum + offset}"
            extra = {("C58" if adc == "U1" else "C59", "1")} if pin == 55 else set()
            exact(f"VCAP{(28, 30, 55, 26).index(pin) + 1}_ADC{number}",
                  {(adc, str(pin)), (cap, "1")} | extra)
            check(f"{cap} value and bypass return", components[cap].findtext("value") == value
                  and net(cap, 2) == ground)
        exact(f"VREFP_ADC{number}", {(adc, "24"), (f"C{19 + offset}", "1"),
                                      (f"C{20 + offset}", "1")})
        for cnum in (19, 20):
            cap = f"C{cnum + offset}"
            check(f"{cap} VREF return", net(cap, 2) == ground)
    for ref, value in (("C58", "0.1uF"), ("C59", "0.1uF"), ("C60", "1uF"),
                       ("C61", "0.1uF"), ("C62", "1uF"), ("C63", "0.1uF")):
        check(f"{ref} required added bypass", components[ref].findtext("value") == value
              and net(ref, 2) == ground
              and (ref in {"C58", "C59"} or net(ref, 1) == rail))
    for ref in ("C6", "C7", "C8", "C9", "C32", "C33", "C34", "C35"):
        check(f"{ref} retained supply decoupling", net(ref, 1) == rail and net(ref, 2) == ground)

    # Compare complete physical pin partitions, independent of net names and layout.
    # Explicitly permit only deleted components, declared additions and MCU remapping.
    mcu_map = {"19": "37", "16": "27", "20": "36", "15": "38"}
    affected_mcu = set(mcu_map) | set(mcu_map.values()) | {"39", "13"}
    expected_partitions = set()
    for baseline_nodes in baseline_nets.values():
        nodes = {n for n in baseline_nodes if n[0] in expected_retained
                 and not (n[0] == "U3" and n[1] in affected_mcu)}
        for old_pin, new_pin in mcu_map.items():
            if ("U3", old_pin) in baseline_nodes:
                nodes.add(("U3", new_pin))
        if ("U2", "47") in baseline_nodes:
            nodes.add(("U3", "39"))
        if nodes:
            expected_partitions.add(frozenset(nodes))
    expected_partitions |= {frozenset({("U3", p)}) for p in mcu_map}
    expected_partitions.add(frozenset({("U3", "13")}))
    actual_partitions = {frozenset(n for n in nodes if n[0] in expected_retained)
                         for nodes in nets.values()}
    actual_partitions.discard(frozenset())
    fmt = lambda groups: [sorted(g) for g in sorted(groups, key=lambda x: sorted(x))]
    check("complete retained V1.2 pin partitions, with explicit changes only",
          actual_partitions == expected_partitions,
          {"missing_partitions": fmt(expected_partitions - actual_partitions),
           "unexpected_partitions": fmt(actual_partitions - expected_partitions)})
    for ref in sorted(expected_retained):
        if ref.startswith(("C", "R")):
            check(f"{ref} retained value", components[ref].findtext("value")
                  == baseline[ref].findtext("value"))
            def requirements(component):
                return {f.get("name"): f.text for f in component.findall("./fields/field")}
            check(f"{ref} retained procurement requirements",
                  all(requirements(components[ref]).get(k) == v
                      for k, v in requirements(baseline[ref]).items()))
    for adc in ("U1", "U2"):
        check(f"{adc} every package pin represented",
              {p for r,p in pin_net if r == adc} == {str(i) for i in range(1,65)})
    for ref in ("C25", "C51", "C58", "C59"):
        check(f"{ref} VCAP3 voltage requirement preserved",
              any("10" in (f.text or "") for f in components[ref].findall("./fields/field")
                  if "voltage" in f.get("name", "").lower()))

    repo = HERE.parents[1]
    manifest = json.loads((HERE / "historical-hashes-task-start.json").read_text())
    changed_history = [name for name, digest in manifest.items()
                       if not (repo/name).is_file()
                       or hashlib.sha256((repo/name).read_bytes()).hexdigest() != digest]
    check("all historical version/review files unchanged", not changed_history, changed_history)
    check("V1.4 project settings unchanged",
          (repo/"v1.4/open-semg-16-v1.4.kicad_pro").read_bytes()
          == (HERE/"before-implementation/open-semg-16-v1.4.kicad_pro").read_bytes())

    erc = json.loads((HERE / f"{phase}-erc.json").read_text())
    violations = [v for sheet in erc.get("sheets", []) for v in sheet.get("violations", [])]
    erc_counts = dict(Counter(v.get("severity", "unknown") for v in violations))
    check("no ERC exclusions", not any(v.get("excluded", False) for v in violations)
          and not erc_counts.get("exclusion", 0))
    expected_erc = Counter({"power_pin_not_driven": 3, "pin_to_pin": 1,
                            "pin_not_connected": 2, "pin_not_driven": 1})
    check("only seven documented ERC diagnostics, no unintended warnings",
          Counter(v.get("type") for v in violations) == expected_erc
          and erc_counts == {"error": 7})
    result = {
        "pass": all(c["pass"] for c in CHECKS),
        "checks": len(CHECKS),
        "passed": sum(c["pass"] for c in CHECKS),
        "component_count_v1_2": len(baseline),
        "component_count_v1_4": len(components),
        "nets_v1_4": len(nets),
        "channels_verified": 16,
        "erc_counts": erc_counts,
        "erc_violations": [{"type": v.get("type"), "severity": v.get("severity"),
                            "description": v.get("description"),
                            "items": [i.get("description") for i in v.get("items", [])]}
                           for v in violations],
        "results": CHECKS,
        "limits": "Connectivity checks do not prove firmware, analog performance, power integrity, assembly or human safety.",
    }
    (HERE / ("candidate-verification.json" if phase == "candidate" else "verification.json")).write_text(json.dumps(result, indent=2) + "\n")
    print(f"V1.4 connectivity: {result['passed']}/{result['checks']} checks passed; "
          f"{len(components)} components, {len(nets)} nets, 16 differential channels.")
    print("ERC counts:", erc_counts)
    for record in CHECKS:
        if not record["pass"]:
            print("FAIL:", record["name"], record.get("detail", ""))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
