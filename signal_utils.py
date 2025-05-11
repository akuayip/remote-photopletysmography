# signal_utils.py

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def bandpass_filter(data, fs=30, low=0.9, high=2.4, order=3):
    b, a = butter(order, [low, high], btype='band', fs=fs)
    return filtfilt(b, a, data)

def calculate_heart_rate(signal, fs=30):
    signal = (signal - np.mean(signal)) / np.std(signal)
    peaks, _ = find_peaks(signal, prominence=0.5)
    bpm = 60 * len(peaks) / (len(signal) / fs)
    return bpm, peaks
