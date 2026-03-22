import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy.signal import butter, filtfilt, iirnotch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder


# ============================================================
# 0) OPTIONAL PLOT STYLE
# ============================================================
plt.style.use("default")


# ============================================================
# 1) USER CONFIG
# ============================================================

# Since your script is inside:
# SEMG-HARDWARE/karen_scripts/semg_pipeline.py
# and your data is inside:
# SEMG-HARDWARE/1298EVM-Data-Collection/karen_21-03-26
DATA_DIR = Path("../1298EVM-Data-Collection/karen_21-03-26")
PLOTS_DIR = Path("./plots")

# Sampling rate
FS = 2000  # Hz

# Windowing
WINDOW_SIZE = 400   # 200 ms
STEP_SIZE = 200     # 50% overlap

# Filtering
BANDPASS_LOW = 20   # Hz
BANDPASS_HIGH = 450 # Hz
NOTCH_FREQ = 60     # Hz

# Convert volts to microvolts for plotting and features
CONVERT_TO_UV = True

# Plot settings
PLOT_RAW_VOLTS = True
PLOT_FILTERED_VOLTS = True
PLOT_HISTOGRAM_FILE = True
PLOT_FFT_FILE = True
SAVE_PLOTS = True
SHOW_PLOTS = True

# Train/test split by trial
TRAIN_DEVICES = [0, 1, 2]
TEST_DEVICES = [3, 4, 5]

# Replace these with your real labels if needed
LABEL_MAP = {
    0: "rest",
    1: "fist",
    2: "open",
    3: "rest",
    4: "fist",
    5: "open",
}

# Colors for channels
CHANNEL_COLORS = {
    "CH1": "tab:blue",
    "CH2": "tab:orange",
    "CH3": "tab:green",
    "CH4": "tab:red",
    "CH5": "tab:purple",
    "CH6": "tab:brown",
    "CH7": "tab:pink",
    "CH8": "tab:gray",
}


# ============================================================
# 2) HELPERS FOR FILE DISCOVERY
# ============================================================

@dataclass
class TrialFiles:
    device_id: int
    volts: Path = None
    fft: Path = None
    histogram: Path = None
    analysis: Path = None
    codes: Path = None


def discover_trials(data_dir: Path) -> Dict[int, TrialFiles]:
    pattern = re.compile(r"Device_(\d+)_(Analysis|Codes|FFT|Histogram|Volts)\.txt$", re.IGNORECASE)
    trials: Dict[int, TrialFiles] = {}

    for file in data_dir.glob("Device_*_*.txt"):
        match = pattern.match(file.name)
        if not match:
            continue

        device_id = int(match.group(1))
        kind = match.group(2).lower()

        if device_id not in trials:
            trials[device_id] = TrialFiles(device_id=device_id)

        setattr(trials[device_id], kind, file)

    return trials


# ============================================================
# 3) FILE PARSERS
# ============================================================

def read_volts_file(path: Path) -> pd.DataFrame:
    """
    Reads exported volts data and keeps only valid rows with 8 numeric columns.
    """
    rows = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = re.split(r"\s+", line.replace("\t", " ").strip())

            if len(parts) != 8:
                continue

            try:
                vals = [float(p) for p in parts]
                rows.append(vals)
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"No valid 8-channel voltage rows found in {path}")

    df = pd.DataFrame(rows, columns=[f"CH{i}" for i in range(1, 9)])
    return df


