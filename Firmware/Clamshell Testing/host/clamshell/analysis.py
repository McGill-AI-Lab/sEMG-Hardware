"""
==============================================================================
 analysis.py  —  the signal-processing maths, free of any plotting or I/O
==============================================================================

Every function takes NumPy arrays and returns plain numbers or arrays, so it
can be tested and reused on its own. The physics behind each one is in
clamshell_validation.md (section numbers given in the docstrings).

LIBRARIES USED
--------------
- NumPy: arrays, statistics (mean, std, percentile), least squares.
- SciPy:
    scipy.signal.welch       power spectral density by Welch's method
                             (average the FFTs of overlapping, windowed segments)
    scipy.signal.coherence   magnitude-squared coherence between two signals
    scipy.signal.find_peaks  locate local maxima in a 1-D array
    scipy.ndimage.median_filter   running median, used as a robust "noise floor"
    scipy.optimize.nnls      least squares with the constraint "all results >= 0"
    scipy.signal.butter / sosfiltfilt   design a Butterworth filter / apply it with zero phase
==============================================================================
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import median_filter
from scipy.optimize import nnls
from scipy.signal import butter, coherence, find_peaks, sosfiltfilt, welch

# Verdict words used everywhere. Order matters: later = worse.
PASS, INFO, WARN, FAIL, SKIP = "PASS", "INFO", "WARN", "FAIL", "SKIP"
_SEVERITY = {SKIP: 0, INFO: 1, PASS: 2, WARN: 3, FAIL: 4}       # how bad each verdict is


def worst(verdicts) -> str:
    """Return the most severe verdict in a list (FAIL > WARN > PASS > INFO > SKIP)."""
    verdicts = [v for v in verdicts if v]                       # ignore empty entries
    if not verdicts:                                            # nothing to judge
        return SKIP
    return max(verdicts, key=lambda v: _SEVERITY.get(v, 0))     # highest severity wins


# ---------------------------------------------------------------------------
# Section 0 / Experiment A: time-domain noise statistics
# ---------------------------------------------------------------------------
def noise_stats(x_uV: np.ndarray) -> dict:
    """
    Offset, RMS, peak-to-peak and pp/rms of one channel (input-referred uV).

    - offset = mean: the DC error of the channel (datasheet "Offset error").
    - rms    = standard deviation after removing the mean.
    - pp     = max - min after removing the mean.
    - pp/rms : for pure Gaussian noise about 6.6 (99.9 % of samples fall
               inside +/-3.3 sigma). With many thousands of samples the
               expected max-min grows to ~7.5-8, so we warn above 8.
    """
    offset = float(np.mean(x_uV))                               # average value
    y = x_uV - offset                                           # remove it
    rms = float(np.std(y))                                      # root-mean-square of what is left
    pp = float(np.max(y) - np.min(y)) if len(y) else 0.0        # full spread
    return {"offset_uV": offset, "rms_uV": rms, "pp_uV": pp, "pp_rms": pp / rms if rms > 0 else float("nan"),
            "n": int(len(y)), "pp_rms_gauss": gaussian_pp_rms(len(y))}


def gaussian_pp_rms(n: int) -> float:
    """
    Typical pp/rms of n samples of PURE Gaussian noise.

    The 6.6 figure in the plan (99.9 % of samples inside +/-3.3 sigma) is for
    a "typical" spread. But the more samples you take, the further the single
    largest and smallest ones reach: the extreme of n Gaussian samples sits
    near the (1 - 1/(2n)) quantile. So max - min is about
        2 * Phi^-1(1 - 1/(2n))     (Phi^-1 = inverse normal CDF, scipy norm.ppf)
    which is ~6.4 for 1 500 samples and ~8.1 for 40 000. Comparing against
    this (times a margin) avoids false "spiky" warnings at high data rates.
    """
    from scipy.stats import norm                                # inverse normal CDF
    if n < 2:                                                   # not meaningful
        return float("nan")
    return float(2 * norm.ppf(1 - 1 / (2 * n)))                 # expected range in units of sigma


def is_spiky(stats: dict, margin: float) -> bool:
    """True if pp/rms exceeds the pure-Gaussian expectation by more than `margin` (e.g. 1.3 = 30 %)."""
    return bool(stats["pp_rms"] > margin * stats["pp_rms_gauss"])   # NaN compares False -> not spiky


# ---------------------------------------------------------------------------
# Experiment B: spectrum
# ---------------------------------------------------------------------------
def welch_asd(x_uV: np.ndarray, fs: float):
    """
    Amplitude spectral density in uV/sqrt(Hz) by Welch's method.

    Segment length: the largest power of two that still gives >= 8 averaged
    segments with 50 % overlap (clamshell_validation.md, section 3), but at
    most fs * 4 samples (0.25 Hz resolution is plenty).
    With 50 % overlap, K segments of length L cover N = (K + 1) * L / 2
    samples, so K >= 8 needs L <= 2N / 9.
    """
    n = len(x_uV)                                               # number of samples
    max_len = max(16, min(int(2 * n / 9), int(fs * 4)))         # length limit from the rules above
    nperseg = 2 ** int(np.floor(np.log2(max_len)))              # round down to a power of two (fast FFT)
    f, psd = welch(x_uV - np.mean(x_uV), fs=fs, window="hann", nperseg=nperseg,
                   noverlap=nperseg // 2, scaling="density")    # PSD in uV^2/Hz, one-sided
    return f, np.sqrt(psd)                                      # ASD = sqrt(PSD), uV/sqrt(Hz)


def white_floor(f: np.ndarray, asd: np.ndarray, fs: float) -> float:
    """
    The "flat" noise floor in uV/sqrt(Hz): median ASD between 5 Hz and 0.25 x fs
    (inside the filter passband, above 1/f noise). The median ignores the
    occasional spectral line.
    """
    band = (f >= 5) & (f <= 0.25 * fs)                          # mask for the flat region
    return float(np.median(asd[band])) if band.any() else float("nan")


def one_over_f_corner(f: np.ndarray, asd: np.ndarray, floor: float) -> float | None:
    """
    Approximate 1/f corner: the highest frequency below 20 Hz where the
    smoothed ASD is still above sqrt(2) x the white floor (that is, where the
    low-frequency noise POWER equals the white noise power). None if the
    spectrum never rises that much.
    """
    low = (f > 0) & (f < 20)                                    # look only below 20 Hz
    if not low.any() or not np.isfinite(floor):                 # nothing to look at
        return None
    sm = median_filter(asd[low], size=5)                        # smooth out the randomness a little
    above = np.nonzero(sm > np.sqrt(2) * floor)[0]              # indices above the threshold
    if len(above) == 0:                                         # never above
        return None
    return float(f[low][above[-1]])                             # highest such frequency


def find_lines(f: np.ndarray, asd: np.ndarray, min_excess_db: float = 10.0, fmin: float = 1.0,
               max_lines: int = 8) -> list[dict]:
    """
    Find narrow spectral lines that stick out of the local noise floor.

    Method: the local floor is a running median over ~41 bins. A line is a
    local maximum at least `min_excess_db` above that floor. Returns up to
    `max_lines` lines, strongest first, each as
    {"f_hz", "asd_uV", "excess_db"}.
    """
    keep = f >= fmin                                            # ignore DC and the 1/f region
    f, asd = f[keep], asd[keep]                                 # trimmed arrays
    if len(asd) < 50:                                           # too short to judge
        return []
    db = 20 * np.log10(np.maximum(asd, 1e-12))                  # amplitude -> dB (avoid log(0))
    floor_db = median_filter(db, size=41, mode="nearest")       # local floor in dB
    excess = db - floor_db                                      # how far above the floor each bin is
    peaks, _ = find_peaks(excess, height=min_excess_db, distance=3)   # local maxima above the threshold
    order = np.argsort(excess[peaks])[::-1][:max_lines]         # strongest first
    return [{"f_hz": float(f[peaks[i]]), "asd_uV": float(asd[peaks[i]]), "excess_db": float(excess[peaks[i]])}
            for i in order]


def label_line(f_hz: float, mains_hz: float, fs: float, tol: float = 1.0) -> str:
    """
    Suggest a likely cause for a spectral line (clamshell_validation.md, table
    in section 3): mains harmonic, USB start-of-frame (1 kHz), WiFi beacon
    (~9.77 Hz), or "unknown".
    """
    k = round(f_hz / mains_hz)                                  # nearest mains harmonic number
    if k >= 1 and abs(f_hz - k * mains_hz) <= tol:              # close to it?
        return f"mains x{k}" if k > 1 else "mains"
    if abs(f_hz - 1000) <= 2 or abs(f_hz - (fs - 1000)) <= 2:   # USB SOF or its alias
        return "USB 1 kHz?"
    beacon = 1 / 0.1024                                         # 102.4 ms beacon interval = 9.766 Hz
    kb = round(f_hz / beacon)                                   # nearest beacon harmonic
    if kb >= 1 and abs(f_hz - kb * beacon) <= 0.3:              # close to it?
        return "WiFi beacon?"
    return "unknown"


# ---------------------------------------------------------------------------
# Experiment C: gain sweep model fit
# ---------------------------------------------------------------------------
def fit_gain_model(gains, rms_in_uV) -> dict:
    """
    Fit  v_in^2 = e_PGA^2 + (e_ADC / G)^2  (clamshell_validation.md, section 0).

    Rewrite as a straight line in the unknowns a = e_PGA^2 and b = e_ADC^2:
        v_in^2 = a * 1 + b * (1 / G^2)
    and solve with non-negative least squares (noise powers cannot be
    negative). Returns e_pga_uV (input-referred PGA noise), e_adc_uV
    (ADC noise at the modulator input, i.e. output-referred), and the model
    prediction for each gain.
    """
    g = np.asarray(gains, dtype=float)                          # gains as floats
    v = np.asarray(rms_in_uV, dtype=float)                      # measured input-referred rms
    A = np.column_stack([np.ones_like(g), 1 / g**2])            # design matrix: columns for a and b
    (a, b), _ = nnls(A, v**2)                                   # solve, a and b >= 0
    pred = np.sqrt(a + b / g**2)                                # model curve at each gain
    return {"e_pga_uV": float(np.sqrt(a)), "e_adc_uV": float(np.sqrt(b)), "pred_uV": pred}


# ---------------------------------------------------------------------------
# Experiment D: data-rate scaling
# ---------------------------------------------------------------------------
def rate_exponent(rates, rms) -> float:
    """
    Slope of log(rms) against log(rate). White noise gives 0.5 (rms grows as
    sqrt(bandwidth)); more than ~0.6 means extra high-frequency interference.
    """
    r = np.log(np.asarray(rates, float))                        # log of rates
    y = np.log(np.asarray(rms, float))                          # log of rms values
    if len(r) < 2:                                              # need at least two points
        return float("nan")
    return float(np.polyfit(r, y, 1)[0])                        # slope of the best straight line


# ---------------------------------------------------------------------------
# Experiment E: correlation between channels
# ---------------------------------------------------------------------------
def correlation_summary(X_uV: np.ndarray, fs: float, highpass_hz: float = 1.0) -> dict:
    """
    X_uV: (N, k) channels. They are first high-pass filtered at `highpass_hz`
    (2nd-order Butterworth, run forwards and backwards with filtfilt so no
    phase shift is added). Why: slow 1/f wander contains very few independent
    samples, so two unrelated channels can show a large correlation by pure
    chance. Above 1 Hz the estimate is stable, and that is the band sEMG uses.
    Returns
      corr       : k x k Pearson correlation matrix
      max_abs_r  : largest |r| off the diagonal
      avg_ratio  : RMS(channel average) / (mean sigma / sqrt(k)).
                   ~1 = independent noise, ~sqrt(k) = fully shared noise.
      f, coh     : mean coherence over all channel pairs vs frequency
    """
    X = X_uV - X_uV.mean(axis=0)                                # remove each column's mean
    if highpass_hz and highpass_hz > 0:                         # remove slow wander
        n = len(X)                                              # samples
        sos = butter(2, highpass_hz, btype="highpass", fs=fs, output="sos")   # filter coefficients
        pad = min(n - 1, int(3 * fs / highpass_hz))             # mirror-extend the ends by ~3 filter time constants
        X = sosfiltfilt(sos, X, axis=0, padlen=pad)             # zero-phase filtering, column by column
        trim = min(int(0.5 * fs / highpass_hz), n // 6)         # the filter's start/end transients have the SAME
        X = X[trim:n - trim]                                    # shape on every channel -> fake correlation; cut them
    k = X.shape[1]                                              # number of channels
    corr = np.corrcoef(X, rowvar=False)                         # columns are variables
    off = corr[~np.eye(k, dtype=bool)]                          # off-diagonal values
    sig = X.std(axis=0)                                         # per-channel sigma
    avg_ratio = float(X.mean(axis=1).std() / (sig.mean() / np.sqrt(k)))   # see docstring
    nper = 2 ** int(np.floor(np.log2(max(64, min(len(X) // 8, fs * 2)))))   # segment length for coherence
    cohs = []                                                   # coherence of each pair
    for i in range(k):
        for j in range(i + 1, k):
            f, c = coherence(X[:, i], X[:, j], fs=fs, nperseg=nper)   # magnitude-squared coherence
            cohs.append(c)
    coh = np.mean(cohs, axis=0) if cohs else None               # average over pairs
    return {"corr": corr, "max_abs_r": float(np.max(np.abs(off))) if len(off) else 0.0,
            "avg_ratio": avg_ratio, "f": f if cohs else None, "coh": coh}


# ---------------------------------------------------------------------------
# Experiment G: square-wave test signal
# ---------------------------------------------------------------------------
def square_wave_stats(x_uV: np.ndarray, fs: float, guard: int = 5) -> dict | None:
    """
    Measure amplitude, midpoint, plateau noise and period of a square wave.

    Steps (clamshell_validation.md, section 8):
      1. threshold half-way between the 5th and 95th percentiles,
      2. each sample is "high" or "low"; an edge is where that changes,
      3. drop `guard` samples on each side of every edge (filter settling),
      4. amplitude = mean(high) - mean(low); midpoint = their average,
      5. period = median spacing of rising edges, using linear
         interpolation of the threshold crossing for sub-sample precision.
    Returns None if fewer than 3 rising edges were found.
    """
    lo, hi = np.percentile(x_uV, [5, 95])                       # rough low and high levels
    thr = (lo + hi) / 2                                         # threshold in between
    state = x_uV > thr                                          # True = high
    change = np.nonzero(np.diff(state.astype(np.int8)))[0]      # index BEFORE each edge
    mask = np.ones(len(x_uV), dtype=bool)                       # samples usable for plateaus
    for e in change:                                            # around every edge ...
        mask[max(0, e - guard + 1):e + guard + 1] = False       # ... mark guard samples as unusable
    high, low = x_uV[state & mask], x_uV[~state & mask]         # plateau samples
    rising = [e for e in change if not state[e] and state[e + 1]]   # low -> high transitions
    if len(rising) < 3 or len(high) < 10 or len(low) < 10:      # not enough to measure
        return None
    cross = np.array([e + (thr - x_uV[e]) / (x_uV[e + 1] - x_uV[e]) for e in rising])   # fractional crossing index
    periods = np.diff(cross) / fs                               # seconds between rising edges
    return {
        "amplitude_uV": float(high.mean() - low.mean()),        # high minus low
        "midpoint_uV": float((high.mean() + low.mean()) / 2),   # offset of the wave
        "std_high_uV": float(high.std()), "std_low_uV": float(low.std()),   # plateau noise
        "period_s": float(np.median(periods)),                  # typical period
        "period_jitter_s": float(np.std(periods)),              # spread of periods
        "n_edges": int(len(rising)),                            # how many rising edges were seen
    }


# ---------------------------------------------------------------------------
# Experiment I: Allan deviation
# ---------------------------------------------------------------------------
def allan_deviation(x: np.ndarray, fs: float, points_per_decade: int = 8):
    """
    Overlapping Allan deviation of x (Allan, 1966).

    For an averaging time tau = m / fs: average x over consecutive blocks of m
    samples, then sigma(tau)^2 = 0.5 * mean((next block - this block)^2).
    Computed with a cumulative sum so every overlapping block average costs
    O(1). Slope on a log-log plot: -1/2 white noise (averaging helps),
    0 flicker noise, > 0 drift (averaging longer makes it worse).
    """
    n = len(x)                                                  # samples
    c = np.concatenate([[0.0], np.cumsum(x - np.mean(x))])      # cumulative sum, starts at 0
    m_max = n // 4                                              # need several blocks for a stable estimate
    ms = np.unique(np.logspace(0, np.log10(max(1, m_max)), points_per_decade * 6).astype(int))   # block sizes
    taus, adev = [], []                                         # results
    for m in ms:                                                # each block size
        if 2 * m >= n:                                          # need two blocks
            break
        avg = (c[m:] - c[:-m]) / m                              # all overlapping block averages
        d = avg[m:] - avg[:-m]                                  # difference of neighbouring blocks
        taus.append(m / fs)                                     # tau in seconds
        adev.append(np.sqrt(0.5 * np.mean(d**2)))               # Allan deviation
    return np.array(taus), np.array(adev)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def block_means(x: np.ndarray, block: int) -> np.ndarray:
    """Average x in consecutive non-overlapping blocks of `block` samples (drops the remainder)."""
    k = len(x) // block                                         # number of full blocks
    return x[:k * block].reshape(k, block).mean(axis=1)         # reshape to (k, block) and average rows


def johnson_noise_uV(r_ohm: float, bandwidth_hz: float, temp_k: float = 300.0) -> float:
    """Thermal noise of a resistor: sqrt(4 k T R B) (Johnson 1928, Nyquist 1928), in uVrms."""
    k_b = 1.380649e-23                                          # Boltzmann constant, J/K
    return float(np.sqrt(4 * k_b * temp_k * r_ohm * bandwidth_hz) * 1e6)
