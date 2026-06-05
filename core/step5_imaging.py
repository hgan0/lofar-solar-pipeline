import os
import subprocess
import logging

def run_imaging(obsvID, SB_Sun, dir_name, size=2048, scale="10asec"):
    """
    Invokes WSClean to perform synthesis Fourier inversions, producing
    high-cadence calibrated FITS output images of solar activity.
    """
    logging.info("📷 Executing Step 5: High-Cadence Synthesis Deconvolution Imaging via WSClean")

    working_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}"
    image_prefix = os.path.join(working_dir, f"images/Sun_flare_DDE_calibrated")
    os.makedirs(os.path.dirname(image_prefix), exist_ok=True)

    # Compile all sub-band files to pass as joint visibility maps
    ms_list = [os.path.join(working_dir, f"{obsvID}_{sb}_trimmed.MS") for sb in SB_Sun]

    wsclean_cmd = [
        "wsclean",
        "-name", image_prefix,
        "-size", str(size), str(size),
        "-scale", scale,
        "-data-column", "CORRECTED_DATA",
        "-niter", "2000",
        "-threshold", "0.005",
        "-weight", "briggs", "0.0",
        "-auto-mask", "3",
        "-multiscale"
    ] + ms_list

    logging.info(f"Launching synthesis imaging inversion loop parameters...")
    subprocess.run(wsclean_cmd, check=True)
    logging.info(f"✅ Step 5 Scientific FITS synthesis images successfully generated under: {os.path.dirname(image_prefix)}")