def read_histogram_file(path: Path) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Returns:
        {
            'CH1': (bin_centers, counts),
            ...
        }
    """
    result = {}
    current_ch = None
    numeric_lines = []

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            ch_match = re.fullmatch(r"CH(\d+)", line)
            if ch_match:
                if current_ch is not None and len(numeric_lines) >= 2:
                    x = np.array([float(v) for v in numeric_lines[0].split()])
                    y = np.array([float(v) for v in numeric_lines[1].split()])
                    result[current_ch] = (x, y)
                current_ch = f"CH{ch_match.group(1)}"
                numeric_lines = []
                continue

            if re.search(r"[Ee][+-]?\d+", line):
                numeric_lines.append(line)

        if current_ch is not None and len(numeric_lines) >= 2:
            x = np.array([float(v) for v in numeric_lines[0].split()])
            y = np.array([float(v) for v in numeric_lines[1].split()])
            result[current_ch] = (x, y)

    return result


def read_fft_file(path: Path) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Returns:
        {
            'CH1': (freqs, magnitudes),
            ...
        }
    """
    result = {}

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    i = 0
    while i < len(lines):
        ch_match = re.fullmatch(r"CH(\d+)", lines[i])
        if not ch_match:
            i += 1
            continue

        current_ch = f"CH{ch_match.group(1)}"
        start_freq = None
        increment = None
        values = []

        i += 1
        while i < len(lines):
            if re.fullmatch(r"CH(\d+)", lines[i]):
                break

            if lines[i].startswith("Starting Frequency"):
                start_freq = float(lines[i].split("=")[1].strip())
            elif lines[i].startswith("Increment"):
                increment = float(lines[i].split("=")[1].strip())
            else:
                parts = lines[i].split()
                try:
                    values.extend(float(p) for p in parts)
                except ValueError:
                    pass
            i += 1

        if start_freq is not None and increment is not None and values:
            freqs = start_freq + increment * np.arange(len(values))
            mags = np.array(values)
            result[current_ch] = (freqs, mags)

    return result


# ============================================================
# 4) SIGNAL PROCESSING
# ============================================================

def butter_bandpass_filter(x: np.ndarray, fs: int, low: float, high: float, order: int = 4) -> np.ndarray:
    nyq = 0.5 * fs
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, x)


def notch_filter(x: np.ndarray, fs: int, freq: float = 60.0, q: float = 30.0) -> np.ndarray:
    b, a = iirnotch(w0=freq, Q=q, fs=fs)
    return filtfilt(b, a, x)


def preprocess_multichannel(df: pd.DataFrame, fs: int) -> pd.DataFrame:
    processed = pd.DataFrame(index=df.index)

    for col in df.columns:
        x = df[col].values
        x = notch_filter(x, fs=fs, freq=NOTCH_FREQ)
        x = butter_bandpass_filter(x, fs=fs, low=BANDPASS_LOW, high=BANDPASS_HIGH)
        processed[col] = x

    return processed


# ============================================================
# 5) FEATURE EXTRACTION
# ============================================================

def zero_crossings(x: np.ndarray, threshold: float = 1e-8) -> int:
    x1 = x[:-1]
    x2 = x[1:]
    return int(np.sum(((x1 * x2) < 0) & (np.abs(x1 - x2) >= threshold)))


def slope_sign_changes(x: np.ndarray, threshold: float = 1e-8) -> int:
    diff1 = np.diff(x[:-1])
    diff2 = np.diff(x[1:])
    return int(np.sum(((diff1 * diff2) < 0) & (np.abs(diff1 - diff2) >= threshold)))


def waveform_length(x: np.ndarray) -> float:
    return float(np.sum(np.abs(np.diff(x))))


def mean_absolute_value(x: np.ndarray) -> float:
    return float(np.mean(np.abs(x)))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)))


def extract_features_from_segment(seg: np.ndarray) -> np.ndarray:
    """
    seg shape: [window_size, n_channels]
    Features per channel:
      MAV, RMS, VAR, WL, ZC, SSC
    """
    feat = []

    for ch in range(seg.shape[1]):
        x = seg[:, ch]
        feat.extend([
            mean_absolute_value(x),
            rms(x),
            float(np.var(x)),
            waveform_length(x),
            float(zero_crossings(x)),
            float(slope_sign_changes(x)),
        ])

    return np.array(feat, dtype=float)


