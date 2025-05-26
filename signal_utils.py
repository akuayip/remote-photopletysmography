# signal_utils.py

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, savgol_filter

# ==========================================
# FILTERS
# ==========================================


def bandpass_filter_rppg(data, fs=30, low=0.9, high=2.4, order=3):
    """
    Bandpass filter for rPPG signal (heart rate domain).
    Default: 54–144 bpm (0.9–2.4 Hz)
    """
    b, a = butter(order, [low, high], btype='band', fs=fs)
    return filtfilt(b, a, data)


def bandpass_filter_respirasi(data, fs=30, low=0.2, high=0.33, order=3):
    """
    Bandpass filter for respiration signal (shoulder movement domain).
    Default: 12–20 breaths/min (0.2–0.33 Hz)
    """
    b, a = butter(order, [low, high], btype='band', fs=fs)
    return filtfilt(b, a, data)

# ==========================================
# HEART & RESPIRATION RATE CALCULATION
# ==========================================


def calculate_heart_rate(signal, fs=30, prominence=0.5):
    """
    Calculate heart rate (BPM) from filtered rPPG signal.
    """
    signal = normalize_signal(signal)
    peaks, _ = find_peaks(signal, prominence=prominence)
    duration_sec = len(signal) / fs
    bpm = 60 * len(peaks) / duration_sec
    return bpm, peaks


def calculate_respiration_rate(signal, fs=30, prominence=0.1):
    """
    Calculate respiration rate (RR) in breaths per minute from filtered signal.
    """
    signal = normalize_signal(signal)
    peaks, _ = find_peaks(signal, prominence=prominence)
    duration_sec = len(signal) / fs
    rr = 60 * len(peaks) / duration_sec
    return rr, peaks

# ==========================================
# UTILITY
# ==========================================


def normalize_signal(signal):
    """
    Normalize signal to zero mean and unit variance.
    """
    signal = np.array(signal)
    return (signal - np.mean(signal)) / (np.std(signal) + 1e-8)


def smooth_signal(signal, window=11, polyorder=2):
    """
    Smooth signal using Savitzky-Golay filter.
    Use only if len(signal) >= window.
    """
    if len(signal) >= window:
        return savgol_filter(signal, window_length=window, polyorder=polyorder)
    return signal