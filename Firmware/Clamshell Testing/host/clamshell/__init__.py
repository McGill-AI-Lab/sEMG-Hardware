"""
clamshell — the PC side of the ADS1298 clamshell validation suite.

Modules (read in this order to follow the data flow):
    ads1298.py      register values and unit conversion
    device.py       serial protocol: commands, binary packets
    simulator.py    a fake board that speaks the same protocol
    experiments.py  the experiments of clamshell_validation.md
    analysis.py     the maths (noise, spectra, fits, Allan deviation)
    palette.py      chart colours
    plots.py        chart styling and saving
    live.py         terminal progress and the live window
    report.py       report.html, summary.md, CSV, JSON
"""