def build_segment_dataset(df: pd.DataFrame, window_size: int, step_size: int) -> np.ndarray:
    X = []
    arr = df.values

    for start in range(0, len(arr) - window_size + 1, step_size):
        seg = arr[start:start + window_size, :]
        feat = extract_features_from_segment(seg)
        X.append(feat)

    return np.array(X)


# ============================================================
# 6) VISUALIZATION
# ============================================================

def ensure_plot_dir():
    if SAVE_PLOTS:
        PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def finalize_plot(title: str, xlabel: str, ylabel: str, save_path: Path = None):
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="best", fontsize=9)
    plt.tight_layout()

    if SAVE_PLOTS and save_path is not None:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close()


def plot_multichannel_volts(df: pd.DataFrame, device_id: int, title: str, filename: str):
    t = np.arange(len(df)) / FS

    plt.figure(figsize=(14, 6))
    for col in df.columns:
        plt.plot(
            t,
            df[col].values,
            label=col,
            color=CHANNEL_COLORS.get(col, None),
            linewidth=1
        )

    finalize_plot(
        title=f"{title} (Device {device_id})",
        xlabel="Time (s)",
        ylabel="Voltage (µV)" if CONVERT_TO_UV else "Voltage (V)",
        save_path=PLOTS_DIR / filename
    )


def plot_histogram_data(hist_data: Dict[str, Tuple[np.ndarray, np.ndarray]], device_id: int):
    if not hist_data:
        return

    plt.figure(figsize=(14, 6))

    for ch in sorted(hist_data.keys()):
        x, y = hist_data[ch]

        if CONVERT_TO_UV:
            x = x * 1e6

        plt.plot(
            x,
            y,
            label=ch,
            color=CHANNEL_COLORS.get(ch, None),
            linewidth=1.5
        )

    finalize_plot(
        title=f"Histogram Distribution (Device {device_id})",
        xlabel="Amplitude (µV)" if CONVERT_TO_UV else "Amplitude (V)",
        ylabel="Count",
        save_path=PLOTS_DIR / f"Device_{device_id}_histogram.png"
    )


def plot_fft_data(fft_data: Dict[str, Tuple[np.ndarray, np.ndarray]], device_id: int, max_freq: float = 500):
    if not fft_data:
        return

    plt.figure(figsize=(14, 6))

    for ch in sorted(fft_data.keys()):
        freqs, mags = fft_data[ch]
        mask = freqs <= max_freq

        plt.plot(
            freqs[mask],
            mags[mask],
            label=ch,
            color=CHANNEL_COLORS.get(ch, None),
            linewidth=1.2
        )

    finalize_plot(
        title=f"FFT Spectrum (Device {device_id})",
        xlabel="Frequency (Hz)",
        ylabel="Magnitude",
        save_path=PLOTS_DIR / f"Device_{device_id}_fft.png"
    )


# ============================================================
# 7) MAIN
# ============================================================

