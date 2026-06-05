import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_step0(date_str, tstart, tstop, obsvID, obsvID2, pointings, SB_Sun, SB_Calibrator, calibrator_name, dir_name):
    """
    Executes raw data truncation windows, masks out RFI anomalies, and isolates
    the active solar flare observation timeline segments.
    """
    logging.info(f"⏳ Executing Step 0: Initial Data Selection and Truncation for {obsvID}")

    base_scratch = f"/net/zernike/scratch3/hgan/processed/{obsvID}"
    output_dir = os.path.join(base_scratch, dir_name)
    os.makedirs(output_dir, exist_ok=True)

    # Example translation of your DP3 script execution loop
    for sb in SB_Sun:
        ms_name = f"{obsvID}_{sb}_raw.MS"
        ms_path = f"/net/zernike/scratch3/hgan/raw/{obsvID}/{ms_name}"
        out_ms_path = os.path.join(output_dir, f"{obsvID}_{sb}_trimmed.MS")

        if not os.path.exists(ms_path):
            logging.warning(f"Skipping missing Measurement Set: {ms_path}")
            continue

        logging.info(f"Slicing MS visibility sub-band matrix: {sb}")

        # Constructing inline DP3 command array parameters dynamically
        dp3_cmd = [
            "DP3",
            f"msin={ms_path}",
            f"msout={out_ms_path}",
            "steps=[count,flag,count]",
            f"msin.starttime={date_str}/{tstart}",
            f"msout.storagemanager=lofarstman",
            "flag.type=preflagger",
            "flag.baseline=[CS*&CS*, RS*&RS*]"
        ]

        try:
            subprocess.run(dp3_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            logging.error(f"DP3 process failure on sub-band {sb}: {e.stderr.decode()}")
            raise e

    logging.info("✅ Step 0 Pre-processing configuration execution sequence finished successfully.")
