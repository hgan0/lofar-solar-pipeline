import os
import subprocess
import logging

def run_step1(obsvID, SB_Sun, SB_Calibrator, calibrator_name, model_schema, solint, dir_name):
    """
    Leverages DP3 gaincal routines to solve initial instrumental phase offsets
    and station clock drifts using a stable reference calibrator model source.
    """
    logging.info(f"🔑 Executing Step 1: Solving Direction-Independent Calibrator Parameters ({calibrator_name})")

    working_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}"
    skymodel_path = f"/app/skymodels/{calibrator_name}.skymodel"

    for sb in SB_Calibrator:
        trimmed_ms = os.path.join(working_dir, f"{obsvID}_{sb}_trimmed.MS")

        if not os.path.exists(trimmed_ms):
            continue

        logging.info(f"Extracting gain solutions for station arrays on channel: {sb}")

        dp3_cal_cmd = [
            "DP3",
            f"msin={trimmed_ms}",
            "msout=.",
            "steps=[cal]",
            "cal.type=gaincal",
            f"cal.sourcedb={skymodel_path}",
            f"cal.solint={solint}",
            "cal.caltype=phaseonly",
            f"cal.parmdb={trimmed_ms}/instrument_di.h5"
        ]

        subprocess.run(dp3_cal_cmd, check=True)

    logging.info("✅ Step 1 Instrument Calibration parameters stored cleanly inside local MS headers.")
