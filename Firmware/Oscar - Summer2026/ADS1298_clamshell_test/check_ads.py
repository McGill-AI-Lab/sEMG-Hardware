"""
Quick "can the ESP32 see the ADS1298?" check.

Resets the ESP32 (which re-runs the firmware's SPI register check), listens
for a few seconds, and prints a PASS/FAIL verdict.

Works with the external-wg-test firmware (921600 baud). For the other tests,
pass --baud 115200.

Usage (from this folder):
    ~/.platformio/penv/bin/python check_ads.py
    ~/.platformio/penv/bin/python check_ads.py --port /dev/cu.usbserial-1140 --seconds 6
"""
import argparse
import glob
import re
import sys
import time

import serial  # pyserial (bundled with PlatformIO's Python)

EXPECTED_ID = 0x92  # ADS1298


def find_port():
    ports = sorted(glob.glob("/dev/cu.usbserial*") + glob.glob("/dev/cu.wchusbserial*")
                   + glob.glob("/dev/cu.SLAB_USBtoUART*") + glob.glob("/dev/cu.usbmodem*"))
    if not ports:
        sys.exit("No ESP32 serial port found. Is the board plugged in (UART USB port)?")
    return ports[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None)
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--seconds", type=float, default=4.0)
    args = ap.parse_args()

    port = args.port or find_port()
    print(f"Port: {port} @ {args.baud} baud")

    try:
        s = serial.Serial(port, args.baud, timeout=0.2)
    except serial.SerialException as e:
        sys.exit(f"Could not open {port}: {e}\n"
                 "Close Teleplot / the PlatformIO serial monitor and try again.")

    # Pulse the ESP32's reset line so the firmware boots and re-checks the ADS.
    s.dtr = False
    s.rts = True
    time.sleep(0.1)
    s.rts = False

    buf = b""
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        buf += s.read(4096)
    s.close()

    lines = [l.strip() for l in buf.decode(errors="ignore").splitlines()]

    print("\n--- Register printout from the board ---")
    for l in lines:
        if l and not l.startswith(">") and not re.fullmatch(r"-?\d+(\.\d+)?", l):
            print(l)

    ids = [int(m.group(1), 16) for l in lines if (m := re.search(r"ID\s*=\s*0x([0-9A-Fa-f]+)", l))]
    samples = []
    for l in lines:
        v = l.split(":", 1)[1] if l.startswith(">") and ":" in l else l
        try:
            samples.append(float(v))
        except ValueError:
            pass

    print("\n--- Verdict ---")
    if not ids:
        print("FAIL: no register printout seen. Wrong baud rate or firmware not flashed?")
    elif ids[-1] == EXPECTED_ID:
        print(f"PASS: ADS1298 answered over SPI (ID = 0x{ids[-1]:02X}).")
    else:
        print(f"FAIL: ID = 0x{ids[-1]:02X}, expected 0x{EXPECTED_ID:02X}. "
              "ESP32 can't talk to the ADS1298 (check power, GND, DOUT->GPIO19, PWDN/RESET high).")

    if samples:
        print(f"Samples received: {len(samples)} in ~{args.seconds:.0f} s "
              f"(min {min(samples):.3f}, max {max(samples):.3f} mV, zeros {samples.count(0.0)})")
    else:
        print("Samples received: 0 (ADS never signalled data ready on DRDY).")


if __name__ == "__main__":
    main()
