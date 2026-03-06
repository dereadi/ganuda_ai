import numpy as np
from scipy import signal
from typing import List, Tuple

def load_spectral_data(file_path: str) -> np.ndarray:
    """
    Load spectral data from a file.
    
    :param file_path: Path to the spectral data file.
    :return: Numpy array containing the spectral data.
    """
    return np.loadtxt(file_path)

def compute_power_spectrum(data: np.ndarray, fs: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the power spectrum of the given data.
    
    :param data: Input data array.
    :param fs: Sampling frequency.
    :return: Frequencies and corresponding power spectrum.
    """
    f, Pxx = signal.welch(data, fs, nperseg=1024)
    return f, Pxx

def find_peaks(frequencies: np.ndarray, power_spectrum: np.ndarray, threshold: float) -> List[Tuple[float, float]]:
    """
    Find peaks in the power spectrum above a given threshold.
    
    :param frequencies: Array of frequencies.
    :param power_spectrum: Array of power spectrum values.
    :param threshold: Peak detection threshold.
    :return: List of tuples (frequency, power) for detected peaks.
    """
    peaks, _ = signal.find_peaks(power_spectrum, height=threshold)
    return [(frequencies[p], power_spectrum[p]) for p in peaks]

def filter_spectral_data(data: np.ndarray, lowcut: float, highcut: float, fs: float, order: int = 5) -> np.ndarray:
    """
    Apply a bandpass filter to the spectral data.
    
    :param data: Input data array.
    :param lowcut: Lower cutoff frequency.
    :param highcut: Higher cutoff frequency.
    :param fs: Sampling frequency.
    :param order: Filter order.
    :return: Filtered data.
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.lfilter(b, a, data)

def save_spectral_data(file_path: str, data: np.ndarray) -> None:
    """
    Save spectral data to a file.
    
    :param file_path: Path to save the spectral data.
    :param data: Numpy array containing the spectral data.
    """
    np.savetxt(file_path, data)