import argparse
import time
import csv
from pathlib import Path

import serial
import numpy as np
import matplotlib.pyplot as plt


def extract_number(line: str):
    """
    Extract one numeric value from a serial line.

    Works with lines like:
        123456
        -123456
        29.249672
        code=613410
        code=613410  mV=29.249672

    It returns the first valid number found.
    """
    line = line.strip()

    if not line:
        return None

    # Fast path: line is only a number
    try:
        return float(line)
    except ValueError:
        pass

    # Slower path: extract first number-like token
    tokens = (
        line.replace("=", " ")
        .replace(",", " ")
        .replace(";", " ")
        .split()
    )

    for token in tokens:
        try:
            return float(token)
        except ValueError:
            continue

    return None


def collect_serial(port, baud, duration=None):
    ser = serial.Serial(
        port=port,
        baudrate=baud,
        timeout=0.001,
    )

    # Give the serial port a moment to open.
    time.sleep(0.2)

    # Flush old boot messages / previous data.
    ser.reset_input_buffer()

    print(f"Collecting from {port} at {baud} baud.")
    print("Press Ctrl+C to stop and plot.")

    values = []
    timestamps = []

    buffer = b""
    t0 = time.perf_counter()

    try:
        while True:
            now = time.perf_counter()

            if duration is not None and (now - t0) >= duration:
                break

            # Read whatever is available. Avoid blocking when possible.
            n_waiting = ser.in_waiting

            if n_waiting:
                chunk = ser.read(n_waiting)
            else:
                chunk = ser.read(256)

            if not chunk:
                continue

            buffer += chunk

            # Split complete lines only. Keep last partial line in buffer.
            lines = buffer.split(b"\n")
            buffer = lines[-1]

            for raw_line in lines[:-1]:
                t = time.perf_counter() - t0

                try:
                    line = raw_line.decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    continue

                value = extract_number(line)

                if value is None:
                    continue

                # Discard zero / near-zero values
                if abs(value) < 1e-6:
                    print("Sikkping 0 values")
                    continue

                timestamps.append(t)
                values.append(value)

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        ser.close()

    return np.array(timestamps), np.array(values)


def save_csv(path, timestamps, values):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "raw_value"])

        for t, v in zip(timestamps, values):
            writer.writerow([f"{t:.9f}", f"{v:.9f}"])


def plot_values(timestamps, values, input_unit):
    if len(values) == 0:
        print("No numeric samples collected.")
        return

    fig, ax = plt.subplots()

    ax.plot(timestamps, values)

    ax.set_xlabel("Time [s]")
    ax.set_ylabel(input_unit)
    ax.set_title("ADS1298 captured serial values")
    ax.grid(True)

    sample_count = len(values)
    total_time = timestamps[-1] - timestamps[0] if sample_count > 1 else 0.0

    if total_time > 0:
        fs_est = (sample_count - 1) / total_time
        print(f"Collected samples: {sample_count}")
        print(f"Duration: {total_time:.3f} s")
        print(f"Estimated sample rate: {fs_est:.2f} samples/s")
    else:
        print(f"Collected samples: {sample_count}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Collect ADS serial values with minimal overhead, then plot after stopping."
    )

    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, e.g. COM5, /dev/ttyUSB0, /dev/cu.usbmodemXXXX",
    )

    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate. Default: 115200",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Optional recording duration in seconds. If omitted, use Ctrl+C to stop.",
    )

    parser.add_argument(
        "--csv",
        default="ads_capture.csv",
        help="CSV output filename. Default: ads_capture.csv",
    )

    parser.add_argument(
        "--unit",
        default="Raw value",
        help="Y-axis label. Use 'ADC code' or 'mV' depending on what Arduino prints.",
    )

    args = parser.parse_args()

    timestamps, values = collect_serial(
        port=args.port,
        baud=args.baud,
        duration=args.duration,
    )

    output_path = Path(args.csv)
    save_csv(output_path, timestamps, values)

    print(f"Saved CSV to: {output_path.resolve()}")

    plot_values(timestamps, values, args.unit)


if __name__ == "__main__":
    main()