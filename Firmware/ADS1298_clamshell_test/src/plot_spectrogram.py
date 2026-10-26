import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, butter, filtfilt

# Usage:
# python plot_spectrogram.py data.csv

csv_path = sys.argv[1]

df = pd.read_csv(csv_path)

# Take first column as time, second column as signal
t = df.iloc[:, 0].to_numpy()
x = df.iloc[:, 1].to_numpy()

# Estimate sampling frequency from time column
dt = np.mean(np.diff(t))
fs_estimated = 1.0 / dt

# Override if you know it is 500 SPS
fs = 1000

print(f"Estimated fs: {fs_estimated:.2f} Hz")
print(f"Using fs: {fs:.2f} Hz")

# Remove DC offset
x = x - np.mean(x)


def highpass_filter(x, fs, cutoff_hz, order=4):
    nyquist = fs / 2

    if cutoff_hz <= 0:
        return x

    if cutoff_hz >= nyquist:
        raise ValueError(
            f"High-pass cutoff must be below Nyquist frequency. "
            f"cutoff={cutoff_hz} Hz, Nyquist={nyquist} Hz"
        )

    b, a = butter(
        order,
        cutoff_hz,
        btype="highpass",
        fs=fs
    )

    return filtfilt(b, a, x)


# High-pass filter
#hp_cutoff = 50  # Hz, try 50, 80, 100, or 150
#x_filtered = highpass_filter(x, fs, hp_cutoff, order=4)

# Compute spectrogram
f, tt, Sxx = spectrogram(
    x,
    fs=fs,
    window="hann",
    nperseg=256,
    noverlap=128,
    scaling="density",
    mode="magnitude"
)

# Plot in dB
Sxx_db = 20 * np.log10(Sxx + 1e-12)

plt.figure()
plt.pcolormesh(tt, f, Sxx_db, shading="gouraud")
plt.colorbar(label="Magnitude [dB]")
plt.xlabel("Time [s]")
plt.ylabel("Frequency [Hz]")
plt.title(f"Spectrogram")
plt.ylim(0, 500)
plt.tight_layout()
plt.show()