def main():
    ensure_plot_dir()

    print("Resolved DATA_DIR:", DATA_DIR.resolve())
    trials = discover_trials(DATA_DIR)

    if not trials:
        raise FileNotFoundError(f"No trial files found in {DATA_DIR.resolve()}")

    print("Discovered devices:", sorted(trials.keys()))

    X_train_list = []
    y_train_list = []
    X_test_list = []
    y_test_list = []

    for device_id in sorted(trials.keys()):
        trial = trials[device_id]

        if trial.volts is None:
            print(f"[WARNING] Device {device_id}: no volts file found, skipped.")
            continue

        if device_id not in LABEL_MAP:
            print(f"[WARNING] Device {device_id}: no label in LABEL_MAP, skipped.")
            continue

        label = LABEL_MAP[device_id]
        print(f"\n=== Processing Device {device_id} | Label: {label} ===")

        # -------------------------
        # Load volts
        # -------------------------
        volts_df = read_volts_file(trial.volts)

        if CONVERT_TO_UV:
            volts_df = volts_df * 1e6

        print(f"Volts shape: {volts_df.shape}")

        # -------------------------
        # Plot raw volts
        # -------------------------
        if PLOT_RAW_VOLTS:
            plot_multichannel_volts(
                volts_df,
                device_id,
                title="Raw sEMG Signal",
                filename=f"Device_{device_id}_raw_volts.png"
            )

        # -------------------------
        # Preprocess
        # -------------------------
        filtered_df = preprocess_multichannel(volts_df, FS)

        # -------------------------
        # Plot filtered volts
        # -------------------------
        if PLOT_FILTERED_VOLTS:
            plot_multichannel_volts(
                filtered_df,
                device_id,
                title="Filtered sEMG Signal",
                filename=f"Device_{device_id}_filtered_volts.png"
            )

        # -------------------------
        # Histogram plot
        # -------------------------
        if PLOT_HISTOGRAM_FILE and trial.histogram is not None:
            try:
                hist_data = read_histogram_file(trial.histogram)
                plot_histogram_data(hist_data, device_id)
            except Exception as e:
                print(f"[WARNING] Could not parse histogram for Device {device_id}: {e}")

        # -------------------------
        # FFT plot
        # -------------------------
        if PLOT_FFT_FILE and trial.fft is not None:
            try:
                fft_data = read_fft_file(trial.fft)
                plot_fft_data(fft_data, device_id)
            except Exception as e:
                print(f"[WARNING] Could not parse FFT for Device {device_id}: {e}")

        # -------------------------
        # Segment -> features
        # -------------------------
        X_trial = build_segment_dataset(filtered_df, WINDOW_SIZE, STEP_SIZE)
        y_trial = np.array([label] * len(X_trial))

        print(f"Extracted segments for Device {device_id}: {len(X_trial)}")

        # -------------------------
        # Train/test split by trial
        # -------------------------
        if device_id in TRAIN_DEVICES:
            X_train_list.append(X_trial)
            y_train_list.append(y_trial)
        elif device_id in TEST_DEVICES:
            X_test_list.append(X_trial)
            y_test_list.append(y_trial)
        else:
            print(f"[INFO] Device {device_id} not in TRAIN_DEVICES or TEST_DEVICES; ignored for modeling.")

    if not X_train_list or not X_test_list:
        raise ValueError("Training or testing data is empty. Check TRAIN_DEVICES / TEST_DEVICES and LABEL_MAP.")

    X_train = np.vstack(X_train_list)
    y_train = np.concatenate(y_train_list)
    X_test = np.vstack(X_test_list)
    y_test = np.concatenate(y_test_list)

    print("\n========== DATASET SUMMARY ==========")
    print("X_train shape:", X_train.shape)
    print("y_train shape:", y_train.shape)
    print("X_test shape :", X_test.shape)
    print("y_test shape :", y_test.shape)

    # -------------------------
    # Encode labels
    # -------------------------
    le = LabelEncoder()
    y_train_enc = le.fit_transform(y_train)
    y_test_enc = le.transform(y_test)

    # -------------------------
    # Train model
    # -------------------------
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )
    clf.fit(X_train, y_train_enc)

    # -------------------------
    # Predict + evaluate
    # -------------------------
    y_pred_enc = clf.predict(X_test)
    y_pred = le.inverse_transform(y_pred_enc)

    print("\n========== RESULTS ==========")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    cm = confusion_matrix(y_test, y_pred, labels=le.classes_)
    cm_df = pd.DataFrame(cm, index=le.classes_, columns=le.classes_)

    print("\nConfusion Matrix:")
    print(cm_df)

    # -------------------------
    # Feature importance
    # -------------------------
    importances = clf.feature_importances_
    feat_names = []
    feature_labels = ["MAV", "RMS", "VAR", "WL", "ZC", "SSC"]

    for ch in range(1, 9):
        for feat_name in feature_labels:
            feat_names.append(f"CH{ch}_{feat_name}")

    feat_imp_df = pd.DataFrame({
        "feature": feat_names,
        "importance": importances
    }).sort_values("importance", ascending=False)

    print("\nTop 20 Feature Importances:")
    print(feat_imp_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()