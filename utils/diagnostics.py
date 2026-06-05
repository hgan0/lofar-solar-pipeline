import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_peak(data):
    """
    Finds the absolute maximum flux peak value inside the processed data matrix array.
    """
    return np.max(data)

def calculate_bkg(data):
    """
    Isolates statistical mean noise values and computes root-mean-square error
    deviations across designated diagnostic pixel windows.
    """
    normalized_data = np.sqrt(data**2)
    mean = np.nanmean(normalized_data)
    std = np.nanstd(normalized_data)
    return mean, std

def run_snr_assessment(data, signal_window=25, background_slice=(50, 250)):
    """
    Automates the computation of Peak Signal-to-Noise Ratios (SNR) across target
    visibility boxes to evaluate step calibration improvements.
    """
    # Isolate quiet background reference values
    bkg_zone = data[background_slice[0]:background_slice[1], background_slice[0]:background_slice[1]]
    _, bkg_std = calculate_bkg(bkg_zone)

    if bkg_std == 0 or np.isnan(bkg_std):
        logging.warning("Background standard deviation returns invalid or null values. SNR calculation skipped.")
        return 0.0, 0.0, 0.0

    peak_flux = calculate_peak(data)
    calculated_snr = peak_flux / bkg_std

    logging.info(f"📊 Analytics Summary - Peak Flux: {peak_flux:.4e} | Noise RMS: {bkg_std:.4e} | Calculated SNR: {calculated_snr:.2f}")
    return peak_flux, bkg_std, calculated_snr
